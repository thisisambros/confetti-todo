"""
Test stop button with exact user simulation to find the double-click bug
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_stop_button_rapid_clicks(page: Page):
    """Test what happens with rapid/multiple clicks on stop button"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Start a task
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    working_zone = page.locator(".working-zone")
    stop_btn = working_zone.locator("button.stop-working-btn")
    
    # Set up monitoring
    page.evaluate("""
        window.stopEvents = [];
        window.zoneUpdates = [];
        
        // Monitor stop button clicks
        const stopBtn = document.querySelector('.stop-working-btn');
        if (stopBtn) {
            // Capture at multiple phases
            ['click', 'mousedown', 'mouseup'].forEach(eventType => {
                stopBtn.addEventListener(eventType, (e) => {
                    window.stopEvents.push({
                        type: eventType,
                        time: Date.now(),
                        workingTask: !!window.workingTask
                    });
                }, true);
            });
        }
        
        // Monitor working zone updates
        const zone = document.getElementById('working-zone');
        const observer = new MutationObserver((mutations) => {
            window.zoneUpdates.push({
                time: Date.now(),
                hasEmpty: zone.classList.contains('empty'),
                innerHTML: zone.innerHTML.substring(0, 100)
            });
        });
        observer.observe(zone, { 
            attributes: true, 
            childList: true, 
            subtree: true,
            attributeFilter: ['class']
        });
    """)
    
    # Try single click first
    print("=== Single Click Test ===")
    stop_btn.click()
    time.sleep(0.5)
    
    events = page.evaluate("window.stopEvents")
    updates = page.evaluate("window.zoneUpdates")
    
    print(f"Events captured: {len(events)}")
    for event in events:
        print(f"  {event['type']}: workingTask={event['workingTask']}")
    
    print(f"\nZone updates: {len(updates)}")
    for update in updates:
        print(f"  hasEmpty={update['hasEmpty']}")
    
    final_class = working_zone.get_attribute("class")
    print(f"\nFinal working zone class: {final_class}")
    
    # Reset for second test
    if "empty" in final_class:
        print("\n✓ Single click worked correctly")
    else:
        print("\n✗ BUG: Single click did not clear working zone")


def test_stop_button_with_delay(page: Page):
    """Test if there's a timing issue with stop button"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    # Start task and let it run for a bit
    tasks.first.locator(".work-btn").click()
    time.sleep(2)  # Let timer run
    
    working_zone = page.locator(".working-zone")
    
    # Check if there's any async operation
    page.evaluate("""
        // Override updateWorkingZone to log calls
        const original = window.updateWorkingZone;
        window.updateCalls = [];
        window.updateWorkingZone = function() {
            window.updateCalls.push({
                time: Date.now(),
                workingTask: !!window.workingTask,
                stack: new Error().stack
            });
            return original.apply(this, arguments);
        };
    """)
    
    # Click stop
    stop_btn = working_zone.locator("button.stop-working-btn")
    stop_btn.click()
    
    # Wait and check
    time.sleep(1)
    
    update_calls = page.evaluate("window.updateCalls")
    print(f"updateWorkingZone called {len(update_calls)} times after stop click")
    
    final_class = working_zone.get_attribute("class")
    assert "empty" in final_class, "Working zone should be empty"


def test_stop_button_focus_blur(page: Page):
    """Test if focus/blur events affect stop button"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Test with focus/blur events
    page.evaluate("""
        const stopBtn = document.querySelector('.stop-working-btn');
        if (stopBtn) {
            // Some apps require focus before click
            stopBtn.focus();
            
            // Add blur handler to see if it interferes
            stopBtn.addEventListener('blur', (e) => {
                console.log('Stop button blurred');
            });
        }
    """)
    
    stop_btn = page.locator("button.stop-working-btn")
    
    # Click with focus
    stop_btn.focus()
    time.sleep(0.1)
    stop_btn.click()
    time.sleep(0.5)
    
    working_zone = page.locator(".working-zone")
    assert "empty" in working_zone.get_attribute("class")


def test_stop_button_prevents_default(page: Page):
    """Check if preventDefault is being called somewhere"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Check if click event is being prevented
    prevented = page.evaluate("""
        let prevented = false;
        const stopBtn = document.querySelector('.stop-working-btn');
        if (stopBtn) {
            stopBtn.addEventListener('click', (e) => {
                if (e.defaultPrevented) {
                    prevented = true;
                }
            }, true);
            
            // Simulate click
            stopBtn.click();
        }
        prevented;
    """)
    
    print(f"Click event prevented: {prevented}")
    
    # Now try real click
    stop_btn = page.locator("button.stop-working-btn")
    stop_btn.click()
    time.sleep(0.5)
    
    working_zone = page.locator(".working-zone")
    assert "empty" in working_zone.get_attribute("class")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])