"""Main TUI loop and event handling."""

import curses
from datetime import datetime, timedelta

from .core.config import load_config, save_config, active_ws_name, DEFAULT_WORKSPACES
from .core.persistence import get_tasks, set_tasks
from .core.tasks import gen_id, find_task, next_position, nav_order
from .ui.colors import init_colors, C_GREEN, C_CYAN, C_RED, C_YELLOW
from .ui.drawing import draw_workspace_bar, draw_header, draw_tasks, draw_footer, saddstr
from .ui.input import text_input
from . import views


def main(scr):
    """Main TUI loop - handles all keyboard events and UI rendering."""
    # Ensure alternate screen is active and no scrollback
    scr.clear()
    init_colors()
    curses.curs_set(0)
    scr.timeout(-1)
    scr.scrollok(False)  # Disable scrolling

    config = load_config()
    current_date = datetime.now()
    cursor = None  # stores task ID
    message = ""
    msg_color = C_YELLOW

    while True:
        ws_name = active_ws_name(config)
        tasks = get_tasks(ws_name, current_date)
        h, w = scr.getmaxyx()
        order = nav_order(tasks)

        # Clamp cursor
        if not order:
            cursor = None
        elif cursor not in order:
            cursor = order[0]

        # Draw
        scr.erase()
        draw_workspace_bar(scr, config, w)
        draw_header(scr, current_date, w)
        draw_tasks(scr, tasks, cursor, start_y=6, h=h, w=w)
        draw_footer(scr, h, w)

        if message:
            saddstr(scr, h - 4, 3, message, curses.color_pair(msg_color))

        scr.refresh()
        message = ""

        # Input
        try:
            ch = scr.get_wch()
        except curses.error:
            continue
        except KeyboardInterrupt:
            break

        key = ch

        # ── Workspace switching (1-9) ──
        if isinstance(key, str) and key in "123456789":
            idx = int(key) - 1
            wsl = config.get("workspaces", DEFAULT_WORKSPACES)
            if idx < len(wsl):
                config["active_workspace"] = wsl[idx]
                save_config(config)
                cursor = None
                message = f"Workspace: {wsl[idx]}"
                msg_color = C_CYAN
            continue

        # ── Navigate down ──
        if key == curses.KEY_DOWN or key == "j":
            if order and cursor in order:
                pos = order.index(cursor)
                if pos < len(order) - 1:
                    cursor = order[pos + 1]

        # ── Navigate up ──
        elif key == curses.KEY_UP or key == "k":
            if order and cursor in order:
                pos = order.index(cursor)
                if pos > 0:
                    cursor = order[pos - 1]

        # ── Day prev ──
        elif key == curses.KEY_LEFT or key == "h" or key == "[":
            current_date -= timedelta(days=1)
            cursor = None

        # ── Day next ──
        elif key == curses.KEY_RIGHT or key == "l" or key == "]":
            current_date += timedelta(days=1)
            cursor = None

        # ── Today ──
        elif key == "t":
            current_date = datetime.now()
            cursor = None

        # ── Add task ──
        elif key == "\n" or key == "a" or (isinstance(key, int) and key in (10, 13, curses.KEY_ENTER)):
            result = text_input(scr, h - 4, 3, "New task: ")
            if result:
                new_task = {
                    "id": gen_id(),
                    "text": result,
                    "done": False,
                    "position": next_position(tasks),
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None,
                }
                tasks.append(new_task)
                set_tasks(ws_name, current_date, tasks)
                cursor = new_task["id"]
                message = "✓ Task added"
                msg_color = C_GREEN

        # ── Toggle done ──
        elif key == " ":  # Space bar
            if cursor:
                idx, task = find_task(tasks, cursor)
                if task:
                    was_todo = not task["done"]
                    task["done"] = not task["done"]
                    if task["done"]:
                        task["completed_at"] = datetime.now().isoformat()
                        # Move to bottom of done section
                        done_tasks = [t for t in tasks if t.get("done") and t.get("id") != task.get("id")]
                        if done_tasks:
                            task["position"] = max(t.get("position", 0) for t in done_tasks) + 1
                        else:
                            task["position"] = 0
                    else:
                        task["completed_at"] = None
                        # Move to bottom of todo section
                        todo_tasks = [t for t in tasks if not t.get("done") and t.get("id") != task.get("id")]
                        if todo_tasks:
                            task["position"] = max(t.get("position", 0) for t in todo_tasks) + 1
                        else:
                            task["position"] = 0
                    set_tasks(ws_name, current_date, tasks)
                    # When marking done, move cursor to next todo item
                    if was_todo:
                        cur_pos = order.index(cursor) if cursor in order else 0
                        todo_ids = [t["id"] for t in sorted(
                            [t for t in tasks if not t.get("done")],
                            key=lambda t: t.get("position", 0)
                        )]
                        # Pick the next todo after current position, or last todo
                        if todo_ids:
                            # Find first todo that was below the toggled task
                            next_cursor = None
                            for tid in todo_ids:
                                old_pos = order.index(tid) if tid in order else -1
                                if old_pos >= cur_pos:
                                    next_cursor = tid
                                    break
                            cursor = next_cursor if next_cursor else todo_ids[-1]
                    message = "✓ Done" if task["done"] else "• Reopened"
                    msg_color = C_GREEN

        # ── Edit ──
        elif key == "e":
            if cursor:
                idx, task = find_task(tasks, cursor)
                if task:
                    result = text_input(scr, h - 4, 3, "Edit: ",
                                        prefill=task["text"])
                    if result:
                        task["text"] = result
                        set_tasks(ws_name, current_date, tasks)
                        message = "✓ Updated"
                        msg_color = C_GREEN

        # ── Delete ──
        elif key == "d":
            if cursor:
                idx, task = find_task(tasks, cursor)
                if task:
                    name = task["text"]
                    avail = w - 25
                    if len(name) > avail > 0:
                        name = name[:avail - 1] + "…"
                    saddstr(scr, h - 4, 3, f"Delete \"{name}\"? (y/n)",
                            curses.color_pair(C_RED))
                    scr.refresh()
                    confirm = scr.getch()
                    if confirm in (ord("y"), ord("Y")):
                        tasks.pop(idx)
                        set_tasks(ws_name, current_date, tasks)
                        # Move cursor to next or previous
                        new_order = nav_order(tasks)
                        if new_order:
                            cursor = new_order[min(idx, len(new_order) - 1)]
                        else:
                            cursor = None
                        message = "Deleted"
                        msg_color = C_RED

        # ── Reorder up (K or Shift+Up) ──
        elif key == "K" or key == curses.KEY_SR:
            if cursor and order:
                pos = order.index(cursor) if cursor in order else -1
                if pos > 0:
                    prev_id = order[pos - 1]
                    _, cur_task = find_task(tasks, cursor)
                    _, prev_task = find_task(tasks, prev_id)
                    if cur_task and prev_task:
                        cur_task["position"], prev_task["position"] = prev_task["position"], cur_task["position"]
                        set_tasks(ws_name, current_date, tasks)

        # ── Reorder down (J or Shift+Down) ──
        elif key == "J" or key == curses.KEY_SF:
            if cursor and order:
                pos = order.index(cursor) if cursor in order else -1
                if 0 <= pos < len(order) - 1:
                    next_id = order[pos + 1]
                    _, cur_task = find_task(tasks, cursor)
                    _, next_task = find_task(tasks, next_id)
                    if cur_task and next_task:
                        cur_task["position"], next_task["position"] = next_task["position"], cur_task["position"]
                        set_tasks(ws_name, current_date, tasks)

        # ── Move task to previous day (Shift+Left) ──
        elif key == curses.KEY_SLEFT:
            if cursor:
                idx, task = find_task(tasks, cursor)
                if task:
                    target_date = current_date - timedelta(days=1)
                    target_tasks = get_tasks(ws_name, target_date)
                    task["position"] = next_position(target_tasks)
                    target_tasks.append(task)
                    tasks.pop(idx)
                    set_tasks(ws_name, current_date, tasks)
                    set_tasks(ws_name, target_date, target_tasks)
                    current_date = target_date
                    message = "← Moved to previous day"
                    msg_color = C_CYAN

        # ── Move task to next day (Shift+Right) ──
        elif key == curses.KEY_SRIGHT:
            if cursor:
                idx, task = find_task(tasks, cursor)
                if task:
                    target_date = current_date + timedelta(days=1)
                    target_tasks = get_tasks(ws_name, target_date)
                    task["position"] = next_position(target_tasks)
                    target_tasks.append(task)
                    tasks.pop(idx)
                    set_tasks(ws_name, current_date, tasks)
                    set_tasks(ws_name, target_date, target_tasks)
                    current_date = target_date
                    message = "→ Moved to next day"
                    msg_color = C_CYAN

        # ── Standup ──
        elif key == "s":
            views.show_standup(scr, ws_name)

        # ── Weekly ──
        elif key == "w":
            views.show_weekly(scr, ws_name)

        # ── Monthly heatmap ──
        elif key == "m":
            views.show_heatmap(scr, ws_name)

        # ── Search ──
        elif key == "/":
            result = views.show_search(scr, ws_name)
            if result:
                dk, task_id = result
                parts = dk.split("-")
                current_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                cursor = task_id

        # ── Workspace management ──
        elif key == "W":
            config = views.show_workspace_manage(scr, config)
            cursor = None

        # ── Quit ──
        elif key == "q" or key == "Q":
            break


__all__ = ['main']
