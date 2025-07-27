# Contributing to Confetti Todo

First off, thank you for considering contributing to Confetti Todo! 🎉

This project aims to help people with ADHD manage their tasks more effectively, and your contributions can make a real difference in people's daily productivity.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **System information** (OS, Python version, browser)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Use case** - Why is this enhancement needed?
- **Proposed solution** - How do you envision it working?
- **Alternatives considered** - What other solutions did you think about?
- **Additional context** - Mockups, examples, etc.

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Simple issues perfect for beginners
- `help wanted` - Issues where we need community help
- `documentation` - Help improve our docs

## Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/yourusername/confetti-todo.git
cd confetti-todo
```

2. **Set up development environment**
```bash
./setup.sh --dev  # or python setup.py --dev
```

3. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

4. **Make your changes**
- Write clean, readable code
- Add tests for new functionality
- Update documentation as needed

5. **Run tests**
```bash
./test.sh  # or python test.py
```

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where appropriate
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

```python
# Good
def calculate_xp(task: Dict[str, Any]) -> int:
    """Calculate XP points based on task effort and friction."""
    effort_minutes = parse_effort(task.get("effort", "30m"))
    friction = task.get("friction", 2)
    return round(100 * (1 + effort_minutes / 60) ** 0.5 * friction)

# Bad
def calc_xp(t):
    m = get_mins(t.get("effort", "30m"))
    f = t.get("friction", 2)
    return round(100 * (1 + m / 60) ** 0.5 * f)
```

### JavaScript Code Style

- Use modern ES6+ features
- Prefer `const` over `let`, avoid `var`
- Use meaningful function and variable names
- Add JSDoc comments for functions

```javascript
// Good
const showConfetti = () => {
    const container = document.getElementById('confetti-container');
    container.innerHTML = '';
    
    for (let i = 0; i < CONFETTI_COUNT; i++) {
        const piece = createConfettiPiece();
        container.appendChild(piece);
    }
};

// Bad
function conf() {
    var c = document.getElementById('confetti-container');
    c.innerHTML = '';
    for (var i = 0; i < 120; i++) {
        var p = document.createElement('div');
        // ...
    }
}
```

### CSS Style Guide

- Use CSS custom properties for theming
- Follow BEM naming convention where applicable
- Mobile-first approach
- Keep specificity low

```css
/* Good */
.task-item {
    display: flex;
    padding: var(--spacing-sm);
}

.task-item--completed {
    opacity: 0.6;
}

/* Bad */
#today-tasks > li.task-item.completed {
    display: flex !important;
}
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add keyboard shortcut for quick task entry
fix: correct XP calculation for subtasks
docs: update README with new setup instructions
test: add coverage for markdown parsing edge cases
```

## Pull Request Process

1. **Ensure all tests pass**
```bash
./test.sh
```

2. **Update documentation**
- Update README.md if needed
- Add/update code comments
- Update CHANGELOG.md

3. **Create Pull Request**
- Use a clear PR title
- Reference any related issues
- Provide a detailed description
- Include screenshots for UI changes

4. **Code Review**
- Address review comments promptly
- Be open to feedback
- Ask questions if something is unclear

5. **Merge**
- PRs require at least one approval
- Squash commits if requested
- Delete your branch after merge

## Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Aim for high test coverage (>90%)
- Test edge cases and error conditions
- Use descriptive test names

```python
def test_calculate_xp_with_completed_subtasks():
    """Test that completed subtasks provide XP bonus."""
    task = {
        'effort': '30m',
        'friction': 2,
        'subtasks': [
            {'is_completed': True},
            {'is_completed': True}
        ]
    }
    xp = calculate_xp(task)
    assert xp == 367  # Base 245 * 1.5 bonus
```

### Running Tests

```bash
# All tests
./test.sh

# Backend only
pytest tests/test_server.py -v

# Frontend
open tests/test_frontend.html

# E2E tests (requires running server)
pytest tests/test_e2e.py -v
```

## Documentation

- Keep documentation up-to-date
- Use clear, simple language
- Include code examples
- Document breaking changes

## Questions?

Feel free to:
- Open an issue for questions
- Join our discussions
- Reach out to maintainers

Thank you for contributing to Confetti Todo! 🎉