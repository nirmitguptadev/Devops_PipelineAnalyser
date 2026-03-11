import requests
from requests.auth import HTTPBasicAuth
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)


class GitHubActionsIntegration:
    def __init__(self, token: str, owner: str = None, repo: str = None):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_workflow_runs(
        self, owner: str = None, repo: str = None, limit: int = 10
    ) -> List[Dict]:
        """Fetch recent workflow runs"""
        owner = owner or self.owner
        repo = repo or self.repo

        if not owner or not repo:
            logger.error("GitHub owner and repo must be specified")
            return []

        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs"
        params = {"per_page": limit, "status": "completed"}

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("workflow_runs", [])
        except Exception as e:
            logger.error(f"Failed to fetch GitHub workflow runs: {e}")
            return []

    def get_failed_runs(
        self, owner: str = None, repo: str = None, limit: int = 10
    ) -> List[Dict]:
        """Get only failed workflow runs"""
        runs = self.get_workflow_runs(owner, repo, limit * 2)
        failed_runs = []

        for run in runs:
            if run.get("conclusion") in ["failure", "cancelled", "timed_out"]:
                logs = self.get_workflow_logs(run["id"], owner, repo)

                if logs:
                    failed_runs.append(
                        {
                            "job_name": run["name"],
                            "build_number": run["run_number"],
                            "result": run["conclusion"].upper(),
                            "timestamp": run["created_at"],
                            "console_log": logs,
                            "url": run["html_url"],
                        }
                    )

                if len(failed_runs) >= limit:
                    break

        return failed_runs

    def get_workflow_logs(
        self, run_id: int, owner: str = None, repo: str = None
    ) -> Optional[str]:
        """Fetch logs for a specific workflow run"""
        owner = owner or self.owner
        repo = repo or self.repo

        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # GitHub returns logs as a zip file, we'll get the text content
            # For simplicity, we'll just return the response text
            return response.text[:10000]  # Limit to first 10k chars
        except Exception as e:
            logger.debug(f"Failed to fetch GitHub workflow logs for run {run_id}: {e}")
            return None

    def list_repositories(self, org: str = None) -> List[Dict]:
        """List repositories for an organization or user"""
        if org:
            url = f"{self.base_url}/orgs/{org}/repos"
        else:
            url = f"{self.base_url}/user/repos"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            repos = response.json()
            return [{"owner": r["owner"]["login"], "name": r["name"]} for r in repos]
        except Exception as e:
            logger.error(f"Failed to list GitHub repositories: {e}")
            return []

    def poll_all_repos(self, repos: List[Dict], limit_per_repo: int = 5) -> List[Dict]:
        """Poll multiple repositories for failed runs"""
        all_failed_runs = []

        logger.info(f"Polling {len(repos)} GitHub repositories...")

        for repo_info in repos:
            try:
                failed_runs = self.get_failed_runs(
                    owner=repo_info["owner"],
                    repo=repo_info["name"],
                    limit=limit_per_repo,
                )
                all_failed_runs.extend(failed_runs)
                if failed_runs:
                    logger.info(
                        f"Found {len(failed_runs)} failed runs in {repo_info['owner']}/{repo_info['name']}"
                    )
            except Exception as e:
                logger.debug(
                    f"Error polling repo {repo_info['owner']}/{repo_info['name']}: {e}"
                )
                continue

        return all_failed_runs
