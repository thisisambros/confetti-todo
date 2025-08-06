"""
Test stop button in real user scenario where double-click is needed
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8000"

def test_stop_button_manual_simulation(page: Page):
    """Simulate exact user behavior when stop button requires double click"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find and start a task
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    print("Starting a task...")
    tasks.first.locator(".work-btn").click()
    time.sleep(1)  # Let it run for a bit like a real user would
    
    working_zone = page.locator(".working-zone")
    print(f"Initial working zone class: {working_zone.get_attribute('class')}")
    
    # First click attempt
    print("\nFirst click on stop button...")
    stop_btn = working_zone.locator("button.stop-working-btn")
    
    # Check button state before click
    btn_html_before = stop_btn.evaluate("el => el.outerHTML")
    print(f"Button HTML before: {btn_html_before}")
    
    # Click and wait
    stop_btn.click()
    time.sleep(0.5)
    
    # Check state after first click
    zone_class_1 = working_zone.get_attribute("class")
    print(f"Working zone after 1st click: {zone_class_1}")
    
    # Check if button still exists
    try:
        if stop_btn.is_visible():
            print("Stop button still visible after first click")
            btn_html_after = stop_btn.evaluate("el => el.outerHTML")
            print(f"Button HTML after: {btn_html_after}")
            
            # Try second click
            print("\nSecond click on stop button...")
            stop_btn.click()
            time.sleep(0.5)
            
            zone_class_2 = working_zone.get_attribute("class")
            print(f"Working zone after 2nd click: {zone_class_2}")
    except:
        print("Stop button no longer visible/exists")
    
    # Final check
    final_class = working_zone.get_attribute("class")
    is_empty = "empty" in final_class
    print(f"\nFinal result: empty={is_empty}, class='{final_class}'")
    
    # This test should fail if double-click is needed
    assert is_empty, "Working zone should be empty after single click"


def test_check_event_bubbling_issue(page: Page):
    """Check if event bubbling might be causing the issue"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Add comprehensive event tracking
    page.evaluate("""
        window.eventLog = [];
        
        // Track all events on stop button and its parents
        const stopBtn = document.querySelector('.stop-working-btn');
        const workingZone = document.getElementById('working-zone');
        
        if (stopBtn && workingZone) {
            // Track events on button
            ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup'].forEach(evt => {
                stopBtn.addEventListener(evt, (e) => {
                    window.eventLog.push({
                        target: 'button',
                        type: evt,
                        phase: 'capture',
                        stopped: e.cancelBubble,
                        prevented: e.defaultPrevented
                    });
                }, true);
                
                stopBtn.addEventListener(evt, (e) => {
                    window.eventLog.push({
                        target: 'button',
                        type: evt,
                        phase: 'bubble',
                        stopped: e.cancelBubble,
                        prevented: e.defaultPrevented
                    });
                }, false);
            });
            
            // Track events on working zone
            ['click', 'mousedown', 'mouseup'].forEach(evt => {
                workingZone.addEventListener(evt, (e) => {
                    if (e.target.classList.contains('stop-working-btn')) {
                        window.eventLog.push({
                            target: 'zone',
                            type: evt,
                            phase: 'bubble',
                            stopped: e.cancelBubble,
                            prevented: e.defaultPrevented
                        });
                    }
                }, false);
            });
        }
    """)
    
    # Click stop button
    stop_btn = page.locator("button.stop-working-btn")
    stop_btn.click()
    time.sleep(0.5)
    
    # Get event log
    events = page.evaluate("window.eventLog")
    print(f"\nCaptured {len(events)} events:")
    for evt in events:
        print(f"  {evt['target']}.{evt['type']} ({evt['phase']}) - stopped:{evt['stopped']}, prevented:{evt['prevented']}")
    
    # Check final state
    working_zone = page.locator(".working-zone")
    is_empty = "empty" in working_zone.get_attribute("class")
    print(f"\nWorking zone empty: {is_empty}")
    
    if not is_empty:
        print("BUG CONFIRMED: Zone not empty after click")
        # Check what prevented it
        working_task = page.evaluate("window.workingTask")
        print(f"workingTask still set: {working_task is not None}")


def test_stop_button_css_pointer_events(page: Page):
    """Check if CSS pointer-events might be interfering"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    tasks = page.locator(".task-item:not(.completed)")
    if tasks.count() == 0:
        pytest.skip("No tasks available")
    
    tasks.first.locator(".work-btn").click()
    time.sleep(0.5)
    
    # Check computed styles on stop button
    styles = page.evaluate("""
        () => {
            const btn = document.querySelector('.stop-working-btn');
            if (!btn) return null;
            
            const computed = window.getComputedStyle(btn);
            const rect = btn.getBoundingClientRect();
            
            return {
                pointerEvents: computed.pointerEvents,
                cursor: computed.cursor,
                display: computed.display,
                visibility: computed.visibility,
                opacity: computed.opacity,
                zIndex: computed.zIndex,
                position: computed.position,
                rect: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                }
            };
        }
    """)
    
    print("Stop button computed styles:")
    for key, value in styles.items():
        print(f"  {key}: {value}")
    
    # Check if anything is overlaying
    element_at_center = page.evaluate("""
        () => {
            const btn = document.querySelector('.stop-working-btn');
            if (!btn) return null;
            
            const rect = btn.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const el = document.elementFromPoint(centerX, centerY);
            return {
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                isStopButton: el === btn
            };
        }
    """)
    
    print(f"\nElement at button center: {element_at_center}")
    
    if not element_at_center['isStopButton']:
        print("WARNING: Something is overlaying the stop button!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])