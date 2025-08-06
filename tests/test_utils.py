"""
Test utilities for Confetti Todo tests
Provides setup/teardown for test data to avoid corrupting production data
"""
import os
from pathlib import Path
import shutil
from playwright.sync_api import Page

# Test data file
TEST_TODO_FILE = Path("todos.test.md")
PROD_TODO_FILE = Path("todos.md")

# Sample test data
TEST_DATA = """# today

- [ ] Test Energy System Task @work !1h %3 ^2025-08-01
- [ ] Quick Energy Test @admin !15m %2 ^2025-08-01
- [ ] High Friction Task @product !30m %5 ^2025-08-01
- [ ] Long Task Test @research !4h %4 ^2025-08-01

# ideas

- [ ] ? Future Energy Feature @development
- [ ] ? Break System Enhancement @ux

# backlog

- [ ] Backlog Task with Energy @selling !2h %3
- [ ] Another Backlog Item @support !30m %1
- [x] Completed Energy Task @admin !1h %2 {2025-07-29}
"""

def setup_test_data():
    """Create test data file with sample tasks"""
    TEST_TODO_FILE.write_text(TEST_DATA)
    
def cleanup_test_data():
    """Remove test data file"""
    if TEST_TODO_FILE.exists():
        TEST_TODO_FILE.unlink()
        
def ensure_test_mode(page: Page) -> str:
    """Ensure the page is using test mode"""
    # Navigate with test mode parameter
    base_url = "http://localhost:8000"
    page.goto(f"{base_url}?test=true")
    page.wait_for_load_state("networkidle")
    return base_url
    
def get_test_base_url() -> str:
    """Get base URL with test mode"""
    return "http://localhost:8000?test=true"
    
class TestDataManager:
    """Context manager for test data"""
    
    def __enter__(self):
        # Set environment variable
        os.environ["TEST_MODE"] = "true"
        # Create test data
        setup_test_data()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        cleanup_test_data()
        # Unset environment variable
        os.environ.pop("TEST_MODE", None)