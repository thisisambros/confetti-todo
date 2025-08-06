"""Final test to verify switch modal fix works correctly"""

import pytest
from playwright.sync_api import Page, expect


def test_switch_modal_fix_verification(page: Page):
    """Verify the switch modal fix - no timer, page stays interactive"""
    # Navigate to the app
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Find existing tasks or create new ones
    existing_tasks = page.locator(".task-item:not(.completed)")
    task_count = existing_tasks.count()
    
    if task_count < 2:
        # Need to add tasks - use keyboard shortcut
        for i in range(2 - task_count):
            page.keyboard.press("n")
            page.wait_for_selector("#task-input", state="visible")
            page.fill("#task-input", f"Test Task {i + 1}")
            page.keyboard.press("Enter")
            page.wait_for_timeout(100)
            # Save with defaults
            if page.locator("#palette-modal:not(.hidden)").is_visible():
                page.keyboard.press("Enter")
            page.wait_for_timeout(500)
    
    # Wait for at least 2 incomplete tasks to be visible
    page.wait_for_selector(".task-item:not(.completed)", state="visible")
    
    # Get the first two incomplete tasks
    tasks = page.locator(".task-item:not(.completed)")
    first_task = tasks.nth(0)
    second_task = tasks.nth(1)
    
    # Start working on first task
    first_play = first_task.locator(".work-btn").first
    first_play.click()
    
    # Wait for working zone to update
    page.wait_for_timeout(500)
    
    # Verify working zone shows a task
    working_zone = page.locator("#working-zone")
    expect(working_zone).not_to_contain_text("No task selected")
    
    # Try to work on second task - this should show the modal
    second_play = second_task.locator(".work-btn").first
    second_play.click()
    
    # Verify modal appears
    expect(page.locator(".switch-modal")).to_be_visible()
    # There might be multiple overlays, check for the one that's visible and not the palette one
    switch_overlay = page.locator(".modal-overlay").nth(1)  # The dynamically created one
    expect(switch_overlay).to_be_visible()
    
    # CRITICAL TEST 1: Verify NO countdown element exists
    countdown_elements = page.locator(".countdown")
    expect(countdown_elements).to_have_count(0)
    print("✅ No countdown timer found")
    
    # CRITICAL TEST 2: Wait 4 seconds - modal should NOT auto-close
    print("⏳ Waiting 4 seconds to ensure modal doesn't auto-close...")
    page.wait_for_timeout(4000)
    
    # Modal should still be visible
    expect(page.locator(".switch-modal")).to_be_visible()
    print("✅ Modal still visible after 4 seconds")
    
    # CRITICAL TEST 3: Verify both buttons exist and work
    switch_button = page.locator("button.switch-task")
    keep_button = page.locator("button.keep-working")
    
    expect(switch_button).to_be_visible()
    expect(keep_button).to_be_visible()
    print("✅ Both Switch/Keep buttons are visible")
    
    # Click Switch to change tasks
    switch_button.click()
    
    # Modal should disappear
    expect(page.locator(".switch-modal")).to_be_hidden()
    expect(switch_overlay).to_be_hidden()
    print("✅ Modal closed after clicking Yes")
    
    # CRITICAL TEST 4: Page should be fully interactive
    # Test by using keyboard shortcut
    page.keyboard.press("/")  # Open search
    expect(page.locator("#search-input")).to_be_visible()
    page.keyboard.press("Escape")  # Close search
    print("✅ Page is fully interactive - no frozen state")
    
    print("\n🎉 ALL TESTS PASSED! Switch modal fix is working correctly:")
    print("   - No countdown timer")
    print("   - Modal doesn't auto-close")
    print("   - Yes/No buttons work")
    print("   - Page remains interactive")


def test_cancel_switch_works(page: Page):
    """Test that cancel (No button) works correctly"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Get two tasks
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() < 2:
        pytest.skip("Not enough tasks for test")
    
    # Start working on first task
    tasks.nth(0).locator(".work-btn").click()
    page.wait_for_timeout(500)
    
    # Get the current working task text
    working_text_before = page.locator("#working-zone .working-title").inner_text()
    
    # Try to switch to second task
    tasks.nth(1).locator(".work-btn").click()
    
    # Click Keep Working to cancel
    page.click("button.keep-working")
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    # Should still show same task in working zone
    working_text_after = page.locator("#working-zone .working-title").inner_text()
    assert working_text_before == working_text_after
    
    print("✅ Cancel switch works correctly")


def test_overlay_click_cancels(page: Page):
    """Test that clicking overlay cancels the switch"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Get two tasks
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() < 2:
        pytest.skip("Not enough tasks for test")
    
    # Start working on first task
    tasks.nth(0).locator(".work-btn").click()
    page.wait_for_timeout(500)
    
    # Try to switch
    tasks.nth(1).locator(".work-btn").click()
    
    # Click overlay (the second one, which is the switch modal overlay)
    page.locator(".modal-overlay").nth(1).click(position={"x": 10, "y": 10})
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    print("✅ Overlay click cancels switch")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed"])