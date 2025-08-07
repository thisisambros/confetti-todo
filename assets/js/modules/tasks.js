// Task Management Module
import { CONFIG } from '../config.js';
import { DOM } from '../utils/dom.js';
import { EventBus } from '../utils/events.js';
import { StorageManager } from '../utils/storage.js';

export class TaskManager {
    constructor() {
        this.currentData = { today: [], ideas: [], backlog: [] };
        this.allTasks = [];
        this.expandedTasks = new Set();
        this.northStarTask = null;
        this.currentFilter = 'all';
        this.currentSort = 'due';
        this.searchTerm = '';
        this.activeCategories = new Set();
    }

    init() {
        this.loadTasks();
        this.loadUIState();
        this.bindEvents();
    }

    async loadTasks() {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/todos`);
            const data = await response.json();
            this.currentData = data;
            this.updateAllTasks();
            this.processAndRender();
            EventBus.emit('tasks:loaded', data);
        } catch (error) {
            console.error('Error loading tasks:', error);
            EventBus.emit('tasks:loadError', error);
        }
    }

    async saveTasks() {
        try {
            await fetch(`${CONFIG.API_URL}/api/todos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.currentData)
            });
            EventBus.emit('tasks:saved', this.currentData);
        } catch (error) {
            console.error('Error saving tasks:', error);
            EventBus.emit('tasks:saveError', error);
        }
    }

    loadUIState() {
        const uiState = StorageManager.get('confettiTodoUI', {});
        
        if (uiState.filter) this.currentFilter = uiState.filter;
        if (uiState.sort) this.currentSort = uiState.sort;
        if (uiState.expandedTasks) this.expandedTasks = new Set(uiState.expandedTasks);
        if (uiState.northStarTaskId) {
            this.northStarTask = this.findTaskById(uiState.northStarTaskId);
        }
        
        // Restore collapsed sections
        if (uiState.collapsedSections) {
            uiState.collapsedSections.forEach(sectionId => {
                const section = DOM.get(`#${sectionId}`);
                if (section) {
                    DOM.addClass(section, 'collapsed');
                }
            });
        }
    }

    saveUIState() {
        const uiState = {
            filter: this.currentFilter,
            sort: this.currentSort,
            expandedTasks: Array.from(this.expandedTasks),
            northStarTaskId: this.northStarTask?.id,
            collapsedSections: Array.from(DOM.getAll('.task-section.collapsed'))
                .map(section => section.id)
        };
        
        StorageManager.set('confettiTodoUI', uiState);
    }

    updateAllTasks() {
        this.allTasks = [
            ...this.currentData.today.map(t => ({ ...t, section: 'today' })),
            ...this.currentData.ideas.map(t => ({ ...t, section: 'ideas' })),
            ...this.currentData.backlog.map(t => ({ ...t, section: 'backlog' }))
        ];
    }

    findTaskById(taskId) {
        return this.allTasks.find(t => t.id === taskId);
    }

    createTask(taskData) {
        const task = {
            id: Date.now().toString(),
            title: taskData.title,
            is_completed: false,
            category: taskData.category || 'other',
            effort: taskData.effort || '30m',
            friction: taskData.friction || 1,
            due_date: taskData.due_date || null,
            subtasks: [],
            created_at: new Date().toISOString()
        };

        // Add to appropriate section
        const section = taskData.is_idea ? 'ideas' : 'today';
        this.currentData[section].push(task);
        
        this.updateAllTasks();
        this.saveTasks();
        this.processAndRender();
        
        EventBus.emit('task:created', task);
        return task;
    }

    updateTask(taskId, updates) {
        const task = this.findTaskById(taskId);
        if (!task) return null;

        Object.assign(task, updates);
        
        // Find and update in the correct section
        for (const section of ['today', 'ideas', 'backlog']) {
            const index = this.currentData[section].findIndex(t => t.id === taskId);
            if (index !== -1) {
                this.currentData[section][index] = { ...task };
                break;
            }
        }

        this.updateAllTasks();
        this.saveTasks();
        this.processAndRender();
        
        EventBus.emit('task:updated', task);
        return task;
    }

    deleteTask(taskId) {
        const task = this.findTaskById(taskId);
        if (!task) return false;

        // Remove from the correct section
        for (const section of ['today', 'ideas', 'backlog']) {
            const index = this.currentData[section].findIndex(t => t.id === taskId);
            if (index !== -1) {
                this.currentData[section].splice(index, 1);
                break;
            }
        }

        // Clean up UI state
        this.expandedTasks.delete(taskId);
        if (this.northStarTask?.id === taskId) {
            this.northStarTask = null;
        }

        this.updateAllTasks();
        this.saveTasks();
        this.processAndRender();
        
        EventBus.emit('task:deleted', task);
        return true;
    }

    toggleTaskComplete(taskId) {
        const task = this.findTaskById(taskId);
        if (!task) return null;

        task.is_completed = !task.is_completed;
        if (task.is_completed) {
            task.completed_at = new Date().toISOString();
        } else {
            delete task.completed_at;
        }

        return this.updateTask(taskId, task);
    }

    moveTask(taskId, toSection) {
        const task = this.findTaskById(taskId);
        if (!task) return false;

        // Remove from current section
        for (const section of ['today', 'ideas', 'backlog']) {
            const index = this.currentData[section].findIndex(t => t.id === taskId);
            if (index !== -1) {
                this.currentData[section].splice(index, 1);
                break;
            }
        }

        // Add to new section
        this.currentData[toSection].push(task);
        task.section = toSection;

        this.updateAllTasks();
        this.saveTasks();
        this.processAndRender();
        
        EventBus.emit('task:moved', { task, toSection });
        return true;
    }

    // Subtask management
    addSubtask(taskId, subtaskTitle) {
        const task = this.findTaskById(taskId);
        if (!task) return null;

        const subtask = {
            id: Date.now().toString(),
            title: subtaskTitle,
            is_completed: false
        };

        if (!task.subtasks) task.subtasks = [];
        task.subtasks.push(subtask);

        this.updateTask(taskId, task);
        EventBus.emit('subtask:added', { task, subtask });
        return subtask;
    }

    toggleSubtask(taskId, subtaskId) {
        const task = this.findTaskById(taskId);
        if (!task || !task.subtasks) return null;

        const subtask = task.subtasks.find(st => st.id === subtaskId);
        if (!subtask) return null;

        subtask.is_completed = !subtask.is_completed;
        if (subtask.is_completed) {
            subtask.completed_at = new Date().toISOString();
        } else {
            delete subtask.completed_at;
        }

        this.updateTask(taskId, task);
        EventBus.emit('subtask:toggled', { task, subtask });
        return subtask;
    }

    // Filtering and sorting
    getFilteredTasks() {
        let tasks = [...this.allTasks];

        // Apply search filter
        if (this.searchTerm) {
            const searchLower = this.searchTerm.toLowerCase();
            tasks = tasks.filter(task => 
                task.title.toLowerCase().includes(searchLower) ||
                task.subtasks?.some(st => st.title.toLowerCase().includes(searchLower))
            );
        }

        // Apply status filter
        switch (this.currentFilter) {
            case 'active':
                tasks = tasks.filter(t => !t.is_completed);
                break;
            case 'completed':
                tasks = tasks.filter(t => t.is_completed);
                break;
            case 'today':
                tasks = tasks.filter(t => t.section === 'today');
                break;
            case 'has-subtasks':
                tasks = tasks.filter(t => t.subtasks && t.subtasks.length > 0);
                break;
            case 'overdue':
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                tasks = tasks.filter(t => 
                    t.due_date && new Date(t.due_date) < today && !t.is_completed
                );
                break;
        }

        // Apply category filter
        if (this.activeCategories.size > 0) {
            tasks = tasks.filter(t => this.activeCategories.has(t.category));
        }

        // Apply sorting
        tasks = this.sortTasks(tasks, this.currentSort);

        return tasks;
    }

    sortTasks(tasks, sortBy) {
        const sortFunctions = {
            due: (a, b) => {
                if (!a.due_date && !b.due_date) return 0;
                if (!a.due_date) return 1;
                if (!b.due_date) return -1;
                return new Date(a.due_date) - new Date(b.due_date);
            },
            effort: (a, b) => {
                const effortOrder = { '5m': 0, '15m': 1, '30m': 2, '1h': 3, '4h': 4 };
                return (effortOrder[a.effort] || 2) - (effortOrder[b.effort] || 2);
            },
            friction: (a, b) => (a.friction || 1) - (b.friction || 1),
            created: (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0),
            alpha: (a, b) => a.title.localeCompare(b.title),
            category: (a, b) => (a.category || 'other').localeCompare(b.category || 'other'),
            completed: (a, b) => {
                if (a.is_completed === b.is_completed) return 0;
                return a.is_completed ? 1 : -1;
            }
        };

        return [...tasks].sort(sortFunctions[sortBy] || sortFunctions.due);
    }

    processAndRender() {
        const tasks = this.getFilteredTasks();
        EventBus.emit('tasks:render', { tasks, filter: this.currentFilter });
        this.saveUIState();
    }

    bindEvents() {
        // Listen for external events
        EventBus.on('filter:changed', ({ filter }) => {
            this.currentFilter = filter;
            this.processAndRender();
        });

        EventBus.on('sort:changed', ({ sort }) => {
            this.currentSort = sort;
            this.processAndRender();
        });

        EventBus.on('search:changed', ({ term }) => {
            this.searchTerm = term;
            this.processAndRender();
        });

        EventBus.on('category:toggled', ({ category }) => {
            if (this.activeCategories.has(category)) {
                this.activeCategories.delete(category);
            } else {
                this.activeCategories.add(category);
            }
            this.processAndRender();
        });

        EventBus.on('task:expanded', ({ taskId }) => {
            this.expandedTasks.add(taskId);
            this.saveUIState();
        });

        EventBus.on('task:collapsed', ({ taskId }) => {
            this.expandedTasks.delete(taskId);
            this.saveUIState();
        });

        EventBus.on('northstar:set', ({ taskId }) => {
            this.northStarTask = this.findTaskById(taskId);
            this.saveUIState();
        });
    }
}