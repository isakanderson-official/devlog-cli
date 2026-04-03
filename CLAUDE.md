# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimal, beautiful terminal-based todo app written in Python using the curses library. The app features a clean TUI with keyboard-driven navigation, workspace management, task tracking across days, and visualization features (standup view, weekly summary, monthly heatmap). It also includes a full CLI mode for programmatic access and LLM integration.

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/isakanderson-official/devlog-cli.git
```

For development, use editable install:

```bash
git clone <repo-url>
cd devlog-cli
pip install -e .
```

## Running the Application

**TUI Mode** (interactive interface):

```bash
devlog
```

**CLI Mode** (command-line operations):

```bash
# List tasks
devlog list --date today

# Add task
devlog add "Task description" --date today

# Mark as done
devlog done <task-id>

# JSON output for programmatic access
devlog --json list
```

**Development mode** (running from source without install):

```bash
python3 devlog-cli.py
```

The app runs as a thin wrapper (`devlog-cli.py`) that imports the `devlog` package. No external dependencies beyond the standard library.

## Architecture

### Package Structure

The codebase is organized into a modular package structure optimized for maintainability and AI agent editing:

```
devlog-cli/
├── devlog-cli.py              # Thin entry point wrapper
├── devlog/                   # Main package
│   ├── __init__.py           # Package entry point with run()
│   ├── core/                 # Business logic layer
│   │   ├── persistence.py    # File I/O and monthly task management (~120 lines)
│   │   ├── tasks.py          # Task model and operations (~90 lines)
│   │   └── config.py         # Configuration management (~40 lines)
│   ├── ui/                   # User interface layer
│   │   ├── colors.py         # Color definitions and initialization (~50 lines)
│   │   ├── drawing.py        # Safe drawing helpers and rendering (~150 lines)
│   │   └── input.py          # Text input widget (~60 lines)
│   ├── views.py              # Modal views (standup, weekly, heatmap, etc.) (~450 lines)
│   ├── cli.py                # CLI commands and parser (~600 lines)
│   └── tui.py                # Main TUI loop and event handling (~260 lines)
```

**Key Benefits:**

- **Separation of concerns**: Core business logic (persistence, tasks, config) is independent of UI
- **Testability**: Core layer can be tested without curses/UI
- **AI-friendly**: Files average 100-200 lines, optimal for AI context windows
- **Clear boundaries**: Each module has a single, well-defined responsibility

### Import Paths

```python
# Core layer
from devlog.core import persistence, tasks, config
from devlog.core.persistence import get_tasks, set_tasks
from devlog.core.tasks import gen_id, find_task, nav_order
from devlog.core.config import load_config, save_config

# UI layer
from devlog.ui import colors, drawing, input
from devlog.ui.colors import init_colors, C_GREEN, C_CYAN
from devlog.ui.drawing import draw_tasks, saddstr

# Views and main modules
from devlog import views, cli, tui
```

### Data Storage

The app uses a file-based storage system:

- **Config file**: `~/.todo-cli/config.json` - stores workspace list, active workspace, and schema version
- **Task files**: `~/.todo-cli/tasks/{workspace}/{YYYY-MM}.json` - monthly task files organized by workspace
- **Schema version**: Currently at version 2 with automatic migration from old flat-file format

### Data Model

Tasks are stored with the following fields:

- `id`: 8-character hex UUID for unique identification
- `text`: Task description
- `done`: Boolean completion status
- `position`: Integer for ordering within done/todo groups
- `created_at`: ISO timestamp of creation
- `completed_at`: ISO timestamp when marked complete (null if not done)

### Key Architecture Patterns

1. **Monthly partitioning**: Tasks are stored in separate JSON files per workspace per month (`YYYY-MM.json`), reducing file I/O and allowing efficient loading of specific date ranges

2. **Atomic writes**: All file writes use a temp-file-then-rename pattern (`_atomic_write()`) to prevent data corruption

3. **Position-based ordering**: Tasks maintain explicit `position` fields that are renormalized after each change via `reposition()`, with separate ordering for TODO and DONE groups

4. **Navigation order**: Display order is computed on-demand via `nav_order()` which returns task IDs in display sequence (todos first by position, then dones by position)

5. **Cursor by ID**: The cursor tracks task IDs rather than indices, allowing stable cursor position across reorders and edits

### Core Modules

**Core Layer** (`devlog/core/`):

- **persistence.py**: File I/O, monthly task file management (`get_tasks`, `set_tasks`, `load_month`, `save_month`)
- **tasks.py**: Task model and operations (`gen_id`, `find_task`, `reposition`, `nav_order`)
- **config.py**: Configuration management (`load_config`, `save_config`, `active_ws_name`)

**UI Layer** (`devlog/ui/`):

- **colors.py**: Color pair definitions and `init_colors()`
- **drawing.py**: Safe drawing helpers (`saddstr`, `fill_line`) and rendering functions (`draw_tasks`, `draw_header`, `draw_footer`)
- **input.py**: Text input widget (`text_input()`)

**Top-level Modules**:

- **views.py**: Modal views (standup, weekly summary, heatmap, search, workspace management)
- **cli.py**: CLI command implementations and argument parser
- **tui.py**: Main TUI event loop and keyboard handling

### Important Functions

**Core layer:**

- `persistence.get_tasks(ws_name, dt)` / `set_tasks(ws_name, dt, tasks)`: Load/save tasks for a specific date
- `tasks.find_task(tasks, task_id)`: Locate task by ID, returns (index, task) tuple
- `tasks.reposition(tasks)`: Normalize position values to 0, 1, 2... within done/todo groups
- `tasks.nav_order(tasks)`: Compute display order as list of task IDs

**UI layer:**

- `input.text_input(scr, y, x, prompt, prefill="")`: Inline text editor for adding/editing tasks
- `drawing.saddstr(scr, y, x, text, attr)`: Safe string drawing that handles boundaries
- `drawing.draw_tasks(scr, tasks, cursor, start_y, h, w)`: Render the task list

## Key Technical Details

### Keybinding Design Philosophy

The keybindings follow established TUI conventions to minimize cognitive load and leverage existing muscle memory:

**Core Actions:**

- `Space` - Toggle task completion
  - **Rationale**: Universal checkbox convention across all GUI and TUI interfaces. Users expect Space to toggle checkboxes.
  - **Cross-app consistency**: Works the same in web forms, native apps, and terminal UIs.

- `d` - Delete task (with confirmation)
  - **Rationale**: Strong convention in terminal apps (vim's `dd`, ranger file manager, tmux, etc.)
  - **Muscle memory**: Users familiar with any TUI will instinctively use `d` for delete/destroy operations.
  - **Why not `x`**: While vim uses `x` for character deletion, `d` is the stronger mnemonic for "delete entire item."

- `e` - Edit task text
  - **Rationale**: Standard edit mnemonic, consistent with vim and other editors.

**Navigation:**

- `j/k` or arrow keys for vertical movement (vim-style navigation)
- `h/l` or arrow keys for date navigation (vim-style horizontal movement)
- `J/K` (Shift) for reordering tasks
- `Shift+arrows` for moving tasks between dates

**Why these conventions matter:**

- Users shouldn't have to re-learn basic operations
- Consistency reduces errors and increases efficiency
- Terminal power users expect vim-like keybindings

### Curses Color Pairs

The app defines color pairs (C_GREEN, C_GREY, C_CURSOR_BG, etc.) in `init_colors()`. All drawing must use `curses.color_pair()` with these constants.

### Safe Drawing

Always use `saddstr()` instead of raw `scr.addstr()` to prevent crashes when text exceeds screen bounds. The `fill_line()` helper fills an entire row with an attribute.

### Text Wrapping

Task text is wrapped using `wrap_text()` which uses Python's `textwrap` module. Each wrapped line is drawn separately in the rendering loop.

### Keyboard Handling

The main loop uses `scr.get_wch()` to handle both regular characters and special keys (arrows, function keys). Key comparisons must handle both string characters and curses key constants.

## Code Conventions

- Task operations always work with task IDs, never indices directly
- After any task list modification, call `set_tasks()` which automatically calls `reposition()`
- The cursor variable stores a task ID (string), not an index
- Date keys are formatted as "YYYY-MM-DD" via the `date_key()` helper
- All user-facing strings use simple ASCII characters; Unicode symbols (✓, •, →) are only for UI chrome

## CLI Mode for LLM Integration

The CLI mode is designed for programmatic access and integration with LLMs like Claude Code. Key features:

### Command Structure

```bash
devlog [--json] [-w WORKSPACE] <command> [args]
```

For development (running from source):

```bash
python3 devlog-cli.py [--json] [-w WORKSPACE] <command> [args]
```

Available commands: `list`, `add`, `done`, `undone`, `delete`, `edit`, `search`, `stats`, `export`, `import`

### Date Parsing

The `parse_date()` function accepts:

- `today`, `now` - current day
- `tomorrow` - next day
- `yesterday` - previous day
- `YYYY-MM-DD` - specific date

### JSON Output

Use `--json` flag before the command for machine-readable output. All CLI commands support JSON output for easy parsing and integration.

### Bulk Operations

Import/export commands support markdown format with checkbox syntax:

```markdown
- [ ] Pending task
- [x] Completed task
```

Import from stdin using `-` as filename for seamless integration with pipes and command substitution.

### Workspace Operations

Use `-w WORKSPACE` to operate on specific workspaces. If not specified, uses the active workspace from config.

### Idempotent Operations

Commands like `done` and `undone` succeed even if the task is already in that state, making automation more reliable.

### Task ID Resolution

Most commands that take a task ID will search across all dates if `--date` is not specified, making it easier to operate on tasks without knowing their exact date.
