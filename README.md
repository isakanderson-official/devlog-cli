# devlog-cli - A minimal, beautiful terminal todo app

[![CI](https://github.com/isakanderson-official/devlog-cli/workflows/CI/badge.svg)](https://github.com/isakanderson-official/devlog-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/isakanderson-official/devlog-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/isakanderson-official/devlog-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A keyboard-driven todo app for developers. Track tasks across workspaces, review daily standups, visualize your productivity with heatmaps. Zero dependencies, works anywhere Python runs.

## Features

- 🎨 **Beautiful TUI** - Clean curses-based interface with vim-style navigation
- 📁 **Workspace Management** - Separate task lists for different projects
- 📅 **Daily Task Tracking** - Navigate through dates, move tasks between days
- 🔍 **Powerful Search** - Find tasks across all dates and workspaces
- 📊 **Visualizations** - Standup view, weekly summary, monthly heatmap
- 🤖 **CLI Mode** - Full command-line interface for automation and LLM integration
- 💾 **Local First** - All data stored in `~/.todo-cli/`, no cloud sync required
- ⚡ **Zero Dependencies** - Only Python standard library, no external packages

## Installation

### macOS (Recommended)

Use [pipx](https://pipx.pypa.io/) to install CLI tools in isolated environments:

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install devlog
pipx install git+https://github.com/isakanderson-official/devlog-cli.git

# Update to latest version
pipx upgrade devlog-cli
```

### Linux / Other

```bash
pip install git+https://github.com/isakanderson-official/devlog-cli.git

# Or with --user flag if you get permission errors
pip install --user git+https://github.com/isakanderson-official/devlog-cli.git
```

### Verify installation

```bash
devlog --help
```

## Quick Start

**Launch interactive mode:**

```bash
devlog
```

**Add tasks via CLI:**

```bash
devlog add "Review pull requests"
devlog add "Update documentation" --date today
```

**List tasks:**

```bash
devlog list --date today
devlog list --date yesterday
devlog list --json  # Machine-readable output
```

**Complete tasks:**

```bash
devlog done <task-id>
```

See [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete CLI documentation.

## TUI Keyboard Shortcuts

| Key             | Action                | Key             | Action                |
| --------------- | --------------------- | --------------- | --------------------- |
| `j` / `↓`       | Move cursor down      | `J` / `Shift+↓` | Move task down        |
| `k` / `↑`       | Move cursor up        | `K` / `Shift+↑` | Move task up          |
| `Enter` / `a`   | Add new todo          | `e`             | Edit task text        |
| `Space`         | Toggle complete       | `d`             | Delete (confirm)      |
| `h` / `←` / `[` | Previous day          | `l` / `→` / `]` | Next day              |
| `Shift+←`       | Move task to prev day | `Shift+→`       | Move task to next day |
| `t`             | Jump to today         | `s`             | Standup view          |
| `w`             | Weekly summary        | `m`             | Monthly heatmap       |
| `/`             | Search all tasks      | `1-9`           | Switch workspace      |
| `W`             | Workspace management  | `q` / `Ctrl-C`  | Quit                  |

### Keybinding Philosophy

- **`Space`** - Toggle completion (universal checkbox convention)
- **`d`** - Delete (TUI convention: vim, ranger, tmux)
- **Vim-style navigation** - `hjkl` for movement, `Shift` for operations

These choices prioritize muscle memory and cross-app consistency for better UX.

## Why devlog?

- **No signup, no sync, no cloud** - Your data stays local in `~/.todo-cli/`
- **Fast and lightweight** - Instant startup, works offline
- **Keyboard-driven** - Optimized for developer workflows
- **Perfect for standups** - Quick daily review with `s` key
- **LLM-friendly** - JSON output mode for automation and AI assistants

## Data Storage

All data is stored locally in your home directory:

- **Config**: `~/.todo-cli/config.json` (workspaces, active workspace)
- **Tasks**: `~/.todo-cli/tasks/{workspace}/{YYYY-MM}.json` (monthly partitioned)

Tasks are stored as JSON with full timestamps, allowing for detailed history and analysis.

## Development

### Quick Start for Contributors

```bash
# Clone the repository
git clone https://github.com/isakanderson-official/devlog-cli.git
cd devlog-cli

# Install with dev dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov --cov-report=html
open htmlcov/index.html
```

### Code Quality Checks

```bash
# Linting
ruff check devlog/

# Formatting
ruff format devlog/

# Type checking
mypy devlog/core/ devlog/cli.py

# Run all checks (what CI runs)
pre-commit run --all-files
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_tasks.py

# With coverage report
pytest --cov --cov-report=html
```

### Project Structure

```
devlog-cli/
├── devlog/               # Main package
│   ├── core/             # Business logic (90%+ test coverage)
│   │   ├── tasks.py      # Task operations
│   │   ├── persistence.py # File I/O
│   │   └── config.py     # Configuration
│   ├── ui/               # UI components (manual testing)
│   │   ├── colors.py
│   │   ├── drawing.py
│   │   └── input.py
│   ├── cli.py            # CLI commands (80%+ coverage)
│   ├── tui.py            # TUI main loop (manual testing)
│   └── views.py          # TUI views (manual testing)
├── tests/                # Test suite
│   ├── unit/             # Unit tests for core modules
│   ├── integration/      # Integration tests for CLI
│   └── fixtures/         # Test data
└── .github/workflows/    # CI/CD pipelines
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Requirements

- **Python 3.8 or higher**
- **Terminal with curses support** (Linux, macOS, BSD)
- **Windows**: Use WSL (Windows Subsystem for Linux)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! This project is in active development. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Quick links:
- Report bugs or request features via [GitHub Issues](https://github.com/isakanderson-official/devlog-cli/issues)
- Submit pull requests with improvements
- Share feedback on the UX and features

All contributions must:
- Pass CI checks (linting, formatting, type checking)
- Include tests for new features
- Maintain or increase code coverage (70%+ target)

---

**Made with ❤️ for developers who live in the terminal**
