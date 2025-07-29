"""
Regression test for the checkbox bug where completing one task
makes all other tasks disappear with an error
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

def test_completing_task_preserves_other_tasks(page: Page, test_server):
    """
    REGRESSION TEST: Completing one task should NOT:
    1. Make other tasks disappear
    2. Show any error messages
    3. Fail to save the completion
    """
    page.goto(BASE_URL)
    
    # Wait for initial tasks to load
    page.wait_for_selector(".task-item", timeout=5000)
    
    # Count initial tasks
    initial_task_count = page.locator(".task-item").count()
    assert initial_task_count > 0, "No tasks found to test with"
    
    # Get text of all tasks before clicking
    tasks_before = []
    for i in range(initial_task_count):
        task_text = page.locator(".task-item .task-title").nth(i).text_content()
        tasks_before.append(task_text)
    
    print(f"Tasks before: {tasks_before}")
    
    # Find first unchecked checkbox
    unchecked_checkbox = page.locator(".task-checkbox:not(.checked)").first
    if unchecked_checkbox.count() == 0:
        # All tasks are already checked, let's uncheck one first
        checked_checkbox = page.locator(".task-checkbox.checked").first
        assert checked_checkbox.count() > 0, "No tasks found at all"
        checked_checkbox.click()
        time.sleep(0.5)
        # Now find the unchecked one
        unchecked_checkbox = page.locator(".task-checkbox:not(.checked)").first
    
    assert unchecked_checkbox.count() > 0, "No unchecked tasks found"
    
    # Click the checkbox
    unchecked_checkbox.click()
    
    # Wait a moment for any errors to appear
    time.sleep(1)
    
    # Check for error messages
    error_toasts = page.locator(".toast:has-text('error'), .toast:has-text('Error'), .toast:has-text('fail')").count()
    assert error_toasts == 0, "Error message appeared after completing task"
    
    # Check that we still have tasks (at least the same number minus potentially completed ones)
    remaining_task_count = page.locator(".task-item").count()
    assert remaining_task_count > 0, "All tasks disappeared after completing one!"
    
    # The count should be one less because completed tasks are hidden
    assert remaining_task_count == initial_task_count - 1, \
        f"Task count should decrease by 1 when completing a task (from {initial_task_count} to {initial_task_count - 1}), but got {remaining_task_count}"
    
    # Since completed tasks are hidden, we can't check for .task-item.completed
    # But we should verify no error occurred and the task disappeared properly
    
    # Verify we got the success toast with XP
    success_toast = page.locator(".toast:has-text('XP')").count()
    assert success_toast > 0, "No success message with XP shown"
    
    # Get text of all remaining tasks
    tasks_after = []
    for i in range(remaining_task_count):
        task_text = page.locator(".task-item .task-title").nth(i).text_content()
        tasks_after.append(task_text)
    
    print(f"Tasks after: {tasks_after}")
    
    # The completed task should not be in the list anymore
    assert len(tasks_after) == len(tasks_before) - 1, "Completed task should be hidden"

def test_api_receives_correct_data_on_complete(page: Page, test_server):
    """
    Test that the API receives properly formatted data when completing a task
    """
    page.goto(BASE_URL)
    
    # Set up request interception to capture API calls
    api_calls = []
    
    def handle_request(route, request):
        if request.url.endswith("/api/todos") and request.method == "POST":
            api_calls.append({
                "url": request.url,
                "method": request.method,
                "data": request.post_data
            })
        route.continue_()
    
    page.route("**/api/todos", handle_request)
    
    # Wait for tasks and complete one
    page.wait_for_selector(".task-item")
    page.locator(".task-checkbox:not(.checked)").first.click()
    
    # Wait for API call
    time.sleep(1)
    
    # Verify API was called
    assert len(api_calls) > 0, "No API call made when completing task"
    
    # Check the data sent
    import json
    data = json.loads(api_calls[0]["data"])
    
    # Data should have the expected structure
    assert isinstance(data, dict), "API data should be a dictionary"
    assert "today" in data or "ideas" in data or "backlog" in data, \
        "API data missing expected sections"
    
    # The data should not be empty
    total_tasks = sum(len(data.get(section, [])) for section in ["today", "ideas", "backlog"])
    assert total_tasks > 0, "API received empty task data"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])