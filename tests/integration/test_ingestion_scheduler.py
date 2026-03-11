import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
sys.path.insert(0, 'src/main')
from ingestion_scheduler import IngestionScheduler
from database import Database

@pytest.fixture
def test_db():
    """Create a test database"""
    db = Database('test_integration.db')
    yield db
    if os.path.exists('test_integration.db'):
        os.remove('test_integration.db')

@pytest.fixture
def mock_jenkins():
    """Mock Jenkins integration"""
    with patch('ingestion_scheduler.JenkinsIntegration') as mock:
        jenkins_instance = Mock()
        jenkins_instance.poll_all_jobs.return_value = [
            {
                'job_name': 'test-job',
                'build_number': 123,
                'result': 'FAILURE',
                'console_log': 'BUILD FAILED: compilation error in Main.java'
            }
        ]
        mock.return_value = jenkins_instance
        yield jenkins_instance

def test_scheduler_initialization():
    """Test that scheduler initializes correctly"""
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123',
        poll_interval=60
    )
    
    assert scheduler.poll_interval == 60
    assert scheduler.running == False

def test_scheduler_start_stop():
    """Test starting and stopping the scheduler"""
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123',
        poll_interval=300
    )
    
    scheduler.start()
    assert scheduler.running == True
    assert scheduler.thread is not None
    
    scheduler.stop()
    assert scheduler.running == False

@patch('ingestion_scheduler.JenkinsIntegration')
@patch('ingestion_scheduler.Database')
def test_poll_and_analyze_with_failures(mock_db_class, mock_jenkins_class):
    """Test polling and analyzing failed builds"""
    # Setup mocks
    mock_jenkins = Mock()
    mock_jenkins.poll_all_jobs.return_value = [
        {
            'job_name': 'test-job',
            'build_number': 123,
            'result': 'FAILURE',
            'console_log': 'BUILD FAILED: compilation error'
        }
    ]
    mock_jenkins_class.return_value = mock_jenkins
    
    mock_db = Mock()
    mock_db.is_build_analyzed.return_value = False
    mock_db_class.return_value = mock_db
    
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123'
    )
    
    scheduler._poll_and_analyze()
    
    # Verify Jenkins was polled
    mock_jenkins.poll_all_jobs.assert_called_once()
    
    # Verify database save was called
    mock_db.save_analysis.assert_called_once()

@patch('ingestion_scheduler.JenkinsIntegration')
@patch('ingestion_scheduler.Database')
def test_skip_already_analyzed_builds(mock_db_class, mock_jenkins_class):
    """Test that already analyzed builds are skipped"""
    mock_jenkins = Mock()
    mock_jenkins.poll_all_jobs.return_value = [
        {
            'job_name': 'test-job',
            'build_number': 123,
            'result': 'FAILURE',
            'console_log': 'BUILD FAILED'
        }
    ]
    mock_jenkins_class.return_value = mock_jenkins
    
    mock_db = Mock()
    mock_db.is_build_analyzed.return_value = True  # Already analyzed
    mock_db_class.return_value = mock_db
    
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123'
    )
    
    scheduler._poll_and_analyze()
    
    # Verify save was NOT called
    mock_db.save_analysis.assert_not_called()

@patch('ingestion_scheduler.JenkinsIntegration')
@patch('ingestion_scheduler.Database')
@patch('ingestion_scheduler.GroqAnalyzer')
def test_ai_analysis_integration(mock_groq_class, mock_db_class, mock_jenkins_class):
    """Test that AI analysis is integrated into the polling flow"""
    # Setup Jenkins mock
    mock_jenkins = Mock()
    mock_jenkins.poll_all_jobs.return_value = [
        {
            'job_name': 'test-job',
            'build_number': 123,
            'result': 'FAILURE',
            'console_log': 'BUILD FAILED: compilation error'
        }
    ]
    mock_jenkins_class.return_value = mock_jenkins
    
    # Setup Database mock
    mock_db = Mock()
    mock_db.is_build_analyzed.return_value = False
    mock_db_class.return_value = mock_db
    
    # Setup Groq mock
    mock_groq = Mock()
    mock_groq.enabled = True
    mock_groq.analyze_failure.return_value = {
        'summary': 'Build failed due to compilation error',
        'troubleshooting': ['Check syntax', 'Review dependencies', 'Run clean build']
    }
    mock_groq_class.return_value = mock_groq
    
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123'
    )
    
    scheduler._poll_and_analyze()
    
    # Verify AI analysis was called
    mock_groq.analyze_failure.assert_called_once()
    
    # Verify save was called with AI insights
    save_call_args = mock_db.save_analysis.call_args[0][0]
    assert 'ai_insights' in save_call_args
    assert 'troubleshooting' in save_call_args
    assert save_call_args['ai_insights'] == 'Build failed due to compilation error'
    assert len(save_call_args['troubleshooting']) == 3

@patch('ingestion_scheduler.JenkinsIntegration')
@patch('ingestion_scheduler.Database')
def test_poll_with_no_failures(mock_db_class, mock_jenkins_class):
    """Test polling when no failures are found"""
    mock_jenkins = Mock()
    mock_jenkins.poll_all_jobs.return_value = []  # No failures
    mock_jenkins_class.return_value = mock_jenkins
    
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    
    scheduler = IngestionScheduler(
        jenkins_url='http://localhost:8080',
        username='admin',
        api_token='token123'
    )
    
    scheduler._poll_and_analyze()
    
    # Verify save was NOT called
    mock_db.save_analysis.assert_not_called()

def test_poll_now_manual_trigger():
    """Test manual poll trigger"""
    with patch('ingestion_scheduler.JenkinsIntegration') as mock_jenkins_class:
        mock_jenkins = Mock()
        mock_jenkins.poll_all_jobs.return_value = []
        mock_jenkins_class.return_value = mock_jenkins
        
        scheduler = IngestionScheduler(
            jenkins_url='http://localhost:8080',
            username='admin',
            api_token='token123'
        )
        
        scheduler.poll_now()
        
        # Verify polling was triggered
        mock_jenkins.poll_all_jobs.assert_called()
