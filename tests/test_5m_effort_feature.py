import pytest
from playwright.sync_api import sync_playwright, expect
import time
import subprocess
import os
import signal
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TODOS_FILE = Path("todos.test.md")

@pytest.fixture(scope="module")
def server():
    """Start the test server before tests and stop it after"""
    env = os.environ.copy()
    env["TEST_MODE"] = "true"
    process = subprocess.Popen(
        ["python", "server.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Wait for server to start
    yield process
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

@pytest.fixture
def setup_test_file():
    """Reset the test todos file before each test"""
    TEST_TODOS_FILE.write_text("# today\n\n# ideas\n\n# backlog\n")
    yield
    if TEST_TODOS_FILE.exists():
        TEST_TODOS_FILE.unlink()

def test_5m_effort_option_exists(server, setup_test_file):
    """Test that the <5m effort option exists in the quick add modal"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Open quick add modal
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        # Type task title
        page.type("#palette-input", "Test 5m effort task")
        page.keyboard.press("Enter")
        
        # Navigate to effort field
        page.keyboard.press("ArrowDown")  # Due date field
        page.keyboard.press("ArrowDown")  # Category field  
        page.keyboard.press("ArrowDown")  # Priority field
        page.keyboard.press("ArrowDown")  # Effort field
        
        # Check that <5m option exists and is first
        effort_options = page.query_selector_all("#effort-options .palette-option")
        assert len(effort_options) >= 4
        
        first_option = effort_options[0]
        assert first_option.get_attribute("data-value") == "5m"
        assert "<5m" in first_option.inner_text()
        
        # Check XP preview exists
        xp_preview = page.query_selector("#xp-5m")
        assert xp_preview is not None
        
        browser.close()

def test_5m_effort_selection_and_save(server, setup_test_file):
    """Test selecting <5m effort and saving a task"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Open quick add modal
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        # Type task title
        task_title = "Quick 5 minute task"
        page.type("#palette-input", task_title)
        page.keyboard.press("Enter")
        
        # Navigate to effort field
        for _ in range(4):
            page.keyboard.press("ArrowDown")
        
        # Select <5m option (press 1)
        page.keyboard.press("1")
        
        # Save task
        page.keyboard.press("Enter")
        
        # Verify task appears in list
        page.wait_for_selector(".task-card", state="visible")
        
        # Check task has correct effort display
        task_metadata = page.query_selector(".task-metadata")
        assert task_metadata is not None
        assert "<5m" in task_metadata.inner_text()
        
        # Verify in todos.test.md
        content = TEST_TODOS_FILE.read_text()
        assert task_title in content
        assert "!5m" in content
        
        browser.close()

def test_5m_effort_xp_calculation(server, setup_test_file):
    """Test that XP is calculated correctly for <5m tasks"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Open quick add modal
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        # Type task title
        page.type("#palette-input", "Test XP calculation")
        page.keyboard.press("Enter")
        
        # Navigate to effort field
        for _ in range(4):
            page.keyboard.press("ArrowDown")
        
        # Select <5m option
        page.keyboard.press("1")
        
        # Check XP preview updates
        xp_preview = page.query_selector("#xp-5m")
        xp_text = xp_preview.inner_text()
        
        # With default friction (1), 5m effort should give specific XP
        # XP = 100 * (1 + 5/60)^0.5 * 1 = ~104
        assert "+104" in xp_text
        
        # Change friction to test XP update
        page.keyboard.press("ArrowDown")  # Move to friction field
        page.keyboard.press("2")  # Select medium friction
        
        # Go back to effort field to check updated XP
        page.keyboard.press("ArrowUp")
        
        # XP should now be doubled (~208)
        xp_preview_updated = page.query_selector("#xp-5m")
        xp_text_updated = xp_preview_updated.inner_text()
        assert "+208" in xp_text_updated
        
        browser.close()

def test_5m_effort_energy_cost(server, setup_test_file):
    """Test that energy cost is calculated correctly for <5m tasks"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Create a task with 5m effort
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        page.type("#palette-input", "Quick energy test task")
        page.keyboard.press("Enter")
        
        # Navigate to effort field and select <5m
        for _ in range(4):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("1")
        
        # Save task
        page.keyboard.press("Enter")
        
        # Wait for task to appear
        page.wait_for_selector(".task-card", state="visible")
        
        # Check energy cost display
        energy_cost = page.query_selector(".energy-cost")
        assert energy_cost is not None
        
        # 5m effort with friction 1 should cost 1 energy
        assert "⚡ 1" in energy_cost.inner_text()
        
        browser.close()

def test_5m_effort_sorting(server, setup_test_file):
    """Test that tasks with <5m effort sort correctly"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Create multiple tasks with different efforts
        efforts = [("5m", "1"), ("30m", "2"), ("1h", "3")]
        
        for effort, key in efforts:
            page.keyboard.press("n")
            page.wait_for_selector("#palette-modal", state="visible")
            
            page.type("#palette-input", f"Task with {effort} effort")
            page.keyboard.press("Enter")
            
            # Navigate to effort field
            for _ in range(4):
                page.keyboard.press("ArrowDown")
            
            # Select effort
            page.keyboard.press(key)
            
            # Save task
            page.keyboard.press("Enter")
            time.sleep(0.5)
        
        # Change sort to effort
        sort_select = page.query_selector("#sort-select")
        sort_select.select_option("effort")
        
        # Get all tasks
        tasks = page.query_selector_all(".task-card")
        
        # Verify order: 5m should be first
        assert len(tasks) >= 3
        first_task_metadata = tasks[0].query_selector(".task-metadata")
        assert "<5m" in first_task_metadata.inner_text()
        
        browser.close()

def test_5m_effort_persistence(server, setup_test_file):
    """Test that <5m effort persists after page reload"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Create task with 5m effort
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        task_title = "Persistent 5m task"
        page.type("#palette-input", task_title)
        page.keyboard.press("Enter")
        
        # Select <5m effort
        for _ in range(4):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("1")
        page.keyboard.press("Enter")
        
        # Wait for save
        page.wait_for_selector(".task-card", state="visible")
        time.sleep(0.5)
        
        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Check task still has 5m effort
        task_card = page.query_selector(".task-card")
        assert task_card is not None
        
        task_metadata = task_card.query_selector(".task-metadata")
        assert "<5m" in task_metadata.inner_text()
        
        # Verify in file
        content = TEST_TODOS_FILE.read_text()
        assert f"{task_title} @other !5m" in content
        
        browser.close()

def test_5m_effort_with_subtasks(server, setup_test_file):
    """Test <5m effort works correctly with subtasks"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL + "?test=true")
        page.wait_for_load_state("networkidle")
        
        # Create parent task with 5m effort
        page.keyboard.press("n")
        page.wait_for_selector("#palette-modal", state="visible")
        
        page.type("#palette-input", "Parent task with subtasks")
        page.keyboard.press("Enter")
        
        # Select <5m effort
        for _ in range(4):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("1")
        page.keyboard.press("Enter")
        
        # Wait for task to appear
        page.wait_for_selector(".task-card", state="visible")
        
        # Add subtask
        add_subtask_btn = page.query_selector(".add-subtask-btn")
        add_subtask_btn.click()
        
        subtask_input = page.query_selector(".subtask-input")
        page.type(".subtask-input", "Quick subtask")
        page.keyboard.press("Enter")
        
        # Verify parent still shows 5m effort
        task_metadata = page.query_selector(".task-metadata")
        assert "<5m" in task_metadata.inner_text()
        
        # Check XP calculation includes subtask bonus
        xp_display = page.query_selector(".xp-display")
        assert xp_display is not None
        
        browser.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])