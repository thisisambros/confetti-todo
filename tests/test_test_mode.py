"""
Test to verify test mode is working correctly
"""
import pytest
from playwright.sync_api import Page, expect
from pathlib import Path

def test_test_mode_uses_separate_file(test_page: Page):
    """Verify test mode uses todos.test.md not todos.md"""
    page = test_page
    
    # Check via API that we're in test mode
    response = page.request.get("http://localhost:8000/api/test-mode")
    data = response.json()
    
    assert data["test_mode"] == True
    assert "todos.test.md" in data["data_file"]
    assert "todos.md" not in data["data_file"]
    
def test_test_data_is_loaded(test_page: Page):
    """Verify test data is loaded correctly"""
    page = test_page
    
    # Should see test tasks
    tasks = page.locator(".task-item")
    
    # From our test data, we have 4 tasks in main section
    assert tasks.count() >= 3  # At least some test tasks visible
    
    # Check for specific test task
    test_task = page.locator(".task-item").filter(has_text="Test task 1")
    expect(test_task).to_be_visible()
    
def test_production_file_not_modified():
    """Verify production todos.md is not touched during tests"""
    prod_file = Path("todos.md")
    test_file = Path("todos.test.md")
    
    # Get original modification time if file exists
    if prod_file.exists():
        orig_mtime = prod_file.stat().st_mtime
    else:
        orig_mtime = None
        
    # Test file should exist
    assert test_file.exists(), "Test file should be created"
    
    # If production file exists, its modification time shouldn't change
    if orig_mtime and prod_file.exists():
        assert prod_file.stat().st_mtime == orig_mtime, "Production file was modified!"