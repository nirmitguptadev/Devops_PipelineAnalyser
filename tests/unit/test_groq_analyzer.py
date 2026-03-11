import pytest
import sys
import os
sys.path.insert(0, 'src/main')
from groq_analyzer import GroqAnalyzer

@pytest.fixture
def analyzer_with_key():
    """Analyzer with API key (mocked or real)"""
    api_key = os.getenv('GROQ_API_KEY', 'test-key')
    return GroqAnalyzer(api_key=api_key)

@pytest.fixture
def analyzer_without_key():
    """Analyzer without API key"""
    return GroqAnalyzer(api_key=None)

def test_analyzer_initialization_with_key(analyzer_with_key):
    """Test that analyzer initializes correctly with API key"""
    assert analyzer_with_key.enabled == True
    assert analyzer_with_key.client is not None

def test_analyzer_initialization_without_key(analyzer_without_key):
    """Test that analyzer handles missing API key gracefully"""
    assert analyzer_without_key.enabled == False

def test_analyze_failure_returns_dict(analyzer_with_key):
    """Test that analyze_failure returns a dictionary with summary and troubleshooting"""
    log_content = "BUILD FAILED: compilation error"
    category = "build_failure"
    error_lines = ["ERROR: compilation failed", "ERROR: missing dependency"]
    
    # Skip if no real API key
    if not os.getenv('GROQ_API_KEY'):
        pytest.skip("No GROQ_API_KEY found, skipping live API test")
    
    result = analyzer_with_key.analyze_failure(log_content, category, error_lines)
    
    assert result is not None
    assert isinstance(result, dict)
    assert 'summary' in result
    assert 'troubleshooting' in result
    assert isinstance(result['summary'], str)
    assert isinstance(result['troubleshooting'], list)

def test_analyze_failure_without_key_returns_none(analyzer_without_key):
    """Test that analyze_failure returns None when API key is missing"""
    result = analyzer_without_key.analyze_failure("log", "category", ["error"])
    assert result is None

def test_suggest_fixes_returns_list(analyzer_with_key):
    """Test that suggest_fixes returns a list of recommendations"""
    if not os.getenv('GROQ_API_KEY'):
        pytest.skip("No GROQ_API_KEY found, skipping live API test")
    
    category = "build_failure"
    root_cause = "Missing dependency in pom.xml"
    
    result = analyzer_with_key.suggest_fixes(category, root_cause)
    
    assert isinstance(result, list)
    assert len(result) <= 3

def test_suggest_fixes_without_key_returns_empty_list(analyzer_without_key):
    """Test that suggest_fixes returns empty list when API key is missing"""
    result = analyzer_without_key.suggest_fixes("category", "root_cause")
    assert result == []

def test_troubleshooting_steps_format(analyzer_with_key):
    """Test that troubleshooting steps are properly formatted"""
    if not os.getenv('GROQ_API_KEY'):
        pytest.skip("No GROQ_API_KEY found, skipping live API test")
    
    result = analyzer_with_key.analyze_failure(
        "BUILD FAILED",
        "build_failure",
        ["ERROR: compilation failed"]
    )
    
    if result and result['troubleshooting']:
        for step in result['troubleshooting']:
            assert isinstance(step, str)
            assert len(step) > 0
