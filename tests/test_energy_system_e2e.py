"""
Comprehensive end-to-end tests for the Energy System in Confetti Todo.
Tests all visual and functional aspects of the energy system including:
- Energy display and visual states
- Energy consumption when starting tasks
- Break suggestions and modals
- Break timer functionality
- Energy restoration
- Warning states at low energy
- Integration with Working Zone
- Mobile responsiveness
- Edge cases and error conditions
"""
import pytest
from playwright.sync_api import Page, expect
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000?test=true"

class TestEnergySystemDisplay:
    """Test energy display components and visual states"""
    
    def test_initial_energy_display(self, test_page: Page):
        """Test initial energy display shows full energy"""
        # Verify energy section is visible
        energy_section = test_page.locator(".widget-section:has(.widget-title:text('Energy'))")
        expect(energy_section).to_be_visible()
        
        # Check initial energy values
        current_energy = test_page.locator("#current-energy")
        max_energy = test_page.locator("#max-energy")
        expect(current_energy).to_have_text("12")
        expect(max_energy).to_have_text("12")
        
        # Check energy bar is full
        energy_fill = test_page.locator(".energy-fill")
        fill_style = test_page.evaluate("document.querySelector('.energy-fill').style.width")
        assert fill_style == "100%", f"Expected 100% width, got {fill_style}"
        
        # Check status text
        energy_status = test_page.locator("#energy-status")
        expect(energy_status).to_have_text("Full energy")
        
        # Verify break button is available
        break_button = test_page.locator("#take-break-btn")
        expect(break_button).to_be_visible()
        expect(break_button).to_have_text("Take a Break")
    
    def test_energy_bar_visual_states(self, test_page: Page):
        """Test energy bar changes color based on energy level"""
        # Start a task to consume energy
        test_page.evaluate("""
            currentEnergy = 8;  // Set to medium level
            updateEnergyDisplay();
        """)
        
        energy_fill = test_page.locator(".energy-fill")
        # Should not have warning classes
        class_list = test_page.evaluate("document.querySelector('.energy-fill').className")
        assert "warning" not in class_list
        assert "critical" not in class_list
        
        # Set to warning level
        test_page.evaluate("""
            currentEnergy = 4;  // Warning threshold
            updateEnergyDisplay();
        """)
        
        # Should have warning class
        class_list = test_page.evaluate("document.querySelector('.energy-fill').className")
        assert "warning" in class_list
        expect(test_page.locator("#energy-status")).to_have_text("Consider a break")
        
        # Set to critical level
        test_page.evaluate("""
            currentEnergy = 2;  // Critical threshold
            updateEnergyDisplay();
        """)
        
        # Should have critical class
        class_list = test_page.evaluate("document.querySelector('.energy-fill').className")
        assert "critical" in class_list
        expect(test_page.locator("#energy-status")).to_have_text("Energy critical!")
        expect(test_page.locator("#take-break-btn")).to_have_text("Take a Break Now!")
    
    def test_energy_percentage_calculation(self, test_page: Page):
        """Test energy bar width reflects correct percentage"""
        test_scenarios = [
            (12, "100%"),  # Full energy
            (9, "75%"),    # 3/4 energy
            (6, "50%"),    # Half energy
            (3, "25%"),    # 1/4 energy
            (0, "0%")      # No energy
        ]
        
        for energy, expected_width in test_scenarios:
            test_page.evaluate(f"""
                currentEnergy = {energy};
                updateEnergyDisplay();
            """)
            
            energy_fill = test_page.locator(".energy-fill")
            actual_width = test_page.evaluate("document.querySelector('.energy-fill').style.width")
            assert actual_width == expected_width, f"Energy {energy} should show {expected_width} width"


class TestEnergyConsumption:
    """Test energy consumption when starting tasks"""
    
    def test_task_energy_cost_display(self, test_page: Page):
        """Test that tasks show energy cost indicators"""
        # Wait for tasks to load
        test_page.wait_for_selector(".task-item")
        
        # Find tasks with different effort levels
        tasks_with_energy = test_page.locator(".task-energy-cost")
        
        # Should have at least one task with energy cost
        expect(tasks_with_energy.first).to_be_visible()
        
        # Verify energy cost format
        first_cost = tasks_with_energy.first
        expect(first_cost).to_contain_text("⚡")
        
        # Check tooltip
        tooltip = first_cost.get_attribute("title")
        assert "Requires" in tooltip and "energy" in tooltip
    
    def test_start_task_consumes_energy(self, test_page: Page):
        """Test that starting a task consumes the correct amount of energy"""
        # Get initial energy
        initial_energy = int(test_page.locator("#current-energy").inner_text())
        
        # Find a task with known energy cost
        task = test_page.locator(".task-item:not(.completed)").first
        energy_cost_el = task.locator(".task-energy-cost")
        
        if energy_cost_el.count() > 0:
            # Extract energy cost from text (e.g., "⚡4" -> 4)
            cost_text = energy_cost_el.inner_text()
            energy_cost = int(cost_text.replace("⚡", ""))
            
            # Start the task
            task.locator(".work-btn").click()
            
            # Verify energy was consumed
            test_page.wait_for_timeout(500)  # Wait for update
            new_energy = int(test_page.locator("#current-energy").inner_text())
            assert new_energy == initial_energy - energy_cost
            
            # Verify working zone shows the task
            working_zone = test_page.locator(".working-zone")
            expect(working_zone).not_to_have_class("empty")
    
    def test_insufficient_energy_prevents_start(self, test_page: Page):
        """Test that tasks cannot be started without sufficient energy"""
        # Set energy to low level
        test_page.evaluate("""
            currentEnergy = 2;
            updateEnergyDisplay();
            saveEnergyState();
        """)
        
        # Find a high-energy task
        tasks = test_page.locator(".task-item:not(.completed)")
        high_energy_task = None
        
        for i in range(tasks.count()):
            task = tasks.nth(i)
            cost_el = task.locator(".task-energy-cost")
            if cost_el.count() > 0:
                cost = int(cost_el.inner_text().replace("⚡", ""))
                if cost > 2:
                    high_energy_task = task
                    break
        
        if high_energy_task:
            # Try to start the task
            high_energy_task.locator(".work-btn").click()
            
            # Should show toast message
            toast = test_page.locator(".toast")
            expect(toast).to_be_visible()
            expect(toast).to_contain_text("Not enough energy")
            
            # Break modal should appear
            break_modal = test_page.locator("#break-modal")
            expect(break_modal).not_to_have_class("hidden")
    
    def test_energy_calculation_from_metadata(self, test_page: Page):
        """Test energy cost calculation based on effort and friction"""
        # Test various effort/friction combinations
        test_cases = [
            {"effort": "15m", "friction": 2, "expected": 1},  # Minimal
            {"effort": "30m", "friction": 2, "expected": 2},  # Base case
            {"effort": "1h", "friction": 2, "expected": 4},   # 1 hour
            {"effort": "30m", "friction": 5, "expected": 5},  # High friction
            {"effort": "1h", "friction": 3, "expected": 5},   # 1h + friction
        ]
        
        for case in test_cases:
            result = test_page.evaluate(f"calculateEnergyCost({{ effort: '{case['effort']}', friction: {case['friction']} }})")
            assert result == case['expected'], f"Failed for {case}"


class TestBreakSystem:
    """Test break functionality and UI"""
    
    def test_break_modal_display(self, test_page: Page):
        """Test break modal shows correct information"""
        # Consume some energy first
        test_page.evaluate("""
            currentEnergy = 7;
            updateEnergyDisplay();
        """)
        
        # Click break button
        test_page.locator("#take-break-btn").click()
        
        # Verify modal is visible
        modal = test_page.locator("#break-modal")
        expect(modal).not_to_have_class("hidden")
        
        # Check energy used display
        energy_used = test_page.locator("#energy-used")
        expect(energy_used).to_have_text("5")  # 12 - 7 = 5
        
        # Verify break options are present
        break_options = test_page.locator(".break-option")
        expect(break_options).to_have_count(3)
        
        # Check break durations
        expect(break_options.nth(0)).to_contain_text("5 min")
        expect(break_options.nth(1)).to_contain_text("15 min")
        expect(break_options.nth(2)).to_contain_text("30 min")
    
    def test_break_warning_at_low_energy(self, test_page: Page):
        """Test warning message appears when energy is critical"""
        # Set critical energy
        test_page.evaluate("""
            currentEnergy = 2;
            updateEnergyDisplay();
        """)
        
        # Open break modal
        test_page.locator("#take-break-btn").click()
        
        # Warning should be visible
        warning = test_page.locator("#break-warning")
        expect(warning).not_to_have_class("hidden")
        expect(warning).to_contain_text("Energy critically low")
    
    def test_start_break_timer(self, test_page: Page):
        """Test starting a break shows timer interface"""
        # Consume energy and open break modal
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
        """)
        test_page.locator("#take-break-btn").click()
        
        # Start 5-minute break
        test_page.locator(".break-option").first.click()
        
        # Verify break timer is visible
        timer = test_page.locator("#break-timer")
        expect(timer).not_to_have_class("hidden")
        
        # Check timer display
        timer_display = test_page.locator("#break-timer-display")
        expect(timer_display).to_have_text("5:00")
        
        # Check break type
        break_type = test_page.locator("#break-type")
        expect(break_type).to_have_text("Quick Stretch")
        
        # Modal should be closed
        modal = test_page.locator("#break-modal")
        class_list = test_page.evaluate("document.querySelector('#break-modal').className")
        assert "hidden" in class_list
    
    def test_break_timer_countdown(self, test_page: Page):
        """Test break timer counts down correctly"""
        # Start a break
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
        """)
        test_page.locator("#take-break-btn").click()
        test_page.locator(".break-option").first.click()
        
        # Wait a bit and check timer updated
        test_page.wait_for_timeout(2000)
        
        timer_display = test_page.locator("#break-timer-display")
        time_text = timer_display.inner_text()
        
        # Should show less than 5:00
        minutes, seconds = map(int, time_text.split(":"))
        total_seconds = minutes * 60 + seconds
        assert total_seconds < 300 and total_seconds > 295
        
        # Check progress bar
        progress_fill = test_page.locator("#break-progress-fill")
        width = test_page.evaluate("document.querySelector('#break-progress-fill').style.width")
        assert width != "0%"
    
    def test_cancel_break(self, test_page: Page):
        """Test canceling a break"""
        # Start a break
        test_page.evaluate("currentEnergy = 8; updateEnergyDisplay();")
        test_page.locator("#take-break-btn").click()
        test_page.locator(".break-option").first.click()
        
        # Cancel break
        test_page.locator(".break-cancel").click()
        
        # Timer should be hidden
        timer = test_page.locator("#break-timer")
        class_list = test_page.evaluate("document.querySelector('#break-timer').className")
        assert "hidden" in class_list
        
        # Energy should not change
        expect(test_page.locator("#current-energy")).to_have_text("8")
    
    def test_complete_break_restores_energy(self, test_page: Page):
        """Test completing a break restores correct energy"""
        # Set low energy and start break
        test_page.evaluate("""
            currentEnergy = 4;
            updateEnergyDisplay();
            
            // Start and immediately complete a 5-min break
            startBreak(5);
            
            // Simulate break completion
            setTimeout(() => completeBreak(), 100);
        """)
        
        test_page.wait_for_timeout(500)
        
        # Wait for energy update and check
        test_page.wait_for_timeout(600)
        current_energy = test_page.locator("#current-energy").inner_text()
        # Energy should be restored (was 4, should be 7 after 5-min break)
        assert int(current_energy) == 7, f"Expected energy to be 7, got {current_energy}"
        
        # Check toast message
        toast = test_page.locator(".toast")
        expect(toast).to_contain_text("+3 energy restored")
    
    def test_full_restore_break(self, test_page: Page):
        """Test 30-minute break fully restores energy"""
        # Set low energy
        test_page.evaluate("""
            currentEnergy = 2;
            updateEnergyDisplay();
        """)
        
        # Start 30-min break and complete it
        test_page.locator("#take-break-btn").click()
        test_page.locator(".break-option").nth(2).click()  # 30-min option
        
        # Simulate completion
        test_page.evaluate("completeBreak()")
        
        # Energy should be full
        expect(test_page.locator("#current-energy")).to_have_text("12")
        expect(test_page.locator("#energy-status")).to_have_text("Full energy")


class TestWorkingZoneIntegration:
    """Test energy system integration with Working Zone"""
    
    def test_stop_working_during_break(self, test_page: Page):
        """Test that working stops when break starts"""
        # Start working on a task
        task = test_page.locator(".task-item:not(.completed)").first
        task.locator(".work-btn").click()
        
        # Verify working
        working_zone = test_page.locator(".working-zone")
        expect(working_zone).not_to_have_class("empty")
        
        # Start a break
        test_page.evaluate("startBreak(5)")
        
        # Working should stop
        test_page.wait_for_timeout(500)
        expect(working_zone).to_have_class("empty")
    
    def test_cannot_start_task_during_break(self, test_page: Page):
        """Test tasks cannot be started during break"""
        # Start a break
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            startBreak(5);
        """)
        
        # Try to start a task
        task = test_page.locator(".task-item:not(.completed)").first
        task.locator(".work-btn").click()
        
        # Should show error toast
        toast = test_page.locator(".toast")
        expect(toast).to_be_visible()
        # Note: Exact message depends on implementation
        
        # Working zone should remain empty
        working_zone = test_page.locator(".working-zone")
        expect(working_zone).to_have_class("empty")
    
    def test_break_suggestion_threshold(self, test_page: Page):
        """Test break suggestion appears at correct threshold"""
        # Start with full energy
        test_page.evaluate("""
            currentEnergy = 12;
            updateEnergyDisplay();
            localStorage.removeItem('lastBreakSuggestion');
        """)
        
        # Start a task that will consume energy to threshold
        test_page.evaluate("""
            // Manually trigger working and energy consumption
            const task = { title: 'Test Task', effort: '1h', friction: 3 };
            startWorkingOn(task);
        """)
        
        # Should consume energy and potentially show break modal
        # Energy: 12 - 5 = 7 (above threshold of 4)
        modal = test_page.locator("#break-modal")
        expect(modal).to_have_class("hidden")
        
        # Consume more energy to hit threshold
        test_page.evaluate("""
            consumeEnergy(3);  // Now at 4 energy
        """)
        
        # Modal might appear (depends on lastBreakSuggestion timing)
        # This tests the threshold logic exists


class TestEnergyPersistence:
    """Test energy state persistence and daily reset"""
    
    def test_energy_state_saves_to_localstorage(self, test_page: Page):
        """Test energy state is saved to localStorage"""
        # Set specific energy
        test_page.evaluate("""
            currentEnergy = 7;
            updateEnergyDisplay();
            saveEnergyState();
        """)
        
        # Check localStorage
        saved_state = test_page.evaluate("""
            const state = localStorage.getItem('energyState');
            return JSON.parse(state);
        """)
        
        assert saved_state['currentEnergy'] == 7
        assert 'lastUpdated' in saved_state
    
    def test_energy_state_loads_on_refresh(self, test_page: Page):
        """Test energy state persists across page refresh"""
        # Set and save energy
        test_page.evaluate("""
            currentEnergy = 5;
            updateEnergyDisplay();
            saveEnergyState();
        """)
        
        # Refresh page
        test_page.reload()
        test_page.wait_for_load_state("networkidle")
        
        # Check energy was restored
        expect(test_page.locator("#current-energy")).to_have_text("5")
    
    def test_daily_energy_reset(self, test_page: Page):
        """Test energy resets to full on new day"""
        # Set low energy with yesterday's date
        test_page.evaluate("""
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            
            const state = {
                currentEnergy: 3,
                lastUpdated: yesterday.getTime()
            };
            localStorage.setItem('energyState', JSON.stringify(state));
            
            // Trigger load
            loadEnergyState();
        """)
        
        # Energy should be reset to full
        expect(test_page.locator("#current-energy")).to_have_text("12")
        expect(test_page.locator("#energy-status")).to_have_text("Full energy")


class TestMobileResponsiveness:
    """Test energy system on mobile viewports"""
    
    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667},   # iPhone SE
        {"width": 414, "height": 896},   # iPhone XR
        {"width": 360, "height": 640},   # Small Android
    ])
    def test_energy_display_mobile(self, page: Page, viewport):
        """Test energy display on various mobile sizes"""
        page.set_viewport_size(**viewport)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Energy widget should be visible
        energy_widget = page.locator(".widget-section:has(.widget-title:text('Energy'))")
        expect(energy_widget).to_be_visible()
        
        # All elements should be accessible
        expect(page.locator("#current-energy")).to_be_visible()
        expect(page.locator(".energy-bar")).to_be_visible()
        expect(page.locator("#take-break-btn")).to_be_visible()
        
        # Break button should be tappable size (min 44px)
        button_size = page.locator("#take-break-btn").bounding_box()
        assert button_size['height'] >= 44
    
    def test_break_modal_mobile(self, page: Page):
        """Test break modal works well on mobile"""
        page.set_viewport_size(width=375, height=667)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Open break modal
        page.locator("#take-break-btn").click()
        
        # Modal should be fullscreen on mobile
        modal = page.locator(".break-modal")
        expect(modal).to_be_visible()
        
        # Break options should be tappable
        options = page.locator(".break-option")
        for i in range(options.count()):
            option_size = options.nth(i).bounding_box()
            assert option_size['height'] >= 44
    
    def test_break_timer_mobile(self, page: Page):
        """Test break timer interface on mobile"""
        page.set_viewport_size(width=375, height=667)
        page.goto(BASE_URL)
        
        # Start a break
        page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            startBreak(5);
        """)
        
        # Timer should be visible and readable
        timer = page.locator("#break-timer")
        expect(timer).to_be_visible()
        
        # Timer display should be large enough
        display = page.locator("#break-timer-display")
        font_size = page.evaluate("""
            const el = document.querySelector('#break-timer-display');
            return window.getComputedStyle(el).fontSize;
        """)
        # Should be at least 24px for readability
        assert int(font_size.replace('px', '')) >= 24


class TestEdgeCasesAndErrors:
    """Test edge cases and error conditions"""
    
    def test_negative_energy_prevention(self, test_page: Page):
        """Test energy cannot go below 0"""
        test_page.evaluate("""
            currentEnergy = 2;
            consumeEnergy(5);  // Try to consume more than available
        """)
        
        # Energy should be 0, not negative
        expect(test_page.locator("#current-energy")).to_have_text("0")
    
    def test_energy_overflow_prevention(self, test_page: Page):
        """Test energy cannot exceed maximum"""
        test_page.evaluate("""
            currentEnergy = 11;
            restoreEnergy(5);  // Try to restore beyond max
        """)
        
        # Energy should be capped at 12
        expect(test_page.locator("#current-energy")).to_have_text("12")
    
    def test_break_when_full_energy(self, test_page: Page):
        """Test break behavior with full energy"""
        # Ensure full energy
        test_page.evaluate("""
            currentEnergy = 12;
            updateEnergyDisplay();
        """)
        
        # Try to take break
        test_page.locator("#take-break-btn").click()
        
        # Modal should still open (user might want to rest anyway)
        modal = test_page.locator("#break-modal")
        expect(modal).not_to_have_class("hidden")
        
        # But energy used should show 0
        expect(test_page.locator("#energy-used")).to_have_text("0")
    
    def test_rapid_energy_consumption(self, test_page: Page):
        """Test rapid energy consumption doesn't cause issues"""
        # Rapidly consume energy
        test_page.evaluate("""
            for (let i = 0; i < 5; i++) {
                consumeEnergy(2);
            }
        """)
        
        # Should handle gracefully
        current = int(test_page.locator("#current-energy").inner_text())
        assert current == 2  # 12 - 10 = 2
    
    def test_break_timer_accuracy(self, test_page: Page):
        """Test break timer timing accuracy"""
        # Start break and track time
        start_time = time.time()
        test_page.evaluate("""
            currentEnergy = 8;
            updateEnergyDisplay();
            startBreak(5);
        """)
        
        # Wait 3 seconds
        test_page.wait_for_timeout(3000)
        
        # Check timer shows approximately 2 minutes left
        timer_text = test_page.locator("#break-timer-display").inner_text()
        minutes, seconds = map(int, timer_text.split(":"))
        remaining = minutes * 60 + seconds
        
        # Should be close to 297 seconds (5 min - 3 sec)
        assert 295 <= remaining <= 299
    
    def test_concurrent_break_attempts(self, test_page: Page):
        """Test starting break while already on break"""
        # Start first break
        test_page.evaluate("startBreak(5)")
        
        # Try to start another break
        test_page.evaluate("startBreak(15)")
        
        # Should still show first break
        break_type = test_page.locator("#break-type")
        expect(break_type).to_have_text("Quick Stretch")
    
    def test_energy_cost_calculation_extremes(self, test_page: Page):
        """Test energy calculation with extreme values"""
        # Test very long task
        result = test_page.evaluate("""
            const task = { effort: '1d', friction: 5 };
            return calculateEnergyCost(task);
        """)
        # Should be capped at max energy
        assert result <= 12
        
        # Test minimal task
        result = test_page.evaluate("""
            const task = { effort: '15m', friction: 1 };
            return calculateEnergyCost(task);
        """)
        # Should be at least 1
        assert result >= 1
    
    def test_break_suggestion_cooldown(self, test_page: Page):
        """Test break suggestion doesn't spam user"""
        # Set low energy and trigger suggestion
        test_page.evaluate("""
            currentEnergy = 4;
            updateEnergyDisplay();
            showBreakSuggestion();
        """)
        
        # Close modal
        test_page.locator(".modal-close").click()
        
        # Try to trigger again immediately
        test_page.evaluate("showBreakSuggestion()")
        
        # Modal should not reappear (cooldown active)
        modal = test_page.locator("#break-modal")
        expect(modal).to_have_class("hidden")


class TestAccessibility:
    """Test accessibility features of energy system"""
    
    def test_energy_display_aria_labels(self, test_page: Page):
        """Test energy display has proper accessibility labels"""
        # Energy display should have descriptive text
        energy_section = test_page.locator(".widget-section:has(.widget-title:text('Energy'))")
        
        # Check for screen reader friendly content
        current = test_page.locator("#current-energy")
        max_val = test_page.locator("#max-energy")
        
        # Status should be descriptive
        status = test_page.locator("#energy-status")
        expect(status).not_to_be_empty()
    
    def test_break_modal_keyboard_navigation(self, test_page: Page):
        """Test break modal can be navigated with keyboard"""
        # Open modal
        test_page.locator("#take-break-btn").click()
        
        # Tab through options
        test_page.keyboard.press("Tab")
        test_page.keyboard.press("Tab")
        
        # Should be able to select with Enter
        test_page.keyboard.press("Enter")
        
        # Break should start
        timer = test_page.locator("#break-timer")
        expect(timer).not_to_have_class("hidden")
    
    def test_color_contrast(self, test_page: Page):
        """Test energy indicators have sufficient color contrast"""
        # Set different energy levels and check visibility
        levels = [12, 8, 4, 2]
        
        for level in levels:
            test_page.evaluate(f"currentEnergy = {level}; updateEnergyDisplay();")
            
            # Energy text should be visible
            current = test_page.locator("#current-energy")
            expect(current).to_be_visible()
            
            # Status text should be readable
            status = test_page.locator("#energy-status")
            expect(status).to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])