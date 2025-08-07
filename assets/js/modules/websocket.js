// WebSocket Module - Handles real-time synchronization
import { CONFIG } from '../config.js';
import { EventBus } from '../utils/events.js';

export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.pingInterval = null;
        this.isConnected = false;
        this.messageQueue = [];
    }

    init() {
        this.connect();
        this.bindEvents();
    }

    connect() {
        try {
            const wsUrl = CONFIG.API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
            this.ws = new WebSocket(`${wsUrl}/ws`);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onclose = () => this.handleClose();
            this.ws.onerror = (error) => this.handleError(error);
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }

    handleOpen() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Send any queued messages
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
        
        // Start ping interval to keep connection alive
        this.startPingInterval();
        
        EventBus.emit('websocket:connected');
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'sync':
                    EventBus.emit('websocket:sync', data.payload);
                    break;
                    
                case 'task_update':
                    EventBus.emit('websocket:taskUpdate', data.payload);
                    break;
                    
                case 'stats_update':
                    EventBus.emit('websocket:statsUpdate', data.payload);
                    break;
                    
                case 'energy_update':
                    EventBus.emit('websocket:energyUpdate', data.payload);
                    break;
                    
                case 'notification':
                    EventBus.emit('websocket:notification', data.payload);
                    break;
                    
                case 'pong':
                    // Server responded to ping
                    break;
                    
                default:
                    console.warn('Unknown WebSocket message type:', data.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    handleClose() {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.stopPingInterval();
        
        EventBus.emit('websocket:disconnected');
        
        // Attempt to reconnect
        this.scheduleReconnect();
    }

    handleError(error) {
        console.error('WebSocket error:', error);
        EventBus.emit('websocket:error', error);
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            EventBus.emit('websocket:reconnectFailed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    send(data) {
        if (!this.isConnected) {
            // Queue message if not connected
            this.messageQueue.push(data);
            return;
        }
        
        try {
            this.ws.send(JSON.stringify(data));
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            this.messageQueue.push(data);
        }
    }

    startPingInterval() {
        this.pingInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }

    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    bindEvents() {
        // Send updates through WebSocket
        EventBus.on('task:created', (task) => {
            this.send({
                type: 'task_created',
                payload: task
            });
        });

        EventBus.on('task:updated', (task) => {
            this.send({
                type: 'task_updated',
                payload: task
            });
        });

        EventBus.on('task:deleted', (task) => {
            this.send({
                type: 'task_deleted',
                payload: { taskId: task.id }
            });
        });

        EventBus.on('task:completed', (task) => {
            this.send({
                type: 'task_completed',
                payload: task
            });
        });

        EventBus.on('stats:updated', (stats) => {
            this.send({
                type: 'stats_updated',
                payload: stats
            });
        });

        EventBus.on('energy:consumed', (data) => {
            this.send({
                type: 'energy_consumed',
                payload: data
            });
        });

        EventBus.on('energy:restored', (data) => {
            this.send({
                type: 'energy_restored',
                payload: data
            });
        });

        // Handle incoming sync events
        EventBus.on('websocket:sync', (data) => {
            // Reload tasks when sync received from another client
            EventBus.emit('tasks:reload');
        });

        EventBus.on('websocket:taskUpdate', (data) => {
            // Update specific task when change received
            EventBus.emit('task:externalUpdate', data);
        });

        EventBus.on('websocket:notification', (data) => {
            // Show notification from server
            EventBus.emit('ui:showToast', data.message, data.type);
        });
    }

    disconnect() {
        this.stopPingInterval();
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        this.isConnected = false;
        this.messageQueue = [];
    }
}

// Create and export singleton instance
export const websocketManager = new WebSocketManager();