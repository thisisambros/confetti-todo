"""
Regression test for the checkbox bug where completing one task
makes all other tasks disappear with an error
"""
import pytest
from playwright.sync_api import Page, expect
import time
from base_test import ConfettiTestBase, get_unique_task_name

def test_completing_task_preserves_other_tasks(test_page: Page):
    """
    REGRESSION TEST: Completing one task should NOT:
    1. Make other tasks disappear
    2. Show any error messages
    3. Fail to save the completion
    """
    base = ConfettiTestBase()
    
    # Create some test tasks to ensure we have data
    test_task1 = get_unique_task_name()
    test_task2 = get_unique_task_name()
    base.create_task(test_page, test_task1)
    base.create_task(test_page, test_task2)
    
    # Wait for tasks to load
    test_page.wait_for_selector(".task-item", timeout=5000)
    
    # Count initial tasks
    initial_task_count = test_page.locator(".task-item").count()
    assert initial_task_count >= 2, "Need at least 2 tasks to test completion"
    
    # Complete the first uncompleted task
    base.complete_first_uncompleted_task(test_page)
    
    # Wait a moment for any errors to appear
    test_page.wait_for_timeout(1000)
    
    # Check for error messages
    error_toasts = test_page.locator(".toast:has-text('error'), .toast:has-text('Error'), .toast:has-text('fail')")
    expect(error_toasts).to_have_count(0)
    
    # Check that remaining tasks are still visible
    remaining_task_count = test_page.locator(".task-item").count()
    assert remaining_task_count >= 1, "Should still have uncompleted tasks visible"
    
    # Verify we got the success feedback (confetti or XP)
    success_indicators = test_page.locator(".toast:has-text('XP'), .confetti")
    success_count = success_indicators.count()
    assert success_count > 0, "Should have success feedback (XP toast or confetti)"

def test_api_receives_correct_data_on_complete(test_page: Page):
    """
    Test that the API receives properly formatted data when completing a task
    """
    base = ConfettiTestBase()
    
    # Create a test task
    test_task = get_unique_task_name()
    base.create_task(test_page, test_task)
    
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
    
    test_page.route("**/api/todos", handle_request)
    
    # Complete the task
    base.complete_first_uncompleted_task(test_page)
    
    # Wait for API call
    test_page.wait_for_timeout(1000)
    
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