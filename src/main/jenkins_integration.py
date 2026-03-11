import requests
from requests.auth import HTTPBasicAuth
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class JenkinsIntegration:
    def __init__(self, jenkins_url: str, username: str, api_token: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, api_token)
        
    def get_job_builds(self, job_name: str, limit: int = 10) -> List[Dict]:
        """Fetch recent builds for a Jenkins job"""
        # URL encode job name to handle spaces and special characters
        from urllib.parse import quote
        encoded_job = quote(job_name, safe='')
        url = f"{self.jenkins_url}/job/{encoded_job}/api/json?tree=builds[number,result,timestamp,url]{{0,{limit}}}"
        
        try:
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get('builds', [])
        except Exception as e:
            logger.debug(f"Failed to fetch builds for {job_name}: {e}")
            return []
    
    def get_build_console_log(self, job_name: str, build_number: int) -> Optional[str]:
        """Fetch console log for a specific build"""
        from urllib.parse import quote
        encoded_job = quote(job_name, safe='')
        url = f"{self.jenkins_url}/job/{encoded_job}/{build_number}/consoleText"
        
        try:
            response = requests.get(url, auth=self.auth, timeout=30, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.debug(f"Failed to fetch console log for {job_name}#{build_number}: {e}")
            return None
    
    def get_failed_builds(self, job_name: str, limit: int = 10) -> List[Dict]:
        """Get only failed builds with their console logs"""
        builds = self.get_job_builds(job_name, limit)
        failed_builds = []
        
        for build in builds:
            if build.get('result') in ['FAILURE', 'UNSTABLE', 'ABORTED']:
                build_number = build['number']
                console_log = self.get_build_console_log(job_name, build_number)
                
                if console_log:
                    failed_builds.append({
                        'job_name': job_name,
                        'build_number': build_number,
                        'result': build['result'],
                        'timestamp': build['timestamp'],
                        'console_log': console_log
                    })
        
        return failed_builds
    
    def get_all_jobs(self) -> List[str]:
        """Get list of all Jenkins jobs"""
        url = f"{self.jenkins_url}/api/json?tree=jobs[name]"
        
        try:
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()
            jobs = data.get('jobs', [])
            # Filter out folders and only get actual jobs
            return [job['name'] for job in jobs if 'name' in job]
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Jenkins at {self.jenkins_url}: {e}")
            return []
        except requests.exceptions.Timeout:
            logger.error(f"Jenkins connection timeout at {self.jenkins_url}")
            return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jenkins HTTP error: {e.response.status_code} - Check credentials")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch jobs list: {e}")
            return []
    
    def poll_all_jobs(self, limit_per_job: int = 5) -> List[Dict]:
        """Poll all jobs and return failed builds"""
        jobs = self.get_all_jobs()
        
        if not jobs:
            logger.warning("No Jenkins jobs found or unable to connect")
            return []
        
        all_failed_builds = []
        logger.info(f"Polling {len(jobs)} Jenkins jobs...")
        
        for job_name in jobs:
            try:
                failed_builds = self.get_failed_builds(job_name, limit_per_job)
                all_failed_builds.extend(failed_builds)
                if failed_builds:
                    logger.info(f"Found {len(failed_builds)} failed builds in {job_name}")
            except Exception as e:
                logger.debug(f"Error polling job {job_name}: {e}")
                continue
        
        return all_failed_builds
