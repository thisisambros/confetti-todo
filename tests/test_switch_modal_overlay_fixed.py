"""
Test for switch modal overlay bug - comprehensive tests after fix
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

class TestSwitchModalOverlayFixed:
    """Test that modal overlay is properly removed after user action"""
    
    def test_overlay_removed_after_keep_working(self, page: Page):
        """Test that grey overlay is removed when clicking 'Keep Working'"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Use existing tasks
        tasks = page.locator(".task-item")
        if tasks.count() < 2:
            pytest.skip("Not enough tasks for test")
        
        first_task = tasks.first
        second_task = tasks.nth(1)
        
        # Start the first task
        first_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to start the second task
        second_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Verify modal and overlay are visible
        modal = page.locator(".switch-modal")
        overlays = page.locator(".modal-overlay")
        
        expect(modal).to_be_visible()
        
        # Count visible overlays
        visible_count = 0
        for i in range(overlays.count()):
            if overlays.nth(i).is_visible():
                visible_count += 1
        assert visible_count > 0, "No visible overlay found"
        
        # Click "Keep Working"
        page.locator("button.keep-working").click()
        time.sleep(0.5)
        
        # Modal should be hidden
        expect(modal).to_be_hidden()
        
        # No overlays should be visible (except the hidden palette one)
        for i in range(overlays.count()):
            overlay = overlays.nth(i)
            if overlay.get_attribute("id") != "modal-overlay":
                expect(overlay).to_be_hidden()
        
        # Verify we can interact with the page
        page.locator("#task-input").click()
        page.locator("#task-input").fill("Test works")
        
    def test_overlay_removed_after_switch_task(self, page: Page):
        """Test that grey overlay is removed when clicking 'Switch Task'"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        tasks = page.locator(".task-item")
        if tasks.count() < 2:
            pytest.skip("Not enough tasks for test")
        
        first_task = tasks.first
        second_task = tasks.nth(1)
        
        # Start first task
        first_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to start second task
        second_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Click "Switch Task"
        page.locator("button.switch-task").click()
        time.sleep(0.5)
        
        # Modal and overlays should be hidden
        modal = page.locator(".switch-modal")
        expect(modal).to_be_hidden()
        
        overlays = page.locator(".modal-overlay")
        for i in range(overlays.count()):
            overlay = overlays.nth(i)
            if overlay.get_attribute("id") != "modal-overlay":
                expect(overlay).to_be_hidden()
        
    def test_overlay_removed_on_mobile(self, page: Page):
        """Test that overlay is properly removed on mobile too"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        tasks = page.locator(".task-item")
        if tasks.count() < 2:
            pytest.skip("Not enough tasks for test")
        
        # Start first task using mobile quick actions
        first_task = tasks.first
        first_quick = first_task.locator(".task-quick-actions button.work")
        if first_quick.count() > 0:
            first_quick.click()
        else:
            first_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to start second task
        second_task = tasks.nth(1)
        second_quick = second_task.locator(".task-quick-actions button.work")
        if second_quick.count() > 0:
            second_quick.click()
        else:
            second_task.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Click keep working
        page.locator("button.keep-working").click()
        time.sleep(0.5)
        
        # Verify overlays are hidden
        overlays = page.locator(".modal-overlay")
        for i in range(overlays.count()):
            overlay = overlays.nth(i)
            if overlay.get_attribute("id") != "modal-overlay":
                expect(overlay).to_be_hidden()
        
        # Verify mobile UI is still interactive
        page.locator("#mobile-add-task").click()
        time.sleep(0.3)
        mobile_input = page.locator("input.mobile-task-input")
        expect(mobile_input).to_be_visible()
        mobile_input.press("Escape")
        
    def test_no_duplicate_overlays(self, page: Page):
        """Test that repeated modal shows don't create duplicate overlays"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        tasks = page.locator(".task-item")
        if tasks.count() < 2:
            pytest.skip("Not enough tasks for test")
        
        # Start first task
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Show and dismiss modal multiple times
        for _ in range(3):
            tasks.nth(1).locator(".work-btn").click()
            time.sleep(0.3)
            page.locator("button.keep-working").click()
            time.sleep(0.3)
        
        # Count total overlays - should only have the palette one
        overlays = page.locator(".modal-overlay")
        non_palette_overlays = []
        for i in range(overlays.count()):
            overlay = overlays.nth(i)
            if overlay.get_attribute("id") != "modal-overlay":
                non_palette_overlays.append(i)
        
        assert len(non_palette_overlays) == 0, f"Found {len(non_palette_overlays)} non-palette overlays, expected 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])