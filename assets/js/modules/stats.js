// Stats Module - Handles XP, levels, and gamification
import { CONFIG } from '../config.js';
import { StatsStorage, StorageManager } from '../utils/storage.js';
import { EventBus } from '../utils/events.js';

export class StatsManager {
    constructor() {
        this.stats = null;
        this.xpForNextLevel = 100; // Base XP for level 2
        this.xpMultiplier = 1.5; // Each level requires 1.5x more XP
    }

    init() {
        this.loadStats();
        this.bindEvents();
        this.updateDisplay();
    }

    loadStats() {
        this.stats = StatsStorage.getStats();
        this.checkDailyStreak();
    }

    saveStats() {
        StatsStorage.saveStats(this.stats);
        EventBus.emit('stats:updated', this.stats);
    }

    checkDailyStreak() {
        const today = new Date().toDateString();
        const lastDate = this.stats.lastCompletionDate ? new Date(this.stats.lastCompletionDate).toDateString() : null;
        
        if (lastDate !== today) {
            // Check if streak should be broken
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            
            if (lastDate !== yesterday.toDateString() && this.stats.currentStreak > 0) {
                // Streak broken
                this.stats.currentStreak = 0;
                EventBus.emit('streak:broken', { previousStreak: this.stats.currentStreak });
            }
        }
    }

    calculateTaskXP(task) {
        if (!task || task.is_idea) return 0;
        
        // Base XP from effort
        const effortXP = CONFIG.EFFORT_VALUES[task.effort] || 6;
        
        // Apply friction multiplier
        const frictionMultiplier = task.friction || 1;
        let xp = effortXP * frictionMultiplier;
        
        // Bonus for completing all subtasks
        if (task.subtasks && task.subtasks.length > 0) {
            const allSubtasksComplete = task.subtasks.every(st => st.is_completed);
            if (allSubtasksComplete) {
                xp *= 1.5; // 50% bonus
            }
        }
        
        // Bonus for completing before due date
        if (task.due_date) {
            const dueDate = new Date(task.due_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (dueDate >= today) {
                xp *= 1.1; // 10% bonus for on-time completion
            }
        }
        
        return Math.round(xp);
    }

    addXP(amount, category = 'other') {
        this.stats.totalXP += amount;
        
        // Update daily XP
        StatsStorage.updateDailyXP(amount);
        
        // Update category XP
        StatsStorage.updateCategoryXP(category, amount);
        
        // Check for level up
        const oldLevel = this.stats.level;
        const newLevel = this.calculateLevel(this.stats.totalXP);
        
        if (newLevel > oldLevel) {
            this.stats.level = newLevel;
            EventBus.emit('level:up', { 
                oldLevel, 
                newLevel, 
                totalXP: this.stats.totalXP 
            });
        }
        
        this.saveStats();
        this.updateDisplay();
        
        return amount;
    }

    completeTask(task) {
        const xp = this.calculateTaskXP(task);
        
        if (xp > 0) {
            this.addXP(xp, task.category || 'other');
        }
        
        // Update completion count
        this.stats.tasksCompleted++;
        
        // Update streak
        const today = new Date().toDateString();
        const lastDate = this.stats.lastCompletionDate ? new Date(this.stats.lastCompletionDate).toDateString() : null;
        
        if (lastDate !== today) {
            // First task of the day
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            
            if (lastDate === yesterday.toDateString() || this.stats.currentStreak === 0) {
                // Continue or start streak
                this.stats.currentStreak++;
                
                if (this.stats.currentStreak > this.stats.longestStreak) {
                    this.stats.longestStreak = this.stats.currentStreak;
                }
                
                EventBus.emit('streak:continued', { 
                    currentStreak: this.stats.currentStreak,
                    isNewRecord: this.stats.currentStreak === this.stats.longestStreak
                });
            }
        }
        
        this.stats.lastCompletionDate = new Date().toISOString();
        this.saveStats();
        
        return { xp, tasksCompleted: this.stats.tasksCompleted };
    }

    calculateLevel(totalXP) {
        let level = 1;
        let xpForCurrentLevel = 0;
        let xpForNextLevel = this.xpForNextLevel;
        
        while (totalXP >= xpForNextLevel) {
            level++;
            xpForCurrentLevel = xpForNextLevel;
            xpForNextLevel = Math.floor(xpForNextLevel * this.xpMultiplier);
        }
        
        return level;
    }

    getProgressToNextLevel() {
        const level = this.calculateLevel(this.stats.totalXP);
        
        // Calculate XP boundaries for current level
        let xpForCurrentLevel = 0;
        let xpForNextLevel = this.xpForNextLevel;
        
        for (let i = 1; i < level; i++) {
            xpForCurrentLevel = xpForNextLevel;
            xpForNextLevel = Math.floor(xpForNextLevel * this.xpMultiplier);
        }
        
        const xpInCurrentLevel = this.stats.totalXP - xpForCurrentLevel;
        const xpNeededForLevel = xpForNextLevel - xpForCurrentLevel;
        const progress = (xpInCurrentLevel / xpNeededForLevel) * 100;
        
        return {
            current: xpInCurrentLevel,
            needed: xpNeededForLevel,
            progress: Math.round(progress),
            nextLevel: level + 1
        };
    }

    getDailyStats() {
        const today = new Date().toISOString().split('T')[0];
        const todayXP = this.stats.dailyXP[today] || 0;
        
        // Get last 7 days of XP
        const weekData = [];
        const date = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const checkDate = new Date(date);
            checkDate.setDate(date.getDate() - i);
            const dateStr = checkDate.toISOString().split('T')[0];
            weekData.push({
                date: dateStr,
                xp: this.stats.dailyXP[dateStr] || 0,
                day: checkDate.toLocaleDateString('en', { weekday: 'short' })
            });
        }
        
        return {
            todayXP,
            weekData,
            averageXP: Math.round(weekData.reduce((sum, d) => sum + d.xp, 0) / 7)
        };
    }

    updateDisplay() {
        // Update level display
        const levelDisplay = document.querySelector('#level-display');
        if (levelDisplay) {
            levelDisplay.textContent = `Level ${this.stats.level}`;
        }
        
        // Update XP display
        const xpDisplay = document.querySelector('#xp-display');
        if (xpDisplay) {
            xpDisplay.textContent = `${this.stats.totalXP.toLocaleString()} XP`;
        }
        
        // Update progress bar
        const progressBar = document.querySelector('#xp-progress-bar');
        if (progressBar) {
            const progress = this.getProgressToNextLevel();
            progressBar.style.width = `${progress.progress}%`;
            
            const progressText = document.querySelector('#xp-progress-text');
            if (progressText) {
                progressText.textContent = `${progress.current} / ${progress.needed} XP`;
            }
        }
        
        // Update streak display
        const streakDisplay = document.querySelector('#streak-display');
        if (streakDisplay) {
            streakDisplay.textContent = `🔥 ${this.stats.currentStreak} day${this.stats.currentStreak !== 1 ? 's' : ''}`;
        }
    }

    bindEvents() {
        EventBus.on('task:completed', ({ task }) => {
            const result = this.completeTask(task);
            
            if (result.xp > 0) {
                EventBus.emit('ui:showToast', `+${result.xp} XP earned! 🎉`, 'success');
            }
        });

        EventBus.on('bonus:xp', ({ amount, reason }) => {
            this.addXP(amount);
            EventBus.emit('ui:showToast', `Bonus +${amount} XP: ${reason}! 🌟`, 'success');
        });

        EventBus.on('level:up', ({ newLevel }) => {
            EventBus.emit('ui:showToast', `Level ${newLevel} reached! 🎊`, 'success', 5000);
            
            // Could trigger special effects or unlock features here
            if (newLevel % 5 === 0) {
                // Milestone level
                EventBus.emit('milestone:reached', { level: newLevel });
            }
        });

        EventBus.on('streak:continued', ({ currentStreak, isNewRecord }) => {
            let message = `${currentStreak} day streak! 🔥`;
            if (isNewRecord) {
                message += ' New record!';
            }
            EventBus.emit('ui:showToast', message, 'success');
        });

        EventBus.on('streak:broken', ({ previousStreak }) => {
            if (previousStreak > 0) {
                EventBus.emit('ui:showToast', `Streak broken after ${previousStreak} days 😔`, 'warning');
            }
        });
    }

    // API integration
    async syncStats() {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/stats`);
            if (response.ok) {
                const serverStats = await response.json();
                
                // Merge with local stats (server has priority)
                this.stats = { ...this.stats, ...serverStats };
                this.saveStats();
                this.updateDisplay();
            }
        } catch (error) {
            console.error('Error syncing stats:', error);
        }
    }

    async awardBonusXP(amount, reason) {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/stats/bonus`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount, reason })
            });
            
            if (response.ok) {
                EventBus.emit('bonus:xp', { amount, reason });
            }
        } catch (error) {
            console.error('Error awarding bonus XP:', error);
        }
    }
}

// Achievements system
export class AchievementManager {
    constructor() {
        this.achievements = [
            { id: 'first_task', name: 'First Steps', description: 'Complete your first task', icon: '🎯' },
            { id: 'level_5', name: 'Rising Star', description: 'Reach level 5', icon: '⭐' },
            { id: 'level_10', name: 'Task Master', description: 'Reach level 10', icon: '🏆' },
            { id: 'streak_7', name: 'Week Warrior', description: '7-day completion streak', icon: '🔥' },
            { id: 'streak_30', name: 'Monthly Champion', description: '30-day completion streak', icon: '💪' },
            { id: 'tasks_10', name: 'Productive', description: 'Complete 10 tasks', icon: '✅' },
            { id: 'tasks_50', name: 'Super Productive', description: 'Complete 50 tasks', icon: '🚀' },
            { id: 'tasks_100', name: 'Productivity Master', description: 'Complete 100 tasks', icon: '👑' },
            { id: 'xp_1000', name: 'XP Hunter', description: 'Earn 1,000 total XP', icon: '💎' },
            { id: 'xp_5000', name: 'XP Collector', description: 'Earn 5,000 total XP', icon: '💰' },
            { id: 'perfect_day', name: 'Perfect Day', description: 'Complete all daily tasks', icon: '🌟' },
            { id: 'early_bird', name: 'Early Bird', description: 'Complete a task before 8 AM', icon: '🌅' },
            { id: 'night_owl', name: 'Night Owl', description: 'Complete a task after 10 PM', icon: '🦉' }
        ];
        
        this.unlockedAchievements = new Set(StorageManager.get('achievements', []));
    }

    checkAchievements(stats, context = {}) {
        const newAchievements = [];
        
        // Check each achievement
        if (!this.unlockedAchievements.has('first_task') && stats.tasksCompleted >= 1) {
            newAchievements.push(this.unlock('first_task'));
        }
        
        if (!this.unlockedAchievements.has('level_5') && stats.level >= 5) {
            newAchievements.push(this.unlock('level_5'));
        }
        
        if (!this.unlockedAchievements.has('level_10') && stats.level >= 10) {
            newAchievements.push(this.unlock('level_10'));
        }
        
        if (!this.unlockedAchievements.has('streak_7') && stats.currentStreak >= 7) {
            newAchievements.push(this.unlock('streak_7'));
        }
        
        if (!this.unlockedAchievements.has('streak_30') && stats.currentStreak >= 30) {
            newAchievements.push(this.unlock('streak_30'));
        }
        
        if (!this.unlockedAchievements.has('tasks_10') && stats.tasksCompleted >= 10) {
            newAchievements.push(this.unlock('tasks_10'));
        }
        
        if (!this.unlockedAchievements.has('tasks_50') && stats.tasksCompleted >= 50) {
            newAchievements.push(this.unlock('tasks_50'));
        }
        
        if (!this.unlockedAchievements.has('tasks_100') && stats.tasksCompleted >= 100) {
            newAchievements.push(this.unlock('tasks_100'));
        }
        
        if (!this.unlockedAchievements.has('xp_1000') && stats.totalXP >= 1000) {
            newAchievements.push(this.unlock('xp_1000'));
        }
        
        if (!this.unlockedAchievements.has('xp_5000') && stats.totalXP >= 5000) {
            newAchievements.push(this.unlock('xp_5000'));
        }
        
        // Context-based achievements
        if (context.hour !== undefined) {
            if (!this.unlockedAchievements.has('early_bird') && context.hour < 8) {
                newAchievements.push(this.unlock('early_bird'));
            }
            
            if (!this.unlockedAchievements.has('night_owl') && context.hour >= 22) {
                newAchievements.push(this.unlock('night_owl'));
            }
        }
        
        return newAchievements;
    }

    unlock(achievementId) {
        const achievement = this.achievements.find(a => a.id === achievementId);
        if (!achievement) return null;
        
        this.unlockedAchievements.add(achievementId);
        StorageManager.set('achievements', Array.from(this.unlockedAchievements));
        
        EventBus.emit('achievement:unlocked', achievement);
        
        return achievement;
    }

    getProgress() {
        return {
            unlocked: this.unlockedAchievements.size,
            total: this.achievements.length,
            percentage: Math.round((this.unlockedAchievements.size / this.achievements.length) * 100)
        };
    }

    getAll() {
        return this.achievements.map(achievement => ({
            ...achievement,
            unlocked: this.unlockedAchievements.has(achievement.id)
        }));
    }
}