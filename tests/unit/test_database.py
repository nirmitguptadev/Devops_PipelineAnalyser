import pytest
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, 'src/main')
from database import Database

@pytest.fixture
def test_db():
    """Create a test database"""
    db = Database('test_pipeline.db')
    yield db
    # Cleanup
    if os.path.exists('test_pipeline.db'):
        os.remove('test_pipeline.db')

def test_database_initialization(test_db):
    """Test that database initializes with correct schema"""
    conn = test_db._get_connection()
    cursor = conn.cursor()
    
    # Check if failures table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='failures'")
    result = cursor.fetchone()
    
    assert result is not None
    assert result[0] == 'failures'
    conn.close()

def test_save_analysis_basic(test_db):
    """Test saving a basic analysis result"""
    result = {
        'pipeline_name': 'test-pipeline',
        'timestamp': datetime.now().isoformat(),
        'category': 'build_failure',
        'root_cause': 'Compilation error',
        'severity': 'high',
        'error_lines': ['ERROR: Build failed'],
        'recommendations': ['Check syntax', 'Review logs'],
        'ci_platform': 'jenkins'
    }
    
    test_db.save_analysis(result)
    
    failures = test_db.get_recent_failures(limit=1)
    assert len(failures) == 1
    assert failures[0]['pipeline_name'] == 'test-pipeline'
    assert failures[0]['category'] == 'build_failure'

def test_save_analysis_with_ai_insights(test_db):
    """Test saving analysis with AI insights and troubleshooting"""
    result = {
        'pipeline_name': 'ai-test-pipeline',
        'timestamp': datetime.now().isoformat(),
        'category': 'test_failure',
        'root_cause': 'Unit test failed',
        'severity': 'medium',
        'error_lines': ['FAILED: test_login'],
        'recommendations': ['Review test case'],
        'ci_platform': 'jenkins',
        'ai_insights': 'The test failed due to authentication issues',
        'troubleshooting': ['Check credentials', 'Verify API endpoint', 'Review logs']
    }
    
    test_db.save_analysis(result)
    
    failures = test_db.get_recent_failures(limit=1)
    assert len(failures) == 1
    assert failures[0]['ai_insights'] == 'The test failed due to authentication issues'
    assert failures[0]['troubleshooting'] is not None
    
    # Parse troubleshooting JSON
    troubleshooting = json.loads(failures[0]['troubleshooting'])
    assert isinstance(troubleshooting, list)
    assert len(troubleshooting) == 3

def test_get_recent_failures_limit(test_db):
    """Test that get_recent_failures respects limit parameter"""
    # Add multiple failures
    for i in range(5):
        result = {
            'pipeline_name': f'pipeline-{i}',
            'timestamp': datetime.now().isoformat(),
            'category': 'build_failure',
            'root_cause': 'Test error',
            'severity': 'low',
            'error_lines': ['ERROR'],
            'recommendations': ['Fix it'],
            'ci_platform': 'jenkins'
        }
        test_db.save_analysis(result)
    
    failures = test_db.get_recent_failures(limit=3)
    assert len(failures) == 3

def test_is_build_analyzed(test_db):
    """Test duplicate build detection"""
    result = {
        'pipeline_name': 'my-job#123',
        'timestamp': datetime.now().isoformat(),
        'category': 'build_failure',
        'root_cause': 'Error',
        'severity': 'high',
        'error_lines': ['ERROR'],
        'recommendations': ['Fix'],
        'ci_platform': 'jenkins'
    }
    
    test_db.save_analysis(result)
    
    # Check if build is detected as analyzed
    is_analyzed = test_db.is_build_analyzed('my-job', 123)
    assert is_analyzed == True
    
    # Check non-existent build
    is_analyzed = test_db.is_build_analyzed('other-job', 999)
    assert is_analyzed == False

def test_get_statistics(test_db):
    """Test statistics calculation"""
    # Add test data
    categories = ['build_failure', 'test_failure', 'build_failure']
    severities = ['high', 'medium', 'critical']
    
    for i, (cat, sev) in enumerate(zip(categories, severities)):
        result = {
            'pipeline_name': f'pipeline-{i}',
            'timestamp': datetime.now().isoformat(),
            'category': cat,
            'root_cause': 'Error',
            'severity': sev,
            'error_lines': ['ERROR'],
            'recommendations': ['Fix'],
            'ci_platform': 'jenkins'
        }
        test_db.save_analysis(result)
    
    stats = test_db.get_statistics()
    
    assert stats['total_failures'] == 3
    assert stats['by_category']['build_failure'] == 2
    assert stats['by_category']['test_failure'] == 1
    assert stats['by_severity']['high'] == 1
    assert stats['by_severity']['medium'] == 1
    assert stats['by_severity']['critical'] == 1

def test_troubleshooting_column_exists(test_db):
    """Test that troubleshooting column exists in schema"""
    conn = test_db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(failures)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    assert 'troubleshooting' in column_names
    conn.close()
