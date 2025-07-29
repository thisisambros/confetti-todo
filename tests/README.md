# Confetti Todo Test Suite Documentation

## Overview

This document provides comprehensive information about the test suite for the Confetti Todo application. The test suite includes unit tests, integration tests, and end-to-end tests covering all 54 functionalities of the application.

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── frontend/           # JavaScript unit tests
│   │   ├── taskManager.test.js
│   │   ├── uiManager.test.js
│   │   ├── apiService.test.js
│   │   ├── paletteManager.test.js
│   │   ├── workingZoneManager.test.js
│   │   ├── northStarManager.test.js
│   │   ├── audioUtils.test.js
│   │   └── storageUtils.test.js
│   └── backend/            # Python unit tests
│       └── test_server.py
├── e2e/                    # End-to-end tests
│   ├── features/          # Organized by feature area
│   │   ├── 01-core-task-management.spec.js
│   │   ├── 02-subtask-management.spec.js
│   │   ├── 03-working-zone.spec.js
│   │   ├── 04-north-star.spec.js
│   │   ├── 05-ideas-management.spec.js
│   │   ├── 06-search-filter.spec.js
│   │   ├── 07-xp-gamification.spec.js
│   │   ├── 08-ui-features.spec.js
│   │   ├── 09-data-persistence.spec.js
│   │   ├── 10-task-properties.spec.js
│   │   └── 11-advanced-features.spec.js
│   ├── pages/             # Page Object Models
│   │   └── TodoPage.js
│   └── helpers/           # Test utilities
│       ├── global-setup.js
│       └── global-teardown.js
├── integration/           # Integration tests
└── fixtures/             # Test data
```

## Running Tests

### Prerequisites

1. Install Node.js (v16 or higher)
2. Install Python (3.9 or higher)
3. Install dependencies:
   ```bash
   npm install
   pip install -r requirements-dev.txt
   ```

### Running All Tests

```bash
# Run all tests with a single command
npm test

# Or run frontend and backend tests separately
npm run test:unit        # Frontend unit tests
npm run test:e2e        # E2E tests
pytest                  # Backend tests
```

### Running Specific Test Suites

#### Frontend Unit Tests (Jest)

```bash
# Run all unit tests
npm run test:unit

# Run tests in watch mode
npm run test:unit:watch

# Run with coverage
npm run test:unit -- --coverage

# Run specific test file
npm run test:unit taskManager.test.js

# Run tests matching pattern
npm run test:unit -- --testNamePattern="calculateXP"
```

#### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test file
npx playwright test 01-core-task-management.spec.js

# Run specific test
npx playwright test -g "Add Task"

# Run on specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run tests in parallel
npx playwright test --workers=4
```

#### Backend Tests (Pytest)

```bash
# Run all backend tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/backend/test_server.py

# Run specific test
pytest -k "test_add_task"

# Run with coverage
pytest --cov=server --cov-report=html

# Run in parallel
pytest -n auto
```

### Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Manual workflow dispatch

## Test Coverage

### Coverage Requirements

- **Overall**: 90% minimum
- **Branches**: 90% minimum
- **Functions**: 90% minimum
- **Lines**: 90% minimum
- **Statements**: 90% minimum

### Viewing Coverage Reports

```bash
# Generate and view frontend coverage
npm run test:coverage
open coverage/lcov-report/index.html

# Generate and view backend coverage
pytest --cov=server --cov-report=html
open htmlcov/index.html

# Upload to Codecov (in CI)
codecov --token=$CODECOV_TOKEN
```

## Test Categories

### 1. Core Task Management (Tests 1-7)
- Add Task
- Complete Task
- Uncomplete Task
- Task Metadata
- Task Display
- Task Progress
- Drag & Drop

### 2. Subtask Management (Tests 8-11)
- Add Subtask
- Complete Subtask
- Expand/Collapse Subtasks
- Subtask XP Bonus

### 3. Working Zone (Tests 12-16)
- Start Working
- Stop Working
- Working Timer
- Complete from Working
- Switch Task Modal

### 4. North Star Feature (Tests 17-21)
- Set North Star
- Remove North Star
- North Star Picker
- North Star XP Bonus
- Planning XP

### 5. Ideas Management (Tests 22-25)
- Add Idea
- Convert Idea to Task
- Delete Idea
- Collapse Ideas Section

### 6. Search & Filter (Tests 26-29)
- Search Tasks
- Filter by Time
- Sort Tasks
- Show More Tasks

### 7. XP & Gamification (Tests 30-34)
- Calculate XP
- Display XP
- Level System
- Daily Stats
- Streak Tracking

### 8. UI Features (Tests 35-39)
- Confetti Animation
- Completion Sound
- Toast Messages
- Empty States
- Keyboard Shortcuts

### 9. Data Persistence (Tests 40-44)
- Save to Markdown
- Auto-reload
- WebSocket Updates
- State Persistence
- Backup System

### 10. Task Properties (Tests 45-49)
- Categories
- Effort Levels
- Friction Levels
- Due Dates
- Completion Timestamps

### 11. Advanced Features (Tests 50-54)
- Quick Win Suggestion
- Category Stats
- Task Count Display
- Overdue Highlighting
- Due Today Highlighting

## Writing New Tests

### Unit Test Example

```javascript
// Frontend unit test
describe('TaskManager', () => {
  let taskManager;
  
  beforeEach(() => {
    taskManager = new TaskManager();
  });
  
  test('should calculate XP correctly', () => {
    const task = {
      effort: '1h',
      friction: 2
    };
    
    const xp = taskManager.calculateXP(task);
    expect(xp).toBe(75); // 50 base * 1.5 friction
  });
});
```

```python
# Backend unit test
def test_add_task():
    response = client.post("/add", json={
        "title": "New task",
        "category": "admin"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "New task"
```

### E2E Test Example

```javascript
test('should add a new task', async ({ page }) => {
  const todoPage = new TodoPage(page);
  await todoPage.goto();
  
  await todoPage.addTask('New task');
  await todoPage.savePaletteDefaults();
  
  const task = await todoPage.getTask('New task');
  await expect(task).toBeVisible();
});
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Page Objects**: Use POM for E2E tests
5. **Mock External Dependencies**: Use mocks for APIs
6. **Test Data**: Use fixtures for consistent data
7. **Parallel Execution**: Tests should run in parallel
8. **Cleanup**: Always clean up after tests
9. **Assertions**: Use specific assertions
10. **Error Cases**: Test both success and failure paths

## Debugging Tests

### Jest (Frontend)

```bash
# Debug specific test
node --inspect-brk node_modules/.bin/jest --runInBand taskManager.test.js

# Use VS Code debugger with launch.json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand", "${file}"]
}
```

### Playwright (E2E)

```bash
# Debug mode
npx playwright test --debug

# Show browser
npx playwright test --headed

# Slow down execution
npx playwright test --slow-mo=1000

# Generate trace
npx playwright test --trace on
```

### Pytest (Backend)

```bash
# Debug with pdb
pytest -s --pdb

# Show print statements
pytest -s

# Verbose output
pytest -vv
```

## CI/CD Integration

Tests are integrated into the CI/CD pipeline:

1. **Linting**: Code quality checks
2. **Unit Tests**: Fast feedback on code changes
3. **Integration Tests**: API and database tests
4. **E2E Tests**: Full user flow validation
5. **Security Scans**: Vulnerability detection
6. **Coverage Reports**: Track test coverage

## Performance Testing

For performance-critical features:

```javascript
test('should handle 1000 tasks efficiently', async ({ page }) => {
  // Measure time to render many tasks
  const startTime = Date.now();
  
  for (let i = 0; i < 1000; i++) {
    await todoPage.addTask(`Task ${i}`);
  }
  
  const renderTime = Date.now() - startTime;
  expect(renderTime).toBeLessThan(30000); // 30 seconds max
});
```

## Accessibility Testing

E2E tests include accessibility checks:

```javascript
test('should be keyboard navigable', async ({ page }) => {
  // Tab through interface
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toHaveAttribute('id', 'task-input');
  
  // Check ARIA attributes
  await expect(modal).toHaveAttribute('role', 'dialog');
  await expect(modal).toHaveAttribute('aria-modal', 'true');
});
```

## Maintenance

1. **Update tests** when features change
2. **Review coverage** regularly
3. **Refactor tests** to reduce duplication
4. **Update dependencies** monthly
5. **Monitor CI performance**
6. **Archive old test data**

## Troubleshooting

### Common Issues

1. **Flaky Tests**: Add proper waits and retries
2. **Port Conflicts**: Ensure ports 8000 are free
3. **Browser Issues**: Update Playwright browsers
4. **Module Errors**: Clear node_modules and reinstall
5. **Python Path**: Use virtual environment

### Getting Help

1. Check test output for detailed errors
2. Review CI logs for failures
3. Use debug mode for complex issues
4. Check browser console in E2E tests
5. Enable verbose logging

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Add to appropriate test file
4. Update this documentation
5. Check coverage remains >90%