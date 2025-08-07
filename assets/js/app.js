// Main Application Entry Point
import { CONFIG } from './config.js';
import { ready } from './utils/dom.js';
import { EventBus } from './utils/events.js';
import { TaskManager } from './modules/tasks.js';
import { UIManager } from './modules/ui.js';
import { EnergySystem } from './modules/energy.js';
import { StatsManager, AchievementManager } from './modules/stats.js';
import { workingZoneManager } from './modules/working-zone.js';
import { websocketManager } from './modules/websocket.js';

// Global app instance
class ConfettiTodoApp {
    constructor() {
        this.modules = {
            tasks: new TaskManager(),
            ui: new UIManager(),
            energy: new EnergySystem(),
            stats: new StatsManager(),
            achievements: new AchievementManager(),
            workingZone: workingZoneManager,
            websocket: websocketManager
        };
        
        // Make some modules globally accessible for HTML event handlers
        window.taskManager = this.modules.tasks;
        window.uiManager = this.modules.ui;
        window.energySystem = this.modules.energy;
        window.statsManager = this.modules.stats;
        window.workingZone = this.modules.workingZone;
    }

    async init() {
        
        try {
            // Initialize modules in order
            this.modules.ui.init();
            this.modules.energy.init();
            this.modules.stats.init();
            this.modules.workingZone.init(this.modules.energy);
            this.modules.websocket.init();
            
            // Initialize tasks last as it triggers initial render
            await this.modules.tasks.init();
            
            // Setup global event handlers
            this.setupEventHandlers();
            
            // Check for achievements on startup
            this.modules.achievements.checkAchievements(this.modules.stats.stats);
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.modules.ui.showToast('Failed to initialize app', 'error');
        }
    }

    setupEventHandlers() {
        // Task events
        EventBus.on('task:create', ({ data }) => {
            const task = this.modules.tasks.createTask(data);
            if (task) {
                this.modules.ui.showToast('Task created!', 'success');
            }
        });

        EventBus.on('task:update', ({ taskId, data }) => {
            const task = this.modules.tasks.updateTask(taskId, data);
            if (task) {
                this.modules.ui.showToast('Task updated!', 'success');
            }
        });

        EventBus.on('task:delete', ({ taskId }) => {
            if (this.modules.tasks.deleteTask(taskId)) {
                this.modules.ui.showToast('Task deleted!', 'info');
            }
        });

        EventBus.on('task:toggle', ({ taskId }) => {
            const task = this.modules.tasks.toggleTaskComplete(taskId);
            if (task) {
                if (task.is_completed) {
                    this.handleTaskCompletion(task);
                }
            }
        });

        EventBus.on('task:complete', ({ taskId }) => {
            const task = this.modules.tasks.findTaskById(taskId);
            if (task && !task.is_completed) {
                task.is_completed = true;
                this.modules.tasks.updateTask(taskId, task);
                this.handleTaskCompletion(task);
            }
        });

        EventBus.on('task:start', ({ taskId }) => {
            const task = this.modules.tasks.findTaskById(taskId);
            if (task) {
                this.modules.workingZone.startTask(task);
            }
        });

        EventBus.on('task:edit', ({ taskId }) => {
            const task = this.modules.tasks.findTaskById(taskId);
            if (task) {
                this.modules.ui.showModal('editTask', { 
                    mode: 'edit', 
                    taskId,
                    task 
                });
            }
        });

        EventBus.on('task:toggleNorthStar', ({ taskId }) => {
            const task = this.modules.tasks.findTaskById(taskId);
            if (task) {
                // Clear previous north star
                this.modules.tasks.allTasks.forEach(t => {
                    if (t.is_north_star) {
                        t.is_north_star = false;
                        this.modules.tasks.updateTask(t.id, t);
                    }
                });
                
                // Set new north star
                task.is_north_star = true;
                this.modules.tasks.updateTask(taskId, task);
                EventBus.emit('northstar:set', { taskId });
                
                this.modules.ui.showToast('North Star task set! ⭐', 'success');
            }
        });

        EventBus.on('task:getById', ({ taskId }) => {
            return this.modules.tasks.findTaskById(taskId);
        });

        EventBus.on('task:isExpanded', ({ taskId }) => {
            return this.modules.tasks.expandedTasks.has(taskId);
        });

        EventBus.on('tasks:reload', async () => {
            await this.modules.tasks.loadTasks();
        });

        // Subtask events
        EventBus.on('subtask:add', ({ taskId, title }) => {
            const subtask = this.modules.tasks.addSubtask(taskId, title);
            if (subtask) {
                this.modules.ui.showToast('Subtask added!', 'success');
            }
        });

        EventBus.on('subtask:toggle', ({ taskId, subtaskId }) => {
            const subtask = this.modules.tasks.toggleSubtask(taskId, subtaskId);
            if (subtask && subtask.is_completed) {
                // Check if all subtasks are completed
                const task = this.modules.tasks.findTaskById(taskId);
                if (task && task.subtasks.every(st => st.is_completed)) {
                    this.modules.ui.showToast('All subtasks completed! 🎯', 'success');
                }
            }
        });

        // Working zone events
        EventBus.on('workingZone:switch', ({ fromTaskId, toTaskId }) => {
            const newTask = this.modules.tasks.findTaskById(toTaskId);
            if (newTask) {
                this.modules.workingZone.switchTask(newTask);
            }
        });

        EventBus.on('task:moveToWorkingZone', ({ task }) => {
            // Visual feedback for task moving to working zone
            this.modules.tasks.processAndRender();
        });

        EventBus.on('task:moveFromWorkingZone', ({ task, completed }) => {
            // Visual feedback for task leaving working zone
            this.modules.tasks.processAndRender();
        });

        // Break events
        EventBus.on('break:start', ({ duration }) => {
            this.modules.energy.breakManager.startBreak(duration);
        });

        EventBus.on('break:cancel', () => {
            this.modules.energy.breakManager.cancelBreak();
        });

        EventBus.on('break:complete', () => {
            const restored = this.modules.energy.breakManager.completeBreak();
            if (restored > 0) {
                this.modules.stats.awardBonusXP(restored * 2, 'Break completion bonus');
            }
        });

        EventBus.on('break:timerUpdate', ({ minutes, seconds }) => {
            // Update break timer display if modal is open
            const timerDisplay = document.querySelector('.break-timer .timer-display');
            if (timerDisplay) {
                timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        });

        // Energy events
        EventBus.on('energy:breakSuggested', () => {
            this.modules.ui.showModal('breakSuggestion');
        });

        // Achievement events
        EventBus.on('achievement:unlocked', (achievement) => {
            this.modules.ui.showToast(
                `🏆 Achievement Unlocked: ${achievement.name}!`,
                'success',
                5000
            );
            
            // Award bonus XP
            this.modules.stats.addXP(50, 'achievement');
        });

        // Quick win
        EventBus.on('quickwin:request', async () => {
            try {
                const response = await fetch(`${CONFIG.API_URL}/api/quick-win`);
                if (response.ok) {
                    const suggestion = await response.json();
                    this.modules.ui.showModal('quickWin', { suggestion });
                }
            } catch (error) {
                console.error('Error getting quick win:', error);
                this.modules.ui.showToast('Failed to get suggestion', 'error');
            }
        });

        // Drag and drop
        this.setupDragAndDrop();
        
        // Keyboard shortcuts (already handled in UI module)
        
        // Window events
        window.addEventListener('beforeunload', () => {
            // Save any pending changes
            this.modules.tasks.saveUIState();
            this.modules.workingZone.saveState();
        });
    }

    handleTaskCompletion(task) {
        // Award XP and update stats
        const result = this.modules.stats.completeTask(task);
        
        // Check achievements
        const hour = new Date().getHours();
        const newAchievements = this.modules.achievements.checkAchievements(
            this.modules.stats.stats,
            { hour }
        );
        
        // Update task
        EventBus.emit('task:completed', { task });
        
        // Show completion effects
        this.modules.ui.showConfetti();
        
        // Check if this was a milestone
        if (result.tasksCompleted % 10 === 0) {
            this.modules.ui.showToast(
                `Milestone: ${result.tasksCompleted} tasks completed! 🎊`,
                'success',
                5000
            );
        }
    }

    setupDragAndDrop() {
        // Setup drop zones
        const dropZones = document.querySelectorAll('.task-list, #working-zone-drop');
        
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                zone.classList.add('drag-over');
            });
            
            zone.addEventListener('dragleave', () => {
                zone.classList.remove('drag-over');
            });
            
            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                
                const taskId = e.dataTransfer.getData('text/plain');
                const targetSection = zone.dataset.section;
                
                if (targetSection === 'working-zone') {
                    // Start task in working zone
                    const task = this.modules.tasks.findTaskById(taskId);
                    if (task) {
                        this.modules.workingZone.startTask(task);
                    }
                } else if (targetSection) {
                    // Move to different section
                    this.modules.tasks.moveTask(taskId, targetSection);
                }
            });
        });
    }
}

// Initialize app when DOM is ready
ready(() => {
    const app = new ConfettiTodoApp();
    app.init();
    
    // Make app instance globally available for debugging
    window.confettiTodoApp = app;
});