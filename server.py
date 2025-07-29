#!/usr/bin/env python3
import asyncio
import re
from datetime import datetime, date
from typing import List, Dict, Optional, Set
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

TODO_FILE = Path("todos.md")
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
async def root():
    return FileResponse("index.html")

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

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)