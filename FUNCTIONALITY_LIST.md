# Confetti Todo - Complete Functionality List

## Core Task Management
1. **Add Task** - Create new task via input field with Enter key
2. **Complete Task** - Mark task as done via checkbox
3. **Uncomplete Task** - Unmark completed task
4. **Task Metadata** - Add category, effort, friction via palette modal
5. **Task Display** - Show tasks with title, category, effort, friction, XP
6. **Task Progress** - Show subtask completion progress bar
7. **Drag & Drop** - Reorder tasks by dragging

## Subtask Management
8. **Add Subtask** - Create subtask under parent task
9. **Complete Subtask** - Mark subtask as done
10. **Expand/Collapse Subtasks** - Toggle subtask visibility
11. **Subtask XP Bonus** - 1.5x XP when all subtasks completed

## Working Zone
12. **Start Working** - Click "Work on this" to start timer
13. **Stop Working** - Stop working on current task
14. **Working Timer** - Display elapsed time
15. **Complete from Working** - Check task directly from working zone
16. **Switch Task Modal** - Confirm when switching between tasks

## North Star Feature
17. **Set North Star** - Mark task as today's main focus
18. **Remove North Star** - Unset North Star task
19. **North Star Picker** - Choose task from modal
20. **North Star XP Bonus** - 3x XP for North Star tasks
21. **Planning XP** - +25 XP for setting first North Star

## Ideas Management
22. **Add Idea** - Quick capture with 'i' shortcut
23. **Convert Idea to Task** - Transform idea into actionable task
24. **Delete Idea** - Remove unwanted ideas
25. **Collapse Ideas Section** - Toggle ideas visibility

## Search & Filter
26. **Search Tasks** - Morphing search by title/category
27. **Filter by Time** - All/Today/This Week/Overdue
28. **Sort Tasks** - By due date/XP/effort/category
29. **Show More Tasks** - Toggle between top 5 and all

## XP & Gamification
30. **Calculate XP** - Based on effort and friction
31. **Display XP** - Show potential XP per task
32. **Level System** - Progress through levels (500 XP each)
33. **Daily Stats** - Tasks completed and XP earned today
34. **Streak Tracking** - Consecutive days with completions

## UI Features
35. **Confetti Animation** - Celebrate task completion
36. **Completion Sound** - Audio feedback
37. **Toast Messages** - Success/error notifications
38. **Empty States** - Helpful messages when no tasks
39. **Keyboard Shortcuts** - N for new task, I for idea, ESC to cancel

## Data Persistence
40. **Save to Markdown** - Store tasks in todos.md
41. **Auto-reload** - Sync changes from file edits
42. **WebSocket Updates** - Real-time multi-client sync
43. **State Persistence** - Remember North Star & working task
44. **Backup System** - Auto-backup on save

## Task Properties
45. **Categories** - @admin, @selling, @research, @product, @hiring, @other
46. **Effort Levels** - 15m, 30m, 1h, 4h (half-day)
47. **Friction Levels** - 🍃 (1), 💨 (2), 🌪️ (3)
48. **Due Dates** - Task scheduling (visual indicators for overdue/today)
49. **Completion Timestamps** - Track when tasks were completed

## Advanced Features
50. **Quick Win Suggestion** - API endpoint for easy tasks
51. **Category Stats** - Track completion by category
52. **Task Count Display** - Show total and filtered counts
53. **Overdue Highlighting** - Visual indicator for late tasks
54. **Due Today Highlighting** - Visual indicator for today's tasks