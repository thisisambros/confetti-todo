"""
Test stop button behavior to identify the double-click issue
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_stop_button_behavior_detailed(page: Page):
    """Detailed test of stop button behavior"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find a task to start
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No uncompleted tasks available")
    
    # Start the first task
    first_task = tasks.first
    task_text = first_task.locator(".task-title").inner_text()
    print(f"Starting task: {task_text}")
    
    work_btn = first_task.locator(".work-btn")
    work_btn.click()
    time.sleep(0.5)
    
    # Check initial state
    working_zone = page.locator(".working-zone")
    print(f"Working zone classes after start: {working_zone.get_attribute('class')}")
    
    # Find stop button and check its state
    stop_btn = working_zone.locator("button.stop-working-btn")
    print(f"Stop button visible: {stop_btn.is_visible()}")
    print(f"Stop button enabled: {stop_btn.is_enabled()}")
    print(f"Stop button text: {stop_btn.inner_text()}")
    
    # Add event listener to track what happens on click
    page.evaluate("""
        const stopBtn = document.querySelector('.stop-working-btn');
        if (stopBtn) {
            window.stopClicks = [];
            stopBtn.addEventListener('click', (e) => {
                window.stopClicks.push({
                    time: Date.now(),
                    defaultPrevented: e.defaultPrevented,
                    propagationStopped: e.cancelBubble,
                    currentTarget: e.currentTarget.className
                });
                console.log('Stop button clicked:', window.stopClicks.length);
            }, true);
        }
    """)
    
    # Click stop button
    print("\n--- First click ---")
    stop_btn.click()
    
    # Check state immediately
    time.sleep(0.1)
    working_zone_class1 = working_zone.get_attribute("class")
    print(f"Working zone classes after 1st click: {working_zone_class1}")
    
    # Check if button is still there
    try:
        still_visible = stop_btn.is_visible()
        print(f"Stop button still visible: {still_visible}")
    except:
        print("Stop button not found after click")
    
    # Wait a bit more
    time.sleep(0.5)
    
    # Check final state
    working_zone_class_final = working_zone.get_attribute("class")
    print(f"Working zone classes final: {working_zone_class_final}")
    
    # Get click events
    clicks = page.evaluate("window.stopClicks || []")
    print(f"\nRecorded clicks: {len(clicks)}")
    for i, click in enumerate(clicks):
        print(f"Click {i+1}: {click}")
    
    # Check if we need a second click
    if "empty" not in working_zone_class_final:
        print("\n!!! BUG CONFIRMED: Working zone not empty after first click")
        print("Attempting second click...")
        
        # Try to find and click again
        try:
            stop_btn2 = working_zone.locator("button.stop-working-btn")
            if stop_btn2.is_visible():
                stop_btn2.click()
                time.sleep(0.5)
                working_zone_class2 = working_zone.get_attribute("class")
                print(f"Working zone after 2nd click: {working_zone_class2}")
        except:
            print("Could not find stop button for second click")
    
    # Final assertion
    assert "empty" in working_zone.get_attribute("class"), "Working zone should be empty after clicking stop"


def test_stop_button_event_handlers(page: Page):
    """Check if there are multiple event handlers causing issues"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Start a task
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Inspect the stop button's onclick and event listeners
    button_info = page.evaluate("""
        () => {
            const btn = document.querySelector('.stop-working-btn');
            if (!btn) return null;
            
            // Get onclick attribute
            const onclickAttr = btn.getAttribute('onclick');
            
            return {
                onclick: onclickAttr,
                className: btn.className,
                disabled: btn.disabled,
                type: btn.type,
                innerHTML: btn.innerHTML
            };
        }
    """)
    
    print("Stop button info:")
    print(f"  onclick: {button_info['onclick']}")
    print(f"  className: {button_info['className']}")
    print(f"  disabled: {button_info['disabled']}")
    print(f"  innerHTML: {button_info['innerHTML']}")
    
    # Test the stopWorking function directly
    print("\nTesting stopWorking() function directly...")
    
    # Check initial state
    working_state_before = page.evaluate("!!window.workingTask")
    print(f"Working task before: {working_state_before}")
    
    # Call stopWorking directly
    page.evaluate("() => window.stopWorking && window.stopWorking()")
    time.sleep(0.5)
    
    # Check after calling
    working_state_after = page.evaluate("!!window.workingTask")
    working_zone_class = page.locator(".working-zone").get_attribute("class")
    print(f"Working task after: {working_state_after}")
    print(f"Working zone class: {working_zone_class}")
    
    assert not working_state_after, "workingTask should be null after stopWorking()"
    assert "empty" in working_zone_class, "Working zone should have empty class"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])