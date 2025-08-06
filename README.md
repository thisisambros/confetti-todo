# 🎉 Confetti Todo

<div align="center">

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

**A dopamine-driven, ADHD-friendly todo list that celebrates your wins**

[Features](#features) • [Quick Start](#quick-start) • [Usage](#usage) • [Development](#development) • [Contributing](#contributing)

</div>

---

## ✨ Features

### 🎯 Built for ADHD Minds
- **Quick Win Suggestions** - Smart recommendations for easy tasks to build momentum
- **XP & Levels** - Gamified progress tracking with visible rewards on every task
- **Visual Progress** - Instant feedback with confetti animations and XP rewards
- **Friction Indicators** - Know at a glance which tasks are quick vs challenging

### 🚀 Productivity Focused
- **Keyboard-First** - Complete workflows without touching the mouse
- **Real-time Sync** - Edit your markdown file directly, see changes instantly
- **Smart Categories** - Organize by @admin, @product, @selling, @research, @hiring
- **Filtering & Sorting** - View tasks by today, this week, overdue, or sort by XP/effort

### 🛠 Developer Friendly
- **Plain Markdown Storage** - Your data in simple, portable `.md` files
- **No Database Required** - Just Python and a text file
- **Minimal Dependencies** - FastAPI backend, vanilla JS frontend
- **94% Test Coverage** - Comprehensive test suite included

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/thisisambros/confetti-todo.git
cd confetti-todo
```

2. **Run the setup script**
```bash
./setup.py  # All platforms
```

3. **Start the app**
```bash
./run.py  # All platforms
```

4. **Open your browser**
Navigate to http://localhost:8000

## 📖 Usage

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `N` | Add new task |
| `1-5` | Quick select in palette |
| `Tab` | Navigate between palette fields |
| `Enter` | Save |
| `Esc` | Cancel |

### Task Format

Tasks are stored in `todos.md` with this simple format:

```markdown
# today
- [ ] Pay bills @admin !30m %2 ^2025-07-30
  - [x] Find account numbers
  - [ ] Make payments
- [ ] Ship feature @product !2h %3

# ideas
- [ ] ? Research new tools @research

# backlog
- [ ] Plan Q4 roadmap @strategy !4h %2
```

**Metadata:**
- `@category` - Task category (admin, product, selling, research, hiring)
- `!effort` - Time estimate (15m, 30m, 1h, 4h, 1d)
- `%friction` - Difficulty (1=easy, 2=medium, 3=hard)
- `^date` - Due date (YYYY-MM-DD)
- `?` - Marks an idea vs actionable task

## 🔧 Development

### Project Structure
```
confetti-todo/
├── server.py           # FastAPI backend
├── index.html          # Frontend (all-in-one)
├── todos.md            # Your tasks (git-ignored)
├── requirements.txt    # Python dependencies
├── setup.py           # Cross-platform setup script
├── run.py             # Cross-platform run script
└── tests/
    ├── test_app.py         # Main application tests
    ├── test_*_e2e.py       # End-to-end tests
    └── integration/        # Integration tests
```

### Setting Up Development Environment

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

3. **Run tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server

# Run specific test file
pytest tests/test_app.py -v
```

### API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## 🤝 Contributing

We love contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for ADHD-friendly productivity tools
- Design aesthetics from [SatoshiLottery](https://github.com/mrawsky/CryptoCracker)
- Built with [FastAPI](https://fastapi.tiangolo.com/) and vanilla JavaScript
- Confetti animation inspired by celebration-driven development

---

<div align="center">
Made with ❤️ and 🎉 for the ADHD community

⭐ Star this repo if it helps you stay productive!
</div>