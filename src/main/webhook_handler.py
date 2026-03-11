from flask import request, jsonify
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self, secret_token: str = None):
        self.secret_token = secret_token
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        if not self.secret_token:
            return True
        
        expected_signature = hmac.new(
            self.secret_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def parse_jenkins_webhook(self, data: dict) -> dict:
        """Parse Jenkins webhook payload"""
        try:
            build_info = {
                'pipeline_name': data.get('name', 'unknown'),
                'build_number': data.get('build', {}).get('number'),
                'status': data.get('build', {}).get('status'),
                'phase': data.get('build', {}).get('phase'),
                'url': data.get('build', {}).get('full_url'),
                'log_url': data.get('build', {}).get('log'),
            }
            
            # Only process completed failed builds
            if build_info['phase'] == 'COMPLETED' and build_info['status'] in ['FAILURE', 'UNSTABLE', 'ABORTED']:
                return build_info
            
            return None
        except Exception as e:
            logger.error(f"Failed to parse Jenkins webhook: {e}")
            return None
    
    def parse_github_actions_webhook(self, data: dict) -> dict:
        """Parse GitHub Actions webhook payload"""
        try:
            if data.get('action') != 'completed':
                return None
            
            workflow_run = data.get('workflow_run', {})
            
            if workflow_run.get('conclusion') not in ['failure', 'cancelled', 'timed_out']:
                return None
            
            build_info = {
                'pipeline_name': workflow_run.get('name', 'unknown'),
                'build_number': workflow_run.get('run_number'),
                'status': workflow_run.get('conclusion').upper(),
                'phase': 'COMPLETED',
                'url': workflow_run.get('html_url'),
                'log_url': workflow_run.get('logs_url'),
                'repository': data.get('repository', {}).get('full_name')
            }
            
            return build_info
        except Exception as e:
            logger.error(f"Failed to parse GitHub Actions webhook: {e}")
            return None
    
    def parse_gitlab_webhook(self, data: dict) -> dict:
        """Parse GitLab CI webhook payload"""
        try:
            if data.get('object_kind') != 'build':
                return None
            
            if data.get('build_status') not in ['failed', 'canceled']:
                return None
            
            build_info = {
                'pipeline_name': data.get('project_name', 'unknown'),
                'build_number': data.get('build_id'),
                'status': data.get('build_status').upper(),
                'phase': 'COMPLETED',
                'url': data.get('repository', {}).get('homepage'),
                'log_url': None,
            }
            
            return build_info
        except Exception as e:
            logger.error(f"Failed to parse GitLab webhook: {e}")
            return None
