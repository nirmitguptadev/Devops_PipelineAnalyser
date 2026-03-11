from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pytest

@pytest.fixture
def driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode for CI/CD
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

def test_dashboard_loads(driver):
    """Test that dashboard page loads successfully"""
    driver.get("http://localhost:5000")
    
    assert "Pipeline Failure Analyzer" in driver.title
    
    # Check for key elements
    assert driver.find_element(By.CLASS_NAME, "navbar")
    assert driver.find_element(By.ID, "activityFeed")
    assert driver.find_element(By.ID, "failuresTable")

def test_stats_cards_display(driver):
    """Test that all stat cards are displayed"""
    driver.get("http://localhost:5000")
    
    assert driver.find_element(By.ID, "totalFailures")
    assert driver.find_element(By.ID, "criticalCount")
    assert driver.find_element(By.ID, "avgMTTR")
    assert driver.find_element(By.ID, "successRate")

def test_activity_feed_exists(driver):
    """Test that activity feed card exists"""
    driver.get("http://localhost:5000")
    
    activity_feed = driver.find_element(By.ID, "activityFeed")
    assert activity_feed is not None
    
    # Check for live status badge
    live_status = driver.find_element(By.ID, "liveStatus")
    assert "Live" in live_status.text

def test_ai_summary_card_exists(driver):
    """Test that AI summary card exists"""
    driver.get("http://localhost:5000")
    
    ai_summary = driver.find_element(By.ID, "aiSummaryCard")
    assert ai_summary is not None
    
    # Should show placeholder initially
    assert "Select a failure" in ai_summary.text or "AI-powered analysis" in ai_summary.text

def test_charts_render(driver):
    """Test that charts are rendered"""
    driver.get("http://localhost:5000")
    
    time.sleep(2)  # Wait for charts to render
    
    category_chart = driver.find_element(By.ID, "categoryChart")
    trend_chart = driver.find_element(By.ID, "trendChart")
    
    assert category_chart is not None
    assert trend_chart is not None

def test_failures_table_displays(driver):
    """Test that failures table is displayed"""
    driver.get("http://localhost:5000")
    
    time.sleep(2)
    
    table = driver.find_element(By.ID, "failuresTable")
    assert table is not None

def test_download_report_button_exists(driver):
    """Test that download report button exists"""
    driver.get("http://localhost:5000")
    
    # Find download button
    download_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Download Report')]")
    assert len(download_buttons) > 0

def test_settings_link_works(driver):
    """Test that settings link navigates correctly"""
    driver.get("http://localhost:5000")
    
    settings_link = driver.find_element(By.XPATH, "//a[@href='/settings']")
    settings_link.click()
    
    time.sleep(1)
    
    assert "/settings" in driver.current_url

def test_ai_badge_displayed(driver):
    """Test that AI-Powered badge is displayed in navbar"""
    driver.get("http://localhost:5000")
    
    ai_badge = driver.find_element(By.CLASS_NAME, "ai-badge")
    assert "AI-Powered" in ai_badge.text or "AI" in ai_badge.text

def test_responsive_layout(driver):
    """Test that layout is responsive"""
    driver.get("http://localhost:5000")
    
    # Test desktop view
    driver.set_window_size(1920, 1080)
    time.sleep(1)
    assert driver.find_element(By.ID, "activityFeed").is_displayed()
    
    # Test tablet view
    driver.set_window_size(768, 1024)
    time.sleep(1)
    assert driver.find_element(By.ID, "activityFeed").is_displayed()

def test_activity_feed_click_shows_ai_summary(driver):
    """Test that clicking a failure in activity feed shows AI summary"""
    driver.get("http://localhost:5000")
    
    time.sleep(3)  # Wait for any failures to load
    
    # Check if there are any failures in the feed
    activity_items = driver.find_elements(By.CSS_SELECTOR, "#activityFeed .alert")
    
    if len(activity_items) > 0:
        # Click first failure
        activity_items[0].click()
        time.sleep(1)
        
        # Check if AI summary card updated
        ai_summary = driver.find_element(By.ID, "aiSummaryCard")
        # Should no longer show placeholder
        assert "Select a failure" not in ai_summary.text

def test_professional_color_scheme(driver):
    """Test that professional color scheme is applied"""
    driver.get("http://localhost:5000")
    
    # Check navbar background color (should be dark professional color)
    navbar = driver.find_element(By.CLASS_NAME, "navbar")
    navbar_bg = navbar.value_of_css_property("background-color")
    
    # Should not be purple gradient (old tacky colors)
    assert "rgb(44, 62, 80)" in navbar_bg or "rgba(44, 62, 80" in navbar_bg

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
