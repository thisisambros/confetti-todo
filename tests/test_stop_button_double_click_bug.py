"""
Test for stop button requiring double click - this is a bug
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_stop_button_single_click(page: Page):
    """Test that stop button works with a single click"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find a task to start
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    # Start the first task
    first_task = tasks.first
    work_btn = first_task.locator(".work-btn")
    work_btn.click()
    time.sleep(0.5)
    
    # Verify task is running in working zone
    working_zone = page.locator(".working-zone")
    expect(working_zone).to_be_visible()
    expect(working_zone).not_to_have_class("empty")
    
    # Find and click the stop button
    stop_btn = working_zone.locator("button.stop-working-btn")
    expect(stop_btn).to_be_visible()
    
    # Click stop button once
    print("Clicking stop button...")
    stop_btn.click()
    time.sleep(0.5)
    
    # Working zone should show empty state after single click
    expect(working_zone).to_have_class("working-zone empty")
    
    # Verify no task is running
    working_task_info = working_zone.locator(".working-task-info")
    expect(working_task_info).to_be_hidden()


def test_stop_button_on_mobile(page: Page):
    """Test that stop button works with single click on mobile too"""
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find and start a task
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    first_task = tasks.first
    # Use mobile quick action
    quick_work = first_task.locator(".task-quick-actions .work")
    if quick_work.count() > 0:
        quick_work.click()
    else:
        first_task.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Click stop button once
    working_zone = page.locator(".working-zone")
    stop_btn = working_zone.locator("button.stop-working-btn")
    stop_btn.click()
    time.sleep(0.5)
    
    # Should be stopped after single click
    expect(working_zone).to_have_class("working-zone empty")


def test_stop_button_click_count(page: Page):
    """Test that stop button doesn't require multiple clicks"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    # Start a task
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Set up to count clicks
    click_count = 0
    
    def count_clicks():
        nonlocal click_count
        click_count += 1
    
    # Add event listener to count clicks
    page.evaluate("""
        window.stopClickCount = 0;
        const stopBtn = document.querySelector('.stop-working-btn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                window.stopClickCount++;
            });
        }
    """)
    
    # Click stop button
    stop_btn = page.locator("button.stop-working-btn")
    stop_btn.click()
    time.sleep(0.5)
    
    # Check if working zone is empty
    working_zone = page.locator(".working-zone")
    is_empty = "empty" in working_zone.get_attribute("class")
    
    # Get click count
    actual_clicks = page.evaluate("window.stopClickCount")
    
    print(f"Stop button was clicked {actual_clicks} times")
    print(f"Working zone is empty: {is_empty}")
    
    # Should only need one click
    assert is_empty, "Working zone should be empty after one click"
    assert actual_clicks == 1, f"Expected 1 click, but got {actual_clicks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])