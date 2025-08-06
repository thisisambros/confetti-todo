"""
Comprehensive test coverage for Confetti Todo - Desktop and Mobile
This file ensures complete coverage of all features on both platforms
"""
import pytest
from playwright.sync_api import Page, expect
import time
import re
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class TestDesktopCore:
    """Core functionality tests for desktop interface"""
    
    def test_task_creation_flow(self, page: Page):
        """Test complete task creation flow on desktop"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Test task input
        task_input = page.locator("#task-input")
        expect(task_input).to_be_visible()
        
        # Create a task
        task_input.fill("Desktop test task")
        task_input.press("Enter")
        
        # Palette should appear for metadata
        palette = page.locator("#palette-modal")
        expect(palette).to_be_visible()
        
        # Check due date field is first
        due_date_field = page.locator("#due-date-field")
        expect(due_date_field).to_be_visible()
        
        # Select today as due date
        today_option = page.locator("[data-value='today']")
        today_option.click()
        
        # Select category
        category_option = page.locator("[data-value='product']")
        category_option.click()
        
        # Select effort
        effort_option = page.locator("[data-value='30m']")
        effort_option.click()
        
        # Select friction
        friction_option = page.locator("[data-value='2']")
        friction_option.click()
        
        # Save task
        page.locator("#palette-dialog-title").press("Enter")
        time.sleep(0.5)
        
        # Verify task appears
        task = page.locator(".task-item").filter(has_text="Desktop test task")
        expect(task).to_be_visible()
        
        # Verify metadata
        expect(task).to_contain_text("@product")
        expect(task).to_contain_text("30m")
        expect(task).to_contain_text("💨")
        
    def test_task_completion(self, page: Page):
        """Test task completion with confetti"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Find an uncompleted task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            pytest.skip("No uncompleted tasks")
            
        # Complete the task
        checkbox = task.locator(".task-checkbox")
        checkbox.click()
        
        # Verify completion
        expect(task).to_have_class(re.compile(r"completed"))
        
        # Check for confetti (canvas should be visible)
        confetti = page.locator("#confetti-canvas")
        expect(confetti).to_be_visible()
        
    def test_subtask_management(self, page: Page):
        """Test subtask creation and management"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Find a task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            pytest.skip("No tasks available")
            
        # Add subtask
        add_btn = task.locator("button:has-text('+ Add Subtask')")
        add_btn.click()
        
        # Enter subtask
        subtask_input = page.locator(".subtask-input input")
        subtask_input.fill("Test subtask")
        subtask_input.press("Enter")
        time.sleep(0.5)
        
        # Verify subtask is visible
        subtask = page.locator(".task-item.subtask").filter(has_text="Test subtask")
        expect(subtask).to_be_visible()
        expect(subtask).to_have_class(re.compile(r"visible"))
        
    def test_working_zone(self, page: Page):
        """Test working zone functionality"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Find a task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            pytest.skip("No tasks available")
            
        # Start working
        work_btn = task.locator("button:has-text('Work on this')")
        work_btn.click()
        time.sleep(0.5)
        
        # Verify working zone
        working_zone = page.locator("#working-zone")
        expect(working_zone).to_be_visible()
        expect(working_zone).not_to_have_class(re.compile(r"empty"))
        
        # Stop working
        stop_btn = working_zone.locator("button:has-text('Stop')")
        stop_btn.click()
        
        # Verify stopped
        expect(working_zone).to_have_class(re.compile(r"empty"))
        
    def test_switch_modal(self, page: Page):
        """Test switch task modal behavior"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Get two tasks
        tasks = page.locator(".task-item:not(.completed)")
        if tasks.count() < 2:
            pytest.skip("Need at least 2 tasks")
            
        # Start working on first task
        tasks.first.locator("button:has-text('Work on this')").click()
        time.sleep(0.5)
        
        # Try to work on second task
        tasks.nth(1).locator("button:has-text('Work on this')").click()
        
        # Modal should appear
        modal = page.locator("#switch-modal")
        expect(modal).to_be_visible()
        
        # No countdown timer
        expect(modal).not_to_contain_text("3")
        expect(modal).not_to_contain_text("2")
        expect(modal).not_to_contain_text("1")
        
        # Test cancel
        page.locator("button:has-text('Keep Working')").click()
        time.sleep(0.3)
        
        # Modal and overlay should be gone
        expect(modal).not_to_be_visible()
        overlays = page.locator(".modal-overlay:not(#palette-overlay)")
        expect(overlays).to_have_count(0)
        
    def test_north_star(self, page: Page):
        """Test North Star functionality"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Open North Star modal
        north_star_btn = page.locator("#pick-north-star")
        north_star_btn.click()
        
        # Select a task
        modal_tasks = page.locator(".north-star-modal .selectable-task")
        if modal_tasks.count() > 0:
            modal_tasks.first.click()
            time.sleep(0.5)
            
            # Verify North Star is set
            north_star_display = page.locator("#north-star-display")
            expect(north_star_display).not_to_contain_text("What's your main focus")
            
    def test_search_functionality(self, page: Page):
        """Test search morphing and functionality"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Click search icon
        search_icon = page.locator("#search-icon")
        search_icon.click()
        
        # Search input should be visible
        search_input = page.locator("#search-input")
        expect(search_input).to_be_visible()
        
        # Type search term
        search_input.fill("test")
        search_input.press("Enter")
        time.sleep(0.5)
        
        # Should show filtered results
        display_info = page.locator("#task-display-info")
        expect(display_info).to_contain_text("matching")
        
    def test_ideas_section(self, page: Page):
        """Test ideas functionality"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Add idea with keyboard shortcut
        page.keyboard.press("i")
        time.sleep(0.3)
        
        # Palette should be in idea mode
        palette = page.locator("#palette-modal")
        expect(palette).to_be_visible()
        expect(palette).to_have_attribute("data-mode", "idea")
        
        # Enter idea
        idea_input = page.locator("#palette-input")
        idea_input.fill("Test idea")
        idea_input.press("Enter")
        time.sleep(0.5)
        
        # Verify idea appears
        idea = page.locator(".idea-item").filter(has_text="Test idea")
        expect(idea).to_be_visible()


class TestMobileCore:
    """Core functionality tests for mobile interface"""
    
    def test_mobile_layout(self, page: Page):
        """Test mobile layout elements"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Mobile nav should be visible
        mobile_nav = page.locator(".mobile-bottom-nav")
        expect(mobile_nav).to_be_visible()
        
        # Desktop elements should be hidden
        desktop_tabs = page.locator(".date-tabs")
        expect(desktop_tabs).not_to_be_visible()
        
    def test_mobile_task_creation(self, page: Page):
        """Test task creation on mobile"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Click add button
        add_btn = page.locator("#mobile-add-task")
        add_btn.click()
        time.sleep(0.3)
        
        # Mobile input should appear
        mobile_input = page.locator(".mobile-task-input")
        expect(mobile_input).to_be_visible()
        
        # Enter task
        mobile_input.fill("Mobile test task")
        mobile_input.press("Enter")
        time.sleep(0.5)
        
        # Palette should appear
        palette = page.locator("#palette-modal")
        expect(palette).to_be_visible()
        
    def test_mobile_task_cards(self, page: Page):
        """Test mobile task card layout"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Task cards should have mobile class
        tasks = page.locator(".task-item")
        if tasks.count() > 0:
            # Quick actions should be visible
            quick_actions = page.locator(".task-quick-actions").first
            expect(quick_actions).to_be_visible()
            
    def test_mobile_filter_sheet(self, page: Page):
        """Test mobile filter sheet"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Open filter sheet
        more_btn = page.locator("#mobile-more-menu")
        more_btn.click()
        time.sleep(0.3)
        
        # Sheet should be visible
        sheet = page.locator("#mobile-filter-sheet")
        expect(sheet).to_have_class(re.compile(r"active"))
        
        # Close sheet
        close_btn = page.locator("#sheet-close")
        close_btn.click()
        time.sleep(0.3)
        
        # Sheet should be hidden
        expect(sheet).not_to_have_class(re.compile(r"active"))
        
    def test_mobile_north_star_display(self, page: Page):
        """Test North Star display on mobile"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # North star should be single line
        north_star = page.locator("#north-star-display")
        # Get computed styles to check it's single line
        height = north_star.evaluate("el => window.getComputedStyle(el).height")
        # Height should be less than 50px for single line
        assert float(height.replace('px', '')) < 50
        
    def test_mobile_working_zone_collapse(self, page: Page):
        """Test working zone collapse on mobile"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Start working on a task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() > 0:
            quick_play = task.locator(".quick-play")
            quick_play.click()
            time.sleep(0.5)
            
            # Working zone should be visible
            working_zone = page.locator(".working-zone")
            expect(working_zone).to_be_visible()
            
            # Click to collapse
            working_zone.click()
            time.sleep(0.3)
            
            # Should have collapsed class
            expect(working_zone).to_have_class(re.compile(r"collapsed"))


class TestResponsiveBehavior:
    """Test responsive behavior between desktop and mobile"""
    
    def test_breakpoint_transition(self, page: Page):
        """Test UI changes at breakpoint"""
        page.goto(BASE_URL)
        
        # Start desktop
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Desktop elements visible
        expect(page.locator(".date-tabs")).to_be_visible()
        expect(page.locator(".mobile-bottom-nav")).not_to_be_visible()
        
        # Resize to mobile
        page.set_viewport_size({"width": 375, "height": 667})
        time.sleep(0.5)
        
        # Mobile elements visible
        expect(page.locator(".mobile-bottom-nav")).to_be_visible()
        expect(page.locator(".date-tabs")).not_to_be_visible()
        
        # Resize back to desktop
        page.set_viewport_size({"width": 1280, "height": 800})
        time.sleep(0.5)
        
        # Desktop elements visible again
        expect(page.locator(".date-tabs")).to_be_visible()
        expect(page.locator(".mobile-bottom-nav")).not_to_be_visible()
        
    def test_quick_actions_responsive(self, page: Page):
        """Test quick actions show/hide based on viewport"""
        page.goto(BASE_URL)
        
        # Desktop - no quick actions
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        quick_actions = page.locator(".task-quick-actions")
        if quick_actions.count() > 0:
            expect(quick_actions.first).not_to_be_visible()
            
        # Mobile - quick actions visible
        page.set_viewport_size({"width": 375, "height": 667})
        time.sleep(0.5)
        
        if quick_actions.count() > 0:
            expect(quick_actions.first).to_be_visible()


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_task_creation(self, page: Page):
        """Test creating task with empty title"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Try to create empty task
        task_input = page.locator("#task-input")
        task_input.fill("")
        task_input.press("Enter")
        
        # Should not create task or show palette
        palette = page.locator("#palette-modal")
        expect(palette).not_to_be_visible()
        
    def test_multiple_overlays(self, page: Page):
        """Test that multiple overlays don't stack"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Create multiple scenarios that could create overlays
        tasks = page.locator(".task-item:not(.completed)")
        if tasks.count() >= 2:
            # Start working
            tasks.first.locator("button:has-text('Work on this')").click()
            time.sleep(0.3)
            
            # Try to switch
            tasks.nth(1).locator("button:has-text('Work on this')").click()
            time.sleep(0.3)
            
            # Count overlays (excluding palette overlay)
            overlays = page.locator(".modal-overlay:not(#palette-overlay)")
            overlay_count = overlays.count()
            
            # Should only have one overlay
            assert overlay_count <= 1, f"Found {overlay_count} overlays, expected <= 1"
            
    def test_overdue_date_visibility(self, page: Page):
        """Test overdue date contrast"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Find overdue task
        overdue_task = page.locator(".task-item.overdue").first
        if overdue_task.count() > 0:
            # Get date element
            date_element = overdue_task.locator(".task-meta span:has-text('📅')")
            if date_element.count() > 0:
                # Check computed color
                color = date_element.evaluate("""
                    el => window.getComputedStyle(el).color
                """)
                # Should not be light pink (rgb(255, 182, 193) or similar)
                assert "255" not in color or "182" not in color, "Overdue date has poor contrast"


class TestDataPersistence:
    """Test data persistence and sync"""
    
    def test_task_persistence(self, page: Page):
        """Test tasks persist after reload"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Create a unique task
        timestamp = datetime.now().strftime("%H%M%S")
        task_title = f"Persistence test {timestamp}"
        
        task_input = page.locator("#task-input")
        task_input.fill(task_title)
        task_input.press("Enter")
        
        # Quick save through palette
        page.keyboard.press("Escape")
        time.sleep(1)
        
        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Task should still exist
        task = page.locator(".task-item").filter(has_text=task_title)
        expect(task).to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])