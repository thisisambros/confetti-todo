# CLAUDE.md - Confetti Todo Development Guide

This file guides Claude Code (claude.ai/code) for development in this repository.

## 🚀 QUICK START

### What is Confetti Todo?
A dopamine-driven, ADHD-friendly todo app with gamification. Single-page web app using FastAPI (Python) backend and vanilla JavaScript frontend.

### First Time Setup
```bash
# 1. Activate virtual environment (REQUIRED for ALL Python operations)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 2. Install dependencies
./setup.sh --dev  # Installs everything needed

# 3. Run the app
./run.sh  # Starts at http://localhost:8000
```

**⚠️ Virtual Environment Rule**: After initial activation, assume venv is active. All commands below assume you're in venv.

## 💡 HOW WE WORK

### Core Philosophy
1. **Match existing style** - Study and mirror the codebase's patterns
2. **No default parameters** - Explicit is better than implicit
3. **Do exactly what's asked** - No more, no less
4. **Edit, don't create** - Modify existing files when possible

### Development Workflow
1. **Code** → 2. **Visual Test** → 3. **Write Tests** → 4. **Verify**

Every feature MUST:
- Be visually tested with Playwright MCP
- Have comprehensive tests (90% coverage minimum)
- Pass all existing tests
- Follow existing patterns

### Code Standards
- **Backend**: FastAPI best practices, type hints, docstrings
- **Frontend**: Vanilla JS in index.html, no frameworks
- **Style**: Match existing indentation, naming, structure
- **Comments**: Only when truly necessary

## 📁 WHERE EVERYTHING GOES

```
confetti-todo/
├── server.py              # FastAPI backend
├── index.html             # Frontend (all JS here)
├── assets/
│   └── css/main.css      # Styles
├── tests/                 # ALL tests go here
│   ├── test_*.py         # Test files
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                  # Documentation
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Dev dependencies
└── todos.md              # Data storage (gitignored)
```

### File Rules
- **Tests**: Only in `tests/` directory
- **Docs**: Only in `docs/` directory  
- **Screenshots**: Use `/tmp/` (auto-cleanup)
- **Never in root**: test files, reports, screenshots, pyproject.toml

## 🧪 TESTING

### Structure
```
tests/
├── test_app.py              # Core tests
├── test_*_bug.py            # Bug regressions
├── test_*_e2e.py            # End-to-end
└── integration/test_*.py    # Integration
```

### Commands
```bash
pytest                       # Run all tests
pytest tests/test_app.py -v  # Specific file
pytest -k "pattern"          # Match pattern
pytest --cov=server          # With coverage (90% required)
pytest -n auto               # Parallel execution
```

### Testing Process
1. **Visual Test First**
   ```javascript
   mcp__playwright__playwright_screenshot({
     name: "feature_test",
     downloadsDir: "/tmp",  // REQUIRED
     storeBase64: false,
     savePng: true
   });
   ```
2. **Write Comprehensive Tests**
   - Happy path + edge cases + errors
   - User perspective
   - Maintain 90% coverage

## 🔧 COMMON TASKS

### Development
```bash
python server.py       # Run server
./run.sh              # Alternative with auto-reload
```

### Code Quality
```bash
black .               # Format code
isort .               # Sort imports  
flake8 .              # Lint
mypy server.py        # Type check
```

### Making Changes
1. Study existing patterns first
2. Make changes following those patterns
3. Visual test with Playwright
4. Write/update tests
5. Verify all tests pass

## 📚 TECHNICAL REFERENCE

### Architecture
- **Backend**: FastAPI + WebSocket for real-time sync
- **Frontend**: Vanilla JS SPA, all code in index.html
- **Data**: Markdown file (`todos.md`) with custom format
- **State**: Server (data) + LocalStorage (UI preferences)

### API Endpoints
```
GET  /                      # Serve frontend
GET  /api/todos            # Get all tasks
POST /api/todos            # Save tasks
GET  /api/stats            # User statistics
GET  /api/energy           # Energy state
POST /api/energy/consume   # Use energy
POST /api/energy/break     # Start break
WS   /ws                   # Real-time updates
```

### Task Format
```markdown
- [ ] Task @category !effort %friction ^due-date
  - [x] Subtask
- [x] Done [timestamp]
```

**Properties**:
- Categories: admin, selling, research, product, hiring, other
- Effort: 5m, 15m, 30m, 1h, 4h  
- Friction: 1-3 (affects difficulty/XP)
- Due date: YYYY-MM-DD

### Key Features
- **Energy System**: 12 units max, depletes with work
- **XP Calculation**: effort × friction (1.5x for full completion)
- **Real-time Sync**: WebSocket broadcasts to all clients
- **Animations**: CSS-based confetti celebrations

## 🛠 TOOLS & DEBUGGING

### Specialized Agents
When task matches, use via Task tool:
- `ux-flow-architect` - UI/UX optimization
- `frontend-architect` - Frontend architecture  
- `fastapi-python-craftsman` - Backend development
- `test-engineer-edge-hunter` - Edge case testing

### Debug Guide
| Issue | Check |
|-------|-------|
| WebSocket fails | Browser console + server logs |
| Tasks disappear | Validate todos.md format |
| XP wrong | Check localStorage `confettiTodoStats` |
| Drag & drop | Test cross-browser |

### Performance Tips
- Use DocumentFragment for bulk DOM updates
- Maintain keyboard navigation
- Keep accessibility (ARIA) attributes
- No build process - keep it simple