# Test Documentation

## Overview
This document describes all test cases for the Pipeline Failure Analyzer project, including unit tests, integration tests, and end-to-end Selenium tests.

## Test Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_analyzer.py          # Pattern matching analyzer tests
│   ├── test_groq_analyzer.py     # AI analyzer tests
│   └── test_database.py          # Database operations tests
├── integration/                   # Integration tests
│   ├── test_api.py               # Flask API endpoint tests
│   └── test_ingestion_scheduler.py # Jenkins polling tests
└── selenium/                      # End-to-end UI tests
    └── test_ui.py                # Browser automation tests
```

## Prerequisites

### Install Test Dependencies
```bash
pip install pytest pytest-cov selenium
```

### Setup Chrome WebDriver (for Selenium tests)
- Download ChromeDriver: https://chromedriver.chromium.org/
- Add to PATH or place in project root

### Environment Variables
```bash
# Optional: For AI-powered tests
export GROQ_API_KEY=your_api_key_here

# For Windows
set GROQ_API_KEY=your_api_key_here
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Run Selenium Tests Only
```bash
# Start the Flask app first
python src/main/app.py

# In another terminal
pytest tests/selenium/ -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=src/main --cov-report=html --cov-report=term
```

### Run Specific Test File
```bash
pytest tests/unit/test_groq_analyzer.py -v
```

### Run Specific Test Function
```bash
pytest tests/unit/test_groq_analyzer.py::test_analyzer_initialization_with_key -v
```

## Test Categories

### 1. Unit Tests

#### test_analyzer.py
Tests the pattern matching analyzer that categorizes failures.

**Test Cases:**
- `test_build_failure_detection` - Detects build failures
- `test_test_failure_detection` - Detects test failures
- `test_deployment_failure_detection` - Detects deployment failures
- `test_error_line_extraction` - Extracts error lines from logs
- `test_recommendations_provided` - Generates recommendations

**Run:**
```bash
pytest tests/unit/test_analyzer.py -v
```

#### test_groq_analyzer.py
Tests the AI-powered Groq analyzer for generating summaries and troubleshooting steps.

**Test Cases:**
- `test_analyzer_initialization_with_key` - Initializes with API key
- `test_analyzer_initialization_without_key` - Handles missing API key
- `test_analyze_failure_returns_dict` - Returns summary and troubleshooting
- `test_analyze_failure_without_key_returns_none` - Graceful degradation
- `test_suggest_fixes_returns_list` - Generates fix suggestions
- `test_troubleshooting_steps_format` - Validates step formatting

**Run:**
```bash
pytest tests/unit/test_groq_analyzer.py -v
```

**Note:** Tests requiring GROQ_API_KEY will be skipped if not set.

#### test_database.py
Tests database operations including the new troubleshooting column.

**Test Cases:**
- `test_database_initialization` - Creates schema correctly
- `test_save_analysis_basic` - Saves basic failure data
- `test_save_analysis_with_ai_insights` - Saves AI insights and troubleshooting
- `test_get_recent_failures_limit` - Respects limit parameter
- `test_is_build_analyzed` - Detects duplicate builds
- `test_get_statistics` - Calculates statistics correctly
- `test_troubleshooting_column_exists` - Validates schema

**Run:**
```bash
pytest tests/unit/test_database.py -v
```

### 2. Integration Tests

#### test_api.py
Tests Flask API endpoints including AI summary features.

**Test Cases:**
- `test_index_route` - Dashboard loads
- `test_settings_route` - Settings page loads
- `test_api_stats_endpoint` - Statistics API works
- `test_api_failures_endpoint` - Failures API works
- `test_api_analyze_endpoint_valid_data` - Analysis endpoint works
- `test_api_analyze_with_ai_enabled` - AI analysis integration
- `test_api_webhook_jenkins` - Jenkins webhook handling
- `test_api_report_download_csv` - CSV report generation
- `test_api_report_download_json` - JSON report generation
- `test_api_report_download_html` - HTML report generation
- `test_api_settings_get` - Get settings
- `test_api_settings_save` - Save settings
- `test_api_analyze_returns_troubleshooting` - Troubleshooting steps

**Run:**
```bash
# Start Flask app first
python src/main/app.py

# In another terminal
pytest tests/integration/test_api.py -v
```

#### test_ingestion_scheduler.py
Tests the Jenkins polling and automatic analysis flow.

**Test Cases:**
- `test_scheduler_initialization` - Initializes correctly
- `test_scheduler_start_stop` - Starts and stops properly
- `test_poll_and_analyze_with_failures` - Processes failures
- `test_skip_already_analyzed_builds` - Avoids duplicates
- `test_ai_analysis_integration` - Integrates AI analysis
- `test_poll_with_no_failures` - Handles empty results
- `test_poll_now_manual_trigger` - Manual polling works

**Run:**
```bash
pytest tests/integration/test_ingestion_scheduler.py -v
```

### 3. Selenium Tests

#### test_ui.py
End-to-end browser tests for the UI including AI summary card.

**Test Cases:**
- `test_dashboard_loads` - Dashboard page loads
- `test_stats_cards_display` - All stat cards visible
- `test_activity_feed_exists` - Activity feed present
- `test_ai_summary_card_exists` - AI summary card present
- `test_charts_render` - Charts render correctly
- `test_failures_table_displays` - Failures table visible
- `test_download_report_button_exists` - Download button present
- `test_settings_link_works` - Navigation works
- `test_ai_badge_displayed` - AI badge visible
- `test_responsive_layout` - Responsive design works
- `test_activity_feed_click_shows_ai_summary` - Click interaction works
- `test_professional_color_scheme` - Professional colors applied

**Run:**
```bash
# Start Flask app first
python src/main/app.py

# In another terminal
pytest tests/selenium/test_ui.py -v
```

**Headless Mode:**
Tests run in headless mode by default for CI/CD. To see browser:
```python
# Edit test_ui.py and comment out:
# chrome_options.add_argument('--headless')
```

## Manual Testing Guide

### Testing AI Summary Feature

1. **Start the Application**
   ```bash
   python src/main/app.py
   ```

2. **Configure Jenkins (if not already done)**
   - Go to http://localhost:5000/settings
   - Enter Jenkins URL, username, and API token
   - Click "Save Settings"

3. **Trigger a Jenkins Build Failure**
   - Create a Jenkins job that will fail
   - Run the build
   - Wait 10 seconds for automatic detection

4. **Verify Live Activity Feed**
   - Check http://localhost:5000
   - New failure should appear in "Live Activity Feed" (left side)
   - Should show pipeline name, category, severity, root cause

5. **Verify AI Summary Card**
   - Click on any failure in the activity feed
   - AI Summary card (right side) should update
   - Should show:
     - AI Analysis summary (2-3 sentences)
     - Troubleshooting Steps (numbered list with green badges)

6. **Test Multiple Failures**
   - Trigger multiple build failures
   - Click different failures in the feed
   - AI Summary card should update for each one

7. **Test Without AI**
   - Remove GROQ_API_KEY from .env
   - Restart application
   - Failures should still be detected
   - AI Summary card should show "No AI analysis available"

### Testing Report Downloads

1. **CSV Report**
   - Click "Download Report" → "CSV Format"
   - Open in Excel/Google Sheets
   - Verify columns: Pipeline, Category, Severity, Root Cause, Platform, Timestamp

2. **HTML Report**
   - Click "Download Report" → "HTML Report"
   - Open in browser
   - Should be professionally formatted and printable

3. **JSON Report**
   - Click "Download Report" → "JSON Data"
   - Open in text editor
   - Should include ai_insights and troubleshooting fields

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov selenium
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src/main
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    
    stages {
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov'
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/unit/ -v --cov=src/main --cov-report=xml'
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'pytest tests/integration/ -v'
            }
        }
    }
    
    post {
        always {
            junit 'test-results/*.xml'
            cobertura coberturaReportFile: 'coverage.xml'
        }
    }
}
```

## Test Coverage Goals

- **Unit Tests:** > 80% coverage
- **Integration Tests:** All API endpoints covered
- **Selenium Tests:** All critical user flows covered

## Troubleshooting

### Selenium Tests Fail
- Ensure ChromeDriver version matches Chrome browser version
- Check if Flask app is running on port 5000
- Try running without headless mode to see what's happening

### AI Tests Skipped
- Set GROQ_API_KEY environment variable
- Verify API key is valid
- Check internet connection

### Database Tests Fail
- Ensure no other process is using test database files
- Check file permissions
- Delete old test database files

### Import Errors
- Ensure you're running from project root
- Check PYTHONPATH includes src/main
- Verify all dependencies are installed

## Contributing

When adding new features:
1. Write unit tests first (TDD approach)
2. Add integration tests for API endpoints
3. Add Selenium tests for UI changes
4. Update this documentation
5. Ensure all tests pass before submitting PR

## Contact

For test-related questions, refer to the main project documentation or create an issue in the repository.
