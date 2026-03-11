import pytest
import sys
sys.path.insert(0, 'src/main')
from analyzer import PipelineAnalyzer

@pytest.fixture
def analyzer():
    return PipelineAnalyzer()

def test_build_failure_detection(analyzer):
    log = "BUILD FAILED: compilation error in Main.java"
    result = analyzer.analyze(log, "test-pipeline")
    assert result['category'] == 'build_failure'
    assert result['severity'] == 'high'

def test_test_failure_detection(analyzer):
    log = "Tests run: 10, Failures: 2, Errors: 0"
    result = analyzer.analyze(log, "test-pipeline")
    assert result['category'] == 'test_failure'
    assert result['severity'] == 'medium'

def test_deployment_failure_detection(analyzer):
    log = "deployment failed: connection refused to server"
    result = analyzer.analyze(log, "test-pipeline")
    assert result['category'] == 'deployment_failure'
    assert result['severity'] == 'critical'

def test_error_line_extraction(analyzer):
    log = "INFO: Starting build\nERROR: Build failed\nINFO: Cleanup"
    result = analyzer.analyze(log, "test-pipeline")
    assert len(result['error_lines']) > 0
    assert any('ERROR' in line for line in result['error_lines'])

def test_recommendations_provided(analyzer):
    log = "BUILD FAILED"
    result = analyzer.analyze(log, "test-pipeline")
    assert len(result['recommendations']) > 0
    assert isinstance(result['recommendations'], list)
