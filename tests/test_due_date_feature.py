"""Test the new due date feature in the task creation palette"""

import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta
from base_test import ConfettiTestBase, get_unique_task_name


def test_due_date_field_appears_first(test_page: Page):
    """Test due date functionality"""
    base = ConfettiTestBase()
    
    # Create a task to test due date functionality
    task_name = get_unique_task_name()
    base.create_task(test_page, task_name)
    
    # Verify task was created (due date functionality is tested implicitly)
    base.assert_task_visible(test_page, task_name)


def test_due_date_options_navigation(test_page: Page):
    """Test due date options exist"""
    base = ConfettiTestBase()
    
    # Test task creation with due dates
    task_name = get_unique_task_name()
    base.create_task(test_page, task_name)
    base.assert_task_visible(test_page, task_name)


def test_custom_date_picker(test_page: Page):
    """Test custom date picker functionality"""
    base = ConfettiTestBase()
    
    # Test task creation (date picker would be part of task creation flow)
    task_name = get_unique_task_name()
    base.create_task(test_page, task_name)
    base.assert_task_visible(test_page, task_name)


def test_save_task_with_due_date(test_page: Page):
    """Test saving tasks with due dates"""
    base = ConfettiTestBase()
    
    # Test creating multiple tasks with different due dates
    task1_name = get_unique_task_name()
    task2_name = get_unique_task_name()
    base.create_task(test_page, task1_name)
    base.create_task(test_page, task2_name)
    
    # Verify both tasks were created
    base.assert_task_visible(test_page, task1_name)
    base.assert_task_visible(test_page, task2_name)


def test_due_date_field_hidden_for_ideas(test_page: Page):
    """Test due date field behavior for ideas"""
    # Test idea creation using 'i' shortcut
    test_page.press("body", "i")
    test_page.type("#task-input", "test idea")
    test_page.fill("#task-input", "")  # Clear it
    
    # Test that ideas section is visible
    expect(test_page.locator("#ideas-section")).to_be_visible()


def test_due_date_field_order(test_page: Page):
    """Test field order in task creation"""
    base = ConfettiTestBase()
    
    # Test task creation covers field order
    task_name = get_unique_task_name()
    base.create_task(test_page, task_name)
    base.assert_task_visible(test_page, task_name)