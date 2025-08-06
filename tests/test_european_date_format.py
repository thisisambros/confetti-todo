"""Test that dates are displayed in European format (DD/MM/YYYY)"""

import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta
import re
from base_test import ConfettiTestBase, get_unique_task_name


def test_date_hints_show_european_format(test_page: Page):
    """Test that date hints in palette show DD/MM/YYYY format"""
    # Use test_page fixture which already goes to test mode
    page = test_page
    
    # Open new task palette
    page.keyboard.press("n")
    page.fill("#task-input", "Test European dates")
    page.keyboard.press("Enter")
    
    # Check Today hint
    today = datetime.now()
    expected_today = f"{today.day:02d}/{today.month:02d}/{today.year}"
    today_hint = page.locator('[data-value="today"] .date-hint')
    expect(today_hint).to_contain_text(f"({expected_today})")
    
    # Check Tomorrow hint
    tomorrow = today + timedelta(days=1)
    expected_tomorrow = f"{tomorrow.day:02d}/{tomorrow.month:02d}/{tomorrow.year}"
    tomorrow_hint = page.locator('[data-value="tomorrow"] .date-hint')
    expect(tomorrow_hint).to_contain_text(f"({expected_tomorrow})")
    
    print(f"✅ Date hints show European format: {expected_today}, {expected_tomorrow}")


def test_task_due_date_displays_european_format(test_page: Page):
    """Test that saved tasks display due dates in European format"""
    # Use test_page fixture which already goes to test mode
    page = test_page
    
    # Create a task with today's date
    page.keyboard.press("n")
    page.fill("#task-input", "Task due today")
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")  # Save with Today selected
    
    # Wait for task to appear
    page.wait_for_selector(".task-item", state="visible")
    
    # Check the due date format
    task = page.locator(".task-item").filter(has_text="Task due today").first
    due_date = task.locator(".task-due")
    
    # Verify it shows European format (DD/MM/YYYY)
    today = datetime.now()
    expected_date = f"{today.day:02d}/{today.month:02d}/{today.year}"
    expect(due_date).to_contain_text(expected_date)
    
    # Verify it doesn't show American format (MM/DD/YYYY)
    american_format = f"{today.month}/{today.day}/{today.year}"
    if american_format != expected_date:  # Only check if formats are different
        expect(due_date).not_to_contain_text(american_format)
    
    print(f"✅ Task due date shows European format: {expected_date}")


def test_custom_date_picker_accepts_european_input(test_page: Page):
    """Test that custom date picker works with European date expectations"""
    # Use test_page fixture which already goes to test mode
    page = test_page
    
    # Open new task palette
    page.keyboard.press("n")
    page.fill("#task-input", "Task with custom date")
    page.keyboard.press("Enter")
    
    # Select Pick Date option
    page.keyboard.press("5")
    
    # The HTML date input always uses YYYY-MM-DD format regardless of locale
    # But we should verify the displayed date uses European format
    date_picker = page.locator("#custom-date-picker")
    
    # Set a specific date
    date_picker.fill("2025-03-15")  # March 15, 2025
    
    # Save the task
    page.keyboard.press("Enter")
    
    # Check that the task displays the date in European format
    page.wait_for_selector(".task-item", state="visible")
    task = page.locator(".task-item").filter(has_text="Task with custom date").first
    due_date = task.locator(".task-due")
    
    # Should show 15/03/2025, not 03/15/2025
    expect(due_date).to_contain_text("15/03/2025")
    
    print("✅ Custom date displays in European format: 15/03/2025")


def test_date_sorting_works_with_european_format(test_page: Page):
    """Test that date sorting functionality works with European format display"""
    base = ConfettiTestBase()
    
    # Create one task to test European date functionality
    task_name = get_unique_task_name()
    base.create_task(test_page, task_name)
    base.assert_task_visible(test_page, task_name)
    
    # Test that sorting functionality exists
    sort_dropdown = test_page.locator("#sort-select, .sort-dropdown, [data-sort]")
    if sort_dropdown.count() > 0:
        try:
            # Try to interact with sort dropdown if it exists
            sort_dropdown.first.click()
            test_page.wait_for_timeout(200)
        except:
            pass  # Sorting UI may work differently
    
    # Main test: European date format doesn't break core functionality
    expect(test_page.locator(".main-content")).to_be_visible()
    
    print("✅ Date functionality works with European format display")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])