"""
Test that task metadata is displayed in the correct order
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_metadata_order_friction_before_effort(page: Page):
    """Test that friction icon appears before effort in task metadata"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find a task that has both friction and effort
    tasks = page.locator(".task-item")
    found_task = None
    
    for i in range(tasks.count()):
        task = tasks.nth(i)
        meta = task.locator(".task-meta")
        meta_text = meta.inner_text()
        
        # Check if task has both friction icon and effort
        has_friction = any(icon in meta_text for icon in ['🍃', '💨', '🌪️'])
        has_effort = any(time in meta_text for time in ['5m', '15m', '30m', '1h', '2h', '4h'])
        
        if has_friction and has_effort:
            found_task = task
            print(f"Found task with metadata: {meta_text}")
            break
    
    if not found_task:
        pytest.skip("No task found with both friction and effort")
    
    # Get all metadata spans
    meta_spans = found_task.locator(".task-meta span")
    metadata_order = []
    
    for i in range(meta_spans.count()):
        span = meta_spans.nth(i)
        text = span.inner_text()
        
        if text.startswith('@'):
            metadata_order.append(('category', text))
        elif text in ['🍃', '💨', '🌪️']:
            metadata_order.append(('friction', text))
        elif text in ['5m', '15m', '30m', '1h', '2h', '4h']:
            metadata_order.append(('effort', text))
        elif '📅' in text:
            metadata_order.append(('due_date', text))
    
    print(f"Metadata order: {metadata_order}")
    
    # Find positions of friction and effort
    friction_pos = None
    effort_pos = None
    
    for i, (type, _) in enumerate(metadata_order):
        if type == 'friction':
            friction_pos = i
        elif type == 'effort':
            effort_pos = i
    
    # Verify friction comes before effort
    if friction_pos is not None and effort_pos is not None:
        assert friction_pos < effort_pos, \
            f"Friction (position {friction_pos}) should come before effort (position {effort_pos})"
    
    # Take screenshot for visual verification
    found_task.screenshot(path="task_metadata_order.png")
    print("Screenshot saved: task_metadata_order.png")


def test_task_overflow_contained(page: Page):
    """Test that task items properly contain their content"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    # Check first few tasks
    for i in range(min(3, tasks.count())):
        task = tasks.nth(i)
        
        # Get computed styles
        styles = task.evaluate("""
            el => {
                const computed = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Check all child elements
                const children = el.querySelectorAll('*');
                let hasOverflow = false;
                
                for (let child of children) {
                    const childRect = child.getBoundingClientRect();
                    if (childRect.right > rect.right || 
                        childRect.bottom > rect.bottom ||
                        childRect.left < rect.left ||
                        childRect.top < rect.top) {
                        hasOverflow = true;
                        break;
                    }
                }
                
                return {
                    overflow: computed.overflow,
                    position: computed.position,
                    hasOverflow: hasOverflow,
                    width: rect.width,
                    height: rect.height
                };
            }
        """)
        
        print(f"Task {i}: {styles}")
        
        # Verify overflow is hidden
        assert styles['overflow'] == 'hidden', "Task items should have overflow: hidden"
        assert not styles['hasOverflow'], "No child elements should overflow the task container"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])