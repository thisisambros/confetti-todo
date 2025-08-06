"""
Pytest configuration and fixtures for Confetti Todo tests
"""
import pytest
import os
from pathlib import Path
from playwright.sync_api import Page
from test_utils import TestDataManager, setup_test_data, cleanup_test_data

@pytest.fixture(scope="session")
def test_mode():
    """Enable test mode for entire test session"""
    os.environ["TEST_MODE"] = "true"
    yield
    os.environ.pop("TEST_MODE", None)
    
@pytest.fixture(autouse=True)
def test_data():
    """Setup and teardown test data for each test"""
    # Setup
    setup_test_data()
    yield
    # Teardown
    cleanup_test_data()
    
@pytest.fixture
def test_page(page: Page):
    """Provide a page that's already in test mode"""
    # Navigate with test parameter
    page.goto("http://localhost:8000?test=true")
    page.wait_for_load_state("networkidle")
    yield page
    
@pytest.fixture
def test_base_url():
    """Provide test mode base URL"""
    return "http://localhost:8000?test=true"