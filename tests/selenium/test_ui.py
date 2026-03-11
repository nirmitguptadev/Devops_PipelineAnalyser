from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_dashboard_loads():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000")
    
    assert "Pipeline Failure Analyzer" in driver.title
    driver.quit()

def test_analyze_pipeline_flow():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000")
    
    pipeline_input = driver.find_element(By.ID, "pipelineName")
    log_input = driver.find_element(By.ID, "logContent")
    
    pipeline_input.send_keys("test-pipeline")
    log_input.send_keys("BUILD FAILED: compilation error")
    
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()
    
    wait = WebDriverWait(driver, 10)
    result_area = wait.until(EC.presence_of_element_located((By.ID, "resultArea")))
    
    assert "build_failure" in result_area.text.lower() or "Category" in result_area.text
    
    driver.quit()

def test_failures_table_displays():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000")
    
    time.sleep(2)
    
    table = driver.find_element(By.ID, "failuresTable")
    assert table is not None
    
    driver.quit()

if __name__ == "__main__":
    test_dashboard_loads()
    test_analyze_pipeline_flow()
    test_failures_table_displays()
    print("All Selenium tests passed!")
