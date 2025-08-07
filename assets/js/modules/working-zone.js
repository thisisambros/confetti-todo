// Working Zone Module - Handles active task management and time tracking
import { CONFIG } from '../config.js';
import { EventBus } from '../utils/events.js';
import { DOM } from '../utils/dom.js';
import { StorageManager } from '../utils/storage.js';

export class WorkingZoneManager {
    constructor() {
        this.activeTask = null;
        this.startTime = null;
        this.elapsedTime = 0;
        this.timer = null;
        this.energySystem = null; // Will be injected
        this.isPaused = false;
        this.pauseStartTime = null;
        this.totalPausedTime = 0;
    }

    init(energySystem) {
        this.energySystem = energySystem;
        this.loadState();
        this.bindEvents();
        this.updateDisplay();
    }

    loadState() {
        const state = StorageManager.get('workingZoneState');
        if (state && state.activeTaskId && state.startTime) {
            // Resume previous session
            this.activeTask = EventBus.emit('task:getById', { taskId: state.activeTaskId });
            if (this.activeTask) {
                this.startTime = new Date(state.startTime);
                this.elapsedTime = state.elapsedTime || 0;
                this.totalPausedTime = state.totalPausedTime || 0;
                this.isPaused = state.isPaused || false;
                
                if (!this.isPaused) {
                    this.startTimer();
                }
            }
        }
    }

    saveState() {
        if (this.activeTask) {
            StorageManager.set('workingZoneState', {
                activeTaskId: this.activeTask.id,
                startTime: this.startTime?.toISOString(),
                elapsedTime: this.elapsedTime,
                totalPausedTime: this.totalPausedTime,
                isPaused: this.isPaused
            });
        } else {
            StorageManager.remove('workingZoneState');
        }
    }

    startTask(task) {
        if (this.activeTask) {
            // Ask to switch task
            EventBus.emit('ui:showModal', 'switchTask', {
                currentTask: this.activeTask,
                newTask: task
            });
            return false;
        }

        // Check energy
        const energyCost = this.calculateEnergyCost(task);
        const hasEnergy = this.energySystem?.currentEnergy >= energyCost;

        if (!hasEnergy) {
            EventBus.emit('ui:showToast', 'Not enough energy! Take a break first.', 'warning');
            EventBus.emit('ui:showModal', 'breakSuggestion');
            return false;
        }

        // Consume energy
        if (this.energySystem) {
            this.energySystem.consume(energyCost);
        }

        // Set active task
        this.activeTask = task;
        this.startTime = new Date();
        this.elapsedTime = 0;
        this.totalPausedTime = 0;
        this.isPaused = false;

        // Move task to working zone section
        EventBus.emit('task:moveToWorkingZone', { task });

        // Update UI
        this.updateDisplay();
        this.startTimer();
        this.saveState();

        EventBus.emit('workingZone:taskStarted', { task, energyCost });
        return true;
    }

    stopTask(completed = false) {
        if (!this.activeTask) return;

        this.stopTimer();

        const totalTime = this.getTotalElapsedTime();
        const task = this.activeTask;

        // Clear active task
        this.activeTask = null;
        this.startTime = null;
        this.elapsedTime = 0;
        this.totalPausedTime = 0;
        this.isPaused = false;

        // Move task back to its section
        EventBus.emit('task:moveFromWorkingZone', { task, completed });

        // Update UI
        this.updateDisplay();
        this.saveState();

        EventBus.emit('workingZone:taskStopped', { 
            task, 
            completed, 
            totalTime,
            actualWorkTime: totalTime - this.totalPausedTime
        });

        if (completed) {
            EventBus.emit('task:complete', { taskId: task.id });
        }
    }

    pauseTask() {
        if (!this.activeTask || this.isPaused) return;

        this.isPaused = true;
        this.pauseStartTime = new Date();
        this.stopTimer();
        
        // Pause energy regeneration
        if (this.energySystem?.regenerationManager) {
            this.energySystem.regenerationManager.pause();
        }

        this.updateDisplay();
        this.saveState();

        EventBus.emit('workingZone:taskPaused', { task: this.activeTask });
    }

    resumeTask() {
        if (!this.activeTask || !this.isPaused) return;

        // Calculate paused duration
        if (this.pauseStartTime) {
            const pausedDuration = Date.now() - this.pauseStartTime.getTime();
            this.totalPausedTime += pausedDuration;
        }

        this.isPaused = false;
        this.pauseStartTime = null;
        
        // Resume energy regeneration
        if (this.energySystem?.regenerationManager) {
            this.energySystem.regenerationManager.start();
        }

        this.startTimer();
        this.updateDisplay();
        this.saveState();

        EventBus.emit('workingZone:taskResumed', { task: this.activeTask });
    }

    switchTask(newTask) {
        if (!this.activeTask) {
            this.startTask(newTask);
            return;
        }

        // Stop current task without completing
        const currentTask = this.activeTask;
        this.stopTask(false);

        // Start new task
        this.startTask(newTask);

        EventBus.emit('workingZone:taskSwitched', { 
            from: currentTask, 
            to: newTask 
        });
    }

    startTimer() {
        if (this.timer) return;

        const startElapsed = this.elapsedTime;
        const timerStart = Date.now();

        this.timer = setInterval(() => {
            if (!this.isPaused) {
                this.elapsedTime = startElapsed + (Date.now() - timerStart);
                this.updateTimerDisplay();
            }
        }, 1000);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    getTotalElapsedTime() {
        if (!this.startTime) return 0;

        if (this.isPaused && this.pauseStartTime) {
            // Currently paused - don't count current pause time
            return this.elapsedTime;
        }

        return this.elapsedTime;
    }

    updateDisplay() {
        const container = DOM.get('#working-zone-container');
        if (!container) return;

        if (!this.activeTask) {
            container.innerHTML = `
                <div class="working-zone-empty">
                    <p>No active task</p>
                    <small>Start a task to begin working</small>
                </div>
            `;
            return;
        }

        const actualWorkTime = this.elapsedTime - this.totalPausedTime;
        
        container.innerHTML = `
            <div class="working-zone-active">
                <div class="task-info">
                    <h3>${this.activeTask.title}</h3>
                    <div class="task-meta">
                        <span class="effort">${this.activeTask.effort || '30m'}</span>
                        <span class="friction">${CONFIG.FRICTION_EMOJI[this.activeTask.friction || 1]}</span>
                        ${this.activeTask.category ? `<span class="category ${this.activeTask.category}">${this.activeTask.category}</span>` : ''}
                    </div>
                </div>
                <div class="timer-section">
                    <div class="timer-display ${this.isPaused ? 'paused' : ''}">
                        <span id="working-zone-timer">00:00</span>
                        ${this.isPaused ? '<span class="pause-indicator">PAUSED</span>' : ''}
                    </div>
                    <div class="timer-controls">
                        ${this.isPaused ? 
                            `<button class="btn btn-primary resume-btn" onclick="window.workingZone.resumeTask()">
                                Resume
                            </button>` :
                            `<button class="btn btn-secondary pause-btn" onclick="window.workingZone.pauseTask()">
                                Pause
                            </button>`
                        }
                        <button class="btn btn-success complete-btn" onclick="window.workingZone.completeTask()">
                            Complete
                        </button>
                        <button class="btn btn-danger stop-btn" onclick="window.workingZone.stopTask()">
                            Stop
                        </button>
                    </div>
                </div>
                ${this.renderSubtasks()}
                ${this.renderEnergyInfo()}
            </div>
        `;

        this.updateTimerDisplay();
    }

    updateTimerDisplay() {
        const timerEl = DOM.get('#working-zone-timer');
        if (!timerEl) return;

        const actualWorkTime = this.elapsedTime - this.totalPausedTime;
        const minutes = Math.floor(actualWorkTime / 60000);
        const seconds = Math.floor((actualWorkTime % 60000) / 1000);

        timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // Check if approaching effort estimate
        const effortMinutes = this.getEffortMinutes();
        if (effortMinutes > 0 && minutes >= effortMinutes * 0.9 && minutes < effortMinutes) {
            DOM.addClass(timerEl, 'approaching-estimate');
        } else if (minutes >= effortMinutes) {
            DOM.addClass(timerEl, 'exceeded-estimate');
        }
    }

    renderSubtasks() {
        if (!this.activeTask.subtasks || this.activeTask.subtasks.length === 0) {
            return '';
        }

        const completed = this.activeTask.subtasks.filter(st => st.is_completed).length;
        const total = this.activeTask.subtasks.length;

        return `
            <div class="subtasks-progress">
                <div class="progress-header">
                    <span>Subtasks: ${completed}/${total}</span>
                    <button class="btn btn-sm expand-subtasks">
                        ${DOM.hasClass(DOM.get('#working-zone-subtasks'), 'expanded') ? '▼' : '▶'}
                    </button>
                </div>
                <div id="working-zone-subtasks" class="subtasks-list">
                    ${this.activeTask.subtasks.map(subtask => `
                        <div class="subtask-item ${subtask.is_completed ? 'completed' : ''}">
                            <input type="checkbox" 
                                   class="subtask-checkbox" 
                                   ${subtask.is_completed ? 'checked' : ''}
                                   data-subtask-id="${subtask.id}">
                            <span class="subtask-title">${subtask.title}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderEnergyInfo() {
        if (!this.energySystem) return '';

        const energyCost = this.calculateEnergyCost(this.activeTask);
        const currentEnergy = this.energySystem.currentEnergy;
        
        return `
            <div class="energy-info">
                <span class="energy-consumed">Energy consumed: ⚡${energyCost}</span>
                <span class="energy-remaining">Remaining: ⚡${currentEnergy}/${CONFIG.MAX_ENERGY}</span>
            </div>
        `;
    }

    getEffortMinutes() {
        const effortMap = {
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240
        };
        return effortMap[this.activeTask?.effort] || 30;
    }

    calculateEnergyCost(task) {
        const effortValue = CONFIG.EFFORT_VALUES[task.effort] || 6;
        return Math.ceil((effortValue / 3) * (task.friction || 1));
    }

    completeTask() {
        if (!this.activeTask) return;
        
        // Check if all subtasks are completed
        if (this.activeTask.subtasks && this.activeTask.subtasks.length > 0) {
            const incompleteSubtasks = this.activeTask.subtasks.filter(st => !st.is_completed);
            if (incompleteSubtasks.length > 0) {
                const proceed = confirm(`${incompleteSubtasks.length} subtasks are incomplete. Complete task anyway?`);
                if (!proceed) return;
            }
        }

        this.stopTask(true);
    }

    bindEvents() {
        // Handle subtask toggles in working zone
        document.addEventListener('change', (e) => {
            if (e.target.matches('#working-zone-container .subtask-checkbox')) {
                const subtaskId = e.target.dataset.subtaskId;
                EventBus.emit('subtask:toggle', { 
                    taskId: this.activeTask.id, 
                    subtaskId 
                });
            }
        });

        // Handle expand/collapse subtasks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.expand-subtasks')) {
                const subtasksList = DOM.get('#working-zone-subtasks');
                if (subtasksList) {
                    DOM.toggleClass(subtasksList, 'expanded');
                    e.target.textContent = DOM.hasClass(subtasksList, 'expanded') ? '▼' : '▶';
                }
            }
        });

        // Listen for task updates
        EventBus.on('task:updated', ({ task }) => {
            if (this.activeTask && task.id === this.activeTask.id) {
                this.activeTask = task;
                this.updateDisplay();
            }
        });

        // Listen for external task deletion
        EventBus.on('task:deleted', ({ task }) => {
            if (this.activeTask && task.id === this.activeTask.id) {
                this.stopTask(false);
                EventBus.emit('ui:showToast', 'Active task was deleted', 'warning');
            }
        });

        // Listen for energy depletion
        EventBus.on('energy:depleted', () => {
            if (this.activeTask) {
                this.pauseTask();
                EventBus.emit('ui:showModal', 'breakSuggestion', { forced: true });
            }
        });
    }
}

// Export singleton instance
export const workingZoneManager = new WorkingZoneManager();