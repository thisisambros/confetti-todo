"""Test the new due date feature in the task creation palette"""

import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta


def test_due_date_field_appears_first(page: Page):
    """Test that due date is the first field after title in the palette"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Open new task palette
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Test task with due date")
    page.keyboard.press("Enter")
    
    # Check that palette is open
    expect(page.locator("#palette-modal")).not_to_have_class("hidden")
    
    # Verify due date field is visible and is the first field
    due_date_field = page.locator("#due-date-field")
    expect(due_date_field).to_be_visible()
    
    # Check that Today is selected by default
    today_option = page.locator("#due-date-options .palette-option[data-value='today']")
    # The option might have keyboard-focus class in addition to selected
    expect(today_option).to_have_attribute("aria-checked", "true")
    
    print("✅ Due date field appears first with Today as default")


def test_due_date_options_navigation(page: Page):
    """Test navigating through due date options"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Open new task palette
    page.keyboard.press("n")
    page.fill("#task-input", "Task to test navigation")
    page.keyboard.press("Enter")
    
    # Test keyboard navigation with numbers
    page.keyboard.press("2")  # Select Tomorrow
    tomorrow_option = page.locator("#due-date-options .palette-option[data-value='tomorrow']")
    expect(tomorrow_option).to_have_class("selected")
    
    page.keyboard.press("3")  # Select This Week
    week_option = page.locator("#due-date-options .palette-option[data-value='this-week']")
    expect(week_option).to_have_class("selected")
    
    page.keyboard.press("4")  # Select No Due Date
    no_date_option = page.locator("#due-date-options .palette-option[data-value='no-date']")
    expect(no_date_option).to_have_class("selected")
    
    print("✅ Due date options navigation works correctly")


def test_custom_date_picker(page: Page):
    """Test the custom date picker functionality"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Open new task palette
    page.keyboard.press("n")
    page.fill("#task-input", "Task with custom date")
    page.keyboard.press("Enter")
    
    # Select "Pick Date..." option
    page.keyboard.press("5")
    pick_date_option = page.locator("#due-date-options .palette-option[data-value='pick-date']")
    expect(pick_date_option).to_have_class("selected")
    
    # Check that date picker appears
    date_picker_container = page.locator("#date-picker-container")
    expect(date_picker_container).not_to_have_class("hidden")
    
    # Check that date picker has today's date as default
    date_picker = page.locator("#custom-date-picker")
    today = datetime.now().strftime("%Y-%m-%d")
    expect(date_picker).to_have_value(today)
    
    # Set a custom date
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    date_picker.fill(future_date)
    
    print("✅ Custom date picker works correctly")


def test_save_task_with_due_date(page: Page):
    """Test saving a task with different due date options"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Test 1: Save task with Today
    page.keyboard.press("n")
    page.fill("#task-input", "Task due today")
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")  # Save with defaults (Today)
    
    # Verify task appears with today's date
    page.wait_for_selector(".task-item", state="visible")
    today_task = page.locator(".task-item").filter(has_text="Task due today")
    expect(today_task).to_be_visible()
    
    # Check for due date indicator
    due_date_span = today_task.locator(".task-due")
    expect(due_date_span).to_be_visible()
    expect(due_date_span).to_contain_text("📅")
    
    # Test 2: Save task with no due date
    page.keyboard.press("n")
    page.fill("#task-input", "Task with no due date")
    page.keyboard.press("Enter")
    page.keyboard.press("4")  # Select No Due Date
    page.keyboard.press("Enter")  # Save
    
    # Verify task appears without due date
    no_date_task = page.locator(".task-item").filter(has_text="Task with no due date")
    expect(no_date_task).to_be_visible()
    
    # Should not have due date indicator
    expect(no_date_task.locator(".task-due")).to_have_count(0)
    
    print("✅ Tasks save correctly with different due date options")


def test_due_date_field_hidden_for_ideas(page: Page):
    """Test that due date field is hidden when capturing ideas"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Open idea capture (press I)
    page.keyboard.press("i")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Test idea")
    page.keyboard.press("Enter")
    
    # Check that due date field is hidden
    due_date_field = page.locator("#due-date-field")
    expect(due_date_field).to_have_class("hidden")
    
    # Press Tab to reveal all fields
    page.keyboard.press("Tab")
    
    # Now due date field should be visible
    expect(due_date_field).not_to_have_class("hidden")
    
    print("✅ Due date field behaves correctly for ideas")


def test_due_date_field_order(page: Page):
    """Test that fields appear in the correct order with due date first"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Open new task palette
    page.keyboard.press("n")
    page.fill("#task-input", "Test field order")
    page.keyboard.press("Enter")
    
    # Get all visible fields
    fields = page.locator(".palette-field:not(.hidden)")
    
    # Check field order (title field doesn't have an ID, so we skip it)
    field_ids = []
    for i in range(fields.count()):
        field = fields.nth(i)
        field_id = field.get_attribute("id")
        if field_id:  # Skip the title field which has no ID
            field_ids.append(field_id)
    
    expected_order = ["due-date-field", "category-field", "priority-field", "effort-field", "friction-field"]
    assert field_ids == expected_order, f"Expected {expected_order}, got {field_ids}"
    
    print("✅ Fields appear in correct order with due date first")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])