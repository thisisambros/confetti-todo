"""
Test that mobile quick action buttons are properly hidden on desktop
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_quick_actions_hidden_on_desktop(page: Page):
    """Test that quick action buttons don't show on desktop"""
    # Set desktop viewport
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find task items
    tasks = page.locator(".task-item")
    if tasks.count() == 0:
        pytest.skip("No tasks available for testing")
    
    # Check first few tasks
    for i in range(min(3, tasks.count())):
        task = tasks.nth(i)
        
        # Quick actions should not be visible on desktop
        quick_actions = task.locator(".task-quick-actions")
        if quick_actions.count() > 0:
            expect(quick_actions).to_be_hidden()
        
        # Individual quick action buttons should also be hidden
        work_btn = task.locator(".task-quick-action.work")
        if work_btn.count() > 0:
            expect(work_btn).to_be_hidden()
            
        complete_btn = task.locator(".task-quick-action.complete")
        if complete_btn.count() > 0:
            expect(complete_btn).to_be_hidden()
    
    # Also verify mobile bottom nav is hidden
    mobile_nav = page.locator(".mobile-bottom-nav")
    expect(mobile_nav).to_be_hidden()
    
    # And mobile filter sheet
    filter_sheet = page.locator(".mobile-filter-sheet")
    expect(filter_sheet).to_be_hidden()


def test_quick_actions_visible_on_mobile(page: Page):
    """Test that quick action buttons are visible on mobile"""
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find non-completed tasks
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available for testing")
    
    # Check first task has quick actions
    first_task = tasks.first
    quick_actions = first_task.locator(".task-quick-actions")
    
    # Quick actions should be visible on mobile
    expect(quick_actions).to_be_visible()
    
    # Check individual buttons
    work_btn = quick_actions.locator(".task-quick-action.work")
    complete_btn = quick_actions.locator(".task-quick-action.complete")
    
    expect(work_btn).to_be_visible()
    expect(complete_btn).to_be_visible()
    
    # Mobile nav should be visible
    mobile_nav = page.locator(".mobile-bottom-nav")
    expect(mobile_nav).to_be_visible()


def test_responsive_quick_actions(page: Page):
    """Test that quick actions respond correctly to viewport changes"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available for testing")
    
    # Start with desktop viewport
    page.set_viewport_size({"width": 1280, "height": 800})
    time.sleep(0.5)
    
    # Quick actions should be hidden
    quick_actions = tasks.first.locator(".task-quick-actions")
    if quick_actions.count() > 0:
        expect(quick_actions).to_be_hidden()
    
    # Switch to mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    time.sleep(0.5)
    
    # Page might need to re-render, so wait a bit
    page.wait_for_timeout(1000)
    
    # Quick actions should now be visible
    # Note: The page might need to be reloaded for JS to detect the change
    page.reload()
    page.wait_for_load_state("networkidle")
    
    quick_actions = page.locator(".task-item:not(.completed)").first.locator(".task-quick-actions")
    expect(quick_actions).to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])