"""Safe drawing helpers and rendering functions for the TUI."""

import curses
import textwrap
from datetime import datetime, timedelta
from .colors import (
    C_GREEN, C_GREY, C_WHITE, C_DIM, C_CURSOR_BG,
    C_CYAN, C_CURSOR_GREEN, C_YELLOW, C_WS_ACTIVE, C_WS_DIM
)
from ..core.config import DEFAULT_WORKSPACES


# ── Safe drawing helpers ─────────────────────────────────────────────────────

def saddstr(scr, y, x, text, attr=0):
    """Safely add a string to the screen, handling boundary conditions."""
    h, w = scr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    text = text[: w - x]
    try:
        scr.addstr(y, x, text, attr)
    except curses.error:
        pass


def fill_line(scr, y, attr):
    """Fill an entire line with a specific attribute."""
    h, w = scr.getmaxyx()
    try:
        scr.addstr(y, 0, " " * (w - 1), attr)
    except curses.error:
        pass


def wrap_text(text, width):
    """Wrap text to fit within a given width."""
    if width < 4:
        return [text]
    lines = textwrap.wrap(text, width=width, break_long_words=True,
                          break_on_hyphens=True)
    return lines if lines else [""]


# ── Rendering functions ──────────────────────────────────────────────────────

def draw_workspace_bar(scr, config, w):
    """Draw workspace tabs at the very top (row 0)."""
    wsl = config.get("workspaces", DEFAULT_WORKSPACES)
    active = config.get("active_workspace", "Personal")
    x = 1
    for i, name in enumerate(wsl):
        if x >= w - 4:
            break
        label = f" {i + 1}:{name} "
        if name == active:
            saddstr(scr, 0, x, label, curses.color_pair(C_WS_ACTIVE) | curses.A_BOLD)
        else:
            saddstr(scr, 0, x, label, curses.color_pair(C_WS_DIM))
        x += len(label) + 1


def draw_header(scr, dt, w):
    """Draw the date header."""
    today = datetime.now().date()
    d = dt.date() if isinstance(dt, datetime) else dt

    if d == today:
        label = "Today"
    elif d == today - timedelta(days=1):
        label = "Yesterday"
    elif d == today + timedelta(days=1):
        label = "Tomorrow"
    else:
        label = dt.strftime("%A, %b %-d")

    cx = max(0, (w - len(label)) // 2)
    saddstr(scr, 2, cx, label, curses.color_pair(C_CYAN) | curses.A_BOLD)

    saddstr(scr, 2, 2, "←", curses.color_pair(C_DIM))
    saddstr(scr, 2, w - 3, "→", curses.color_pair(C_DIM))
    saddstr(scr, 4, 0, "─" * (w - 1), curses.color_pair(C_DIM))


def draw_tasks(scr, tasks, cursor, start_y, h, w):
    """Draw tasks with text wrapping, sorted by position."""
    todos = sorted([t for t in tasks if not t.get("done")], key=lambda t: t.get("position", 0))
    dones = sorted([t for t in tasks if t.get("done")], key=lambda t: t.get("position", 0))

    y = start_y
    max_y = h - 3
    text_col = 7
    wrap_w = w - text_col - 2

    # TODO section
    saddstr(scr, y, 2, f"TODO ({len(todos)})", curses.color_pair(C_DIM))
    y += 2

    if not todos:
        saddstr(scr, y, 5, "No tasks — press Enter to add", curses.color_pair(C_DIM))
        y += 1

    for task in todos:
        if y >= max_y:
            break
        is_cur = (task.get("id") == cursor)
        text = task["text"]
        lines = wrap_text(text, wrap_w)

        for li, line in enumerate(lines):
            if y >= max_y:
                break
            if is_cur:
                fill_line(scr, y, curses.color_pair(C_CURSOR_BG))
                if li == 0:
                    saddstr(scr, y, 4, "○", curses.color_pair(C_CURSOR_BG))
                saddstr(scr, y, text_col, line, curses.color_pair(C_CURSOR_BG))
            else:
                if li == 0:
                    saddstr(scr, y, 4, "○", curses.color_pair(C_WHITE))
                saddstr(scr, y, text_col, line, curses.color_pair(C_WHITE))
            y += 1
        y += 1

    y += 1

    # DONE section
    if y < max_y:
        saddstr(scr, y, 2, f"DONE ({len(dones)})", curses.color_pair(C_DIM))
        y += 2

    for task in dones:
        if y >= max_y:
            break
        is_cur = (task.get("id") == cursor)
        text = task["text"]
        lines = wrap_text(text, wrap_w)

        for li, line in enumerate(lines):
            if y >= max_y:
                break
            if is_cur:
                fill_line(scr, y, curses.color_pair(C_CURSOR_BG))
                if li == 0:
                    saddstr(scr, y, 4, "✓", curses.color_pair(C_CURSOR_GREEN))
                saddstr(scr, y, text_col, line, curses.color_pair(C_CURSOR_BG))
            else:
                if li == 0:
                    saddstr(scr, y, 4, "✓", curses.color_pair(C_GREEN))
                saddstr(scr, y, text_col, line, curses.color_pair(C_GREY))
            y += 1
        y += 1


def draw_footer(scr, h, w, mode="normal"):
    """Draw the footer with keyboard hints."""
    y = h - 2
    saddstr(scr, y, 0, "─" * (w - 1), curses.color_pair(C_DIM))
    y = h - 1

    if mode == "normal":
        hints = [
            ("Enter", "new"), ("Space", "done"), ("e", "edit"),
            ("d", "del"), ("J/K/S-↑↓", "reorder"),
            ("←→", "day"), ("S-←→", "move task"),
            ("/", "search"), ("m", "heatmap"),
            ("1-9", "ws"), ("W", "ws mgmt"), ("q", "quit"),
        ]
    elif mode == "standup":
        hints = [("q", "back")]
    elif mode == "weekly":
        hints = [("q", "back")]
    elif mode == "heatmap":
        hints = [("h/l", "month"), ("q", "back")]
    elif mode == "search":
        hints = [("j/k", "nav"), ("Enter", "go"), ("q", "back")]
    elif mode == "ws_manage":
        hints = [("j/k", "nav"), ("Enter", "switch"), ("a", "add"), ("r", "rename"), ("d", "delete"), ("Esc", "back")]
    else:
        hints = [("Esc", "cancel")]

    x = 1
    for key, label in hints:
        if x >= w - 4:
            break
        saddstr(scr, y, x, key, curses.color_pair(C_YELLOW) | curses.A_BOLD)
        x += len(key) + 1
        saddstr(scr, y, x, label, curses.color_pair(C_DIM))
        x += len(label) + 2


__all__ = [
    'saddstr', 'fill_line', 'wrap_text',
    'draw_workspace_bar', 'draw_header', 'draw_tasks', 'draw_footer'
]
