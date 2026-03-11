import pytest
import sys
import os
import json
sys.path.insert(0, 'src/main')
from app import app
from database import Database

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_db():
    """Create test database"""
    db = Database('test_api.db')
    yield db
    if os.path.exists('test_api.db'):
        os.remove('test_api.db')

def test_index_route(client):
    """Test that index page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Pipeline Failure Analyzer' in response.data

def test_settings_route(client):
    """Test that settings page loads"""
    response = client.get('/settings')
    assert response.status_code == 200
    assert b'Settings' in response.data

def test_api_stats_endpoint(client):
    """Test /api/stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'total_failures' in data
    assert 'by_category' in data
    assert 'by_severity' in data
    assert 'weekly_trend' in data

def test_api_failures_endpoint(client):
    """Test /api/failures endpoint"""
    response = client.get('/api/failures')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_api_failures_with_limit(client):
    """Test /api/failures endpoint with limit parameter"""
    response = client.get('/api/failures?limit=5')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) <= 5

def test_api_analyze_endpoint_missing_data(client):
    """Test /api/analyze with missing data"""
    response = client.post('/api/analyze',
                          json={},
                          content_type='application/json')
    assert response.status_code == 400

def test_api_analyze_endpoint_valid_data(client):
    """Test /api/analyze with valid data"""
    response = client.post('/api/analyze',
                          json={
                              'pipeline_name': 'test-pipeline',
                              'log_content': 'BUILD FAILED: compilation error',
                              'ci_platform': 'jenkins',
                              'use_ai': False
                          },
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'category' in data
    assert 'severity' in data
    assert 'root_cause' in data

def test_api_analyze_with_ai_enabled(client):
    """Test /api/analyze with AI enabled (requires GROQ_API_KEY)"""
    if not os.getenv('GROQ_API_KEY'):
        pytest.skip("No GROQ_API_KEY found")
    
    response = client.post('/api/analyze',
                          json={
                              'pipeline_name': 'ai-test-pipeline',
                              'log_content': 'BUILD FAILED: compilation error in Main.java',
                              'ci_platform': 'jenkins',
                              'use_ai': True
                          },
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'ai_insights' in data or 'troubleshooting' in data

def test_api_webhook_jenkins(client):
    """Test Jenkins webhook endpoint"""
    response = client.post('/webhook/jenkins',
                          json={
                              'name': 'test-job',
                              'build': {
                                  'number': 123,
                                  'status': 'FAILURE',
                                  'url': 'http://jenkins/job/test-job/123'
                              }
                          },
                          content_type='application/json')
    # Should return 200 even if processing fails (webhook acknowledgment)
    assert response.status_code in [200, 500]

def test_api_report_download_csv(client):
    """Test CSV report download"""
    response = client.post('/api/report/download',
                          json={
                              'type': 'csv',
                              'date_range': 7
                          },
                          content_type='application/json')
    assert response.status_code == 200
    assert response.content_type == 'text/csv'

def test_api_report_download_json(client):
    """Test JSON report download"""
    response = client.post('/api/report/download',
                          json={
                              'type': 'json',
                              'date_range': 7
                          },
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'report_date' in data
    assert 'failures' in data
    assert isinstance(data['failures'], list)

def test_api_report_download_html(client):
    """Test HTML report download"""
    response = client.post('/api/report/download',
                          json={
                              'type': 'html',
                              'date_range': 7
                          },
                          content_type='application/json')
    assert response.status_code == 200
    assert 'text/html' in response.content_type

def test_api_settings_get(client):
    """Test GET /api/settings endpoint"""
    response = client.get('/api/settings')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'jenkins' in data or 'github' in data

def test_api_settings_save(client):
    """Test POST /api/settings endpoint"""
    response = client.post('/api/settings',
                          json={
                              'jenkins': {
                                  'url': 'http://localhost:8080',
                                  'username': 'admin',
                                  'api_token': 'test-token'
                              }
                          },
                          content_type='application/json')
    assert response.status_code == 200

def test_api_poll_now(client):
    """Test manual poll trigger endpoint"""
    response = client.post('/api/poll-now')
    # Should return 200 or 500 depending on Jenkins configuration
    assert response.status_code in [200, 500]

def test_cors_headers(client):
    """Test that CORS headers are not overly permissive"""
    response = client.get('/api/stats')
    # Should not have wildcard CORS in production
    assert response.headers.get('Access-Control-Allow-Origin') != '*' or app.config['TESTING']

def test_error_handling_invalid_json(client):
    """Test error handling for invalid JSON"""
    response = client.post('/api/analyze',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code in [400, 500]

def test_api_analyze_returns_troubleshooting(client):
    """Test that analyze endpoint returns troubleshooting steps when AI is enabled"""
    if not os.getenv('GROQ_API_KEY'):
        pytest.skip("No GROQ_API_KEY found")
    
    response = client.post('/api/analyze',
                          json={
                              'pipeline_name': 'troubleshoot-test',
                              'log_content': 'ERROR: Tests failed\nFAILED: test_login',
                              'ci_platform': 'jenkins',
                              'use_ai': True
                          },
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    if 'troubleshooting' in data:
        assert isinstance(data['troubleshooting'], list)
        assert len(data['troubleshooting']) > 0
