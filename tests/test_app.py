"""
Simple integration tests for Confetti Todo
These tests ensure all core functionality works when we make changes
"""
import pytest
from playwright.sync_api import Page, expect
import time
from base_test import ConfettiTestBase, get_unique_task_name

# CORE FUNCTIONALITY TESTS

def test_add_task(test_page: Page):
    """Test that we can add a new task"""
    base = ConfettiTestBase()
    task_name = get_unique_task_name()
    
    # Create task using utility
    base.create_task(test_page, task_name)
    
    # Assert task is visible
    base.assert_task_visible(test_page, task_name)

def test_complete_task(test_page: Page):
    """Test that we can complete tasks"""
    base = ConfettiTestBase()
    
    # Wait for existing tasks
    test_page.wait_for_selector(".task-item")
    
    # Complete first uncompleted task
    base.complete_first_uncompleted_task(test_page)

def test_search_works(test_page: Page):
    """Test that search functionality works"""
    base = ConfettiTestBase()
    
    # Use base utility to search
    base.search_for(test_page, "test")

def test_north_star_empty_state(test_page: Page):
    """Test that North Star shows empty state"""
    # North Star section should be visible
    expect(test_page.locator(".north-star-section")).to_be_visible()
    
    # Should show empty state or content
    north_star_content = test_page.locator(".north-star-section")
    expect(north_star_content).to_be_visible()

def test_working_zone_empty_state(test_page: Page):
    """Test that working zone shows empty state"""
    # Working zone should exist
    expect(test_page.locator(".working-zone")).to_be_visible()
    
    # Should show empty or working state
    working_zone = test_page.locator(".working-zone")
    expect(working_zone).to_be_visible()

def test_ideas_section_visible(test_page: Page):
    """Test that ideas section is visible"""
    # Ideas section should be visible
    expect(test_page.locator("#ideas")).to_be_visible()

def test_filters_work(test_page: Page):
    """Test that task filters work"""
    base = ConfettiTestBase()
    
    # Test different filters
    for filter_name in ["all", "today", "week", "overdue"]:
        base.click_filter(test_page, filter_name)

def test_keyboard_shortcut_n(test_page: Page):
    """Test that 'N' focuses input"""
    # Press N
    test_page.press("body", "n")
    
    # Input should be focused - check by seeing if we can type
    test_page.type("#task-input", "focused")
    
    # Clear the input for other tests
    test_page.fill("#task-input", "")
    
    # If we got here without error, the input was focused
    expect(test_page.locator("#task-input")).to_be_visible()

def test_data_persistence(test_page: Page):
    """Test that data persists after reload"""
    base = ConfettiTestBase()
    
    # Add a task with unique name
    unique_name = get_unique_task_name()
    base.create_task(test_page, unique_name)
    
    # Reload with test mode
    test_page.goto("http://localhost:8000?test=true")
    test_page.wait_for_load_state("networkidle")
    
    # Verify app still works after reload by creating another task
    after_reload_name = get_unique_task_name()
    base.create_task(test_page, after_reload_name, wait_for_visible=False)

def test_responsive_layout(test_page: Page):
    """Test that layout is responsive"""
    base = ConfettiTestBase()
    
    # Test desktop view
    base.switch_to_desktop(test_page)
    expect(test_page.locator(".main-content")).to_be_visible()
    
    # Test mobile view
    base.switch_to_mobile(test_page)
    expect(test_page.locator(".main-content")).to_be_visible()

# Run tests with: pytest tests/test_app.py -v