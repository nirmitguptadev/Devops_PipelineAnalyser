import threading
import time
import logging
from jenkins_integration import JenkinsIntegration
from analyzer import PipelineAnalyzer
from database import Database

logger = logging.getLogger(__name__)


class IngestionScheduler:
    def __init__(
        self,
        jenkins_url: str,
        username: str,
        api_token: str,
        poll_interval: int = 10,
        groq_analyzer=None,
    ):
        self.jenkins = JenkinsIntegration(jenkins_url, username, api_token)
        self.analyzer = PipelineAnalyzer()
        self.db = Database()
        self.poll_interval = poll_interval
        self.groq_analyzer = groq_analyzer
        self.running = False
        self.thread = None

        # Store the exact time the scheduler was initialized
        # Only fetch Jenkins builds that fail AFTER the application boot
        from datetime import datetime, timezone

        self.startup_time = int(datetime.now(timezone.utc).timestamp() * 1000)

    def start(self):
        """Start the background polling thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started Jenkins polling every {self.poll_interval} seconds")

    def stop(self):
        """Stop the background polling thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stopped Jenkins polling")

    def _poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                self._poll_and_analyze()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

            time.sleep(self.poll_interval)

    def _poll_and_analyze(self):
        """Poll Jenkins and analyze failed builds"""
        logger.info("Starting Jenkins poll...")

        try:
            failed_builds = self.jenkins.poll_all_jobs(limit_per_job=5)

            if not failed_builds:
                logger.info("No failed builds found")
                return

            analyzed_count = 0
            for build in failed_builds:
                try:
                    # Ignore historical builds - only analyze failures that occur AFTER the dashboard spins up
                    if build.get("timestamp", 0) < self.startup_time:
                        continue

                    # Check if already analyzed
                    if self.db.is_build_analyzed(
                        build["job_name"], build["build_number"]
                    ):
                        logger.debug(
                            f"Skipping already analyzed: {build['job_name']}#{build['build_number']}"
                        )
                        continue

                    # Analyze the build
                    pipeline_name = f"{build['job_name']}#{build['build_number']}"
                    result = self.analyzer.analyze(build["console_log"], pipeline_name)

                    # Add build metadata
                    result["build_number"] = build["build_number"]
                    result["jenkins_status"] = build["result"]
                    result["ci_platform"] = "jenkins"

                    # Add AI insights if available
                    try:
                        groq = self.groq_analyzer
                        if groq and groq.enabled:
                            ai_result = groq.analyze_failure(
                                build["console_log"],
                                result["category"],
                                result["error_lines"],
                            )
                            if ai_result:
                                result["ai_insights"] = ai_result.get("summary", "")
                                result["troubleshooting"] = ai_result.get(
                                    "troubleshooting", []
                                )
                                logger.info(f"AI analysis added for {pipeline_name}")
                    except Exception as e:
                        logger.warning(f"AI analysis failed for {pipeline_name}: {e}")

                    # Save to database
                    self.db.save_analysis(result)
                    analyzed_count += 1
                    logger.info(
                        f"✅ Analyzed and saved: {pipeline_name} - {result['category']} ({result['severity']})"
                    )
                except Exception as e:
                    logger.error(
                        f"Error analyzing build {build.get('job_name', 'unknown')}: {e}"
                    )
                    continue

            if analyzed_count > 0:
                logger.info(f"🎉 Poll complete. Analyzed {analyzed_count} new builds")
            else:
                logger.info("Poll complete. No new builds to analyze")
        except Exception as e:
            logger.error(f"Error in poll and analyze: {e}")

    def poll_now(self):
        """Trigger immediate poll (for manual testing)"""
        logger.info("Manual poll triggered")
        self._poll_and_analyze()
