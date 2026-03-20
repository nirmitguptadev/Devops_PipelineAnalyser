import sqlite3
import json
from datetime import datetime
from typing import Dict, List


class Database:
    def __init__(self, db_path="pipeline_analyzer.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                root_cause TEXT,
                severity TEXT,
                error_lines TEXT,
                recommendations TEXT,
                ci_platform TEXT DEFAULT 'jenkins',
                ai_insights TEXT,
                troubleshooting TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS build_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                build_number INTEGER NOT NULL,
                result TEXT NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_name, build_number)
            )
        """
        )

        conn.commit()
        conn.close()

    def save_analysis(self, result: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Prevent race condition duplicates between webhook & scheduler
        cursor.execute(
            "SELECT COUNT(*) FROM failures WHERE pipeline_name = ?",
            (result["pipeline_name"],),
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        cursor.execute(
            """
            INSERT INTO failures (pipeline_name, timestamp, category, root_cause, 
                                severity, error_lines, recommendations, ci_platform, ai_insights, troubleshooting)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result["pipeline_name"],
                result["timestamp"],
                result["category"],
                result["root_cause"],
                result["severity"],
                json.dumps(result["error_lines"]),
                json.dumps(result["recommendations"]),
                result.get("ci_platform", "jenkins"),
                result.get("ai_insights"),
                json.dumps(result.get("troubleshooting", [])),
            ),
        )

        conn.commit()
        conn.close()

    def get_recent_failures(self, limit: int = 50, after_id: int = 0) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM failures
            WHERE id > ?
            ORDER BY created_at DESC 
            LIMIT ?
        """,
            (after_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def is_build_analyzed(self, pipeline_name: str, build_number: int) -> bool:
        """Check if a build has already been analyzed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # In the context of our ingestors, pipeline_name usually doesn't have the build number appended yet
        # However, to be completely safe against different pipeline formats:
        full_pipeline_name = f"{pipeline_name}#{build_number}"

        cursor.execute(
            """
            SELECT COUNT(*) FROM failures 
            WHERE pipeline_name = ? AND timestamp > datetime('now', '-7 days')
        """,
            (full_pipeline_name,),
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def record_build(self, job_name: str, build_number: int, result: str):
        """Record a build seen during polling (for success rate calculation)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO build_stats (job_name, build_number, result) VALUES (?, ?, ?)",
            (job_name, build_number, result),
        )
        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM failures")
        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT category, COUNT(*) as count 
            FROM failures 
            GROUP BY category
        """
        )
        by_category = dict(cursor.fetchall())

        cursor.execute(
            """
            SELECT severity, COUNT(*) as count 
            FROM failures 
            GROUP BY severity
        """
        )
        by_severity = dict(cursor.fetchall())

        # Get weekly trend
        cursor.execute(
            """
            SELECT 
                date(created_at) as day,
                COUNT(*) as count
            FROM failures
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY day
        """
        )
        weekly_trend = dict(cursor.fetchall())

        # Avg MTTR: average minutes between failure timestamp and analysis (created_at)
        cursor.execute(
            """
            SELECT AVG(
                (julianday(created_at) - julianday(timestamp)) * 1440
            ) FROM failures
            WHERE timestamp IS NOT NULL AND created_at IS NOT NULL
        """
        )
        avg_mttr_minutes = cursor.fetchone()[0]

        # Success rate from build_stats
        cursor.execute("SELECT COUNT(*) FROM build_stats")
        total_builds = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM build_stats WHERE result NOT IN ('SUCCESS', 'success')")
        failed_builds = cursor.fetchone()[0]

        if total_builds > 0:
            success_rate = round((total_builds - failed_builds) / total_builds * 100, 1)
        else:
            success_rate = None

        conn.close()

        return {
            "total_failures": total,
            "by_category": by_category,
            "by_severity": by_severity,
            "weekly_trend": weekly_trend,
            "avg_mttr_minutes": round(avg_mttr_minutes, 1) if avg_mttr_minutes else None,
            "success_rate": success_rate,
        }
