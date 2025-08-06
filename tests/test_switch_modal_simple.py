"""Simple test to verify the switch modal fix works correctly"""

import pytest
from playwright.sync_api import Page, expect


def test_switch_modal_no_timer(page: Page):
    """Test that the switch modal doesn't have a timer and doesn't break the page"""
    # Navigate to the app
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Add two tasks using the keyboard shortcut
    # First task - press N to open palette
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Task One")
    page.keyboard.press("Enter")  # This opens the palette
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")  # Save with defaults
    
    # Second task
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Task Two")
    page.keyboard.press("Enter")  # This opens the palette
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")  # Save with defaults
    
    # Wait for tasks to appear
    page.wait_for_selector(".task-item", state="visible")
    
    # Start working on first task
    first_play_button = page.locator(".task-item").first.locator(".work-btn")
    first_play_button.click()
    
    # Verify working zone shows the task
    expect(page.locator("#working-zone")).to_contain_text("Task One")
    
    # Try to work on second task - this should show the modal
    second_play_button = page.locator(".task-item").nth(1).locator(".work-btn")
    second_play_button.click()
    
    # Verify modal appears
    expect(page.locator(".switch-modal")).to_be_visible()
    expect(page.locator(".modal-overlay")).to_be_visible()
    
    # Verify NO countdown element
    expect(page.locator(".countdown")).to_have_count(0)
    
    # Verify modal has both buttons
    expect(page.locator("button:has-text('Yes, switch')")).to_be_visible()
    expect(page.locator("button:has-text('No, keep working')")).to_be_visible()
    
    # Test Yes button - switch tasks
    page.click("button:has-text('Yes, switch')")
    
    # Modal should disappear
    expect(page.locator(".switch-modal")).to_be_hidden()
    expect(page.locator(".modal-overlay")).to_be_hidden()
    
    # Should now be working on Task Two
    expect(page.locator("#working-zone")).to_contain_text("Task Two")
    
    # Page should still be interactive - test by pressing N for new task
    page.keyboard.press("n")
    expect(page.locator("#task-input")).to_be_visible()
    page.keyboard.press("Escape")  # Cancel
    
    print("✅ Switch modal test passed - no timer, page remains interactive")


def test_switch_modal_cancel_keeps_current_task(page: Page):
    """Test that canceling the switch keeps the current task"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Add two tasks
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Current Task")
    page.keyboard.press("Enter")
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")
    
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Other Task")
    page.keyboard.press("Enter")
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")
    
    # Start working on first task
    page.locator(".task-item").first.locator(".work-btn").click()
    
    # Try to switch
    page.locator(".task-item").nth(1).locator(".work-btn").click()
    
    # Click No to keep working
    page.click("button:has-text('No, keep working')")
    
    # Should still be working on Current Task
    expect(page.locator("#working-zone")).to_contain_text("Current Task")
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    print("✅ Cancel switch test passed")


def test_switch_modal_overlay_click_cancels(page: Page):
    """Test that clicking the overlay cancels the switch"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Add two tasks
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Task A")
    page.keyboard.press("Enter")
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")
    
    page.keyboard.press("n")
    page.wait_for_selector("#task-input", state="visible")
    page.fill("#task-input", "Task B")
    page.keyboard.press("Enter")
    page.wait_for_selector("#palette-modal:not(.hidden)", state="visible")
    page.keyboard.press("Enter")
    
    # Start working on first task
    page.locator(".task-item").first.locator(".work-btn").click()
    
    # Try to switch
    page.locator(".task-item").nth(1).locator(".work-btn").click()
    
    # Click overlay (outside modal)
    page.locator(".modal-overlay").click(position={"x": 10, "y": 10})
    
    # Should still be working on Task A
    expect(page.locator("#working-zone")).to_contain_text("Task A")
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    print("✅ Overlay click cancel test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])  # Run with browser visible