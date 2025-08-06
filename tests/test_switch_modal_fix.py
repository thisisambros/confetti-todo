"""Simple focused test to verify the switch modal fix"""

import pytest
from playwright.sync_api import Page, expect
import time


def test_switch_modal_basic_functionality(page: Page):
    """Test the basic switch modal functionality without timer"""
    # Navigate to the app
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Clear any existing tasks and create test tasks
    page.evaluate("""
        // Clear all existing data
        window.currentData = {
            today: [],
            ideas: [],
            backlog: []
        };
        window.allTasks = [];
        
        // Add our test tasks
        window.currentData.today = [
            {
                id: 'task1',
                title: 'First Task',
                is_completed: false,
                category: 'admin',
                effort: '30m',
                friction: 2,
                subtasks: []
            },
            {
                id: 'task2', 
                title: 'Second Task',
                is_completed: false,
                category: 'product',
                effort: '1h',
                friction: 3,
                subtasks: []
            }
        ];
        
        // Force re-render
        window.processAndRender();
    """)
    
    # Wait for tasks to render
    page.wait_for_selector(".task-item", state="visible")
    expect(page.locator(".task-item")).to_have_count(2)
    
    # Start working on first task
    first_play = page.locator(".task-item").first.locator(".work-btn")
    first_play.click()
    
    # Verify working zone shows first task
    expect(page.locator("#working-zone")).to_contain_text("First Task")
    
    # Try to work on second task - should show modal
    second_play = page.locator(".task-item").nth(1).locator(".work-btn")
    second_play.click()
    
    # Verify modal appears
    expect(page.locator(".switch-modal")).to_be_visible()
    expect(page.locator(".modal-overlay")).to_be_visible()
    
    # CRITICAL: Verify NO countdown element
    expect(page.locator(".countdown")).to_have_count(0)
    
    # Verify modal content
    expect(page.locator(".switch-modal")).to_contain_text("Are you sure you want to switch tasks?")
    expect(page.locator(".switch-modal")).to_contain_text("First Task")
    expect(page.locator(".switch-modal")).to_contain_text("Second Task")
    
    # Verify both buttons exist
    expect(page.locator("button:has-text('Yes, switch')")).to_be_visible()
    expect(page.locator("button:has-text('No, keep working')")).to_be_visible()
    
    # Wait to ensure modal doesn't auto-close (was 3 seconds with timer)
    page.wait_for_timeout(4000)
    
    # Modal should still be visible
    expect(page.locator(".switch-modal")).to_be_visible()
    
    # Test "Yes" button - switch tasks
    page.click("button:has-text('Yes, switch')")
    
    # Modal should disappear
    expect(page.locator(".switch-modal")).to_be_hidden()
    expect(page.locator(".modal-overlay")).to_be_hidden()
    
    # Should now be working on Second Task
    expect(page.locator("#working-zone")).to_contain_text("Second Task")
    
    # Page should be fully interactive - test by opening search
    page.keyboard.press("/")
    expect(page.locator("#search-input")).to_be_visible()
    page.keyboard.press("Escape")
    
    print("✅ Switch modal test PASSED - No timer, page remains interactive!")


def test_switch_modal_cancel_functionality(page: Page):
    """Test canceling the switch keeps current task"""
    page.goto("http://localhost:8000")
    page.wait_for_load_state("networkidle")
    
    # Clear and create test tasks
    page.evaluate("""
        window.currentData = {
            today: [
                {id: 'task1', title: 'Keep This Task', is_completed: false, subtasks: []},
                {id: 'task2', title: 'Other Task', is_completed: false, subtasks: []}
            ],
            ideas: [],
            backlog: []
        };
        window.allTasks = [];
        window.processAndRender();
    """)
    
    # Start working on first task
    page.locator(".task-item").first.locator(".work-btn").click()
    
    # Try to switch
    page.locator(".task-item").nth(1).locator(".work-btn").click()
    
    # Click "No" to cancel
    page.click("button:has-text('No, keep working')")
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    # Should still be working on first task
    expect(page.locator("#working-zone")).to_contain_text("Keep This Task")
    
    print("✅ Cancel switch test PASSED!")


def test_switch_modal_overlay_click(page: Page):
    """Test clicking overlay cancels switch"""
    page.goto("http://localhost:8000") 
    page.wait_for_load_state("networkidle")
    
    # Clear and create test tasks
    page.evaluate("""
        window.currentData = {
            today: [
                {id: 'task1', title: 'Task A', is_completed: false, subtasks: []},
                {id: 'task2', title: 'Task B', is_completed: false, subtasks: []}
            ],
            ideas: [],
            backlog: []
        };
        window.allTasks = [];
        window.processAndRender();
    """)
    
    # Start working on first task
    page.locator(".task-item").first.locator(".work-btn").click()
    
    # Try to switch
    page.locator(".task-item").nth(1).locator(".work-btn").click()
    
    # Click overlay at top-left corner
    overlay = page.locator(".modal-overlay").first
    overlay.click(position={"x": 10, "y": 10})
    
    # Modal should be gone
    expect(page.locator(".switch-modal")).to_be_hidden()
    
    # Should still be working on Task A
    expect(page.locator("#working-zone")).to_contain_text("Task A")
    
    print("✅ Overlay click test PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed"])