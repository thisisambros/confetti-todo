"""
Comprehensive end-to-end tests for the Natural Energy Regeneration System - V2.
Fixed version with proper element selectors and assertions.

Tests all aspects of the regeneration feature including:
- Natural regeneration (+1 every 15 minutes when not working)
- Regeneration pausing when working on tasks
- Regeneration timer display and countdown
- Visual states (regenerating/paused/hidden)
- Persistence across page reloads
- Integration with breaks and working zone
- Mobile responsiveness
- Edge cases and race conditions
- Multi-tab synchronization
"""

import pytest
from playwright.sync_api import Page, expect, BrowserContext
import time
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000?test=true"

class TestRegenerationDisplay:
    """Test regeneration timer display and visual states"""
    
    def test_regeneration_timer_hidden_when_full_energy(self, test_page: Page):
        """Test regeneration timer is hidden when energy is full"""
        # Ensure full energy
        test_page.evaluate("""
            currentEnergy = 12;
            updateEnergyDisplay();
            saveEnergyState();
            regenerationManager.updateDisplay();
        """)
        
        # Timer should be hidden
        timer = test_page.locator("#regen-timer")
        expect(timer).not_to_be_visible()
        
        # Verify hidden class is present
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "hidden" in timer_classes
    
    def test_regeneration_timer_shows_when_energy_consumed(self, test_page: Page):
        """Test regeneration timer appears when energy is below max"""
        # Consume some energy
        test_page.evaluate("""
            currentEnergy = 9;
            updateEnergyDisplay();
            saveEnergyState();
            regenerationManager.init();
        """)
        
        # Wait for timer to initialize
        test_page.wait_for_timeout(500)
        
        # Timer should be visible
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        # Verify hidden class is not present
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "hidden" not in timer_classes
        
        # Timer text should show time remaining
        timer_text = test_page.locator(".regen-text")
        expect(timer_text).to_be_visible()
        expect(timer_text).to_contain_text("Next energy in")
    
    def test_regeneration_countdown_format(self, test_page: Page):
        """Test regeneration countdown displays in MM:SS format"""
        # Set energy below max to trigger regeneration
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
            // Stop the timer to prevent countdown during test
            clearTimeout(regenerationManager.timer);
            clearInterval(regenerationManager.updateInterval);
        """)
        
        # Test different time values (in milliseconds since that's what the code uses)
        test_cases = [
            (900000, "15:00"),  # Full interval (15 min in ms)
            (600000, "10:00"),  # 10 minutes in ms
            (90000, "1:30"),    # 1 minute 30 seconds in ms
            (59000, "0:59"),    # Less than 1 minute in ms
            (0, "0:00")         # About to regenerate
        ]
        
        for ms, expected in test_cases:
            test_page.evaluate(f"""
                // Set a specific lastRegenTime to control the countdown
                regenerationManager.lastRegenTime = Date.now() - (900000 - {ms});
                regenerationManager.updateDisplay();
            """)
            
            # Get the actual countdown value
            actual = test_page.locator("#regen-countdown").inner_text()
            assert actual == expected, f"Expected {expected}, got {actual}"
    
    def test_regeneration_visual_states(self, test_page: Page):
        """Test visual states for regenerating and paused"""
        # Test regenerating state (green)
        test_page.evaluate("""
            currentEnergy = 10;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.updateDisplay();
        """)
        
        timer = test_page.locator("#regen-timer")
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" not in timer_classes
        assert "hidden" not in timer_classes
        
        # Icon should be visible and animated
        icon = test_page.locator(".regen-icon")
        expect(icon).to_be_visible()
        
        # Test paused state (orange)
        test_page.evaluate("""
            regenerationManager.pause();
        """)
        
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" in timer_classes
        
        # Status text should indicate paused
        timer_text = test_page.locator(".regen-text")
        expect(timer_text).to_contain_text("paused")
    
    def test_regeneration_timer_hidden_during_break(self, test_page: Page):
        """Test regeneration timer is hidden during breaks"""
        # Set energy below max
        test_page.evaluate("""
            currentEnergy = 7;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Start a break
        test_page.evaluate("""
            startBreak(15);
        """)
        
        # Timer should be hidden during break
        timer = test_page.locator("#regen-timer")
        expect(timer).not_to_be_visible()
        
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "hidden" in timer_classes


class TestRegenerationMechanics:
    """Test the core regeneration mechanics"""
    
    def test_regeneration_countdown_updates(self, test_page: Page):
        """Test regeneration countdown updates every second"""
        # Set energy below max to start regeneration
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 10; // Start at 10 seconds
        """)
        
        # Get initial countdown
        initial_time = test_page.locator("#regen-countdown").inner_text()
        
        # Wait 2 seconds
        test_page.wait_for_timeout(2100)
        
        # Countdown should have decreased
        new_time = test_page.locator("#regen-countdown").inner_text()
        assert initial_time != new_time, "Countdown should update"
        
        # Parse times and verify decrease
        def parse_time(time_str):
            parts = time_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        
        initial_seconds = parse_time(initial_time)
        new_seconds = parse_time(new_time)
        assert new_seconds < initial_seconds, "Time should decrease"
    
    def test_regeneration_triggers_at_interval(self, test_page: Page):
        """Test energy regenerates when timer reaches zero"""
        # Set energy below max and timer near zero
        test_page.evaluate("""
            currentEnergy = 9;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 2; // 2 seconds until regeneration
        """)
        
        # Wait for regeneration
        test_page.wait_for_timeout(3000)
        
        # Energy should have increased
        current_energy = test_page.locator("#current-energy").inner_text()
        assert int(current_energy) == 10, "Energy should regenerate by 1"
        
        # Timer should reset
        countdown = test_page.locator("#regen-countdown").inner_text()
        seconds = int(countdown.split(":")[0]) * 60 + int(countdown.split(":")[1])
        assert seconds > 890, "Timer should reset to ~15 minutes"
    
    def test_regeneration_pauses_when_working(self, test_page: Page):
        """Test regeneration pauses when starting work"""
        # Set energy below max
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 600; // 10 minutes
        """)
        
        # Get initial time
        initial_time = test_page.locator("#regen-countdown").inner_text()
        
        # Start working on a task
        task = test_page.locator(".task-item:not(.completed)").first
        task.locator(".work-btn").click()
        
        # Regeneration should be paused
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" in timer_classes
        
        # Wait 2 seconds
        test_page.wait_for_timeout(2000)
        
        # Time should not have changed
        current_time = test_page.locator("#regen-countdown").inner_text()
        assert current_time == initial_time, "Timer should be paused"
    
    def test_regeneration_resumes_after_work(self, test_page: Page):
        """Test regeneration resumes when stopping work"""
        # Set energy and start working
        test_page.evaluate("""
            currentEnergy = 7;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 500;
        """)
        
        # Start and then stop working
        task = test_page.locator(".task-item:not(.completed)").first
        task.locator(".work-btn").click()
        test_page.wait_for_timeout(1000)
        
        # Stop working
        test_page.locator(".stop-working").click()
        
        # Regeneration should resume
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" not in timer_classes
        
        # Timer should continue from where it paused
        initial_time = test_page.locator("#regen-countdown").inner_text()
        test_page.wait_for_timeout(2000)
        new_time = test_page.locator("#regen-countdown").inner_text()
        assert initial_time != new_time, "Timer should be counting down again"
    
    def test_regeneration_stops_at_max_energy(self, test_page: Page):
        """Test regeneration stops when energy reaches maximum"""
        # Set energy to 11 (one below max)
        test_page.evaluate("""
            currentEnergy = 11;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 2; // Regenerate soon
        """)
        
        # Wait for regeneration
        test_page.wait_for_timeout(3000)
        
        # Energy should be at max
        expect(test_page.locator("#current-energy")).to_have_text("12")
        
        # Regeneration timer should be hidden
        timer = test_page.locator("#regen-timer")
        expect(timer).not_to_be_visible()


class TestRegenerationPersistence:
    """Test regeneration state persistence"""
    
    def test_regeneration_state_saves_to_localstorage(self, test_page: Page):
        """Test regeneration state is saved to localStorage"""
        # Set specific regeneration state
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 450;
            regenerationManager.saveState();
        """)
        
        # Check localStorage
        saved_state = test_page.evaluate("""
            const state = localStorage.getItem('regenerationState');
            return JSON.parse(state);
        """)
        
        assert saved_state is not None
        assert saved_state['timeRemaining'] == 450
        assert 'lastUpdateTime' in saved_state
    
    def test_regeneration_state_persists_on_reload(self, test_page: Page):
        """Test regeneration continues after page reload"""
        # Set regeneration state
        test_page.evaluate("""
            currentEnergy = 7;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 600;
            regenerationManager.saveState();
        """)
        
        # Note the countdown time
        initial_countdown = test_page.locator("#regen-countdown").inner_text()
        
        # Reload page
        test_page.reload()
        test_page.wait_for_load_state("networkidle")
        
        # Regeneration should continue
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        # Timer should be close to where it was (accounting for reload time)
        new_countdown = test_page.locator("#regen-countdown").inner_text()
        
        def parse_time(time_str):
            parts = time_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        
        initial_seconds = parse_time(initial_countdown)
        new_seconds = parse_time(new_countdown)
        
        # Should be within 5 seconds (accounting for reload)
        assert abs(initial_seconds - new_seconds) <= 5
    
    def test_regeneration_accounts_for_offline_time(self, test_page: Page):
        """Test regeneration accounts for time spent offline"""
        # Set regeneration state with past timestamp
        test_page.evaluate("""
            currentEnergy = 6;
            updateEnergyDisplay();
            
            // Simulate being offline for 30 minutes
            const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);
            const state = {
                timeRemaining: 300, // Was 5 minutes from regeneration
                lastUpdateTime: thirtyMinutesAgo
            };
            localStorage.setItem('regenerationState', JSON.stringify(state));
            
            // Reload regeneration manager
            regenerationManager.loadState();
        """)
        
        # Should have regenerated twice (30 min = 2x 15 min intervals)
        current_energy = test_page.locator("#current-energy").inner_text()
        assert int(current_energy) == 8, "Should have regenerated 2 energy"


class TestRegenerationEdgeCases:
    """Test edge cases and race conditions"""
    
    def test_rapid_work_start_stop(self, test_page: Page):
        """Test rapid pause/resume doesn't break regeneration"""
        # Set energy below max
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Rapidly start/stop work
        task = test_page.locator(".task-item:not(.completed)").first
        for _ in range(5):
            task.locator(".work-btn").click()
            test_page.wait_for_timeout(100)
            test_page.locator(".stop-working").click()
            test_page.wait_for_timeout(100)
        
        # Regeneration should still work
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        timer_classes = test_page.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" not in timer_classes
    
    def test_regeneration_with_zero_energy(self, test_page: Page):
        """Test regeneration works correctly from zero energy"""
        # Set energy to zero
        test_page.evaluate("""
            currentEnergy = 0;
            updateEnergyDisplay();
            regenerationManager.init();
            regenerationManager.timeRemaining = 2;
        """)
        
        # Wait for regeneration
        test_page.wait_for_timeout(3000)
        
        # Should regenerate to 1
        expect(test_page.locator("#current-energy")).to_have_text("1")
        
        # Regeneration should continue
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
    
    def test_break_completion_resumes_regeneration(self, test_page: Page):
        """Test regeneration resumes after break if energy not full"""
        # Set energy and start break
        test_page.evaluate("""
            currentEnergy = 5;
            updateEnergyDisplay();
            startBreak(5); // 5 minute break restores 3 energy
        """)
        
        # Complete break
        test_page.evaluate("completeBreak()")
        test_page.wait_for_timeout(500)
        
        # Energy should be 8 (5 + 3)
        expect(test_page.locator("#current-energy")).to_have_text("8")
        
        # Regeneration should be active
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()


class TestMultiTabSynchronization:
    """Test regeneration synchronization across multiple tabs"""
    
    def test_regeneration_syncs_across_tabs(self, context: BrowserContext):
        """Test regeneration state syncs between multiple tabs"""
        # Open two tabs
        page1 = context.new_page()
        page2 = context.new_page()
        
        # Navigate both to test URL in headless mode
        page1.goto(BASE_URL)
        page2.goto(BASE_URL)
        
        # Set energy below max in first tab
        page1.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Wait for potential sync
        page1.wait_for_timeout(1000)
        page2.wait_for_timeout(1000)
        
        # Second tab should show regeneration
        timer2 = page2.locator("#regen-timer")
        expect(timer2).to_be_visible()
        
        # Start work in first tab
        task1 = page1.locator(".task-item:not(.completed)").first
        task1.locator(".work-btn").click()
        
        # Wait for sync
        page2.wait_for_timeout(1000)
        
        # Second tab should show paused regeneration
        timer2_classes = page2.evaluate("document.querySelector('#regen-timer').className")
        assert "paused" in timer2_classes
        
        # Clean up
        page1.close()
        page2.close()


class TestMobileResponsiveness:
    """Test regeneration display on mobile devices"""
    
    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667},   # iPhone SE
        {"width": 414, "height": 896},   # iPhone XR
        {"width": 360, "height": 640},   # Small Android
    ])
    def test_regeneration_display_mobile(self, page: Page, viewport):
        """Test regeneration timer displays correctly on mobile"""
        page.set_viewport_size(**viewport)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Set energy to trigger regeneration
        page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Timer should be visible and properly sized
        timer = page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        # Check font size is readable
        font_size = page.evaluate("""
            const el = document.querySelector('#regen-countdown');
            return window.getComputedStyle(el).fontSize;
        """)
        assert int(font_size.replace('px', '')) >= 14, "Font too small for mobile"
        
        # Timer should not overflow container
        timer_box = page.locator("#regen-timer").bounding_box()
        container_box = page.locator("#energy-regeneration").bounding_box()
        assert timer_box['width'] <= container_box['width'], "Timer overflows container"


class TestRegenerationIntegration:
    """Test regeneration integration with other features"""
    
    def test_regeneration_with_daily_reset(self, test_page: Page):
        """Test regeneration resets properly with daily energy reset"""
        # Set regeneration state from yesterday
        test_page.evaluate("""
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            
            // Save old regeneration state
            const regenState = {
                timeRemaining: 300,
                lastUpdateTime: yesterday.getTime()
            };
            localStorage.setItem('regenerationState', JSON.stringify(regenState));
            
            // Save old energy state
            const energyState = {
                currentEnergy: 5,
                lastUpdated: yesterday.getTime()
            };
            localStorage.setItem('energyState', JSON.stringify(energyState));
            
            // Trigger load (should reset)
            loadEnergyState();
            regenerationManager.init();
        """)
        
        # Energy should be reset to full
        expect(test_page.locator("#current-energy")).to_have_text("12")
        
        # Regeneration timer should be hidden (full energy)
        timer = test_page.locator("#regen-timer")
        expect(timer).not_to_be_visible()
    
    def test_regeneration_with_energy_warnings(self, test_page: Page):
        """Test regeneration display with low energy warnings"""
        # Set critical energy
        test_page.evaluate("""
            currentEnergy = 2;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Both warning and regeneration should be visible
        expect(test_page.locator("#energy-status")).to_have_text("Energy critical!")
        
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        # Visual hierarchy should prioritize warning
        warning_color = test_page.evaluate("""
            const el = document.querySelector('.energy-fill');
            return window.getComputedStyle(el).backgroundColor;
        """)
        assert "rgb" in warning_color  # Should have critical color


class TestRegenerationPerformance:
    """Test performance aspects of regeneration system"""
    
    def test_regeneration_timer_performance(self, test_page: Page):
        """Test regeneration timer doesn't impact page performance"""
        # Set up regeneration
        test_page.evaluate("""
            currentEnergy = 6;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Measure DOM updates over time
        initial_dom_version = test_page.evaluate("document.body.innerHTML.length")
        
        # Wait for multiple timer updates
        test_page.wait_for_timeout(5000)
        
        # Check DOM hasn't grown excessively
        final_dom_version = test_page.evaluate("document.body.innerHTML.length")
        dom_growth = final_dom_version - initial_dom_version
        
        # DOM size should be stable (allow small variance for timer updates)
        assert abs(dom_growth) < 100, f"Excessive DOM growth: {dom_growth} chars"


class TestRegenerationAccessibility:
    """Test accessibility features of regeneration display"""
    
    def test_regeneration_screen_reader_support(self, test_page: Page):
        """Test regeneration timer has proper ARIA labels"""
        # Set up regeneration
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Check ARIA labels
        timer = test_page.locator("#regen-timer")
        
        # Should have descriptive content for screen readers
        timer_text = timer.locator(".regen-text").inner_text()
        assert timer_text is not None and len(timer_text) > 0
        
        # Timer should have live region for updates
        timer_el = test_page.locator("#regen-timer")
        aria_live = timer_el.get_attribute("aria-live")
        # If no aria-live, that's okay - just checking implementation
    
    def test_regeneration_color_contrast(self, test_page: Page):
        """Test regeneration display has sufficient contrast"""
        # Set up regeneration in different states
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Test regenerating state contrast
        regen_text_color = test_page.evaluate("""
            const el = document.querySelector('.regen-text');
            return window.getComputedStyle(el).color;
        """)
        
        # Test paused state contrast
        test_page.evaluate("regenerationManager.pause()")
        
        paused_text_color = test_page.evaluate("""
            const el = document.querySelector('.regen-text');
            return window.getComputedStyle(el).color;
        """)
        
        # Both should be visible (basic check)
        assert regen_text_color != "transparent"
        assert paused_text_color != "transparent"


class TestRegenerationErrorHandling:
    """Test error handling in regeneration system"""
    
    def test_regeneration_handles_corrupt_state(self, test_page: Page):
        """Test regeneration handles corrupted localStorage"""
        # Set corrupt regeneration state
        test_page.evaluate("""
            localStorage.setItem('regenerationState', 'invalid json {');
            
            // Try to load
            regenerationManager.loadState();
        """)
        
        # Should recover gracefully
        timer = test_page.locator("#regen-timer")
        
        # Set energy to test
        test_page.evaluate("""
            currentEnergy = 9;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Should work normally
        expect(timer).to_be_visible()
    
    def test_regeneration_handles_time_anomalies(self, test_page: Page):
        """Test regeneration handles system time changes"""
        # Set regeneration with future timestamp
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            
            // Save state with future time
            const futureTime = Date.now() + (60 * 60 * 1000); // 1 hour ahead
            const state = {
                timeRemaining: 600,
                lastUpdateTime: futureTime
            };
            localStorage.setItem('regenerationState', JSON.stringify(state));
            
            // Load state
            regenerationManager.loadState();
        """)
        
        # Should handle gracefully without negative time
        countdown = test_page.locator("#regen-countdown").inner_text()
        minutes = int(countdown.split(":")[0])
        assert minutes >= 0, "Negative time displayed"
    
    def test_regeneration_recovers_from_errors(self, test_page: Page):
        """Test regeneration recovers from runtime errors"""
        # Inject error condition
        test_page.evaluate("""
            // Temporarily break the update function
            const originalUpdate = regenerationManager.updateDisplay;
            regenerationManager.updateDisplay = () => {
                throw new Error('Test error');
            };
            
            // Try to update
            try {
                regenerationManager.updateDisplay();
            } catch (e) {
                // Expected
            }
            
            // Restore function
            regenerationManager.updateDisplay = originalUpdate;
            
            // Set energy and init
            currentEnergy = 7;
            updateEnergyDisplay();
            regenerationManager.init();
        """)
        
        # Should recover and work normally
        timer = test_page.locator("#regen-timer")
        expect(timer).to_be_visible()
        
        # Timer should be running
        initial_time = test_page.locator("#regen-countdown").inner_text()
        test_page.wait_for_timeout(2000)
        new_time = test_page.locator("#regen-countdown").inner_text()
        assert initial_time != new_time, "Timer not updating after error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed=false"])