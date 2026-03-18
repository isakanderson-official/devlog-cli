# devlog-cli - A minimal, beautiful terminal todo app

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

**Install from GitHub:**

```bash
pip install git+https://github.com/isakanderson-official/devlog-cli.git
```

**Verify installation:**

```bash
devlog --help
```

**Update to latest version:**

```bash
pip install --upgrade git+https://github.com/isakanderson-official/devlog-cli.git
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

**Editable install for contributors:**

```bash
git clone https://github.com/isakanderson-official/devlog-cli.git
cd devlog-cli
pip install -e .
```

Now you can edit the code and test changes immediately:

```bash
devlog  # Runs from your local checkout
```

**Project structure:**

```
devlog-cli/
├── devlog/            # Main package
│   ├── core/          # Data model and persistence
│   ├── ui/            # Curses drawing and input
│   ├── cli.py         # CLI commands
│   ├── tui.py         # TUI main loop
│   └── views.py       # Modal views (standup, weekly, etc)
├── devlog-cli.py      # Entry point script (for development)
└── pyproject.toml     # Package configuration
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

## Requirements

- **Python 3.8 or higher**
- **Terminal with curses support** (Linux, macOS, BSD)
- **Windows**: Use WSL (Windows Subsystem for Linux)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! This project is in active development. Feel free to:

- Report bugs or request features via [GitHub Issues](https://github.com/isakanderson-official/devlog-cli/issues)
- Submit pull requests with improvements
- Share feedback on the UX and features

---

**Made with ❤️ for developers who live in the terminal**
