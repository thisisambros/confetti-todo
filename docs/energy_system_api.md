# Energy System API Documentation

## Overview
The Energy System tracks user energy levels, consumption during task work, and restoration through breaks. Energy is capped at 12 units and resets daily.

## API Endpoints

### 1. GET /api/energy
Get current energy state for a session.

**Query Parameters:**
- `session_id` (optional, default: "default"): Session identifier

**Response:**
```json
{
  "current_energy": 12,
  "max_energy": 12,
  "is_on_break": false,
  "break_end_time": null,
  "last_reset_date": "2025-07-30",
  "session_id": "default"
}
```

### 2. POST /api/energy/consume
Consume energy when starting work on a task.

**Request Body:**
```json
{
  "amount": 3,  // Will be overridden if task_metadata is provided
  "task_id": "task_123",
  "task_metadata": {
    "effort": "1h",
    "friction": 3
  }
}
```

**Energy Calculation:**
- Requires both `effort` and `friction` in task_metadata for automatic calculation
- Base cost: 1 energy per 30 minutes of effort
- Friction modifier: +(friction - 2) energy
- Formula: `energy_cost = min(12, max(1, base_cost + (friction - 2)))`
- Maximum: 12 energy per task
- If task_metadata is not provided or incomplete, uses the `amount` field directly

**Response:**
```json
{
  "current_energy": 9,
  "energy_consumed": 3,
  "success": true
}
```

**Errors:**
- 400: Insufficient energy
- 400: Cannot consume energy while on break

### 3. POST /api/energy/break
Start a break to restore energy.

**Query Parameters:**
- `duration_minutes` (optional, default: 15): Break duration (5-60 minutes)
- `session_id` (optional, default: "default"): Session identifier

**Response:**
```json
{
  "break_end_time": "2025-07-30T15:30:00",
  "duration_minutes": 15,
  "energy_to_restore": 1
}
```

**Energy Restoration:**
- 1 energy point per 15 minutes of break
- Capped only by maximum energy (12) and current energy deficit
- Formula: `energy_to_restore = min(max_energy - current_energy, duration_minutes // 15)`

**Errors:**
- 400: Already on break
- 400: Energy is already full

### 4. POST /api/energy/restore
Complete a break early and restore energy based on actual break duration.

**Query Parameters:**
- `session_id` (optional, default: "default"): Session identifier

**Response:**
```json
{
  "current_energy": 10,
  "energy_restored": 1,
  "success": true
}
```

**Errors:**
- 400: Not currently on break
- 400: No break end time set

## WebSocket Messages

Connect to `/ws` to receive real-time energy updates.

### Message Types:

#### 1. energy_consumed
Broadcast when energy is consumed.
```json
{
  "type": "energy_consumed",
  "data": {
    "current_energy": 9,
    "max_energy": 12,
    "energy_consumed": 3,
    "task_id": "task_123"
  }
}
```

#### 2. break_started
Broadcast when a break starts.
```json
{
  "type": "break_started",
  "data": {
    "break_end_time": "2025-07-30T15:30:00",
    "duration_minutes": 15,
    "energy_to_restore": 1
  }
}
```

#### 3. energy_restored
Broadcast when energy is restored (break completed).
```json
{
  "type": "energy_restored",
  "data": {
    "current_energy": 10,
    "max_energy": 12,
    "energy_restored": 1
  }
}
```

## Usage Examples

### Starting Work on a Task
```javascript
// Frontend example
async function startTask(task) {
  const response = await fetch('/api/energy/consume', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount: 1,  // Will be calculated from metadata
      task_id: task.id,
      task_metadata: {
        effort: task.effort || '30m',
        friction: task.friction || 2
      }
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    if (error.detail.includes('Insufficient energy')) {
      // Prompt user to take a break
      showBreakPrompt();
    }
  }
}
```

### Taking a Break
```javascript
async function takeBreak(minutes = 15) {
  const response = await fetch(`/api/energy/break?duration_minutes=${minutes}`, {
    method: 'POST'
  });
  
  const data = await response.json();
  // Show break timer UI
  showBreakTimer(data.break_end_time);
}
```

### WebSocket Integration
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'energy_consumed':
      updateEnergyBar(message.data.current_energy, message.data.max_energy);
      break;
    
    case 'break_started':
      showBreakNotification(message.data);
      break;
    
    case 'energy_restored':
      updateEnergyBar(message.data.current_energy, message.data.max_energy);
      showEnergyRestoredNotification(message.data.energy_restored);
      break;
  }
};
```

## Daily Reset
Energy automatically resets to maximum (12) at midnight each day. The reset is checked on each energy state access, ensuring consistency across sessions.