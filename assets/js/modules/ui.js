// UI Module - Handles all rendering and UI interactions
import { CONFIG } from '../config.js';
import { DOM, ready } from '../utils/dom.js';
import { EventBus } from '../utils/events.js';
import { StorageManager } from '../utils/storage.js';

export class UIManager {
    constructor() {
        this.modals = {};
        this.activeModal = null;
        this.toastTimeout = null;
        this.confettiTimeout = null;
    }

    init() {
        this.cacheElements();
        this.bindGlobalEvents();
        this.initializeModals();
        this.restoreUIState();
        EventBus.emit('ui:initialized');
    }

    cacheElements() {
        this.elements = {
            taskLists: {
                today: DOM.get('#today-list'),
                ideas: DOM.get('#ideas-list'),
                backlog: DOM.get('#backlog-list')
            },
            searchBar: DOM.get('#search-bar'),
            searchMorphing: DOM.get('#search-morphing'),
            searchIcon: DOM.get('#search-icon-morph'),
            searchClear: DOM.get('#search-clear'),
            filterButtons: DOM.getAll('.filter-btn'),
            sortButtons: DOM.getAll('.sort-btn'),
            categoryFilters: DOM.getAll('.category-filter'),
            newTaskBtn: DOM.get('#new-task-btn'),
            newIdeaBtn: DOM.get('#new-idea-btn'),
            quickWinBtn: DOM.get('#quick-win-btn'),
            statsDisplay: DOM.get('#stats-display'),
            energyWidget: DOM.get('.energy-widget'),
            workingZone: DOM.get('#working-zone'),
            northStarContainer: DOM.get('#north-star-container')
        };
    }

    bindGlobalEvents() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.matches('input, textarea')) return;
            
            switch(e.key) {
                case 'n':
                case 'N':
                    if (!e.metaKey && !e.ctrlKey) {
                        e.preventDefault();
                        this.showNewTaskModal();
                    }
                    break;
                case 'i':
                case 'I':
                    if (!e.metaKey && !e.ctrlKey) {
                        e.preventDefault();
                        this.showNewIdeaModal();
                    }
                    break;
                case '/':
                    e.preventDefault();
                    this.elements.searchBar?.focus();
                    break;
                case 'Escape':
                    if (this.activeModal) {
                        this.hideModal(this.activeModal);
                    }
                    break;
            }
        });

        // Click outside modals to close
        document.addEventListener('click', (e) => {
            if (this.activeModal && e.target.classList.contains('modal-overlay')) {
                this.hideModal(this.activeModal);
            }
        });

        // Search functionality
        if (this.elements.searchBar && this.elements.searchIcon && this.elements.searchMorphing) {
            // Search icon click - activate search
            this.elements.searchIcon.addEventListener('click', () => {
                DOM.addClass(this.elements.searchMorphing, 'active');
                this.elements.searchBar.focus();
            });
            
            // Search input
            let searchTimeout;
            this.elements.searchBar.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    EventBus.emit('search:changed', { term: e.target.value });
                }, 300);
            });
            
            // Search clear button
            if (this.elements.searchClear) {
                this.elements.searchClear.addEventListener('click', () => {
                    this.elements.searchBar.value = '';
                    EventBus.emit('search:changed', { term: '' });
                    DOM.removeClass(this.elements.searchMorphing, 'active');
                });
            }
            
            // Close search on escape or blur
            this.elements.searchBar.addEventListener('blur', () => {
                if (!this.elements.searchBar.value) {
                    DOM.removeClass(this.elements.searchMorphing, 'active');
                }
            });
        }

        // Filter buttons
        this.elements.filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const filter = btn.dataset.filter;
                this.setActiveFilter(filter);
                EventBus.emit('filter:changed', { filter });
            });
        });

        // Sort buttons
        this.elements.sortButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const sort = btn.dataset.sort;
                this.setActiveSort(sort);
                EventBus.emit('sort:changed', { sort });
            });
        });

        // Category filters
        this.elements.categoryFilters.forEach(btn => {
            btn.addEventListener('click', () => {
                const category = btn.dataset.category;
                DOM.toggleClass(btn, 'active');
                EventBus.emit('category:toggled', { category });
            });
        });

        // New task/idea buttons
        if (this.elements.newTaskBtn) {
            this.elements.newTaskBtn.addEventListener('click', () => this.showNewTaskModal());
        }
        if (this.elements.newIdeaBtn) {
            this.elements.newIdeaBtn.addEventListener('click', () => this.showNewIdeaModal());
        }

        // Section collapse toggles
        DOM.getAll('.section-header').forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.task-section');
                DOM.toggleClass(section, 'collapsed');
                this.saveUIState();
            });
        });
    }

    initializeModals() {
        // Initialize all modal instances
        this.modals = {
            newTask: new TaskModal('new-task-modal'),
            editTask: new TaskModal('edit-task-modal'),
            switchTask: new SwitchTaskModal('switch-task-modal'),
            quickWin: new QuickWinModal('quick-win-modal'),
            breakSuggestion: new BreakModal('break-suggestion-modal'),
            stats: new StatsModal('stats-modal')
        };
    }

    // Rendering methods
    renderTasks(tasks) {
        // Clear all lists
        Object.values(this.elements.taskLists).forEach(list => {
            if (list) list.innerHTML = '';
        });

        // Group tasks by section
        const tasksBySection = {
            today: [],
            ideas: [],
            backlog: []
        };

        tasks.forEach(task => {
            tasksBySection[task.section].push(task);
        });

        // Render each section
        Object.entries(tasksBySection).forEach(([section, sectionTasks]) => {
            const list = this.elements.taskLists[section];
            if (!list) return;

            const fragment = document.createDocumentFragment();
            sectionTasks.forEach(task => {
                const taskEl = this.createTaskElement(task);
                fragment.appendChild(taskEl);
            });
            list.appendChild(fragment);
        });

        this.updateEmptyStates();
    }

    createTaskElement(task) {
        const taskEl = DOM.create('div', {
            className: 'task-item' + (task.is_completed ? ' completed' : '') + 
                      (task.due_date && this.isOverdue(task) ? ' overdue' : ''),
            'data-task-id': task.id,
            draggable: !task.is_completed
        });

        // Task header
        const header = DOM.create('div', { className: 'task-header' });
        
        // Checkbox
        const checkbox = DOM.create('input', {
            type: 'checkbox',
            className: 'task-checkbox',
            checked: task.is_completed
        });
        checkbox.addEventListener('change', () => {
            EventBus.emit('task:toggle', { taskId: task.id });
        });
        header.appendChild(checkbox);

        // Title
        const title = DOM.create('span', {
            className: 'task-title',
            textContent: task.is_idea ? '💡 ' + task.title : task.title
        });
        header.appendChild(title);

        // Metadata
        const metadata = DOM.create('div', { className: 'task-metadata' });
        
        if (task.category && task.category !== 'other') {
            metadata.appendChild(DOM.create('span', {
                className: `category-tag ${task.category}`,
                textContent: task.category
            }));
        }

        if (task.effort) {
            metadata.appendChild(DOM.create('span', {
                className: 'effort-tag',
                textContent: task.effort
            }));
        }

        if (task.friction > 1) {
            metadata.appendChild(DOM.create('span', {
                className: 'friction-tag',
                textContent: CONFIG.FRICTION_EMOJI[task.friction]
            }));
        }

        if (task.due_date) {
            const dueEl = DOM.create('span', {
                className: 'due-date' + (this.isOverdue(task) ? ' overdue' : ''),
                textContent: this.formatDate(task.due_date)
            });
            metadata.appendChild(dueEl);
        }

        // Energy cost
        if (!task.is_completed && !task.is_idea) {
            const energyCost = this.calculateEnergyCost(task);
            metadata.appendChild(DOM.create('span', {
                className: 'energy-cost',
                textContent: `⚡${energyCost}`
            }));
        }

        header.appendChild(metadata);

        // Actions
        const actions = DOM.create('div', { className: 'task-actions' });
        
        if (!task.is_completed) {
            actions.appendChild(this.createActionButton('edit', '✏️', () => {
                EventBus.emit('task:edit', { taskId: task.id });
            }));
            
            if (!task.is_idea) {
                actions.appendChild(this.createActionButton('start', '▶️', () => {
                    EventBus.emit('task:start', { taskId: task.id });
                }));
                
                actions.appendChild(this.createActionButton('star', task.is_north_star ? '⭐' : '☆', () => {
                    EventBus.emit('task:toggleNorthStar', { taskId: task.id });
                }));
            }
        }
        
        actions.appendChild(this.createActionButton('delete', '🗑️', () => {
            if (confirm('Delete this task?')) {
                EventBus.emit('task:delete', { taskId: task.id });
            }
        }));

        header.appendChild(actions);
        taskEl.appendChild(header);

        // Subtasks
        if (task.subtasks && task.subtasks.length > 0) {
            const subtasksContainer = this.createSubtasksElement(task);
            taskEl.appendChild(subtasksContainer);
        }

        // Bind drag events
        this.bindDragEvents(taskEl, task);

        return taskEl;
    }

    createSubtasksElement(task) {
        const container = DOM.create('div', { className: 'subtasks-container' });
        const isExpanded = EventBus.emit('task:isExpanded', { taskId: task.id });
        
        const toggle = DOM.create('div', {
            className: 'subtasks-toggle' + (isExpanded ? ' expanded' : ''),
            innerHTML: `<span class="toggle-icon">${isExpanded ? '▼' : '▶'}</span> 
                       ${task.subtasks.filter(st => st.is_completed).length}/${task.subtasks.length} subtasks`
        });
        
        toggle.addEventListener('click', () => {
            const expanded = DOM.toggleClass(toggle, 'expanded');
            DOM.toggleClass(list, 'expanded');
            EventBus.emit(expanded ? 'task:expanded' : 'task:collapsed', { taskId: task.id });
        });
        
        container.appendChild(toggle);

        const list = DOM.create('div', {
            className: 'subtasks-list' + (isExpanded ? ' expanded' : '')
        });

        task.subtasks.forEach(subtask => {
            const subtaskEl = DOM.create('div', {
                className: 'subtask-item' + (subtask.is_completed ? ' completed' : '')
            });

            const checkbox = DOM.create('input', {
                type: 'checkbox',
                className: 'subtask-checkbox',
                checked: subtask.is_completed
            });
            checkbox.addEventListener('change', () => {
                EventBus.emit('subtask:toggle', { taskId: task.id, subtaskId: subtask.id });
            });

            const title = DOM.create('span', {
                className: 'subtask-title',
                textContent: subtask.title
            });

            subtaskEl.appendChild(checkbox);
            subtaskEl.appendChild(title);
            list.appendChild(subtaskEl);
        });

        // Add new subtask input
        if (!task.is_completed) {
            const addSubtask = DOM.create('div', { className: 'add-subtask' });
            const input = DOM.create('input', {
                type: 'text',
                className: 'add-subtask-input',
                placeholder: 'Add subtask...'
            });
            
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    EventBus.emit('subtask:add', { taskId: task.id, title: input.value.trim() });
                    input.value = '';
                }
            });

            addSubtask.appendChild(input);
            list.appendChild(addSubtask);
        }

        container.appendChild(list);
        return container;
    }

    createActionButton(action, icon, handler) {
        const btn = DOM.create('button', {
            className: `action-btn ${action}`,
            textContent: icon,
            title: action.charAt(0).toUpperCase() + action.slice(1)
        });
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            handler();
        });
        return btn;
    }

    bindDragEvents(element, task) {
        element.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', task.id);
            DOM.addClass(element, 'dragging');
        });

        element.addEventListener('dragend', () => {
            DOM.removeClass(element, 'dragging');
        });
    }

    // UI State Management
    setActiveFilter(filter) {
        this.elements.filterButtons.forEach(btn => {
            DOM.toggleClass(btn, 'active', btn.dataset.filter === filter);
        });
    }

    setActiveSort(sort) {
        this.elements.sortButtons.forEach(btn => {
            DOM.toggleClass(btn, 'active', btn.dataset.sort === sort);
        });
    }

    updateEmptyStates() {
        Object.entries(this.elements.taskLists).forEach(([section, list]) => {
            if (!list) return;
            
            const isEmpty = list.children.length === 0;
            const emptyState = list.parentElement.querySelector('.empty-state');
            
            if (emptyState) {
                DOM.toggle(emptyState, isEmpty);
            }
        });
    }

    // Modal Management
    showModal(modalName, data = {}) {
        const modal = this.modals[modalName];
        if (!modal) return;

        if (this.activeModal) {
            this.hideModal(this.activeModal);
        }

        modal.show(data);
        this.activeModal = modalName;
    }

    hideModal(modalName) {
        const modal = this.modals[modalName];
        if (!modal) return;

        modal.hide();
        this.activeModal = null;
    }

    showNewTaskModal() {
        this.showModal('newTask', { mode: 'create' });
    }

    showNewIdeaModal() {
        this.showModal('newTask', { mode: 'idea' });
    }

    // Toast notifications
    showToast(message, type = 'info', duration = 3000) {
        const toast = DOM.create('div', {
            className: `toast ${type}`,
            textContent: message
        });

        const container = DOM.get('#toast-container') || this.createToastContainer();
        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            DOM.addClass(toast, 'show');
        });

        // Remove after duration
        clearTimeout(this.toastTimeout);
        this.toastTimeout = setTimeout(() => {
            DOM.removeClass(toast, 'show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    createToastContainer() {
        const container = DOM.create('div', { id: 'toast-container' });
        document.body.appendChild(container);
        return container;
    }

    // Confetti animation
    showConfetti() {
        const confetti = DOM.get('#confetti-container') || this.createConfettiContainer();
        DOM.addClass(confetti, 'active');

        clearTimeout(this.confettiTimeout);
        this.confettiTimeout = setTimeout(() => {
            DOM.removeClass(confetti, 'active');
        }, 3000);
    }

    createConfettiContainer() {
        const container = DOM.create('div', { id: 'confetti-container' });
        
        // Create confetti pieces
        for (let i = 0; i < 50; i++) {
            const piece = DOM.create('div', {
                className: 'confetti-piece',
                style: `
                    left: ${Math.random() * 100}%;
                    animation-delay: ${Math.random() * 3}s;
                    background-color: hsl(${Math.random() * 360}, 70%, 50%);
                `
            });
            container.appendChild(piece);
        }
        
        document.body.appendChild(container);
        return container;
    }

    // Utility methods
    isOverdue(task) {
        if (!task.due_date || task.is_completed) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(task.due_date) < today;
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === tomorrow.toDateString()) {
            return 'Tomorrow';
        } else {
            return date.toLocaleDateString();
        }
    }

    calculateEnergyCost(task) {
        const effortValue = CONFIG.EFFORT_VALUES[task.effort] || 6;
        return Math.ceil((effortValue / 3) * (task.friction || 1));
    }

    restoreUIState() {
        const uiState = StorageManager.get('confettiTodoUI', {});
        
        // Restore theme
        if (uiState.theme) {
            document.body.setAttribute('data-theme', uiState.theme);
        }
        
        // Restore sidebar state
        if (uiState.sidebarCollapsed) {
            DOM.addClass(DOM.get('.sidebar'), 'collapsed');
        }
    }

    saveUIState() {
        const uiState = {
            theme: document.body.getAttribute('data-theme') || 'light',
            sidebarCollapsed: DOM.hasClass(DOM.get('.sidebar'), 'collapsed'),
            collapsedSections: Array.from(DOM.getAll('.task-section.collapsed'))
                .map(section => section.id)
        };
        
        StorageManager.set('confettiTodoUI', uiState);
    }
}

// Modal base class
class Modal {
    constructor(modalId) {
        this.modal = DOM.get(`#${modalId}`);
        this.overlay = this.modal?.querySelector('.modal-overlay');
        this.content = this.modal?.querySelector('.modal-content');
        this.bindEvents();
    }

    bindEvents() {
        if (!this.modal) return;

        // Close button
        const closeBtn = this.modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // ESC key handled by UIManager
    }

    show(data = {}) {
        if (!this.modal) return;
        
        this.beforeShow(data);
        DOM.removeClass(this.modal, 'hidden');
        this.afterShow(data);
    }

    hide() {
        if (!this.modal) return;
        
        this.beforeHide();
        DOM.addClass(this.modal, 'hidden');
        this.afterHide();
    }

    // Override in subclasses
    beforeShow(data) {}
    afterShow(data) {}
    beforeHide() {}
    afterHide() {}
}

// Task modal for creating/editing tasks
class TaskModal extends Modal {
    constructor(modalId) {
        super(modalId);
        this.setupForm();
    }

    setupForm() {
        this.form = this.modal?.querySelector('form');
        if (!this.form) return;

        this.inputs = {
            title: this.form.querySelector('#task-title'),
            category: this.form.querySelector('#task-category'),
            effort: this.form.querySelector('#task-effort'),
            friction: this.form.querySelector('#task-friction'),
            dueDate: this.form.querySelector('#task-due-date')
        };

        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
    }

    beforeShow(data) {
        this.mode = data.mode || 'create';
        this.taskId = data.taskId;

        // Reset form
        this.form?.reset();

        if (this.mode === 'edit' && data.task) {
            this.populateForm(data.task);
        } else if (this.mode === 'idea') {
            // Hide fields not needed for ideas
            DOM.hide(this.form.querySelector('.effort-field'));
            DOM.hide(this.form.querySelector('.friction-field'));
        }
    }

    populateForm(task) {
        if (this.inputs.title) this.inputs.title.value = task.title;
        if (this.inputs.category) this.inputs.category.value = task.category || 'other';
        if (this.inputs.effort) this.inputs.effort.value = task.effort || '30m';
        if (this.inputs.friction) this.inputs.friction.value = task.friction || 1;
        if (this.inputs.dueDate && task.due_date) {
            this.inputs.dueDate.value = task.due_date.split('T')[0];
        }
    }

    handleSubmit() {
        const data = {
            title: this.inputs.title?.value.trim(),
            category: this.inputs.category?.value,
            effort: this.inputs.effort?.value,
            friction: parseInt(this.inputs.friction?.value || 1),
            due_date: this.inputs.dueDate?.value || null,
            is_idea: this.mode === 'idea'
        };

        if (!data.title) {
            this.showError('Title is required');
            return;
        }

        const event = this.mode === 'edit' ? 'task:update' : 'task:create';
        EventBus.emit(event, { taskId: this.taskId, data });
        
        this.hide();
    }

    showError(message) {
        const error = this.form?.querySelector('.form-error') || 
                     DOM.create('div', { className: 'form-error', textContent: message });
        
        if (!error.parentElement) {
            this.form?.prepend(error);
        } else {
            error.textContent = message;
        }

        setTimeout(() => error.remove(), 3000);
    }
}

// Switch task modal
class SwitchTaskModal extends Modal {
    beforeShow(data) {
        this.currentTaskId = data.currentTaskId;
        this.renderTaskList(data.availableTasks);
    }

    renderTaskList(tasks) {
        const list = this.modal?.querySelector('.task-list');
        if (!list) return;

        list.innerHTML = '';

        tasks.forEach(task => {
            const item = DOM.create('div', {
                className: 'switch-task-item',
                'data-task-id': task.id
            });

            item.innerHTML = `
                <span class="task-title">${task.title}</span>
                <span class="task-metadata">
                    ${task.effort || '30m'} • ${CONFIG.FRICTION_EMOJI[task.friction || 1]}
                </span>
            `;

            item.addEventListener('click', () => {
                EventBus.emit('workingZone:switch', { 
                    fromTaskId: this.currentTaskId,
                    toTaskId: task.id 
                });
                this.hide();
            });

            list.appendChild(item);
        });
    }
}

// Quick win modal
class QuickWinModal extends Modal {
    beforeShow(data) {
        if (data.suggestion) {
            this.renderSuggestion(data.suggestion);
        }
    }

    renderSuggestion(task) {
        const content = this.modal?.querySelector('.suggestion-content');
        if (!content) return;

        content.innerHTML = `
            <h3>${task.title}</h3>
            <div class="suggestion-details">
                <span class="effort">${task.effort}</span>
                <span class="category">${task.category}</span>
                ${task.due_date ? `<span class="due-date">${this.formatDate(task.due_date)}</span>` : ''}
            </div>
            <div class="suggestion-actions">
                <button class="btn btn-primary start-task" data-task-id="${task.id}">
                    Start This Task
                </button>
                <button class="btn btn-secondary" onclick="this.closest('.modal').classList.remove('active')">
                    Show Another
                </button>
            </div>
        `;

        const startBtn = content.querySelector('.start-task');
        startBtn?.addEventListener('click', () => {
            EventBus.emit('task:start', { taskId: task.id });
            this.hide();
        });
    }
}

// Break suggestion modal
class BreakModal extends Modal {
    setupTimer() {
        this.timerInterval = null;
        this.breakDuration = null;
    }

    beforeShow(data) {
        this.breakDuration = data.duration || 5;
        this.renderBreakOptions();
    }

    renderBreakOptions() {
        const content = this.modal?.querySelector('.break-content');
        if (!content) return;

        content.innerHTML = `
            <h3>Time for a break! 🌟</h3>
            <p>You've been working hard. Your energy is running low.</p>
            <div class="break-options">
                <button class="btn btn-primary start-break" data-duration="5">
                    Take 5-minute break (+4 energy)
                </button>
                <button class="btn btn-primary start-break" data-duration="15">
                    Take 15-minute break (full restore)
                </button>
                <button class="btn btn-secondary dismiss-break">
                    Keep working
                </button>
            </div>
            <div class="break-timer" style="display: none;">
                <h3>On break</h3>
                <div class="timer-display">00:00</div>
                <button class="btn btn-secondary cancel-break">Cancel Break</button>
            </div>
        `;

        // Bind break buttons
        content.querySelectorAll('.start-break').forEach(btn => {
            btn.addEventListener('click', () => {
                const duration = parseInt(btn.dataset.duration);
                this.startBreak(duration);
            });
        });

        content.querySelector('.dismiss-break')?.addEventListener('click', () => {
            this.hide();
        });

        content.querySelector('.cancel-break')?.addEventListener('click', () => {
            this.cancelBreak();
        });
    }

    startBreak(duration) {
        EventBus.emit('break:start', { duration });
        
        const options = this.modal?.querySelector('.break-options');
        const timer = this.modal?.querySelector('.break-timer');
        
        DOM.hide(options);
        DOM.show(timer);

        this.breakEndTime = Date.now() + (duration * 60 * 1000);
        this.updateTimer();
        
        this.timerInterval = setInterval(() => {
            this.updateTimer();
        }, 1000);
    }

    updateTimer() {
        const remaining = Math.max(0, this.breakEndTime - Date.now());
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        
        const display = this.modal?.querySelector('.timer-display');
        if (display) {
            display.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (remaining === 0) {
            this.completeBreak();
        }
    }

    cancelBreak() {
        clearInterval(this.timerInterval);
        EventBus.emit('break:cancel');
        this.hide();
    }

    completeBreak() {
        clearInterval(this.timerInterval);
        EventBus.emit('break:complete');
        this.hide();
        EventBus.emit('ui:showToast', 'Break completed! Energy restored ⚡');
    }

    beforeHide() {
        clearInterval(this.timerInterval);
    }
}

// Stats modal
class StatsModal extends Modal {
    beforeShow(data) {
        if (data.stats) {
            this.renderStats(data.stats);
        }
    }

    renderStats(stats) {
        const content = this.modal?.querySelector('.stats-content');
        if (!content) return;

        content.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total XP</h4>
                    <div class="stat-value">${stats.totalXP.toLocaleString()}</div>
                </div>
                <div class="stat-card">
                    <h4>Level</h4>
                    <div class="stat-value">${stats.level}</div>
                </div>
                <div class="stat-card">
                    <h4>Tasks Completed</h4>
                    <div class="stat-value">${stats.tasksCompleted}</div>
                </div>
                <div class="stat-card">
                    <h4>Current Streak</h4>
                    <div class="stat-value">${stats.currentStreak} days</div>
                </div>
            </div>
            <div class="category-breakdown">
                <h4>XP by Category</h4>
                ${this.renderCategoryChart(stats.categoryXP)}
            </div>
        `;
    }

    renderCategoryChart(categoryXP) {
        const total = Object.values(categoryXP).reduce((sum, xp) => sum + xp, 0);
        
        return Object.entries(categoryXP)
            .sort(([,a], [,b]) => b - a)
            .map(([category, xp]) => {
                const percentage = total > 0 ? (xp / total * 100).toFixed(1) : 0;
                return `
                    <div class="category-bar">
                        <span class="category-name">${category}</span>
                        <div class="bar-container">
                            <div class="bar-fill ${category}" style="width: ${percentage}%"></div>
                        </div>
                        <span class="category-xp">${xp.toLocaleString()} XP</span>
                    </div>
                `;
            }).join('');
    }
}

// Event listeners for UI updates
EventBus.on('tasks:render', ({ tasks }) => {
    const ui = window.uiManager;
    if (ui) ui.renderTasks(tasks);
});

EventBus.on('ui:showToast', (message) => {
    const ui = window.uiManager;
    if (ui) ui.showToast(message);
});

EventBus.on('task:completed', () => {
    const ui = window.uiManager;
    if (ui) {
        ui.showConfetti();
        // Play completion sound if available
        const audio = new Audio('/assets/sounds/complete.mp3');
        audio.play().catch(() => {}); // Ignore errors if sound doesn't exist
    }
});