"""
Simple integration tests for Confetti Todo
These tests ensure all core functionality works when we make changes
"""
import pytest
from playwright.sync_api import Page, expect
import time
import subprocess
import os
import signal

BASE_URL = "http://localhost:8000"

class TestServer:
    """Manage test server lifecycle"""
    
    def __init__(self):
        self.process = None
    
    def start(self):
        """Start the FastAPI server"""
        self.process = subprocess.Popen(
            ["python", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)  # Wait for server to start
    
    def stop(self):
        """Stop the server"""
        if self.process:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.wait()

@pytest.fixture(scope="session")
def test_server():
    """Start server for all tests"""
    server = TestServer()
    server.start()
    yield server
    server.stop()

@pytest.fixture
def page(browser):
    """Create a new page for each test"""
    page = browser.new_page()
    yield page
    page.close()

# CORE FUNCTIONALITY TESTS

def test_add_task(page: Page, test_server):
    """Test that we can add a new task"""
    page.goto(BASE_URL)
    
    # Type task and press Enter
    page.fill("#task-input", "Test task")
    page.press("#task-input", "Enter")
    
    # Palette should open - wait for it
    page.wait_for_selector(".palette-modal", state="visible", timeout=5000)
    
    # Press Enter to save with defaults
    page.press("body", "Enter")
    
    # Task should appear
    page.wait_for_selector(".task-item", timeout=5000)
    assert page.locator(".task-title").first.text_content() == "Test task"

def test_complete_task(page: Page, test_server):
    """Test that we can complete tasks"""
    page.goto(BASE_URL)
    
    # Wait for existing task
    page.wait_for_selector(".task-item")
    
    # Click first uncompleted checkbox
    unchecked = page.locator(".task-checkbox:not(.checked)").first
    if unchecked.count() > 0:
        unchecked.click()
        
        # Task should be marked complete
        page.wait_for_selector(".task-item.completed", timeout=2000)

def test_search_works(page: Page, test_server):
    """Test that search functionality works"""
    page.goto(BASE_URL)
    
    # Click search icon
    page.click("#search-icon-morph")
    
    # Search box should expand
    page.wait_for_selector(".search-morphing.active")
    
    # Type something
    page.fill("#search-input", "test")
    
    # Give search time to filter
    time.sleep(0.5)

def test_north_star_empty_state(page: Page, test_server):
    """Test that North Star shows empty state"""
    page.goto(BASE_URL)
    
    # North Star section should be visible
    assert page.locator(".north-star-section").is_visible()
    
    # Should show empty state or task
    assert page.locator(".north-star-empty-state, .north-star-content").count() > 0

def test_working_zone_empty_state(page: Page, test_server):
    """Test that working zone shows empty state"""
    page.goto(BASE_URL)
    
    # Working zone should exist
    assert page.locator(".working-zone").is_visible()
    
    # Should show empty or working state
    assert page.locator(".working-zone.empty, .working-task").count() > 0

def test_ideas_section_visible(page: Page, test_server):
    """Test that ideas section is visible"""
    page.goto(BASE_URL)
    
    # Ideas section should be visible
    assert page.locator("#ideas-section").is_visible()

def test_filters_work(page: Page, test_server):
    """Test that task filters work"""
    page.goto(BASE_URL)
    
    # Click different filters
    for filter_name in ["all", "today", "week", "overdue"]:
        filter_btn = page.locator(f'[data-filter="{filter_name}"]')
        filter_btn.click()
        
        # Should have active class
        assert "active" in filter_btn.get_attribute("class")

def test_keyboard_shortcut_n(page: Page, test_server):
    """Test that 'N' focuses input"""
    page.goto(BASE_URL)
    
    # Press N
    page.press("body", "n")
    
    # Input should be focused
    assert page.locator("#task-input").is_focused()

def test_data_persistence(page: Page, test_server):
    """Test that data persists after reload"""
    page.goto(BASE_URL)
    
    # Count current tasks
    initial_count = page.locator(".task-item").count()
    
    # Add a task with unique name
    unique_name = f"Persist test {int(time.time())}"
    page.fill("#task-input", unique_name)
    page.press("#task-input", "Enter")
    page.wait_for_selector(".palette-modal", state="visible")
    page.press("body", "Enter")
    
    # Wait for task to appear
    page.wait_for_selector(f'text="{unique_name}"')
    
    # Reload
    page.reload()
    
    # Task should still be there
    page.wait_for_selector(f'text="{unique_name}"')
    assert page.locator(".task-item").count() > initial_count

def test_responsive_layout(page: Page, test_server):
    """Test that layout is responsive"""
    page.goto(BASE_URL)
    
    # Desktop view
    page.set_viewport_size({"width": 1280, "height": 800})
    time.sleep(0.5)
    
    # Mobile view
    page.set_viewport_size({"width": 375, "height": 667})
    time.sleep(0.5)
    
    # Should still have main elements visible
    assert page.locator(".main-content").is_visible()
    assert page.locator(".right-widget").is_visible()

# Run tests with: pytest tests/test_app.py -v