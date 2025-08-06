"""
Test for switch modal overlay bug - the grey overlay remains after clicking buttons
Following TDD: Write failing test first, then fix the bug
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

class TestSwitchModalOverlayBug:
    """Test that modal overlay is properly removed after user action"""
    
    def test_overlay_removed_after_keep_working(self, page: Page):
        """Test that grey overlay is removed when clicking 'Keep Working'"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add first task
        page.locator("#task-input").fill("First Task")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        
        # Complete palette by pressing Enter on the default "task" option
        page.keyboard.press("Enter")
        time.sleep(0.5)
        
        # Add second task
        page.locator("#task-input").fill("Second Task")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        
        # Complete palette by pressing Enter on the default "task" option
        page.keyboard.press("Enter")
        time.sleep(0.5)
        
        # Debug: Take screenshot to see what's on screen
        page.screenshot(path="debug_before_click.png")
        
        # Start the first task
        first_task = page.locator(".task-item").filter(has_text="First Task")
        first_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to start the second task - this should show the modal
        second_task = page.locator(".task-item").filter(has_text="Second Task")
        second_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Verify modal and overlay are visible
        modal = page.locator(".switch-modal")
        overlay = page.locator(".modal-overlay").first  # Get first overlay if multiple
        
        expect(modal).to_be_visible()
        expect(overlay).to_be_visible()
        
        # Click "Keep Working"
        keep_button = page.locator("button.keep-working")
        keep_button.click()
        time.sleep(0.5)
        
        # Both modal and overlay should be hidden
        expect(modal).to_be_hidden()
        expect(overlay).to_be_hidden()
        
        # Verify we can interact with the page (no blocking overlay)
        # Try clicking the task input to ensure no overlay is blocking
        task_input = page.locator("#task-input")
        task_input.click()
        task_input.fill("Test interaction")
        # If overlay was still there, this would fail
        
    def test_overlay_removed_after_switch_task(self, page: Page):
        """Test that grey overlay is removed when clicking 'Switch Task'"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add two tasks
        page.locator("#task-input").fill("Task A")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        
        page.locator("#task-input").fill("Task B")
        page.locator("#task-input").press("Enter")
        time.sleep(0.5)
        
        # Start Task A
        task_a = page.locator(".task-item").filter(has_text="Task A")
        task_a.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to start Task B - this should show the modal
        task_b = page.locator(".task-item").filter(has_text="Task B")
        task_b.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Verify modal and overlay are visible
        modal = page.locator(".switch-modal")
        overlay = page.locator(".modal-overlay").first
        
        expect(modal).to_be_visible()
        expect(overlay).to_be_visible()
        
        # Click "Switch Task"
        switch_button = page.locator("button.switch-task")
        switch_button.click()
        time.sleep(0.5)
        
        # Both modal and overlay should be hidden
        expect(modal).to_be_hidden()
        expect(overlay).to_be_hidden()
        
        # Verify the task actually switched
        working_zone = page.locator(".working-zone")
        expect(working_zone).to_contain_text("Task B")
        
        # Verify we can interact with the page
        task_input = page.locator("#task-input")
        task_input.click()
        task_input.fill("Test after switch")
        
    def test_overlay_removed_on_mobile(self, page: Page):
        """Test that overlay is properly removed on mobile too"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add tasks using mobile flow
        page.locator("#mobile-add-task").click()
        time.sleep(0.3)
        mobile_input = page.locator("input.mobile-task-input")
        mobile_input.fill("Mobile Task 1")
        mobile_input.press("Enter")
        time.sleep(0.5)
        
        page.locator("#mobile-add-task").click()
        time.sleep(0.3)
        mobile_input = page.locator("input.mobile-task-input")
        mobile_input.fill("Mobile Task 2")
        mobile_input.press("Enter")
        time.sleep(0.5)
        
        # Start first task using mobile quick actions
        task1 = page.locator(".task-item").filter(has_text="Mobile Task 1")
        task1.locator(".task-quick-actions button.work").click()
        time.sleep(0.5)
        
        # Try to start second task
        task2 = page.locator(".task-item").filter(has_text="Mobile Task 2")
        task2.locator(".task-quick-actions button.work").click()
        time.sleep(0.5)
        
        # Verify modal and overlay are visible
        modal = page.locator(".switch-modal")
        overlay = page.locator(".modal-overlay").first
        
        expect(modal).to_be_visible()
        expect(overlay).to_be_visible()
        
        # Click keep working
        keep_button = page.locator("button.keep-working")
        keep_button.click()
        time.sleep(0.5)
        
        # Both should be hidden
        expect(modal).to_be_hidden()
        expect(overlay).to_be_hidden()
        
        # Verify we can interact with mobile UI
        page.locator("#mobile-add-task").click()
        time.sleep(0.3)
        # This would fail if overlay was blocking
        mobile_input = page.locator("input.mobile-task-input")
        expect(mobile_input).to_be_visible()
        mobile_input.press("Escape")  # Close the input
        
    def test_multiple_overlays_not_created(self, page: Page):
        """Test that multiple overlays are not created on repeated modal shows"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add tasks
        for i in range(3):
            page.locator("#task-input").fill(f"Task {i+1}")
            page.locator("#task-input").press("Enter")
            time.sleep(0.3)
        
        # Start Task 1
        page.locator(".task-item").filter(has_text="Task 1").locator(".work-btn").click()
        time.sleep(0.5)
        
        # Repeatedly try to switch tasks
        for i in range(3):
            # Try to start Task 2
            page.locator(".task-item").filter(has_text="Task 2").locator(".work-btn").click()
            time.sleep(0.5)
            
            # Click keep working
            page.locator("button.keep-working").click()
            time.sleep(0.5)
        
        # Count overlays - should be 0 or 1 max (hidden)
        overlays = page.locator(".modal-overlay")
        overlay_count = overlays.count()
        
        # Should have at most 1 overlay element
        assert overlay_count <= 1, f"Found {overlay_count} overlay elements, expected 0 or 1"
        
        # If there is an overlay, it should be hidden
        if overlay_count == 1:
            expect(overlays.first).to_be_hidden()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])