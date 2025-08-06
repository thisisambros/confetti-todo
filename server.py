#!/usr/bin/env python3
import asyncio
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Set
from pathlib import Path
import json
import threading
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Check if running in test mode via query parameter or environment variable
import os
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TODO_FILE = Path("todos.test.md") if TEST_MODE else Path("todos.md")
BACKUP_DIR = Path("backups")

class Task(BaseModel):
    id: str
    title: str
    is_idea: bool = False
    is_completed: bool = False
    category: Optional[str] = None
    effort: Optional[str] = None
    friction: Optional[int] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    subtasks: List['Task'] = []
    parent_id: Optional[str] = None
    
Task.model_rebuild()

class EnergyState(BaseModel):
    current_energy: int = Field(ge=0, le=12, default=12)
    max_energy: int = Field(default=12)
    is_on_break: bool = Field(default=False)
    break_end_time: Optional[datetime] = None
    last_reset_date: Optional[date] = None
    session_id: str = Field(default="default")
    # Regeneration fields
    last_regeneration_time: datetime = Field(default_factory=datetime.now)
    is_regenerating: bool = Field(default=True)
    regeneration_paused_at: Optional[datetime] = None

class ConsumeEnergyRequest(BaseModel):
    amount: int = Field(ge=1, le=12)
    task_id: Optional[str] = None
    task_metadata: Optional[Dict] = None

class BreakResponse(BaseModel):
    break_end_time: datetime
    duration_minutes: int
    energy_to_restore: int

class RegenerationState(BaseModel):
    regeneration_time_remaining: int  # seconds until next regeneration
    is_regenerating: bool
    last_regeneration_time: datetime

# Constants
REGENERATION_INTERVAL = 15 * 60  # 15 minutes in seconds
REGENERATION_AMOUNT = 1  # Energy points regenerated per interval

# In-memory energy storage per session
energy_storage: Dict[str, EnergyState] = {}
regeneration_locks: Dict[str, threading.Lock] = {}  # Thread locks for safe regeneration updates

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        self.active_connections -= disconnected

manager = ConnectionManager()

def get_or_create_energy_state(session_id: str = "default") -> EnergyState:
    """Get or create energy state for a session"""
    if session_id not in energy_storage:
        energy_storage[session_id] = EnergyState(session_id=session_id)
        regeneration_locks[session_id] = threading.Lock()
    
    # Check for daily reset
    state = energy_storage[session_id]
    today = date.today()
    if state.last_reset_date != today:
        state.current_energy = state.max_energy
        state.is_on_break = False
        state.break_end_time = None
        state.last_reset_date = today
        state.last_regeneration_time = datetime.now()
        state.is_regenerating = True
        state.regeneration_paused_at = None
    
    return state

def calculate_regeneration_state(state: EnergyState) -> RegenerationState:
    """Calculate current regeneration state"""
    now = datetime.now()
    
    # Regeneration is paused if: on break, at max energy, or manually paused
    if state.is_on_break or state.current_energy >= state.max_energy or not state.is_regenerating:
        return RegenerationState(
            regeneration_time_remaining=0,
            is_regenerating=False,
            last_regeneration_time=state.last_regeneration_time
        )
    
    # Calculate time elapsed since last regeneration
    if state.regeneration_paused_at:
        # If paused, use the pause time instead of current time
        elapsed = (state.regeneration_paused_at - state.last_regeneration_time).total_seconds()
    else:
        elapsed = (now - state.last_regeneration_time).total_seconds()
    
    # Calculate remaining time until next regeneration
    time_remaining = max(0, REGENERATION_INTERVAL - elapsed)
    
    return RegenerationState(
        regeneration_time_remaining=int(time_remaining),
        is_regenerating=state.is_regenerating and state.regeneration_paused_at is None,
        last_regeneration_time=state.last_regeneration_time
    )

def calculate_energy_cost(task_metadata: Dict) -> int:
    """Calculate energy cost based on task metadata"""
    if not task_metadata:
        raise ValueError("Task metadata is required to calculate energy cost")
    
    effort = task_metadata.get('effort')
    friction = task_metadata.get('friction')
    
    if not effort:
        raise ValueError("Task effort is required to calculate energy cost")
    if friction is None:
        raise ValueError("Task friction is required to calculate energy cost")
    
    # Parse effort to minutes
    if effort.endswith('m'):
        minutes = int(effort[:-1])
    elif effort.endswith('h'):
        minutes = int(effort[:-1]) * 60
    elif effort.endswith('d'):
        minutes = int(effort[:-1]) * 8 * 60
    else:
        raise ValueError(f"Invalid effort format: {effort}")
    
    # Calculate energy cost: base 1 energy per 30 minutes, scaled by friction
    base_cost = max(1, minutes // 30)
    energy_cost = min(12, max(1, base_cost + (friction - 2)))  # Cap at 12
    
    return energy_cost

def parse_markdown_line(line: str, line_num: int, parent_id: Optional[str] = None) -> Optional[Dict]:
    """Parse a single markdown line into a task object"""
    indent_level = (len(line) - len(line.lstrip())) // 2
    line = line.strip()
    
    if not line.startswith("- ["):
        return None
        
    is_completed = line[3] == "x"
    content = line[5:].strip()
    
    is_idea = content.startswith("?")
    if is_idea:
        content = content[1:].strip()
    
    # Extract metadata
    category_match = re.search(r'@(\w+)', content)
    category = category_match.group(1) if category_match else None
    
    effort_match = re.search(r'!(\d+[mhd])', content)
    effort = effort_match.group(1) if effort_match else None
    
    friction_match = re.search(r'%(\d)', content)
    friction = int(friction_match.group(1)) if friction_match else None
    
    due_match = re.search(r'\^(\d{4}-\d{2}-\d{2})', content)
    due_date = due_match.group(1) if due_match else None
    
    completed_match = re.search(r'\{([^}]+)\}', content)
    completed_at = completed_match.group(1) if completed_match else None
    
    # Remove metadata from title
    title = content
    for pattern in [r'@\w+', r'!\d+[mhd]', r'%\d', r'\^\d{4}-\d{2}-\d{2}', r'\{[^}]+\}']:
        title = re.sub(pattern, '', title).strip()
    
    return {
        "id": f"task_{line_num}",
        "title": title,
        "is_idea": is_idea,
        "is_completed": is_completed,
        "category": category,
        "effort": effort,
        "friction": friction,
        "due_date": due_date,
        "completed_at": completed_at,
        "indent_level": indent_level,
        "parent_id": parent_id,
        "subtasks": []
    }

def parse_markdown() -> Dict[str, List[Task]]:
    """Parse the markdown file into structured data"""
    if not TODO_FILE.exists():
        TODO_FILE.write_text("# today\n\n# ideas\n\n# backlog\n")
        return {"today": [], "ideas": [], "backlog": []}
    
    content = TODO_FILE.read_text()
    sections = {"today": [], "ideas": [], "backlog": []}
    current_section = None
    task_stack = []
    
    for line_num, line in enumerate(content.split('\n')):
        if line.strip().startswith("# "):
            current_section = line.strip()[2:].lower()
            task_stack = []
            continue
            
        if current_section and line.strip().startswith("- ["):
            task_data = parse_markdown_line(line, line_num)
            if task_data:
                indent_level = task_data.pop("indent_level")
                
                # Find parent based on indent level
                while len(task_stack) > indent_level:
                    task_stack.pop()
                
                if indent_level > 0 and task_stack:
                    parent = task_stack[-1]
                    task_data["parent_id"] = parent["id"]
                    parent["subtasks"].append(task_data)
                else:
                    sections[current_section].append(task_data)
                
                if indent_level == len(task_stack):
                    task_stack.append(task_data)
    
    return sections

def task_to_markdown(task: Dict, indent: int = 0) -> str:
    """Convert a task object back to markdown format"""
    prefix = "  " * indent + "- "
    check = "[x]" if task.get("is_completed") else "[ ]"
    
    parts = [prefix, check, " "]
    
    if task.get("is_idea"):
        parts.append("? ")
    
    parts.append(task["title"])
    
    if task.get("category"):
        parts.append(f" @{task['category']}")
    
    if task.get("effort"):
        parts.append(f" !{task['effort']}")
    
    if task.get("friction"):
        parts.append(f" %{task['friction']}")
    
    if task.get("due_date"):
        parts.append(f" ^{task['due_date']}")
    
    if task.get("completed_at"):
        parts.append(f" {{{task['completed_at']}}}")
    
    lines = ["".join(parts)]
    
    for subtask in task.get("subtasks", []):
        lines.append(task_to_markdown(subtask, indent + 1))
    
    return "\n".join(lines)

def save_markdown(sections: Dict[str, List[Dict]]):
    """Save the structured data back to markdown"""
    # Create backup
    if TODO_FILE.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_name = datetime.now().strftime("todos_%Y%m%d_%H%M%S.md")
        (BACKUP_DIR / backup_name).write_text(TODO_FILE.read_text())
    
    lines = []
    for section_name, tasks in sections.items():
        lines.append(f"# {section_name}")
        for task in tasks:
            lines.append(task_to_markdown(task))
        lines.append("")
    
    TODO_FILE.write_text("\n".join(lines))

@app.get("/")
async def root(test: bool = False):
    global TEST_MODE, TODO_FILE
    if test:
        TEST_MODE = True
        TODO_FILE = Path("todos.test.md")
    return FileResponse("index.html")

@app.get("/api/test-mode")
async def get_test_mode():
    return {"test_mode": TEST_MODE, "data_file": str(TODO_FILE)}

@app.get("/api/todos")
async def get_todos():
    return parse_markdown()

@app.post("/api/todos")
async def update_todos(sections: Dict[str, List[Dict]]):
    save_markdown(sections)
    await manager.broadcast({"type": "update", "data": sections})
    return {"status": "ok"}

@app.get("/api/stats")
async def get_stats():
    sections = parse_markdown()
    
    def count_tasks(tasks):
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("is_completed"))
        for task in tasks:
            sub_total, sub_completed = count_tasks(task.get("subtasks", []))
            total += sub_total
            completed += sub_completed
        return total, completed
    
    stats = {
        "categories": {},
        "total_tasks": 0,
        "completed_today": 0,
        "xp_today": 0,
        "total_xp": 0,
        "level": 1,
        "xp_for_next_level": 500,
        "xp_progress": 0,
        "streak": 0
    }
    
    # Count by category
    for section_tasks in sections.values():
        total, completed = count_tasks(section_tasks)
        stats["total_tasks"] += total
        
        def collect_categories(tasks):
            for task in tasks:
                if task.get("category") and not task.get("is_idea"):
                    cat = task["category"]
                    if cat not in stats["categories"]:
                        stats["categories"][cat] = {"total": 0, "completed": 0}
                    stats["categories"][cat]["total"] += 1
                    if task.get("is_completed"):
                        stats["categories"][cat]["completed"] += 1
                collect_categories(task.get("subtasks", []))
        
        collect_categories(section_tasks)
    
    # Calculate completed today and XP
    today = date.today().isoformat()
    for section_tasks in sections.values():
        def process_tasks(tasks):
            count = 0
            xp_today = 0
            total_xp = 0
            for task in tasks:
                if task.get("is_completed"):
                    task_xp = calculate_xp(task)
                    total_xp += task_xp
                    if task.get("completed_at") and task["completed_at"].startswith(today):
                        count += 1
                        xp_today += task_xp
                sub_count, sub_xp_today, sub_total_xp = process_tasks(task.get("subtasks", []))
                count += sub_count
                xp_today += sub_xp_today
                total_xp += sub_total_xp
            return count, xp_today, total_xp
        
        count, xp_today, total_xp = process_tasks(section_tasks)
        stats["completed_today"] += count
        stats["xp_today"] += xp_today
        stats["total_xp"] += total_xp
    
    # Calculate level (each level requires 500 XP)
    stats["level"] = 1 + (stats["total_xp"] // 500)
    stats["xp_progress"] = stats["total_xp"] % 500
    stats["xp_for_next_level"] = 500
    
    return stats

class BonusXP(BaseModel):
    xp: int
    reason: str

@app.post("/api/stats/bonus")
async def add_bonus_xp(data: BonusXP):
    # For now, just return a mock response since we don't persist stats
    # In a real app, you'd update persistent stats storage
    return {
        "status": "ok",
        "xp_added": data.xp,
        "reason": data.reason
    }

@app.get("/api/quick-win")
async def get_quick_win():
    sections = parse_markdown()
    
    # Find low-effort incomplete tasks
    candidates = []
    
    def collect_candidates(tasks):
        for task in tasks:
            if not task.get("is_completed") and not task.get("is_idea"):
                effort = task.get("effort", "30m")
                effort_minutes = 30
                if effort:
                    if effort.endswith("m"):
                        effort_minutes = int(effort[:-1])
                    elif effort.endswith("h"):
                        effort_minutes = int(effort[:-1]) * 60
                
                if effort_minutes <= 30:
                    candidates.append({
                        **task,
                        "effort_minutes": effort_minutes,
                        "xp": calculate_xp(task)
                    })
            
            collect_candidates(task.get("subtasks", []))
    
    for section_tasks in sections.values():
        collect_candidates(section_tasks)
    
    # Sort by effort (ascending) and XP (descending)
    candidates.sort(key=lambda x: (x["effort_minutes"], -x["xp"]))
    
    return candidates[0] if candidates else None

def calculate_xp(task: Dict) -> int:
    """Calculate XP based on effort and friction"""
    effort = task.get("effort", "30m")
    minutes = 30
    if effort:
        if effort.endswith("m"):
            minutes = int(effort[:-1])
        elif effort.endswith("h"):
            minutes = int(effort[:-1]) * 60
        elif effort.endswith("d"):
            minutes = int(effort[:-1]) * 8 * 60
    
    friction = task.get("friction") or 2
    base_xp = round(100 * (1 + minutes / 60) ** 0.5 * friction)
    
    # Bonus for subtasks
    if task.get("subtasks"):
        completed_subtasks = sum(1 for st in task["subtasks"] if st.get("is_completed"))
        total_subtasks = len(task["subtasks"])
        if completed_subtasks == total_subtasks and total_subtasks > 0:
            base_xp = int(base_xp * 1.5)
    
    return base_xp

@app.get("/api/energy")
async def get_energy(session_id: str = "default"):
    """Get current energy state"""
    state = get_or_create_energy_state(session_id)
    
    # Check if break is complete
    if state.is_on_break and state.break_end_time and datetime.now() >= state.break_end_time:
        # Restore energy
        duration = (state.break_end_time - datetime.now()).total_seconds() / 60
        energy_restored = min(state.max_energy - state.current_energy, max(1, int(duration / 15)))
        state.current_energy = min(state.max_energy, state.current_energy + energy_restored)
        state.is_on_break = False
        state.break_end_time = None
        
        # Broadcast update
        await manager.broadcast({
            "type": "energy_restored",
            "data": {
                "current_energy": state.current_energy,
                "max_energy": state.max_energy,
                "energy_restored": energy_restored
            }
        })
    
    return state

@app.post("/api/energy/consume")
async def consume_energy(request: ConsumeEnergyRequest, session_id: str = "default"):
    """Consume energy when starting work on a task"""
    state = get_or_create_energy_state(session_id)
    
    if state.is_on_break:
        raise HTTPException(status_code=400, detail="Cannot consume energy while on break")
    
    # Calculate actual energy cost if task metadata provided
    energy_cost = request.amount
    if request.task_metadata:
        energy_cost = calculate_energy_cost(request.task_metadata)
    
    if state.current_energy < energy_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient energy. Current: {state.current_energy}, Required: {energy_cost}"
        )
    
    state.current_energy -= energy_cost
    
    # Don't automatically pause regeneration on consume
    # The frontend will call the pause endpoint when actually working
    
    # Broadcast energy update
    await manager.broadcast({
        "type": "energy_consumed",
        "data": {
            "current_energy": state.current_energy,
            "max_energy": state.max_energy,
            "energy_consumed": energy_cost,
            "task_id": request.task_id
        }
    })
    
    return {
        "current_energy": state.current_energy,
        "energy_consumed": energy_cost,
        "success": True
    }

@app.post("/api/energy/break")
async def start_break(duration_minutes: int = 15, session_id: str = "default") -> BreakResponse:
    """Start a break and calculate when energy will be restored"""
    state = get_or_create_energy_state(session_id)
    
    if state.current_energy >= state.max_energy:
        raise HTTPException(status_code=400, detail="Energy is already full")
    
    if state.is_on_break:
        raise HTTPException(status_code=400, detail="Already on break")
    
    # Calculate break duration and energy restoration
    duration_minutes = max(5, min(60, duration_minutes))  # Between 5 and 60 minutes
    break_end_time = datetime.now() + timedelta(minutes=duration_minutes)
    
    # Energy restored: 1 point per 15 minutes of break
    energy_to_restore = min(
        state.max_energy - state.current_energy,
        max(1, duration_minutes // 15)
    )
    
    state.is_on_break = True
    state.break_end_time = break_end_time
    
    # Pause regeneration during break
    if state.is_regenerating and state.regeneration_paused_at is None:
        state.regeneration_paused_at = datetime.now()
    
    # Broadcast break started
    await manager.broadcast({
        "type": "break_started",
        "data": {
            "break_end_time": break_end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "energy_to_restore": energy_to_restore
        }
    })
    
    return BreakResponse(
        break_end_time=break_end_time,
        duration_minutes=duration_minutes,
        energy_to_restore=energy_to_restore
    )

@app.post("/api/energy/restore")
async def complete_break(session_id: str = "default"):
    """Complete break early and restore energy"""
    state = get_or_create_energy_state(session_id)
    
    if not state.is_on_break:
        raise HTTPException(status_code=400, detail="Not currently on break")
    
    if not state.break_end_time:
        raise HTTPException(status_code=400, detail="No break end time set")
    
    # Calculate energy to restore based on actual break duration
    actual_duration = (datetime.now() - (state.break_end_time - timedelta(minutes=15))).total_seconds() / 60
    energy_restored = min(
        state.max_energy - state.current_energy,
        max(1, int(actual_duration / 15))
    )
    
    state.current_energy = min(state.max_energy, state.current_energy + energy_restored)
    state.is_on_break = False
    state.break_end_time = None
    
    # Resume regeneration if not at max energy
    if state.current_energy < state.max_energy:
        state.is_regenerating = True
        state.regeneration_paused_at = None
        state.last_regeneration_time = datetime.now()
    
    # Broadcast energy restored
    await manager.broadcast({
        "type": "energy_restored",
        "data": {
            "current_energy": state.current_energy,
            "max_energy": state.max_energy,
            "energy_restored": energy_restored
        }
    })
    
    return {
        "current_energy": state.current_energy,
        "energy_restored": energy_restored,
        "success": True
    }

@app.get("/api/energy/regeneration")
async def get_regeneration_state(session_id: str = "default") -> RegenerationState:
    """Get current regeneration state"""
    state = get_or_create_energy_state(session_id)
    return calculate_regeneration_state(state)

@app.post("/api/energy/regeneration/pause")
async def pause_regeneration(session_id: str = "default"):
    """Pause regeneration when work starts"""
    state = get_or_create_energy_state(session_id)
    
    # Only pause if currently regenerating
    if state.is_regenerating and state.regeneration_paused_at is None and not state.is_on_break:
        state.regeneration_paused_at = datetime.now()
        
        # Broadcast regeneration paused
        regen_state = calculate_regeneration_state(state)
        await manager.broadcast({
            "type": "regeneration_paused",
            "data": {
                "regeneration_time_remaining": regen_state.regeneration_time_remaining,
                "is_regenerating": regen_state.is_regenerating,
                "last_regeneration_time": regen_state.last_regeneration_time.isoformat()
            }
        })
    
    return {"success": True}

@app.post("/api/energy/regeneration/resume")
async def resume_regeneration(session_id: str = "default"):
    """Resume regeneration when work stops"""
    state = get_or_create_energy_state(session_id)
    
    # Only resume if we were paused and not on break
    if state.regeneration_paused_at and not state.is_on_break:
        # Calculate elapsed pause time
        pause_duration = (datetime.now() - state.regeneration_paused_at).total_seconds()
        
        # Adjust last regeneration time to account for pause
        state.last_regeneration_time = state.last_regeneration_time + timedelta(seconds=pause_duration)
        state.regeneration_paused_at = None
        state.is_regenerating = True
        
        # Broadcast regeneration resumed
        regen_state = calculate_regeneration_state(state)
        await manager.broadcast({
            "type": "regeneration_resumed",
            "data": {
                "regeneration_time_remaining": regen_state.regeneration_time_remaining,
                "is_regenerating": regen_state.is_regenerating,
                "last_regeneration_time": regen_state.last_regeneration_time.isoformat()
            }
        })
    
    return {"success": True}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# File watcher for auto-reload
async def watch_file():
    last_mtime = 0
    while True:
        try:
            if TODO_FILE.exists():
                mtime = TODO_FILE.stat().st_mtime
                if mtime > last_mtime:
                    last_mtime = mtime
                    sections = parse_markdown()
                    await manager.broadcast({"type": "file_changed", "data": sections})
        except Exception as e:
            print(f"Watch error: {e}")
        await asyncio.sleep(1)

# Background task for automatic energy regeneration
async def regeneration_task():
    """Background task that checks for energy regeneration every second"""
    while True:
        try:
            # Check all sessions for regeneration
            for session_id, state in list(energy_storage.items()):
                if not state.is_regenerating or state.regeneration_paused_at:
                    continue
                
                # Skip if on break or at max energy
                if state.is_on_break or state.current_energy >= state.max_energy:
                    continue
                
                # Check if it's time to regenerate
                elapsed = (datetime.now() - state.last_regeneration_time).total_seconds()
                if elapsed >= REGENERATION_INTERVAL:
                    # Use lock to ensure thread safety
                    with regeneration_locks.get(session_id, threading.Lock()):
                        # Double-check conditions after acquiring lock
                        if (state.current_energy < state.max_energy and 
                            state.is_regenerating and 
                            not state.regeneration_paused_at and 
                            not state.is_on_break):
                            
                            # Regenerate energy
                            state.current_energy = min(state.max_energy, state.current_energy + REGENERATION_AMOUNT)
                            state.last_regeneration_time = datetime.now()
                            
                            # Broadcast regeneration
                            await manager.broadcast({
                                "type": "energy_regenerated",
                                "data": {
                                    "current_energy": state.current_energy,
                                    "max_energy": state.max_energy,
                                    "energy_regenerated": REGENERATION_AMOUNT,
                                    "session_id": session_id
                                }
                            })
                            
                            # If at max energy, stop regenerating
                            if state.current_energy >= state.max_energy:
                                state.is_regenerating = False
        
        except Exception as e:
            print(f"Regeneration error: {e}")
        
        await asyncio.sleep(1)  # Check every second

# Store background tasks
background_tasks = []

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the app starts"""
    # Start file watcher
    task1 = asyncio.create_task(watch_file())
    background_tasks.append(task1)
    
    # Start regeneration task
    task2 = asyncio.create_task(regeneration_task())
    background_tasks.append(task2)
    
    print("✅ Background tasks started: file watcher, energy regeneration")

@app.on_event("shutdown")
async def shutdown_event():
    """Cancel background tasks when the app shuts down"""
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    print("✅ Background tasks stopped")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)