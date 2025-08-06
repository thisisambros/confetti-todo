"""
End-to-end Playwright tests for the Switch Task Modal feature.
These tests verify the actual UI behavior in a real browser.
"""

import pytest
from playwright.sync_api import Page, expect
import time
import re


class TestSwitchTaskModalE2E:
    """E2E tests for switch task modal using Playwright"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup for each test"""
        # Navigate to the app
        page.goto("http://localhost:8000")
        # Wait for app to load
        page.wait_for_load_state("networkidle")
        
        # Add some test tasks if needed
        task_count = page.locator(".task-item:not(.completed)").count()
        if task_count < 2:
            # Add first task
            task_input = page.locator("#task-input")
            task_input.fill("First test task")
            task_input.press("Enter")
            time.sleep(0.3)
            # Quick escape from palette
            page.keyboard.press("Escape")
            time.sleep(0.5)
            
            # Add second task
            task_input.fill("Second test task")
            task_input.press("Enter")
            time.sleep(0.3)
            # Quick escape from palette
            page.keyboard.press("Escape")
            time.sleep(0.5)
    
    def test_switch_modal_appears_when_switching_tasks(self, page: Page):
        """Test that switch modal appears when trying to work on another task"""
        # Get tasks
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        first_task_play = tasks.first.locator(".work-btn")
        first_task_play.click()
        time.sleep(0.5)
        
        # Verify working zone shows a task
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class("empty")
        
        # Try to work on second task
        second_task_play = tasks.nth(1).locator(".work-btn")
        second_task_play.click()
        
        # Verify modal appears
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # Verify overlay appears (not the palette overlay)
        overlay = page.locator(".modal-overlay:not(#palette-overlay)")
        expect(overlay).to_be_visible()
        
        # Verify modal content
        expect(modal).to_contain_text("Switch Task Confirmation")
        expect(modal).to_contain_text("Currently working on")
        expect(modal).to_contain_text("Switch to")
    
    def test_modal_has_no_countdown_timer(self, page: Page):
        """Test that the modal doesn't have a countdown timer"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # Verify no countdown numbers appear
        expect(modal).not_to_contain_text("3")
        expect(modal).not_to_contain_text("2")
        expect(modal).not_to_contain_text("1")
        
        # Wait 4 seconds to ensure modal doesn't auto-close
        page.wait_for_timeout(4000)
        
        # Modal should still be visible
        expect(modal).to_be_visible()
    
    def test_yes_button_switches_tasks(self, page: Page):
        """Test that clicking Yes switches to the new task"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Click Switch Task button
        page.locator("button:has-text('Switch Task')").click()
        time.sleep(0.5)
        
        # Verify modal is gone
        modal = page.locator(".switch-modal")
        expect(modal).not_to_be_visible()
        
        # Verify no overlays (except palette)
        overlays = page.locator(".modal-overlay:not(#palette-overlay)")
        expect(overlays).to_have_count(0)
        
        # Verify working zone is not empty
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class("empty")
    
    def test_no_button_keeps_current_task(self, page: Page):
        """Test that clicking No keeps working on current task"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Click Keep Working button
        page.locator("button:has-text('Keep Working')").click()
        time.sleep(0.3)
        
        # Verify modal is gone
        modal = page.locator(".switch-modal")
        expect(modal).not_to_be_visible()
        
        # Verify no overlays (except palette)
        overlays = page.locator(".modal-overlay:not(#palette-overlay)")
        expect(overlays).to_have_count(0)
        
        # Verify still working (working zone not empty)
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class("empty")
    
    def test_clicking_overlay_cancels_switch(self, page: Page):
        """Test that clicking the overlay cancels the switch"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Click overlay (outside modal) - use the first non-palette overlay
        overlay = page.locator(".modal-overlay:not(#palette-overlay)").first
        overlay.click(position={"x": 10, "y": 10})
        time.sleep(0.3)
        
        # Verify modal is gone
        modal = page.locator(".switch-modal")
        expect(modal).not_to_be_visible()
        
        # Verify no overlays (except palette)
        overlays = page.locator(".modal-overlay:not(#palette-overlay)")
        expect(overlays).to_have_count(0)
        
        # Verify still working
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class("empty")
    
    def test_modal_blocks_page_interaction(self, page: Page):
        """Test that modal overlay prevents interaction with page behind it"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Verify overlay is visible
        overlay = page.locator(".modal-overlay:not(#palette-overlay)").first
        expect(overlay).to_be_visible()
        
        # Modal should be visible
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
    
    def test_rapid_task_switching(self, page: Page):
        """Test rapid task switching doesn't cause issues"""
        # Add a third task
        task_input = page.locator("#task-input")
        task_input.fill("Third test task")
        task_input.press("Enter")
        time.sleep(0.3)
        page.keyboard.press("Escape")
        time.sleep(0.5)
        
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Rapidly try to switch between tasks
        for i in range(3):
            # Try to switch to second task
            tasks.nth(1).locator(".work-btn").click()
            time.sleep(0.2)
            # Immediately try third task (should not create second modal)
            tasks.nth(2).locator(".work-btn").click()
            time.sleep(0.2)
            
            # Should only have one modal
            modal_count = page.locator(".switch-modal:visible").count()
            assert modal_count == 1, f"Expected 1 modal, found {modal_count}"
            
            # Cancel
            page.locator("button:has-text('Keep Working')").click()
            time.sleep(0.3)
    
    def test_switch_updates_working_timer(self, page: Page):
        """Test that switching tasks resets the working timer"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Wait a bit for timer to advance
        page.wait_for_timeout(2000)
        
        # Get timer value
        timer = page.locator(".working-timer")
        first_timer = timer.inner_text()
        
        # Switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        page.locator("button:has-text('Switch Task')").click()
        time.sleep(0.5)
        
        # Timer should reset to 0:00
        new_timer = timer.inner_text()
        assert new_timer in ["0:00", "0:01"], f"Timer should reset, but shows {new_timer}"
    
    def test_switch_from_completed_working_task(self, page: Page):
        """Test completing a task while working on it and switching"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Complete the task while working on it
        page.locator("#working-zone .task-checkbox").click()
        time.sleep(0.5)
        
        # Working zone should clear
        working_zone = page.locator("#working-zone")
        expect(working_zone).to_have_class(re.compile(r"empty"))
        
        # Should be able to start working on another task without modal
        remaining_tasks = page.locator(".task-item:not(.completed)")
        if remaining_tasks.count() > 0:
            remaining_tasks.first.locator(".work-btn").click()
            time.sleep(0.3)
            
            # No modal should appear
            modal = page.locator(".switch-modal")
            expect(modal).not_to_be_visible()
            
            # Should be working on the new task
            expect(working_zone).not_to_have_class(re.compile(r"empty"))
    
    def test_keyboard_navigation_in_modal(self, page: Page):
        """Test keyboard navigation within the modal"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second task
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Modal should be visible
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # Test Escape key closes modal
        page.keyboard.press("Escape")
        time.sleep(0.3)
        
        # Modal should be closed
        expect(modal).not_to_be_visible()
    
    def test_modal_with_long_task_titles(self, page: Page):
        """Test modal display with very long task titles"""
        # Add tasks with long titles
        task_input = page.locator("#task-input")
        
        long_title1 = "This is a very long task title that might cause layout issues"
        task_input.fill(long_title1)
        task_input.press("Enter")
        time.sleep(0.3)
        page.keyboard.press("Escape")
        time.sleep(0.5)
        
        long_title2 = "Another extremely long task title that should wrap properly"
        task_input.fill(long_title2)
        task_input.press("Enter")
        time.sleep(0.3)
        page.keyboard.press("Escape")
        time.sleep(0.5)
        
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first long task
        tasks.nth(-2).locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch to second long task
        tasks.nth(-1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Modal should be visible and properly sized
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # Check modal doesn't overflow viewport
        modal_box = modal.bounding_box()
        viewport = page.viewport_size
        
        if modal_box:
            assert modal_box["width"] < viewport["width"]
            assert modal_box["height"] < viewport["height"]
    
    def test_no_modal_when_no_working_task(self, page: Page):
        """Test that no modal appears when no task is being worked on"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Don't start any task, just try to click play on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Should start working without modal
        modal = page.locator(".switch-modal")
        expect(modal).not_to_be_visible()
        
        # Should be working
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class(re.compile(r"empty"))
    
    def test_persistence_after_page_reload(self, page: Page):
        """Test that working state persists but modal doesn't after reload"""
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch (modal appears)
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # Reload page while modal is open
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Modal should not reappear
        expect(modal).not_to_be_visible()
        
        # Should still be working (working zone not empty)
        working_zone = page.locator("#working-zone")
        expect(working_zone).not_to_have_class(re.compile(r"empty"))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])  # Run with browser visible