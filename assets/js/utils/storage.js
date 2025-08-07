// Local Storage Management
export class StorageManager {
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return defaultValue;
        }
    }

    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error writing to localStorage:', e);
            return false;
        }
    }

    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    }

    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Error clearing localStorage:', e);
            return false;
        }
    }
}

// Stats-specific storage operations
export class StatsStorage {
    static KEY = 'confettiTodoStats';

    static getStats() {
        return StorageManager.get(this.KEY, {
            totalXP: 0,
            tasksCompleted: 0,
            currentStreak: 0,
            longestStreak: 0,
            lastCompletionDate: null,
            level: 1,
            dailyXP: {},
            categoryXP: {}
        });
    }

    static saveStats(stats) {
        return StorageManager.set(this.KEY, stats);
    }

    static updateDailyXP(xp) {
        const stats = this.getStats();
        const today = new Date().toISOString().split('T')[0];
        stats.dailyXP[today] = (stats.dailyXP[today] || 0) + xp;
        return this.saveStats(stats);
    }

    static updateCategoryXP(category, xp) {
        const stats = this.getStats();
        stats.categoryXP[category] = (stats.categoryXP[category] || 0) + xp;
        return this.saveStats(stats);
    }
}

// Energy-specific storage operations
export class EnergyStorage {
    static KEY = 'confettiTodoEnergy';

    static getEnergyState() {
        return StorageManager.get(this.KEY, {
            currentEnergy: 12,
            lastRegenTime: Date.now(),
            isPaused: false,
            lastUpdateDate: new Date().toDateString()
        });
    }

    static saveEnergyState(state) {
        return StorageManager.set(this.KEY, state);
    }

    static resetDailyEnergy() {
        const state = this.getEnergyState();
        state.currentEnergy = 12;
        state.lastRegenTime = Date.now();
        state.lastUpdateDate = new Date().toDateString();
        return this.saveEnergyState(state);
    }
}