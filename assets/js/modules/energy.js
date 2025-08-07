// Energy System Module
import { CONFIG } from '../config.js';
import { EnergyStorage } from '../utils/storage.js';
import { DOM } from '../utils/dom.js';
import { EventBus } from '../utils/events.js';

export class EnergySystem {
    constructor() {
        this.currentEnergy = CONFIG.MAX_ENERGY;
        this.regenerationManager = new RegenerationManager();
        this.breakManager = new BreakManager();
        this.isInitialized = false;
    }

    init() {
        if (this.isInitialized) return;
        
        this.loadState();
        this.checkDailyReset();
        this.regenerationManager.init();
        this.updateDisplay();
        this.isInitialized = true;
    }

    loadState() {
        const state = EnergyStorage.getEnergyState();
        this.currentEnergy = state.currentEnergy;
    }

    saveState() {
        EnergyStorage.saveEnergyState({
            currentEnergy: this.currentEnergy,
            lastRegenTime: this.regenerationManager.lastRegenTime,
            isPaused: this.regenerationManager.isPaused,
            lastUpdateDate: new Date().toDateString()
        });
    }

    checkDailyReset() {
        const state = EnergyStorage.getEnergyState();
        const today = new Date().toDateString();
        
        if (state.lastUpdateDate !== today) {
            this.currentEnergy = CONFIG.MAX_ENERGY;
            EnergyStorage.resetDailyEnergy();
            EventBus.emit('energy:dailyReset');
        }
    }

    consume(amount) {
        if (this.currentEnergy < amount) {
            return false;
        }
        
        this.currentEnergy -= amount;
        this.saveState();
        this.updateDisplay();
        EventBus.emit('energy:consumed', { amount, remaining: this.currentEnergy });
        
        if (this.currentEnergy <= CONFIG.ENERGY_SUGGESTION_THRESHOLD) {
            this.suggestBreak();
        }
        
        return true;
    }

    restore(amount) {
        const actualRestore = Math.min(amount, CONFIG.MAX_ENERGY - this.currentEnergy);
        this.currentEnergy += actualRestore;
        this.saveState();
        this.updateDisplay();
        EventBus.emit('energy:restored', { amount: actualRestore, total: this.currentEnergy });
        return actualRestore;
    }

    calculateTaskCost(effort, friction) {
        const effortValue = CONFIG.EFFORT_VALUES[effort] || 6;
        return Math.ceil((effortValue / 3) * friction);
    }

    suggestBreak() {
        if (this.currentEnergy <= CONFIG.ENERGY_SUGGESTION_THRESHOLD) {
            EventBus.emit('energy:breakSuggested', { currentEnergy: this.currentEnergy });
        }
    }

    updateDisplay() {
        const energyBar = DOM.get('#energy-bar');
        const energyText = DOM.get('#energy-text');
        const energyWidget = DOM.get('.energy-widget');
        
        if (!energyBar || !energyText) return;
        
        const percentage = (this.currentEnergy / CONFIG.MAX_ENERGY) * 100;
        energyBar.style.width = `${percentage}%`;
        energyText.textContent = `${this.currentEnergy}/${CONFIG.MAX_ENERGY}`;
        
        // Update colors based on energy level
        DOM.removeClass(energyWidget, 'warning danger');
        if (this.currentEnergy <= CONFIG.ENERGY_WARNING_THRESHOLD) {
            DOM.addClass(energyWidget, 'danger');
        } else if (this.currentEnergy <= CONFIG.ENERGY_SUGGESTION_THRESHOLD) {
            DOM.addClass(energyWidget, 'warning');
        }
    }
}

// Regeneration Manager
class RegenerationManager {
    constructor() {
        this.timer = null;
        this.lastRegenTime = Date.now();
        this.isPaused = false;
        this.updateInterval = null;
        this.timeRemaining = CONFIG.REGENERATION_INTERVAL;
    }

    init() {
        this.loadState();
        this.start();
        this.updateDisplay();
    }

    loadState() {
        const state = EnergyStorage.getEnergyState();
        this.lastRegenTime = state.lastRegenTime || Date.now();
        this.isPaused = state.isPaused || false;
    }

    start() {
        if (this.timer) return;
        
        // Calculate time elapsed since last regen
        const elapsed = Date.now() - this.lastRegenTime;
        
        // Check if we should regenerate multiple points
        if (elapsed >= CONFIG.REGENERATION_INTERVAL) {
            const pointsToRegen = Math.floor(elapsed / CONFIG.REGENERATION_INTERVAL);
            const actualRegen = Math.min(pointsToRegen, CONFIG.MAX_ENERGY - window.energySystem.currentEnergy);
            
            if (actualRegen > 0 && !this.isPaused) {
                window.energySystem.restore(actualRegen);
                EventBus.emit('ui:showToast', `+${actualRegen} energy regenerated! ⚡`);
                this.lastRegenTime = Date.now() - (elapsed % CONFIG.REGENERATION_INTERVAL);
            }
        }
        
        // Calculate remaining time until next regen
        const timeSinceLastRegen = Date.now() - this.lastRegenTime;
        this.timeRemaining = Math.max(0, CONFIG.REGENERATION_INTERVAL - timeSinceLastRegen);
        
        // Set timer for next regeneration
        this.timer = setTimeout(() => {
            this.regenerate();
        }, this.timeRemaining);
        
        // Update display every second
        this.updateInterval = setInterval(() => {
            this.updateDisplay();
        }, 1000);
        
        this.isPaused = false;
        this.updateDisplay();
    }

    pause() {
        if (!this.timer) return;
        
        clearTimeout(this.timer);
        clearInterval(this.updateInterval);
        this.timer = null;
        this.updateInterval = null;
        
        const elapsed = Date.now() - this.lastRegenTime;
        this.timeRemaining = Math.max(0, CONFIG.REGENERATION_INTERVAL - elapsed);
        
        this.isPaused = true;
        this.updateDisplay();
    }

    regenerate() {
        if (window.energySystem.currentEnergy < CONFIG.MAX_ENERGY && !this.isPaused) {
            const restored = window.energySystem.restore(1);
            if (restored > 0) {
                EventBus.emit('ui:showToast', '+1 energy regenerated! ⚡');
            }
        }
        
        this.lastRegenTime = Date.now();
        this.start(); // Restart the timer
    }

    updateDisplay() {
        const timerElement = DOM.get('#regen-timer');
        if (!timerElement) return;
        
        const energyWidget = DOM.get('.energy-widget');
        
        if (window.energySystem.currentEnergy >= CONFIG.MAX_ENERGY) {
            DOM.hide(timerElement);
            return;
        }
        
        DOM.show(timerElement);
        
        const timeSinceLastRegen = Date.now() - this.lastRegenTime;
        const timeUntilNext = Math.max(0, CONFIG.REGENERATION_INTERVAL - timeSinceLastRegen);
        
        const minutes = Math.floor(timeUntilNext / 60000);
        const seconds = Math.floor((timeUntilNext % 60000) / 1000);
        
        timerElement.textContent = `Next +1 in ${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (this.isPaused) {
            DOM.addClass(energyWidget, 'paused');
        } else {
            DOM.removeClass(energyWidget, 'paused');
        }
    }
}

// Break Manager
class BreakManager {
    constructor() {
        this.timer = null;
        this.startTime = null;
        this.duration = null;
        this.isOnBreak = false;
    }

    startBreak(duration) {
        this.isOnBreak = true;
        this.startTime = Date.now();
        this.duration = duration;
        
        EventBus.emit('break:started', { duration });
        
        this.timer = setInterval(() => {
            this.updateBreakTimer();
        }, 1000);
    }

    cancelBreak() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        
        this.isOnBreak = false;
        this.startTime = null;
        this.duration = null;
        
        EventBus.emit('break:cancelled');
    }

    completeBreak() {
        const energyToRestore = this.duration === 5 ? 4 : CONFIG.MAX_ENERGY;
        const restored = window.energySystem.restore(energyToRestore);
        
        this.cancelBreak();
        EventBus.emit('break:completed', { restored });
        
        return restored;
    }

    updateBreakTimer() {
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const remaining = Math.max(0, this.duration * 60 - elapsed);
        
        if (remaining === 0) {
            this.completeBreak();
            return;
        }
        
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        
        EventBus.emit('break:timerUpdate', { minutes, seconds, remaining });
    }
}