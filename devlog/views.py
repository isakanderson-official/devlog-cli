"""Modal views: standup, weekly summary, heatmap, search, workspace management."""

import calendar
import curses
import platform
import shutil
import subprocess
from datetime import datetime, timedelta

from .core.config import (
    DEFAULT_WORKDAYS,
    DEFAULT_WORKSPACES,
    get_workdays,
    previous_workday,
    save_config,
)
from .core.persistence import TASKS_DIR, get_tasks, load_all_ws_tasks, load_month
from .ui.colors import (
    C_CURSOR_BG,
    C_CURSOR_GREEN,
    C_CYAN,
    C_DIM,
    C_GREEN,
    C_GREY,
    C_HEAT_1,
    C_HEAT_2,
    C_HEAT_3,
    C_HEAT_4,
    C_RED,
    C_WHITE,
)
from .ui.drawing import draw_footer, fill_line, saddstr
from .ui.input import text_input

# ── Clipboard utilities ──────────────────────────────────────────────────────


def copy_to_clipboard(text):
    """Copy text to system clipboard. Returns True on success, False on failure."""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        elif system == "Linux":
            # Try xclip first, then xsel
            try:
                process = subprocess.Popen(
                    ["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE
                )
                process.communicate(text.encode("utf-8"))
                return process.returncode == 0
            except FileNotFoundError:
                process = subprocess.Popen(
                    ["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE
                )
                process.communicate(text.encode("utf-8"))
                return process.returncode == 0
        elif system == "Windows":
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        return False
    except Exception:
        return False


# ── Standup view ─────────────────────────────────────────────────────────────


def show_standup(scr, ws_name, config=None):
    """Show standup view with previous workday's completed and today's todos + done."""
    h, w = scr.getmaxyx()
    today = datetime.now()
    workdays = get_workdays(config) if config else DEFAULT_WORKDAYS
    prev_day = previous_workday(today, workdays)

    y_done = [t for t in get_tasks(ws_name, prev_day) if t.get("done")]
    today_tasks = get_tasks(ws_name, today)
    t_todo = [t for t in today_tasks if not t.get("done")]
    t_done = [t for t in today_tasks if t.get("done")]

    message = ""  # For showing copy confirmation or errors
    message_color = C_GREEN

    while True:
        scr.clear()
        saddstr(scr, 1, max(0, (w - 7) // 2), "Standup", curses.color_pair(C_CYAN) | curses.A_BOLD)
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        y = 5
        if (today - prev_day).days == 1:
            prev_label = "Yesterday"
        else:
            prev_label = prev_day.strftime("%A, %b %-d")
        saddstr(scr, y, 3, f"{prev_label} — completed ({len(y_done)})", curses.color_pair(C_DIM))
        y += 2
        for t in y_done:
            if y >= h - 4:
                break
            saddstr(scr, y, 5, "✓  " + t["text"], curses.color_pair(C_GREEN))
            y += 1

        y += 2
        saddstr(
            scr,
            y,
            3,
            f"Today — to do ({len(t_todo)}), done ({len(t_done)})",
            curses.color_pair(C_DIM),
        )
        y += 2

        # Show todo tasks first
        for t in t_todo:
            if y >= h - 4:
                break
            saddstr(scr, y, 5, "•  " + t["text"], curses.color_pair(C_WHITE))
            y += 1

        # Then show done tasks
        for t in t_done:
            if y >= h - 4:
                break
            saddstr(scr, y, 5, "✓  " + t["text"], curses.color_pair(C_GREEN))
            y += 1

        # Show message if present
        if message:
            msg_y = h - 3
            msg_x = max(0, (w - len(message)) // 2)
            saddstr(scr, msg_y, msg_x, message, curses.color_pair(message_color))

        draw_footer(scr, h, w, "standup")
        scr.refresh()
        ch = scr.getch()

        # Clear message after any keypress
        if message:
            message = ""

        if ch in (ord("q"), ord("Q"), 27):
            break
        elif ch == ord("c"):
            # Format standup text for Slack
            lines = []
            lines.append(f"*{prev_label}*")
            for t in y_done:
                lines.append(f"✓ {t['text']}")
            if not y_done:
                lines.append("_(none)_")
            lines.append("")
            lines.append("*Today*")
            for t in t_todo:
                lines.append(f"• {t['text']}")
            for t in t_done:
                lines.append(f"✓ {t['text']}")
            if not t_todo and not t_done:
                lines.append("_(none)_")

            standup_text = "\n".join(lines)

            if copy_to_clipboard(standup_text):
                message = "✓ Copied to clipboard!"
                message_color = C_GREEN
            else:
                message = "✗ Failed to copy to clipboard"
                message_color = C_RED


# ── Weekly summary ───────────────────────────────────────────────────────────


def show_weekly(scr, ws_name):
    """Show weekly summary with task counts for the last 7 days."""
    h, w = scr.getmaxyx()
    today = datetime.now()

    while True:
        scr.clear()
        saddstr(
            scr,
            1,
            max(0, (w - 14) // 2),
            "Weekly Summary",
            curses.color_pair(C_CYAN) | curses.A_BOLD,
        )
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        y = 5
        for i in range(6, -1, -1):
            if y >= h - 4:
                break
            dt = today - timedelta(days=i)
            tasks = get_tasks(ws_name, dt)
            done_c = sum(1 for t in tasks if t.get("done"))
            todo_c = sum(1 for t in tasks if not t.get("done"))
            day_label = dt.strftime("%a %b %-d")
            if dt.date() == today.date():
                day_label += "  (today)"

            bar = "█" * done_c + "░" * todo_c
            summary = f"  {done_c} done, {todo_c} todo" if tasks else "  —"

            saddstr(scr, y, 3, day_label, curses.color_pair(C_CYAN))
            saddstr(
                scr,
                y + 1,
                5,
                bar + summary,
                curses.color_pair(C_GREEN) if tasks else curses.color_pair(C_DIM),
            )
            y += 3

        draw_footer(scr, h, w, "weekly")
        scr.refresh()
        ch = scr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            break


# ── Monthly heatmap ──────────────────────────────────────────────────────────


def heat_color(count):
    """Return color pair for heatmap based on task count."""
    if count == 0:
        return C_DIM
    elif count <= 2:
        return C_HEAT_1
    elif count <= 4:
        return C_HEAT_2
    elif count <= 6:
        return C_HEAT_3
    else:
        return C_HEAT_4


def show_heatmap(scr, ws_name):
    """Show monthly heatmap with task completion visualization."""
    h, w = scr.getmaxyx()
    today = datetime.now()
    view_year = today.year
    view_month = today.month

    while True:
        scr.clear()

        month_name = calendar.month_name[view_month]
        title = f"{month_name} {view_year}"
        saddstr(
            scr, 1, max(0, (w - len(title)) // 2), title, curses.color_pair(C_CYAN) | curses.A_BOLD
        )
        saddstr(scr, 1, 2, "←", curses.color_pair(C_DIM))
        saddstr(scr, 1, w - 3, "→", curses.color_pair(C_DIM))
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        days_header = "  Mon   Tue   Wed   Thu   Fri   Sat   Sun"
        cx = max(0, (w - len(days_header)) // 2)
        saddstr(scr, 5, cx, days_header, curses.color_pair(C_DIM))

        cal = calendar.monthcalendar(view_year, view_month)
        month_data = load_month(ws_name, view_year, view_month)
        y = 7

        total_done = 0
        total_tasks = 0
        for week in cal:
            if y >= h - 6:
                break
            x = cx
            for day_num in week:
                if day_num == 0:
                    saddstr(scr, y, x, "  ·   ", curses.color_pair(C_DIM))
                else:
                    dt_key = f"{view_year}-{view_month:02d}-{day_num:02d}"
                    day_tasks = month_data.get(dt_key, [])
                    done_count = sum(1 for t in day_tasks if t.get("done"))
                    total_count = len(day_tasks)
                    total_done += done_count
                    total_tasks += total_count

                    is_today = (
                        view_year == today.year
                        and view_month == today.month
                        and day_num == today.day
                    )

                    cell = f"{day_num:>2}"
                    if done_count > 0:
                        block = " ■"
                    else:
                        block = "  "

                    cp = heat_color(done_count)
                    if is_today:
                        saddstr(scr, y, x, f"[{cell}]", curses.color_pair(C_CYAN) | curses.A_BOLD)
                        saddstr(scr, y, x + 4, block, curses.color_pair(cp))
                    else:
                        saddstr(scr, y, x, f" {cell} ", curses.color_pair(cp))
                        saddstr(scr, y, x + 4, block, curses.color_pair(cp))
                x += 6
            y += 2

        y += 1
        if y < h - 4:
            saddstr(scr, y, cx, "Legend:", curses.color_pair(C_DIM))
            legend_x = cx + 8
            saddstr(scr, y, legend_x, "·", curses.color_pair(C_DIM))
            saddstr(scr, y, legend_x + 2, "0", curses.color_pair(C_DIM))
            saddstr(scr, y, legend_x + 5, "■", curses.color_pair(C_HEAT_1))
            saddstr(scr, y, legend_x + 7, "1-2", curses.color_pair(C_DIM))
            saddstr(scr, y, legend_x + 12, "■", curses.color_pair(C_HEAT_2))
            saddstr(scr, y, legend_x + 14, "3-4", curses.color_pair(C_DIM))
            saddstr(scr, y, legend_x + 19, "■", curses.color_pair(C_HEAT_3))
            saddstr(scr, y, legend_x + 21, "5-6", curses.color_pair(C_DIM))
            saddstr(scr, y, legend_x + 26, "■", curses.color_pair(C_HEAT_4))
            saddstr(scr, y, legend_x + 28, "7+", curses.color_pair(C_DIM))

        y += 2
        if y < h - 3:
            stat = f"{total_done} completed / {total_tasks} total tasks this month"
            saddstr(scr, y, max(0, (w - len(stat)) // 2), stat, curses.color_pair(C_GREEN))

        draw_footer(scr, h, w, "heatmap")
        scr.refresh()

        ch = scr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            break
        elif ch in (ord("h"), curses.KEY_LEFT, ord("[")):
            view_month -= 1
            if view_month < 1:
                view_month = 12
                view_year -= 1
        elif ch in (ord("l"), curses.KEY_RIGHT, ord("]")):
            view_month += 1
            if view_month > 12:
                view_month = 1
                view_year += 1
        elif ch == ord("t"):
            view_year = today.year
            view_month = today.month


# ── Search ───────────────────────────────────────────────────────────────────


def show_search(scr, ws_name):
    """
    Search all tasks across all dates in the current workspace.
    Returns (date_str, task_id) if user selects a result, else None.
    """
    h, w = scr.getmaxyx()

    query = text_input(scr, h - 4, 3, "Search: ")
    if not query:
        return None

    q_lower = query.lower()

    all_tasks = load_all_ws_tasks(ws_name)
    results = []
    for dk in sorted(all_tasks.keys(), reverse=True):
        for task in all_tasks[dk]:
            if q_lower in task["text"].lower():
                results.append((dk, task.get("id"), task))

    if not results:
        scr.clear()
        saddstr(
            scr,
            h // 2,
            max(0, (w - 20) // 2),
            f'No results for "{query}"',
            curses.color_pair(C_DIM),
        )
        scr.refresh()
        scr.getch()
        return None

    sel = 0
    scroll = 0
    max_visible = h - 7

    while True:
        scr.clear()
        title = f'Search: "{query}" — {len(results)} result{"s" if len(results) != 1 else ""}'
        saddstr(
            scr, 1, max(0, (w - len(title)) // 2), title, curses.color_pair(C_CYAN) | curses.A_BOLD
        )
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        y = 5
        if scroll > 0:
            saddstr(scr, y - 1, w - 5, "↑more", curses.color_pair(C_DIM))

        for ri in range(scroll, min(scroll + max_visible, len(results))):
            if y >= h - 3:
                break
            dk, tid, task = results[ri]
            done = task.get("done", False)
            is_cur = ri == sel
            marker = "✓" if done else "•"
            text = task["text"]
            avail = w - 22
            if avail > 0 and len(text) > avail:
                text = text[: avail - 1] + "…"

            if is_cur:
                fill_line(scr, y, curses.color_pair(C_CURSOR_BG))
                saddstr(scr, y, 2, dk, curses.color_pair(C_CURSOR_BG))
                saddstr(
                    scr, y, 14, marker, curses.color_pair(C_CURSOR_GREEN if done else C_CURSOR_BG)
                )
                saddstr(scr, y, 17, text, curses.color_pair(C_CURSOR_BG))
            else:
                saddstr(scr, y, 2, dk, curses.color_pair(C_DIM))
                saddstr(scr, y, 14, marker, curses.color_pair(C_GREEN if done else C_WHITE))
                saddstr(scr, y, 17, text, curses.color_pair(C_GREY if done else C_WHITE))
            y += 1

        if scroll + max_visible < len(results):
            saddstr(scr, min(y, h - 3), w - 5, "↓more", curses.color_pair(C_DIM))

        draw_footer(scr, h, w, "search")
        scr.refresh()

        ch = scr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            return None
        elif ch in (curses.KEY_DOWN, ord("j")):
            if sel < len(results) - 1:
                sel += 1
                if sel >= scroll + max_visible:
                    scroll += 1
        elif ch in (curses.KEY_UP, ord("k")):
            if sel > 0:
                sel -= 1
                if sel < scroll:
                    scroll -= 1
        elif ch in (10, 13, curses.KEY_ENTER):
            dk, tid, task = results[sel]
            return (dk, tid)


# ── Workspace management ─────────────────────────────────────────────────────


def show_workspace_manage(scr, config):
    """Workspace management modal. Returns updated config."""
    h, w = scr.getmaxyx()
    wsl = config.get("workspaces", list(DEFAULT_WORKSPACES))
    active = config.get("active_workspace", "Personal")

    # Find initial cursor position (current active workspace)
    cursor_idx = wsl.index(active) if active in wsl else 0

    while True:
        scr.clear()
        title = "Workspace Management"
        saddstr(
            scr, 1, max(0, (w - len(title)) // 2), title, curses.color_pair(C_CYAN) | curses.A_BOLD
        )
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        y = 5
        saddstr(scr, y, 3, f"Current: {active}", curses.color_pair(C_WHITE))
        y += 2
        saddstr(scr, y, 3, "Workspaces:", curses.color_pair(C_DIM))
        y += 1

        # Clamp cursor
        if cursor_idx >= len(wsl):
            cursor_idx = len(wsl) - 1
        if cursor_idx < 0:
            cursor_idx = 0

        for i, name in enumerate(wsl):
            if y >= h - 5:
                break
            is_cursor = i == cursor_idx
            is_active = name == active

            if is_cursor:
                fill_line(scr, y, curses.color_pair(C_CURSOR_BG))
                marker = "→" if is_active else " "
                saddstr(scr, y, 4, marker, curses.color_pair(C_CYAN if is_active else C_CURSOR_BG))
                saddstr(scr, y, 6, f"{i + 1}: {name}", curses.color_pair(C_CURSOR_BG))
            else:
                marker = "→" if is_active else " "
                saddstr(scr, y, 4, marker, curses.color_pair(C_CYAN))
                saddstr(
                    scr,
                    y,
                    6,
                    f"{i + 1}: {name}",
                    curses.color_pair(C_WHITE if is_active else C_DIM),
                )
            y += 1

        draw_footer(scr, h, w, "ws_manage")
        scr.refresh()

        ch = scr.getch()
        if ch in (27, ord("q"), ord("Q")):
            break

        # Navigate down
        elif ch in (curses.KEY_DOWN, ord("j")):
            if cursor_idx < len(wsl) - 1:
                cursor_idx += 1

        # Navigate up
        elif ch in (curses.KEY_UP, ord("k")):
            if cursor_idx > 0:
                cursor_idx -= 1

        # Switch to selected workspace
        elif ch in (10, 13, curses.KEY_ENTER):
            if 0 <= cursor_idx < len(wsl):
                config["active_workspace"] = wsl[cursor_idx]
                active = wsl[cursor_idx]
                save_config(config)

        elif ch == ord("a"):
            name = text_input(scr, h - 4, 3, "New workspace: ")
            if name:
                if name in wsl:
                    saddstr(scr, h - 4, 3, f'"{name}" already exists', curses.color_pair(C_RED))
                    scr.refresh()
                    scr.getch()
                else:
                    wsl.append(name)
                    config["workspaces"] = wsl
                    save_config(config)
                    # Create workspace directory
                    (TASKS_DIR / name).mkdir(parents=True, exist_ok=True)
                    cursor_idx = len(wsl) - 1  # Move cursor to new workspace

        elif ch == ord("r"):
            if 0 <= cursor_idx < len(wsl):
                selected_ws = wsl[cursor_idx]
                new_name = text_input(scr, h - 4, 3, "Rename to: ", prefill=selected_ws)
                if new_name and new_name != selected_ws:
                    if new_name in wsl:
                        saddstr(
                            scr, h - 4, 3, f'"{new_name}" already exists', curses.color_pair(C_RED)
                        )
                        scr.refresh()
                        scr.getch()
                    else:
                        # Rename in workspace list
                        wsl[cursor_idx] = new_name
                        config["workspaces"] = wsl
                        if selected_ws == active:
                            config["active_workspace"] = new_name
                            active = new_name
                        save_config(config)
                        # Rename tasks directory
                        old_dir = TASKS_DIR / selected_ws
                        new_dir = TASKS_DIR / new_name
                        if old_dir.exists():
                            old_dir.rename(new_dir)

        elif ch == ord("d"):
            if len(wsl) <= 1:
                saddstr(scr, h - 4, 3, "Cannot delete the last workspace", curses.color_pair(C_RED))
                scr.refresh()
                scr.getch()
            elif 0 <= cursor_idx < len(wsl):
                selected_ws = wsl[cursor_idx]
                saddstr(
                    scr,
                    h - 4,
                    3,
                    f'Delete "{selected_ws}" and all its tasks? (y/n)',
                    curses.color_pair(C_RED),
                )
                scr.refresh()
                confirm = scr.getch()
                if confirm in (ord("y"), ord("Y")):
                    # Remove workspace directory
                    ws_dir = TASKS_DIR / selected_ws
                    if ws_dir.exists():
                        shutil.rmtree(ws_dir)
                    # Update config
                    wsl.remove(selected_ws)
                    config["workspaces"] = wsl
                    # If we deleted the active workspace, switch to first
                    if selected_ws == active:
                        config["active_workspace"] = wsl[0]
                        active = wsl[0]
                    save_config(config)
                    # Adjust cursor position
                    if cursor_idx >= len(wsl):
                        cursor_idx = len(wsl) - 1

    return config


# ── Workdays settings ────────────────────────────────────────────────────────

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def show_workdays(scr, config):
    """Workdays settings modal. Toggle which days count as workdays."""
    h, w = scr.getmaxyx()
    workdays = list(config.get("workdays", DEFAULT_WORKDAYS))
    cursor_idx = 0

    while True:
        scr.clear()
        title = "Active Workdays"
        saddstr(scr, 1, max(0, (w - len(title)) // 2), title, curses.color_pair(C_CYAN) | curses.A_BOLD)
        saddstr(scr, 3, 0, "─" * (w - 1), curses.color_pair(C_DIM))

        y = 5
        saddstr(scr, y, 3, "Toggle days to include in standup lookback:", curses.color_pair(C_DIM))
        y += 2

        for i, name in enumerate(DAY_NAMES):
            if y >= h - 4:
                break
            is_cursor = i == cursor_idx
            active = i in workdays
            marker = "✓" if active else " "
            label = f" [{marker}]  {name}"

            if is_cursor:
                fill_line(scr, y, curses.color_pair(C_CURSOR_BG))
                saddstr(scr, y, 4, label, curses.color_pair(C_CURSOR_BG))
            else:
                color = C_GREEN if active else C_DIM
                saddstr(scr, y, 4, label, curses.color_pair(color))
            y += 1

        draw_footer(scr, h, w, "workdays")
        scr.refresh()

        ch = scr.getch()
        if ch in (27, ord("q"), ord("Q")):
            break
        elif ch in (curses.KEY_DOWN, ord("j")):
            if cursor_idx < 6:
                cursor_idx += 1
        elif ch in (curses.KEY_UP, ord("k")):
            if cursor_idx > 0:
                cursor_idx -= 1
        elif ch in (ord(" "), 10, 13, curses.KEY_ENTER):
            if cursor_idx in workdays:
                workdays.remove(cursor_idx)
            else:
                workdays.append(cursor_idx)
                workdays.sort()
            config["workdays"] = workdays
            save_config(config)

    return config


__all__ = [
    "show_standup",
    "show_weekly",
    "show_heatmap",
    "show_search",
    "show_workspace_manage",
    "show_workdays",
]
