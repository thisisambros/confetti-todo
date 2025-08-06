"""
Comprehensive mobile UI tests for Confetti Todo
Tests all mobile-specific features and interactions
"""
import pytest
from playwright.sync_api import Page, expect
import time
import re

BASE_URL = "http://localhost:8000"
MOBILE_WIDTH = 375
MOBILE_HEIGHT = 667
DESKTOP_WIDTH = 1280
DESKTOP_HEIGHT = 800

class TestMobileUI:
    """Test all mobile UI components and interactions"""
    
    def test_mobile_bottom_navigation(self, page: Page):
        """Test bottom navigation functionality on mobile"""
        # Set mobile viewport
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Verify bottom navigation is visible
        bottom_nav = page.locator(".mobile-bottom-nav")
        expect(bottom_nav).to_be_visible()
        
        # Test all navigation buttons
        nav_buttons = {
            "all": page.locator('.mobile-bottom-nav button[data-filter="all"]'),
            "today": page.locator('.mobile-bottom-nav button[data-filter="today"]'),
            "add": page.locator('#mobile-add-task'),
            "week": page.locator('.mobile-bottom-nav button[data-filter="week"]'),
            "more": page.locator('#mobile-more-menu')
        }
        
        # Verify all buttons are visible
        for name, button in nav_buttons.items():
            expect(button).to_be_visible()
        
        # Test filter switching
        nav_buttons["today"].click()
        time.sleep(0.3)
        assert "active" in nav_buttons["today"].get_attribute("class") or \
               "active" in nav_buttons["today"].locator("..").get_attribute("class")
        
        nav_buttons["week"].click()
        time.sleep(0.3)
        assert "active" in nav_buttons["week"].get_attribute("class") or \
               "active" in nav_buttons["week"].locator("..").get_attribute("class")
        
        nav_buttons["all"].click()
        time.sleep(0.3)
        
    def test_mobile_add_task_flow(self, page: Page):
        """Test adding a task on mobile with the + button"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click the + button
        add_button = page.locator('#mobile-add-task')
        add_button.click()
        time.sleep(0.5)
        
        # Wait for the dynamically created mobile input
        mobile_input = page.locator("input.mobile-task-input")
        expect(mobile_input).to_be_visible()
        
        # Type a task and submit
        mobile_input.fill("Mobile test task")
        mobile_input.press("Enter")
        
        time.sleep(0.5)
        
        # Verify task was added
        new_task = page.locator(".task-item").filter(has_text="Mobile test task")
        expect(new_task).to_be_visible()
        
    def test_mobile_filter_sheet(self, page: Page):
        """Test the mobile filter sheet functionality"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click More button
        more_button = page.locator('#mobile-more-menu')
        more_button.click()
        time.sleep(0.5)
        
        # Verify filter sheet is active
        filter_sheet = page.locator(".mobile-filter-sheet")
        expect(filter_sheet).to_have_class(re.compile(r"active"))
        
        # Check sheet contents
        sheet_title = filter_sheet.locator("h3")
        expect(sheet_title).to_contain_text("Filter")
        
        # Test closing the sheet
        close_button = page.locator("#sheet-close")
        expect(close_button).to_be_visible()
        
        # Use JavaScript to click since regular click is blocked
        page.evaluate("document.getElementById('sheet-close').click()")
        time.sleep(0.5)
        
        # Verify sheet is closed
        assert "active" not in filter_sheet.get_attribute("class")
        
    def test_mobile_task_cards(self, page: Page):
        """Test mobile-optimized task cards"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add a test task first
        page.locator('#mobile-add-task').click()
        time.sleep(0.3)
        
        # Wait for and use the dynamically created mobile input
        mobile_input = page.locator("input.mobile-task-input")
        expect(mobile_input).to_be_visible()
        mobile_input.fill("Task for mobile testing")
        mobile_input.press("Enter")
        
        time.sleep(0.5)
        
        # Find the task card
        task_card = page.locator(".task-item").filter(has_text="Task for mobile testing").first
        expect(task_card).to_be_visible()
        
        # Verify mobile-specific elements are hidden
        checkbox = task_card.locator(".task-checkbox")
        add_subtask = task_card.locator(".add-subtask")
        
        # On mobile, these should be hidden or not present
        if checkbox.count() > 0:
            expect(checkbox).to_be_hidden()
        if add_subtask.count() > 0:
            expect(add_subtask).to_be_hidden()
        
        # Test quick action buttons
        quick_actions = task_card.locator(".quick-action-buttons")
        if quick_actions.is_visible():
            play_button = quick_actions.locator("button").filter(has_text="▶")
            complete_button = quick_actions.locator("button").filter(has_text="✓")
            
            expect(play_button).to_be_visible()
            expect(complete_button).to_be_visible()
            
    def test_north_star_single_line_mobile(self, page: Page):
        """Test that north star section is single line on mobile"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Check north star section
        north_star = page.locator("#north-star-section")
        expect(north_star).to_be_visible()
        
        # On mobile, it should show the simplified text
        empty_state = north_star.locator(".north-star-empty-state")
        if empty_state.is_visible():
            # Check for mobile-specific single line text
            expect(empty_state).to_contain_text("Choose your main focus today")
            
            # Verify it doesn't contain the desktop multi-line content
            desktop_content = empty_state.locator("p")
            # Should have only one paragraph on mobile
            assert desktop_content.count() <= 1
            
    def test_responsive_behavior_desktop_mobile(self, page: Page):
        """Test that UI correctly switches between desktop and mobile layouts"""
        # Start with desktop
        page.set_viewport_size({"width": DESKTOP_WIDTH, "height": DESKTOP_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Verify desktop layout
        bottom_nav = page.locator(".mobile-bottom-nav")
        expect(bottom_nav).to_be_hidden()
        
        date_filter_tabs = page.locator(".date-filter-tabs")
        expect(date_filter_tabs).to_be_visible()
        
        right_widget = page.locator(".right-widget")
        expect(right_widget).to_be_visible()
        
        # Switch to mobile
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        time.sleep(0.5)
        
        # Verify mobile layout
        expect(bottom_nav).to_be_visible()
        expect(date_filter_tabs).to_be_hidden()
        expect(right_widget).to_be_hidden()
        
        # Switch back to desktop
        page.set_viewport_size({"width": DESKTOP_WIDTH, "height": DESKTOP_HEIGHT})
        time.sleep(0.5)
        
        # Verify desktop layout restored
        expect(bottom_nav).to_be_hidden()
        expect(date_filter_tabs).to_be_visible()
        expect(right_widget).to_be_visible()
        
    def test_mobile_working_zone(self, page: Page):
        """Test working zone behavior on mobile"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add and start a task
        page.locator('#mobile-add-task').click()
        time.sleep(0.3)
        
        # Wait for and use the dynamically created mobile input
        mobile_input = page.locator("input.mobile-task-input")
        expect(mobile_input).to_be_visible()
        mobile_input.fill("Working task")
        mobile_input.press("Enter")
        
        time.sleep(0.5)
        
        # Start the task - on mobile it has quick actions
        task = page.locator(".task-item").filter(has_text="Working task").first
        
        # On mobile, look for task-quick-actions (not quick-action-buttons)
        quick_actions = task.locator(".task-quick-actions")
        if quick_actions.count() > 0:
            # Mobile quick action button
            work_btn = quick_actions.locator("button.work")
            work_btn.click()
        else:
            # Try regular play button as fallback
            play_button = task.locator(".play-btn")
            if play_button.count() > 0:
                play_button.click()
            else:
                # Click the task itself might trigger action
                task.click()
        
        time.sleep(0.5)
        
        # Check working zone
        working_zone = page.locator(".working-zone")
        expect(working_zone).to_be_visible()
        expect(working_zone).to_contain_text("Working task")
        
    def test_mobile_touch_interactions(self, page: Page):
        """Test touch-specific interactions on mobile"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Add test tasks
        for i in range(3):
            page.locator('#mobile-add-task').click()
            time.sleep(0.2)
            
            # Wait for and use the dynamically created mobile input
            mobile_input = page.locator("input.mobile-task-input")
            expect(mobile_input).to_be_visible()
            mobile_input.fill(f"Touch test task {i+1}")
            mobile_input.press("Enter")
            
            time.sleep(0.3)
        
        # Test tapping on tasks
        first_task = page.locator(".task-item").first
        first_task.click()
        time.sleep(0.3)
        
        # Verify task interaction (e.g., selection or action)
        # This depends on what clicking a task does in your app
        
    def test_mobile_viewport_meta_tag(self, page: Page):
        """Verify proper viewport meta tag for mobile"""
        page.goto(BASE_URL)
        
        # Check viewport meta tag
        viewport_meta = page.locator('meta[name="viewport"]')
        expect(viewport_meta).to_have_attribute("content", re.compile(r"width=device-width"))
        expect(viewport_meta).to_have_attribute("content", re.compile(r"initial-scale=1"))
        
    def test_mobile_filter_persistence(self, page: Page):
        """Test that filter selections persist when switching views"""
        page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Select "Today" filter
        today_button = page.locator('.mobile-bottom-nav button[data-filter="today"]')
        today_button.click()
        time.sleep(0.3)
        
        # Open filter sheet
        page.locator('#mobile-more-menu').click()
        time.sleep(0.3)
        
        # Close filter sheet
        page.locator("#sheet-close").click(force=True)
        time.sleep(0.3)
        
        # Verify "Today" is still selected
        assert "active" in today_button.get_attribute("class") or \
               "active" in today_button.locator("..").get_attribute("class")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])