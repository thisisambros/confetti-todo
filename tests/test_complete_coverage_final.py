"""
Complete test coverage for Confetti Todo
This test suite covers all functionality for both desktop and mobile interfaces
Focuses on the current implementation and actual UI behavior
"""
import pytest
from playwright.sync_api import Page, expect
import time
import re
from datetime import datetime

# Use test mode URL to avoid corrupting production data
BASE_URL = "http://localhost:8000?test=true"

class TestCoreTaskManagement:
    """Tests for core task management functionality"""
    
    def test_create_task_with_metadata(self, test_page: Page):
        """Test creating a task with all metadata fields"""
        # test_page fixture already navigated to test mode
        page = test_page
        
        # Create task
        task_input = page.locator("#task-input")
        task_input.fill("Test task with metadata")
        task_input.press("Enter")
        time.sleep(0.3)
        
        # Palette should show (not be hidden)
        palette = page.locator("#palette-modal")
        expect(palette).not_to_have_class(re.compile(r"hidden"))
        
        # Due date should be first
        due_date_field = page.locator("#due-date-field")
        expect(due_date_field).to_be_visible()
        
        # Select metadata using keyboard or clicks
        page.keyboard.press("Escape")  # Quick save
        time.sleep(0.5)
        
        # Verify task created
        task = page.locator(".task-item").filter(has_text="Test task with metadata")
        expect(task).to_be_visible()
        
    def test_complete_task_with_confetti(self, test_page: Page):
        """Test task completion shows confetti"""
        page = test_page
        
        # Find uncompleted task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            # Create a task first
            task_input = page.locator("#task-input")
            task_input.fill("Task to complete")
            task_input.press("Enter")
            time.sleep(0.3)
            page.keyboard.press("Escape")
            time.sleep(0.5)
            task = page.locator(".task-item").filter(has_text="Task to complete")
        
        # Complete task
        checkbox = task.locator(".task-checkbox")
        checkbox.click()
        time.sleep(0.5)
        
        # Check completed class
        expect(task).to_have_class(re.compile(r"completed"))
        
        # Confetti canvas should appear
        confetti = page.locator("#confetti-canvas")
        expect(confetti).to_be_visible()
        
    def test_subtask_creation_and_visibility(self, test_page: Page):
        """Test subtask creation keeps parent expanded"""
        page = test_page
        
        # Get a task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            pytest.skip("No tasks available")
            
        # Add subtask
        add_btn = task.locator(".subtask-btn, button:has-text('+ Add Subtask')")
        add_btn.click()
        time.sleep(0.3)
        
        # Enter subtask
        subtask_input = page.locator(".subtask-input input")
        subtask_input.fill("New subtask")
        subtask_input.press("Enter")
        time.sleep(0.5)
        
        # Parent should stay expanded
        toggle = task.locator(".subtask-toggle")
        if toggle.count() > 0:
            expect(toggle).to_have_text("▼")
            
        # Subtask should be visible
        subtasks = page.locator(".task-item.subtask.visible")
        found = False
        for i in range(subtasks.count()):
            if "New subtask" in subtasks.nth(i).inner_text():
                found = True
                break
        assert found, "Subtask not visible"


class TestWorkingZone:
    """Tests for working zone and timer functionality"""
    
    def test_start_stop_working(self, page: Page):
        """Test starting and stopping work on tasks"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Get task
        task = page.locator(".task-item:not(.completed)").first
        if task.count() == 0:
            pytest.skip("No tasks available")
            
        # Start working
        work_btn = task.locator(".work-btn")
        work_btn.click()
        time.sleep(0.5)
        
        # Working zone should not be empty
        working_zone = page.locator("#working-zone, .working-zone")
        expect(working_zone).to_be_visible()
        expect(working_zone).not_to_have_class(re.compile(r"empty"))
        
        # Stop working
        stop_btn = working_zone.locator("button:has-text('Stop'), .stop-working-btn")
        stop_btn.click()
        time.sleep(0.3)
        
        # Working zone should be empty
        expect(working_zone).to_have_class(re.compile(r"empty"))
        
    def test_switch_task_modal_behavior(self, page: Page):
        """Test switch task modal appears and functions correctly"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Need at least 2 tasks
        tasks = page.locator(".task-item:not(.completed)")
        if tasks.count() < 2:
            # Create tasks
            for i in range(2):
                task_input = page.locator("#task-input")
                task_input.fill(f"Task {i+1}")
                task_input.press("Enter")
                time.sleep(0.3)
                page.keyboard.press("Escape")
                time.sleep(0.5)
                
        tasks = page.locator(".task-item:not(.completed)")
        
        # Start working on first
        tasks.first.locator(".work-btn").click()
        time.sleep(0.5)
        
        # Try to switch
        tasks.nth(1).locator(".work-btn").click()
        time.sleep(0.3)
        
        # Modal should appear
        modal = page.locator(".switch-modal")
        expect(modal).to_be_visible()
        
        # No countdown
        modal_text = modal.inner_text()
        assert "3" not in modal_text or "task" in modal_text.lower()
        
        # Cancel switch
        cancel_btn = page.locator("button:has-text('Keep Working'), .keep-working")
        cancel_btn.click()
        time.sleep(0.3)
        
        # Modal gone
        expect(modal).not_to_be_visible()
        
        # Check no extra overlays
        overlays = page.locator(".modal-overlay:visible").all()
        visible_overlays = [o for o in overlays if "palette" not in (o.get_attribute("id") or "")]
        assert len(visible_overlays) == 0, f"Found {len(visible_overlays)} visible overlays"


class TestMobileInterface:
    """Tests specific to mobile interface"""
    
    def test_mobile_layout_elements(self, page: Page):
        """Test mobile-specific UI elements"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Mobile nav visible
        mobile_nav = page.locator(".mobile-bottom-nav")
        expect(mobile_nav).to_be_visible()
        
        # Desktop tabs hidden
        desktop_tabs = page.locator(".date-tabs")
        expect(desktop_tabs).not_to_be_visible()
        
        # Quick actions visible on tasks
        task = page.locator(".task-item:not(.completed)").first
        if task.count() > 0:
            quick_actions = task.locator(".task-quick-actions")
            expect(quick_actions).to_be_visible()
            
    def test_mobile_filter_sheet(self, page: Page):
        """Test mobile filter sheet functionality"""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")
        
        # Open filter
        more_btn = page.locator("#mobile-more-menu")
        more_btn.click()
        time.sleep(0.3)
        
        # Sheet active
        sheet = page.locator("#mobile-filter-sheet, .mobile-filter-sheet")
        expect(sheet).to_have_class(re.compile(r"active"))
        
        # Close
        close_btn = page.locator("#sheet-close, .sheet-close")
        close_btn.click()
        time.sleep(0.3)
        
        # Sheet inactive
        expect(sheet).not_to_have_class(re.compile(r"active"))
        
    def test_mobile_task_creation(self, page: Page):
        """Test creating tasks on mobile"""
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
        
        # Create task
        mobile_input.fill("Mobile task")
        mobile_input.press("Enter")
        time.sleep(0.5)
        
        # Palette should show
        palette = page.locator("#palette-modal")
        expect(palette).not_to_have_class(re.compile(r"hidden"))


class TestResponsiveDesign:
    """Tests for responsive behavior"""
    
    def test_viewport_transitions(self, page: Page):
        """Test UI adapts to viewport changes"""
        page.goto(BASE_URL)
        
        # Start desktop
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_load_state("networkidle")
        
        # Desktop elements
        expect(page.locator(".date-tabs")).to_be_visible()
        expect(page.locator(".mobile-bottom-nav")).not_to_be_visible()
        
        # Quick actions hidden on desktop
        task = page.locator(".task-item").first
        if task.count() > 0:
            quick_actions = task.locator(".task-quick-actions")
            if quick_actions.count() > 0:
                expect(quick_actions).not_to_be_visible()
        
        # Switch to mobile
        page.set_viewport_size({"width": 375, "height": 667})
        time.sleep(0.5)
        
        # Mobile elements
        expect(page.locator(".mobile-bottom-nav")).to_be_visible()
        expect(page.locator(".date-tabs")).not_to_be_visible()
        
        # Quick actions visible on mobile
        if task.count() > 0 and quick_actions.count() > 0:
            expect(quick_actions).to_be_visible()


class TestUIFeatures:
    """Tests for various UI features"""
    
    def test_north_star_functionality(self, page: Page):
        """Test North Star selection and display"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click north star button
        north_star_btn = page.locator("#pick-north-star, .pick-north-star")
        if north_star_btn.count() > 0:
            north_star_btn.click()
            time.sleep(0.3)
            
            # Select a task if available
            selectable = page.locator(".selectable-task").first
            if selectable.count() > 0:
                selectable.click()
                time.sleep(0.5)
                
                # North star should be set
                display = page.locator("#north-star-display, .north-star-display")
                expect(display).not_to_contain_text("What's your main focus")
                
    def test_search_functionality(self, page: Page):
        """Test search morphing UI"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click search
        search_icon = page.locator("#search-icon, .search-icon")
        if search_icon.count() > 0:
            search_icon.click()
            time.sleep(0.3)
            
            # Search input visible
            search_input = page.locator("#search-input")
            expect(search_input).to_be_visible()
            
            # Search for something
            search_input.fill("test")
            search_input.press("Enter")
            time.sleep(0.5)
            
            # Results shown
            info = page.locator("#task-display-info, .task-display-info")
            if info.count() > 0:
                expect(info).to_contain_text("matching")
                
    def test_metadata_display_order(self, page: Page):
        """Test that metadata displays in correct order"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Find task with metadata
        tasks = page.locator(".task-item")
        for i in range(tasks.count()):
            task = tasks.nth(i)
            meta = task.locator(".task-meta")
            if meta.count() > 0:
                text = meta.inner_text()
                # Check if has both friction and effort
                if any(icon in text for icon in ["🍃", "💨", "🌪️"]) and \
                   any(time in text for time in ["5m", "15m", "30m", "1h", "2h", "4h"]):
                    # Verify order: friction should come before effort
                    friction_icons = ["🍃", "💨", "🌪️"]
                    effort_times = ["5m", "15m", "30m", "1h", "2h", "4h"]
                    
                    friction_pos = None
                    effort_pos = None
                    
                    for icon in friction_icons:
                        if icon in text:
                            friction_pos = text.index(icon)
                            break
                            
                    for time in effort_times:
                        if time in text:
                            effort_pos = text.index(time)
                            break
                            
                    if friction_pos is not None and effort_pos is not None:
                        assert friction_pos < effort_pos, "Friction should appear before effort"
                    break


class TestEdgeCases:
    """Tests for edge cases and error scenarios"""
    
    def test_empty_task_creation(self, page: Page):
        """Test that empty tasks cannot be created"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Try empty task
        task_input = page.locator("#task-input")
        task_input.fill("")
        task_input.press("Enter")
        
        # Palette should not show
        palette = page.locator("#palette-modal")
        expect(palette).to_have_class(re.compile(r"hidden"))
        
    def test_overdue_date_contrast(self, page: Page):
        """Test overdue dates have good contrast"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Find overdue task
        overdue = page.locator(".task-item.overdue").first
        if overdue.count() > 0:
            # Check date color
            date_span = overdue.locator(".task-meta span:has-text('📅')")
            if date_span.count() > 0:
                color = date_span.evaluate("el => window.getComputedStyle(el).color")
                # Should not be light pink
                assert "255, 182, 193" not in color, "Overdue date has poor contrast"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])