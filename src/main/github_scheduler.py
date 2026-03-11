import threading
import time
import logging
from github_integration import GitHubActionsIntegration
from analyzer import PipelineAnalyzer
from database import Database

logger = logging.getLogger(__name__)


class GithubScheduler:
    def __init__(
        self, token: str, owner: str = None, repo: str = None, poll_interval: int = 10, groq_analyzer=None
    ):
        self.github = GitHubActionsIntegration(token, owner, repo)
        self.analyzer = PipelineAnalyzer()
        self.db = Database()
        self.poll_interval = poll_interval
        self.groq_analyzer = groq_analyzer
        self.running = False
        self.thread = None
        self.owner = owner
        self.repo = repo

    def start(self):
        """Start the background polling thread"""
        if self.running:
            logger.warning("GitHub Scheduler already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started GitHub polling every {self.poll_interval} seconds")

    def stop(self):
        """Stop the background polling thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stopped GitHub polling")

    def _poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                self._poll_and_analyze()
            except Exception as e:
                logger.error(f"Error in GitHub polling loop: {e}")

            time.sleep(self.poll_interval)

    def _poll_and_analyze(self):
        """Poll GitHub Actions and analyze failed runs"""
        logger.info("Starting GitHub Actions poll...")

        try:
            repos_to_poll = []
            if self.owner and self.repo:
                repos_to_poll.append({"owner": self.owner, "name": self.repo})
            else:
                repos_to_poll = self.github.list_repositories(self.owner)

            if not repos_to_poll:
                logger.warning("No GitHub repositories found or unable to list.")
                return

            failed_runs = self.github.poll_all_repos(repos_to_poll, limit_per_repo=5)

            if not failed_runs:
                logger.info("No failed GitHub runs found")
                return

            analyzed_count = 0
            for run in failed_runs:
                try:
                    pipeline_name = f"{run['job_name']}#{run['build_number']}"

                    # Check if already analyzed
                    if self.db.is_build_analyzed(run["job_name"], run["build_number"]):
                        logger.debug(f"Skipping already analyzed: {pipeline_name}")
                        continue

                    # Analyze the build
                    result = self.analyzer.analyze(run["console_log"], pipeline_name)

                    # Add build metadata
                    result["build_number"] = run["build_number"]
                    result["jenkins_status"] = run["result"]  # keep structure similar
                    result["ci_platform"] = "github"

                    # Add AI insights if available
                    try:
                        groq = self.groq_analyzer
                        if groq and groq.enabled:
                            ai_result = groq.analyze_failure(
                                run["console_log"],
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
                        f"Error analyzing GitHub run {run.get('job_name', 'unknown')}: {e}"
                    )
                    continue

            if analyzed_count > 0:
                logger.info(
                    f"🎉 Poll complete. Analyzed {analyzed_count} new GitHub runs"
                )
            else:
                logger.info("Poll complete. No new GitHub runs to analyze")
        except Exception as e:
            logger.error(f"Error in GitHub poll and analyze: {e}")

    def poll_now(self):
        """Trigger immediate poll (for manual testing)"""
        logger.info("Manual GitHub poll triggered")
        self._poll_and_analyze()
