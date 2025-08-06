"""Test the stacked checkbox progress visualization for subtasks"""

import pytest
from playwright.sync_api import Page, expect
import time


def test_mini_checkboxes_display(page: Page):
    """Test that mini checkboxes appear for tasks with subtasks"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Create a task with subtasks
    page.keyboard.press("n")
    page.fill("#task-input", "Task with subtasks")
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")  # Save with defaults
    
    # Wait for task to appear
    page.wait_for_selector(".task-item", state="visible")
    
    # Find the task and add subtasks
    task = page.locator(".task-item").filter(has_text="Task with subtasks").first
    task.locator(".subtask-btn").click()
    
    # Add first subtask
    page.fill(".subtask-input input", "Subtask 1")
    page.click(".save-subtask")
    page.wait_for_timeout(200)
    
    # Add second subtask
    task.locator(".subtask-btn").click()
    page.fill(".subtask-input input", "Subtask 2")
    page.click(".save-subtask")
    page.wait_for_timeout(200)
    
    # Add third subtask
    task.locator(".subtask-btn").click()
    page.fill(".subtask-input input", "Subtask 3")
    page.click(".save-subtask")
    page.wait_for_timeout(200)
    
    # Verify mini checkboxes container appears
    progress_container = task.locator(".task-progress-checkboxes")
    expect(progress_container).to_be_visible()
    
    # Verify 3 mini checkboxes are displayed
    mini_checkboxes = progress_container.locator(".mini-checkbox")
    expect(mini_checkboxes).to_have_count(3)
    
    # Verify progress counter shows 0/3
    counter = task.locator(".task-progress-counter")
    expect(counter).to_have_text("0/3")
    
    print("✅ Mini checkboxes display correctly for tasks with subtasks")


def test_mini_checkbox_click_toggle(page: Page):
    """Test clicking mini checkboxes toggles subtask completion"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Find task with subtasks (from previous test or create new)
    task = page.locator(".task-item").filter(has_text="Task with subtasks").first
    
    if task.count() == 0:
        # Create task if doesn't exist
        page.keyboard.press("n")
        page.fill("#task-input", "Task with subtasks")
        page.keyboard.press("Enter")
        page.keyboard.press("Enter")
        page.wait_for_selector(".task-item", state="visible")
        
        task = page.locator(".task-item").filter(has_text="Task with subtasks").first
        # Add subtasks
        for i in range(3):
            task.locator(".subtask-btn").click()
            page.fill(".subtask-input input", f"Subtask {i+1}")
            page.click(".save-subtask")
            page.wait_for_timeout(200)
    
    # Get mini checkboxes
    progress_container = task.locator(".task-progress-checkboxes")
    mini_checkboxes = progress_container.locator(".mini-checkbox")
    
    # Click first mini checkbox
    mini_checkboxes.nth(0).click()
    page.wait_for_timeout(300)
    
    # Verify it's marked as completed
    expect(mini_checkboxes.nth(0)).to_have_class("mini-checkbox completed")
    
    # Verify counter updated to 1/3
    counter = task.locator(".task-progress-counter")
    expect(counter).to_have_text("1/3")
    
    # Click second mini checkbox
    mini_checkboxes.nth(1).click()
    page.wait_for_timeout(300)
    
    # Verify counter updated to 2/3
    expect(counter).to_have_text("2/3")
    
    # Click first checkbox again to uncheck
    mini_checkboxes.nth(0).click()
    page.wait_for_timeout(300)
    
    # Verify it's no longer completed
    expect(mini_checkboxes.nth(0)).not_to_have_class("mini-checkbox completed")
    expect(counter).to_have_text("1/3")
    
    print("✅ Mini checkbox click toggling works correctly")


def test_hover_tooltip_display(page: Page):
    """Test that hovering over checkboxes shows subtask details"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Find task with subtasks
    task = page.locator(".task-item").filter(has_text="Task with subtasks").first
    progress_container = task.locator(".task-progress-checkboxes")
    
    # Hover over the progress container
    progress_container.hover()
    page.wait_for_timeout(100)
    
    # Check for tooltip
    tooltip = page.locator(".subtask-tooltip")
    expect(tooltip).to_be_visible()
    
    # Verify tooltip content
    expect(tooltip).to_contain_text("Subtask 1")
    expect(tooltip).to_contain_text("Subtask 2")
    expect(tooltip).to_contain_text("Subtask 3")
    
    # Move mouse away
    page.mouse.move(0, 0)
    page.wait_for_timeout(100)
    
    # Tooltip should disappear
    expect(tooltip).not_to_be_visible()
    
    print("✅ Hover tooltip displays subtask details correctly")


def test_all_subtasks_completed_bonus(page: Page):
    """Test XP bonus when all subtasks are completed"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Create a new task with subtasks
    page.keyboard.press("n")
    page.fill("#task-input", "Complete all subtasks test")
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")
    
    page.wait_for_selector(".task-item", state="visible")
    task = page.locator(".task-item").filter(has_text="Complete all subtasks test").first
    
    # Add 2 subtasks
    for i in range(2):
        task.locator(".subtask-btn").click()
        page.fill(".subtask-input input", f"Test subtask {i+1}")
        page.click(".save-subtask")
        page.wait_for_timeout(200)
    
    # Get initial XP value
    xp_element = task.locator(".task-xp")
    initial_xp = xp_element.inner_text()
    
    # Complete both subtasks using mini checkboxes
    progress_container = task.locator(".task-progress-checkboxes")
    mini_checkboxes = progress_container.locator(".mini-checkbox")
    
    mini_checkboxes.nth(0).click()
    page.wait_for_timeout(300)
    mini_checkboxes.nth(1).click()
    page.wait_for_timeout(300)
    
    # Verify all checkboxes are completed
    expect(mini_checkboxes.nth(0)).to_have_class("mini-checkbox completed")
    expect(mini_checkboxes.nth(1)).to_have_class("mini-checkbox completed")
    
    # Verify counter shows 2/2
    counter = task.locator(".task-progress-counter")
    expect(counter).to_have_text("2/2")
    
    # Verify XP bonus is applied (should have ✨ emoji)
    expect(xp_element).to_contain_text("✨")
    
    print("✅ XP bonus applied when all subtasks completed")


def test_mini_checkbox_hover_effects(page: Page):
    """Test hover effects on individual mini checkboxes"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Find task with subtasks
    task = page.locator(".task-item").filter(has_text="Task with subtasks").first
    progress_container = task.locator(".task-progress-checkboxes")
    first_checkbox = progress_container.locator(".mini-checkbox").first
    
    # Get initial position and size
    box_before = first_checkbox.bounding_box()
    
    # Hover over individual checkbox
    first_checkbox.hover()
    page.wait_for_timeout(100)
    
    # Check that title attribute shows subtask name
    title = first_checkbox.get_attribute("title")
    assert title == "Subtask 1", f"Expected title 'Subtask 1', got '{title}'"
    
    # Move away and hover over another checkbox
    second_checkbox = progress_container.locator(".mini-checkbox").nth(1)
    second_checkbox.hover()
    page.wait_for_timeout(100)
    
    title = second_checkbox.get_attribute("title")
    assert title == "Subtask 2", f"Expected title 'Subtask 2', got '{title}'"
    
    print("✅ Mini checkbox hover effects work correctly")


def test_progress_bar_removed(page: Page):
    """Verify old progress bar elements are completely removed"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Check that no old progress bar elements exist
    old_progress = page.locator(".task-progress")
    expect(old_progress).to_have_count(0)
    
    old_progress_fill = page.locator(".task-progress-fill")
    expect(old_progress_fill).to_have_count(0)
    
    print("✅ Old progress bar elements successfully removed")


def test_empty_task_no_checkboxes(page: Page):
    """Test that tasks without subtasks don't show checkboxes"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Create a task without subtasks
    page.keyboard.press("n")
    page.fill("#task-input", "Task without subtasks")
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")
    
    page.wait_for_selector(".task-item", state="visible")
    task = page.locator(".task-item").filter(has_text="Task without subtasks").first
    
    # Verify no progress checkboxes appear
    progress_container = task.locator(".task-progress-checkboxes")
    expect(progress_container).to_have_count(0)
    
    # Verify no progress counter appears
    counter = task.locator(".task-progress-counter")
    expect(counter).to_have_count(0)
    
    print("✅ Tasks without subtasks correctly show no progress indicators")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])