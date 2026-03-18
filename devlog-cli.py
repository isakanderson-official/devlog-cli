#!/usr/bin/env python3
"""
devlog-cli — A minimal, beautiful terminal todo app.

Keys:
  j / ↓          Move cursor down          J / Shift+↓    Move task down
  k / ↑          Move cursor up            K / Shift+↑    Move task up
  Enter / a      Add new todo              e              Edit task text
  Space          Toggle complete           d              Delete (confirm)
  h / ← / [      Previous day              l / → / ]      Next day
  Shift+←        Move task to prev day     Shift+→        Move task to next day
  t              Jump to today              s              Standup view
  w              Weekly summary             m              Monthly heatmap
  /              Search all tasks           1-9            Switch workspace
  W              Workspace management       q / Ctrl-C     Quit

Keybinding Design Philosophy:
  Space → Toggle complete (universal checkbox convention across all interfaces)
  d     → Delete (strong TUI convention: vim, ranger, most terminal apps)
  These choices prioritize muscle memory and cross-app consistency for better UX.

Usage:
    devlog                          # Launch TUI (after pip install)
    devlog list                     # CLI commands

    # OR for development:
    python3 devlog-cli.py           # Launch TUI from source
    python3 devlog-cli.py list      # CLI commands from source
"""

import locale
locale.setlocale(locale.LC_ALL, "")

from devlog import run

if __name__ == "__main__":
    run()
