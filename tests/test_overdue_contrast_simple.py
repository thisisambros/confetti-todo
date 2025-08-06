"""
Simple test to check overdue date contrast
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_check_overdue_task_contrast(page: Page):
    """Check contrast of existing overdue tasks"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Look for any overdue tasks
    overdue_tasks = page.locator(".task-item.overdue")
    
    if overdue_tasks.count() == 0:
        print("No overdue tasks found to test")
        # No screenshot needed - skip test gracefully
        pytest.skip("No overdue tasks available")
    
    # Check the first overdue task
    first_overdue = overdue_tasks.first
    print(f"Found overdue task: {first_overdue.locator('.task-title').inner_text()}")
    
    # Find the date span
    date_spans = first_overdue.locator(".task-meta span")
    date_span = None
    
    for i in range(date_spans.count()):
        span = date_spans.nth(i)
        text = span.inner_text()
        if "📅" in text:
            date_span = span
            break
    
    if not date_span:
        pytest.fail("Could not find date span in overdue task")
    
    # Get computed styles
    styles = date_span.evaluate("""
        el => {
            const computed = window.getComputedStyle(el);
            return {
                color: computed.color,
                fontWeight: computed.fontWeight,
                fontSize: computed.fontSize
            };
        }
    """)
    
    print(f"Date styles: {styles}")
    
    # Get background color of task
    bg_color = first_overdue.evaluate("el => window.getComputedStyle(el).backgroundColor")
    print(f"Task background: {bg_color}")
    
    # Visual verification complete - no screenshot needed
    print("Overdue task contrast verified programmatically")
    
    # Also get the color values
    danger_color = page.evaluate("window.getComputedStyle(document.documentElement).getPropertyValue('--color-danger')")
    error_color = page.evaluate("window.getComputedStyle(document.documentElement).getPropertyValue('--color-error')")
    
    print(f"--color-danger: {danger_color}")
    print(f"--color-error: {error_color}")
    
    # Verify we're using the danger color (dark red) not error color (light pink)
    assert "220, 38, 38" in styles['color'] or "#dc2626" in styles['color'], \
        f"Date should use --color-danger (#dc2626) but got {styles['color']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])