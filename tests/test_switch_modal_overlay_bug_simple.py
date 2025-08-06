"""
Test for switch modal overlay bug - simplified version
Testing that the grey overlay is properly removed after modal actions
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_overlay_removed_after_modal_action(page: Page):
    """Test that grey overlay is removed when modal is closed"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # First, let's check if there are existing tasks we can use
    tasks = page.locator(".task-item")
    task_count = tasks.count()
    print(f"Found {task_count} existing tasks")
    
    # If we have at least 2 tasks, use them. Otherwise create new ones.
    if task_count >= 2:
        # Use existing tasks
        first_task = tasks.first
        second_task = tasks.nth(1)
    else:
        # Need to create tasks - use simple approach
        # Add first task through the input
        page.locator("#task-input").click()
        page.locator("#task-input").fill("Test Task 1")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        # Press Enter to accept default type
        page.keyboard.press("Enter")
        time.sleep(1)
        
        # Add second task
        page.locator("#task-input").click()
        page.locator("#task-input").fill("Test Task 2")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        # Press Enter to accept default type
        page.keyboard.press("Enter")
        time.sleep(1)
        
        # Now find the tasks
        tasks = page.locator(".task-item")
        first_task = tasks.filter(has_text="Test Task 1").first
        second_task = tasks.filter(has_text="Test Task 2").first
    
    # Start the first task
    print("Starting first task...")
    work_btn = first_task.locator("button.work-btn")
    if work_btn.count() == 0:
        # Try alternative selector
        work_btn = first_task.locator("button:has-text('▶')")
    work_btn.click()
    time.sleep(0.5)
    
    # Verify working zone shows the task
    working_zone = page.locator(".working-zone")
    expect(working_zone).to_be_visible()
    
    # Try to start the second task - this should show the modal
    print("Trying to start second task...")
    work_btn2 = second_task.locator("button.work-btn")
    if work_btn2.count() == 0:
        work_btn2 = second_task.locator("button:has-text('▶')")
    work_btn2.click()
    time.sleep(0.5)
    
    # Verify modal and overlay are visible
    modal = page.locator(".switch-modal")
    overlay = page.locator(".modal-overlay")
    
    print(f"Modal visible: {modal.is_visible()}")
    print(f"Overlay count: {overlay.count()}")
    
    expect(modal).to_be_visible()
    
    # There might be multiple overlays, check at least one is visible
    visible_overlays = []
    for i in range(overlay.count()):
        ov = overlay.nth(i)
        if ov.is_visible():
            visible_overlays.append(i)
    
    print(f"Visible overlays: {visible_overlays}")
    assert len(visible_overlays) > 0, "No visible overlay found"
    
    # Click "Keep Working"
    print("Clicking Keep Working button...")
    keep_button = page.locator("button.keep-working")
    keep_button.click()
    time.sleep(0.5)
    
    # Modal should be hidden
    expect(modal).to_be_hidden()
    
    # Check all overlays - none should be visible
    visible_after_click = []
    for i in range(overlay.count()):
        ov = overlay.nth(i)
        if ov.is_visible():
            visible_after_click.append(i)
    
    print(f"Visible overlays after click: {visible_after_click}")
    assert len(visible_after_click) == 0, f"Overlay still visible after clicking Keep Working. Visible overlays: {visible_after_click}"
    
    # Verify we can interact with the page (no blocking overlay)
    task_input = page.locator("#task-input")
    task_input.click()
    task_input.fill("Test interaction works")
    # If overlay was still there, the click would fail


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed"])