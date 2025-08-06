# Energy Regeneration API Documentation

## Overview

The Energy Regeneration System provides automatic energy restoration when users are not actively working. Energy regenerates at a rate of +1 point every 15 minutes when the following conditions are met:
- User is not actively working on a task (regeneration_paused_at is null)
- User is not on a break
- Current energy is below maximum (12 points)
- The is_regenerating flag is true
- Thread-safe locking ensures concurrent regeneration updates are handled properly

## API Endpoints

### Get Regeneration State

```http
GET /api/energy/regeneration?session_id={session_id}
```

Returns the current regeneration state for a session.

**Response:**
```json
{
  "regeneration_time_remaining": 897,  // seconds until next regeneration
  "is_regenerating": true,              // whether regeneration is active
  "last_regeneration_time": "2025-07-31T12:45:00"  // ISO timestamp
}
```

### Pause Regeneration

```http
POST /api/energy/regeneration/pause?session_id={session_id}
```

Pauses energy regeneration when user starts working on a task. This should be called by the frontend when a task timer starts.

**Response:**
```json
{
  "success": true
}
```

**WebSocket Broadcast:**
```json
{
  "type": "regeneration_paused",
  "data": {
    "regeneration_time_remaining": 450,
    "is_regenerating": false,
    "last_regeneration_time": "2025-07-31T12:45:00"
  }
}
```

### Resume Regeneration

```http
POST /api/energy/regeneration/resume?session_id={session_id}
```

Resumes energy regeneration when user stops working. The timer continues from where it was paused by adjusting the `last_regeneration_time` to account for the pause duration, ensuring the next regeneration occurs at the correct time.

**Response:**
```json
{
  "success": true
}
```

**WebSocket Broadcast:**
```json
{
  "type": "regeneration_resumed",
  "data": {
    "regeneration_time_remaining": 450,
    "is_regenerating": true,
    "last_regeneration_time": "2025-07-31T12:45:00"
  }
}
```

## WebSocket Events

### Energy Regenerated

Broadcast when automatic regeneration occurs (every 15 minutes):

```json
{
  "type": "energy_regenerated",
  "data": {
    "current_energy": 8,
    "max_energy": 12,
    "energy_regenerated": 1,
    "session_id": "default"
  }
}
```

## Integration with Existing Energy System

### Energy Consumption
- Consuming energy no longer automatically pauses regeneration
- Frontend must explicitly call `/api/energy/regeneration/pause` when starting work

### Breaks
- Taking a break automatically pauses regeneration
- Completing a break resumes regeneration if energy is not at maximum

### Daily Reset
- Regeneration state is reset with daily energy reset
- Timer starts fresh each day

## Implementation Details

### Backend Components

1. **EnergyState Model** - Extended with regeneration fields:
   - `last_regeneration_time`: Timestamp of last regeneration
   - `is_regenerating`: Whether regeneration is active
   - `regeneration_paused_at`: Timestamp when regeneration was paused

2. **Background Task** - Runs every second to check for regeneration:
   - Thread-safe with session-specific locks
   - Handles multiple concurrent sessions
   - Broadcasts WebSocket updates on regeneration

3. **Timing Calculations**:
   - Regeneration interval: 15 minutes (900 seconds)
   - Regeneration amount: 1 energy point per interval
   - Pause time is excluded from regeneration timer

### Frontend Integration

The frontend RegenerationManager should:

1. Call `/api/energy/regeneration` on initialization to get current state
2. Call `/api/energy/regeneration/pause` when `workingTask` is set
3. Call `/api/energy/regeneration/resume` when `workingTask` is cleared
4. Listen for WebSocket events to update the UI:
   - `regeneration_paused`
   - `regeneration_resumed`
   - `energy_regenerated`

### Thread Safety

The regeneration system uses thread locks to ensure safe concurrent access:
- Each session has its own lock for regeneration updates
- Background task acquires lock before modifying energy state
- Prevents race conditions between API calls and background regeneration

## Testing

Comprehensive test coverage includes:
- Regeneration state endpoint functionality
- Pause/resume behavior
- Timing calculations and countdown
- Integration with breaks and energy consumption
- WebSocket event broadcasting
- Thread safety and concurrent sessions

Run tests with:
```bash
./venv/bin/python -m pytest tests/test_energy_regeneration.py -v
```