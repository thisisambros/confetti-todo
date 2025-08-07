// DOM Utilities
export const DOM = {
    // Query selectors
    get(selector) {
        return document.querySelector(selector);
    },

    getAll(selector) {
        return document.querySelectorAll(selector);
    },

    // Element creation
    create(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof Element) {
                element.appendChild(child);
            }
        });

        return element;
    },

    // Class manipulation
    addClass(element, className) {
        if (typeof className === 'string' && className.includes(' ')) {
            className.split(' ').forEach(cls => element.classList.add(cls));
        } else {
            element.classList.add(className);
        }
    },

    removeClass(element, className) {
        if (typeof className === 'string' && className.includes(' ')) {
            className.split(' ').forEach(cls => element.classList.remove(cls));
        } else {
            element.classList.remove(className);
        }
    },

    toggleClass(element, className) {
        element.classList.toggle(className);
    },

    hasClass(element, className) {
        return element.classList.contains(className);
    },

    // Visibility
    show(element) {
        element.style.display = '';
    },

    hide(element) {
        element.style.display = 'none';
    },

    toggle(element, force) {
        if (force !== undefined) {
            element.style.display = force ? '' : 'none';
        } else {
            element.style.display = element.style.display === 'none' ? '' : 'none';
        }
    },

    isVisible(element) {
        return element.offsetParent !== null;
    },

    // Content
    setHTML(element, html) {
        element.innerHTML = html;
    },

    setText(element, text) {
        element.textContent = text;
    },

    // Events
    on(element, event, handler) {
        element.addEventListener(event, handler);
    },

    off(element, event, handler) {
        element.removeEventListener(event, handler);
    },

    once(element, event, handler) {
        element.addEventListener(event, handler, { once: true });
    },

    // Animation
    fadeIn(element, duration = 300) {
        element.style.opacity = 0;
        element.style.display = 'block';
        element.style.transition = `opacity ${duration}ms`;
        
        requestAnimationFrame(() => {
            element.style.opacity = 1;
        });
    },

    fadeOut(element, duration = 300) {
        element.style.transition = `opacity ${duration}ms`;
        element.style.opacity = 0;
        
        setTimeout(() => {
            element.style.display = 'none';
        }, duration);
    }
};

// DOM Ready helper
export function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}