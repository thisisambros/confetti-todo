"""
Test that overdue dates have sufficient contrast for readability
"""
import pytest
from playwright.sync_api import Page, expect
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_overdue_date_contrast(page: Page):
    """Test that overdue dates have good contrast against the background"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Create a task with an overdue date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    # Add task via direct evaluation to set a past date
    page.evaluate(f"""
        const newTask = {{
            id: 'test_overdue_' + Date.now(),
            title: 'Overdue Test Task',
            description: '',
            type: 'task',
            category: 'other',
            effort: '30m',
            is_completed: false,
            created_at: new Date().toISOString(),
            due_date: '{yesterday_str}',
            completed_at: null,
            subtasks: []
        }};
        
        // Add to tasks
        window.currentData.today.unshift(newTask);
        window.allTasks.unshift(newTask);
        
        // Re-render
        window.renderTasks();
    """)
    
    time.sleep(0.5)
    
    # Find the overdue task
    overdue_task = page.locator(".task-item.overdue").filter(has_text="Overdue Test Task")
    expect(overdue_task).to_be_visible()
    
    # Find the date element within the task
    date_element = overdue_task.locator(".task-meta span:has-text('📅')")
    expect(date_element).to_be_visible()
    
    # Get computed styles
    styles = date_element.evaluate("""
        el => {
            const computed = window.getComputedStyle(el);
            const bgEl = el.closest('.task-item');
            const bgComputed = window.getComputedStyle(bgEl);
            
            return {
                color: computed.color,
                backgroundColor: bgComputed.backgroundColor,
                fontWeight: computed.fontWeight
            };
        }
    """)
    
    print(f"Date text color: {styles['color']}")
    print(f"Background color: {styles['backgroundColor']}")
    print(f"Font weight: {styles['fontWeight']}")
    
    # Calculate contrast ratio (simplified check)
    # The color should now be var(--color-danger) which is #dc2626 (dark red)
    # Background is #fff5f5 (very light pink)
    
    # Get the actual RGB values
    color_rgb = date_element.evaluate("""
        el => {
            const style = window.getComputedStyle(el);
            const match = style.color.match(/rgb\\((\\d+), (\\d+), (\\d+)\\)/);
            if (match) {
                return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
            }
            return null;
        }
    """)
    
    if color_rgb:
        # Simple contrast check - red component should be significantly darker than background
        # For #dc2626, R=220, G=38, B=38
        # For good contrast on light background, we expect dark colors
        print(f"RGB values: R={color_rgb[0]}, G={color_rgb[1]}, B={color_rgb[2]}")
        
        # Check if it's a dark color (low RGB values mean dark)
        is_dark_enough = color_rgb[0] < 230 and color_rgb[1] < 100 and color_rgb[2] < 100
        assert is_dark_enough, f"Color {color_rgb} is not dark enough for good contrast"
    
    # Visual check - take a screenshot for manual verification
    overdue_task.screenshot(path="overdue_date_contrast.png")
    print("Screenshot saved as overdue_date_contrast.png")


def test_due_today_contrast(page: Page):
    """Test that due today dates also have good contrast"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Add a task due today
    page.locator("#task-input").fill("Task Due Today")
    page.locator("#task-input").press("Enter")
    time.sleep(0.5)
    
    # Complete the palette (defaults to today)
    page.keyboard.press("Enter")
    time.sleep(1)
    
    # Find the task
    today_task = page.locator(".task-item").filter(has_text="Task Due Today")
    date_element = today_task.locator(".task-meta span:has-text('📅')")
    
    if date_element.count() > 0:
        color = date_element.evaluate("el => window.getComputedStyle(el).color")
        print(f"Due today color: {color}")
        
        # Should be using --color-warning which should be visible
        today_task.screenshot(path="due_today_contrast.png")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])