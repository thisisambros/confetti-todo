"""
Test that subtasks remain visible after adding a new subtask
"""
import pytest
from playwright.sync_api import Page, expect
import time
import re

BASE_URL = "http://localhost:8000"

def test_subtask_remains_expanded_after_add(page: Page):
    """Test that accordion stays open after adding a subtask"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find a task to add subtask to
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    # Use the first task
    first_task = tasks.first
    # Get just the task title text, not including the toggle
    task_title_element = first_task.locator(".task-title span").last
    task_title = task_title_element.inner_text()
    print(f"Adding subtask to: {task_title}")
    
    # Check initial state - subtasks should be collapsed
    subtask_toggle = first_task.locator(".subtask-toggle")
    if subtask_toggle.count() > 0:
        # Task already has subtasks, expand them first
        initial_toggle_text = subtask_toggle.inner_text()
        if initial_toggle_text == "▶":
            subtask_toggle.click()
            time.sleep(0.3)
    
    # Click add subtask button
    add_subtask_btn = first_task.locator(".subtask-btn, button:has-text('+ Add Subtask')")
    add_subtask_btn.click()
    time.sleep(0.3)
    
    # Find the subtask input
    subtask_input = page.locator(".subtask-input input")
    expect(subtask_input).to_be_visible()
    
    # Enter subtask title
    subtask_title = "Test subtask - should be visible"
    subtask_input.fill(subtask_title)
    
    # Save the subtask
    subtask_input.press("Enter")
    time.sleep(1)  # Wait for save and re-render
    
    # Find the task again (it may have been re-rendered)
    updated_task = page.locator(".task-item").filter(has_text=task_title).first
    
    # Check that the subtask toggle shows expanded state
    updated_toggle = updated_task.locator(".subtask-toggle")
    expect(updated_toggle).to_be_visible()
    toggle_text = updated_toggle.inner_text()
    assert toggle_text == "▼", f"Expected expanded toggle (▼) but got {toggle_text}"
    
    # Find all visible subtasks on the page
    all_subtasks = page.locator(".task-item.subtask.visible")
    
    # Find the specific subtask we just added
    found = False
    for i in range(all_subtasks.count()):
        subtask = all_subtasks.nth(i)
        if subtask_title in subtask.inner_text():
            found = True
            # Verify it has the 'visible' class
            expect(subtask).to_have_class(re.compile(r"visible"))
            break
    
    assert found, f"Could not find subtask with title: {subtask_title}"
    
    print("✓ Subtask is visible after adding")
    print("✓ Parent task accordion remains expanded")
    
    # Take screenshot for verification
    updated_task.screenshot(path="subtask_expanded_after_add.png")
    print("Screenshot saved: subtask_expanded_after_add.png")


def test_multiple_subtasks_remain_visible(page: Page):
    """Test adding multiple subtasks keeps them all visible"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    first_task = tasks.first
    # Get just the task title text, not including the toggle
    task_title_element = first_task.locator(".task-title span").last
    task_title = task_title_element.inner_text()
    
    # Add multiple subtasks
    for i in range(3):
        # Click add subtask
        add_btn = first_task.locator(".subtask-btn, button:has-text('+ Add Subtask')")
        add_btn.click()
        time.sleep(0.3)
        
        # Enter subtask
        subtask_input = page.locator(".subtask-input input")
        subtask_input.fill(f"Subtask {i+1}")
        subtask_input.press("Enter")
        time.sleep(0.5)
        
        # Re-find the task after re-render
        first_task = page.locator(".task-item").filter(has_text=task_title).first
    
    # Verify all subtasks are visible
    subtasks = page.locator(".task-item.subtask.visible")
    actual_count = subtasks.count()
    assert actual_count >= 3, f"Expected at least 3 visible subtasks, found {actual_count}"
    
    # Verify parent is still expanded
    toggle = first_task.locator(".subtask-toggle")
    assert toggle.inner_text() == "▼", "Parent task should remain expanded"
    
    print(f"✓ All {actual_count} subtasks are visible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])