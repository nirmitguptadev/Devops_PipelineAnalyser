import re
from datetime import datetime
from typing import Dict, List

class PipelineAnalyzer:
    def __init__(self):
        self.patterns = {
            'build_failure': [
                r'BUILD FAILED',
                r'compilation error',
                r'cannot find symbol',
                r'SyntaxError',
            ],
            'test_failure': [
                r'Tests run:.*Failures: [1-9]',
                r'FAILED.*test',
                r'AssertionError',
                r'Test.*failed',
            ],
            'deployment_failure': [
                r'deployment failed',
                r'rollback',
                r'connection refused',
                r'timeout.*deploy',
            ],
            'infrastructure_failure': [
                r'out of memory',
                r'disk space',
                r'network.*error',
                r'permission denied',
            ],
            'dependency_failure': [
                r'could not resolve dependencies',
                r'package not found',
                r'module.*not found',
                r'ImportError',
            ]
        }
        
        self.root_causes = {
            'build_failure': 'Code compilation or build configuration issue',
            'test_failure': 'Test case failure or assertion error',
            'deployment_failure': 'Deployment configuration or environment issue',
            'infrastructure_failure': 'Resource or infrastructure constraint',
            'dependency_failure': 'Missing or incompatible dependencies'
        }
        
        self.recommendations = {
            'build_failure': [
                'Check syntax errors in recent commits',
                'Verify build configuration files',
                'Ensure all dependencies are available'
            ],
            'test_failure': [
                'Review failed test cases',
                'Check test data and fixtures',
                'Verify environment configuration'
            ],
            'deployment_failure': [
                'Verify deployment credentials',
                'Check target environment availability',
                'Review deployment scripts'
            ],
            'infrastructure_failure': [
                'Check resource allocation',
                'Monitor system metrics',
                'Scale infrastructure if needed'
            ],
            'dependency_failure': [
                'Update dependency versions',
                'Check package repository availability',
                'Verify dependency lock files'
            ]
        }

    def analyze(self, log_content: str, pipeline_name: str) -> Dict:
        category = self._categorize_failure(log_content)
        error_lines = self._extract_error_lines(log_content)
        
        result = {
            'pipeline_name': pipeline_name,
            'timestamp': datetime.utcnow().isoformat(),
            'category': category,
            'root_cause': self.root_causes.get(category, 'Unknown failure'),
            'error_lines': error_lines[:5],
            'recommendations': self.recommendations.get(category, ['Review logs manually']),
            'severity': self._calculate_severity(category)
        }
        
        return result

    def _categorize_failure(self, log_content: str) -> str:
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, log_content, re.IGNORECASE):
                    return category
        return 'unknown'

    def _extract_error_lines(self, log_content: str) -> List[str]:
        error_keywords = ['error', 'failed', 'exception', 'fatal']
        lines = log_content.split('\n')
        error_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in error_keywords):
                error_lines.append(line.strip())
        
        return error_lines

    def _calculate_severity(self, category: str) -> str:
        severity_map = {
            'build_failure': 'high',
            'test_failure': 'medium',
            'deployment_failure': 'critical',
            'infrastructure_failure': 'critical',
            'dependency_failure': 'high',
            'unknown': 'low'
        }
        return severity_map.get(category, 'low')
