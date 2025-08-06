"""Integration tests for Confetti Todo app using Playwright"""
import pytest
from playwright.sync_api import Page, expect
import time
import os
import re

# Base URL for tests
BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def live_server():
    """Start the FastAPI server for testing"""
    import subprocess
    import time
    
    # Start server
    process = subprocess.Popen(['python', 'server.py'])
    time.sleep(2)  # Wait for server to start
    
    yield
    
    # Cleanup
    process.terminate()
    process.wait()

def test_add_task(page: Page, live_server):
    """Test adding a new task"""
    page.goto(BASE_URL)
    
    # Wait for page to load
    page.wait_for_selector("#task-input")
    
    # Add a task
    page.fill("#task-input", "Test task from Playwright")
    page.press("#task-input", "Enter")
    
    # Should open palette modal
    page.wait_for_selector("#palette-modal:not(.hidden)")
    
    # Save with defaults
    page.press("body", "Enter")
    
    # Check task appears
    page.wait_for_selector(".task-item")
    expect(page.locator(".task-title")).to_contain_text("Test task from Playwright")

def test_complete_task(page: Page, live_server):
    """Test completing a task"""
    page.goto(BASE_URL)
    page.wait_for_selector(".task-item")
    
    # Click checkbox
    page.click(".task-checkbox:first-child")
    
    # Should show confetti (check class added)
    page.wait_for_selector(".confetti-piece", timeout=1000)
    
    # Task should be marked complete
    expect(page.locator(".task-item:first-child")).to_have_class(re.compile("completed"))

def test_north_star_feature(page: Page, live_server):
    """Test North Star task selection"""
    page.goto(BASE_URL)
    
    # North Star section should be visible with empty state
    expect(page.locator(".north-star-section")).to_be_visible()
    expect(page.locator(".choose-north-star-btn")).to_be_visible()
    
    # Click choose button
    page.click(".choose-north-star-btn")
    
    # Should show picker modal
    page.wait_for_selector(".north-star-picker-modal")
    
    # Select first task if available
    if page.locator(".north-star-option").count() > 0:
        page.click(".north-star-option:first-child")
        
        # Should show toast with XP bonus
        expect(page.locator(".toast")).to_contain_text("+25 XP")

def test_search_functionality(page: Page, live_server):
    """Test the morphing search"""
    page.goto(BASE_URL)
    page.wait_for_selector("#search-icon-morph")
    
    # Click search icon
    page.click("#search-icon-morph")
    
    # Search should expand
    expect(page.locator(".search-morphing")).to_have_class(re.compile("active"))
    
    # Type search term
    page.fill("#search-input", "test")
    
    # Should filter tasks
    time.sleep(0.5)  # Wait for search to process

def test_working_zone(page: Page, live_server):
    """Test working on a task"""
    page.goto(BASE_URL)
    page.wait_for_selector(".task-item")
    
    # Click work button on first task
    if page.locator(".work-btn").count() > 0:
        page.click(".work-btn:first-child")
        
        # Working zone should update
        expect(page.locator(".working-zone")).not_to_have_class(re.compile("empty"))
        
        # Timer should be visible
        expect(page.locator(".working-timer")).to_be_visible()

def test_add_subtask(page: Page, live_server):
    """Test adding a subtask"""
    page.goto(BASE_URL)
    page.wait_for_selector(".task-item")
    
    # Click add subtask button
    if page.locator(".subtask-btn").count() > 0:
        page.click(".subtask-btn:first-child")
        
        # Input should appear
        page.wait_for_selector(".subtask-input")
        
        # Type subtask
        page.fill(".subtask-input input", "Test subtask")
        page.click(".save-subtask")
        
        # Subtask should be added
        page.wait_for_selector(".subtask")

def test_filter_tasks(page: Page, live_server):
    """Test task filtering"""
    page.goto(BASE_URL)
    
    # Click Today filter
    page.click('[data-filter="today"]')
    
    # Filter should be active
    expect(page.locator('[data-filter="today"]')).to_have_class(re.compile("active"))

def test_sort_tasks(page: Page, live_server):
    """Test task sorting"""
    page.goto(BASE_URL)
    
    # Change sort order
    page.select_option("#sort-select", "xp")
    
    # Should update display (tasks re-render)
    time.sleep(0.5)

def test_ideas_section(page: Page, live_server):
    """Test ideas management"""
    page.goto(BASE_URL)
    
    # Ideas section should be visible
    expect(page.locator("#ideas-section")).to_be_visible()
    
    # Quick add idea with 'i' key
    page.press("body", "i")
    page.wait_for_timeout(100)
    
    # Should focus input with idea mode
    expect(page.locator("#task-input")).to_be_focused()

def test_keyboard_shortcuts(page: Page, live_server):
    """Test keyboard shortcuts"""
    page.goto(BASE_URL)
    
    # Press 'n' to add task
    page.press("body", "n")
    
    # Should focus input
    expect(page.locator("#task-input")).to_be_focused()
    
    # Press Escape to cancel
    page.press("#task-input", "Escape")
    
    # Should blur input
    expect(page.locator("#task-input")).not_to_be_focused()

def test_xp_calculation(page: Page, live_server):
    """Test XP display and calculation"""
    page.goto(BASE_URL)
    page.wait_for_selector(".task-item")
    
    # XP should be visible on tasks
    if page.locator(".task-xp").count() > 0:
        xp_text = page.locator(".task-xp").first.text_content()
        assert "XP" in xp_text

def test_responsive_design(page: Page, live_server):
    """Test responsive layout"""
    page.goto(BASE_URL)
    
    # Test mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    
    # Right widget should stack below main content
    time.sleep(0.5)
    
    # Test desktop viewport
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Layout should be side-by-side
    time.sleep(0.5)

def test_data_persistence(page: Page, live_server):
    """Test that data persists across reloads"""
    page.goto(BASE_URL)
    
    # Add a task
    page.fill("#task-input", "Persistent task")
    page.press("#task-input", "Enter")
    page.press("body", "Enter")
    
    # Reload page
    page.reload()
    
    # Task should still be there
    page.wait_for_selector(".task-item")
    expect(page.locator(".task-title")).to_contain_text("Persistent task")

def test_empty_states(page: Page, live_server):
    """Test empty state messages"""
    page.goto(BASE_URL)
    
    # If no tasks, should show empty state
    if page.locator(".task-item").count() == 0:
        expect(page.locator("#empty-state")).to_be_visible()
        expect(page.locator("#empty-state")).to_contain_text("No tasks yet")

def test_confetti_animation(page: Page, live_server):
    """Test confetti celebration animation"""
    page.goto(BASE_URL)
    
    # Need at least one task to complete
    if page.locator(".task-item").count() > 0:
        # Complete a task
        page.click(".task-checkbox:not(.checked):first-child")
        
        # Confetti should appear
        page.wait_for_selector(".confetti-piece", timeout=1000)
        
        # Confetti should disappear after animation
        page.wait_for_selector(".confetti-piece", state="detached", timeout=2000)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])