// Event Bus for decoupled communication between modules
export class EventBus {
    static listeners = {};

    static on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    static off(event, callback) {
        if (!this.listeners[event]) return;
        
        this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }

    static emit(event, data = {}) {
        if (!this.listeners[event]) return;
        
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event listener for ${event}:`, error);
            }
        });
    }

    static once(event, callback) {
        const wrapper = (data) => {
            callback(data);
            this.off(event, wrapper);
        };
        this.on(event, wrapper);
    }
}