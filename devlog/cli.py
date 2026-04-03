"""CLI commands and argument parser."""

import argparse
import json
import sys
from datetime import datetime, timedelta

from .core.config import active_ws_name, load_config
from .core.persistence import date_key, get_tasks, load_all_ws_tasks, set_tasks
from .core.tasks import find_task, gen_id, next_position

# ── Date parsing ─────────────────────────────────────────────────────────────


def parse_date(date_str):
    """Parse date string. Supports: today, tomorrow, yesterday, YYYY-MM-DD."""
    if not date_str:
        return datetime.now()

    date_str = date_str.lower().strip()
    today = datetime.now()

    if date_str in ("today", "now"):
        return today
    elif date_str == "tomorrow":
        return today + timedelta(days=1)
    elif date_str == "yesterday":
        return today - timedelta(days=1)
    else:
        # Try to parse YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(
                f"Error: Invalid date format '{date_str}'. Use: today, tomorrow, yesterday, or YYYY-MM-DD",
                file=sys.stderr,
            )
            sys.exit(1)


# ── CLI commands ─────────────────────────────────────────────────────────────


def cli_list(args):
    """List tasks for a given date and workspace."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    dt = parse_date(args.date)
    tasks = get_tasks(ws_name, dt)

    if args.json:
        output = {"date": date_key(dt), "workspace": ws_name, "tasks": tasks}
        print(json.dumps(output, indent=2))
    else:
        todos = [t for t in tasks if not t.get("done")]
        dones = [t for t in tasks if t.get("done")]

        print(f"Tasks for {date_key(dt)} ({ws_name}):")
        print()

        if todos:
            print(f"TODO ({len(todos)}):")
            for t in sorted(todos, key=lambda x: x.get("position", 0)):
                print(f"  • [{t['id']}] {t['text']}")
            print()

        if dones:
            print(f"DONE ({len(dones)}):")
            for t in sorted(dones, key=lambda x: x.get("position", 0)):
                print(f"  ✓ [{t['id']}] {t['text']}")


def cli_add(args):
    """Add a new task."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    dt = parse_date(args.date)
    tasks = get_tasks(ws_name, dt)

    new_task = {
        "id": gen_id(),
        "text": args.text,
        "done": False,
        "position": next_position(tasks),
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    tasks.append(new_task)
    set_tasks(ws_name, dt, tasks)

    if args.json:
        print(json.dumps(new_task, indent=2))
    else:
        print(f"✓ Added task: {new_task['text']}")
        print(f"  ID: {new_task['id']}")
        print(f"  Date: {date_key(dt)}")


def cli_done(args):
    """Mark a task as done."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)

    # Search for task across all dates if needed
    if args.date:
        dt = parse_date(args.date)
        tasks = get_tasks(ws_name, dt)
        idx, task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task {args.task_id} not found on {date_key(dt)}", file=sys.stderr)
            sys.exit(1)

        task["done"] = True
        task["completed_at"] = datetime.now().isoformat()
        # Move to bottom of done section
        done_tasks = [t for t in tasks if t.get("done") and t.get("id") != task.get("id")]
        if done_tasks:
            task["position"] = max(t.get("position", 0) for t in done_tasks) + 1
        else:
            task["position"] = 0
        set_tasks(ws_name, dt, tasks)

        if args.json:
            print(json.dumps(task, indent=2))
        else:
            print(f"✓ Marked as done: {task['text']}")
    else:
        # Search all dates
        found = False
        all_tasks = load_all_ws_tasks(ws_name)
        for dk, day_tasks in all_tasks.items():
            idx, task = find_task(day_tasks, args.task_id)
            if task:
                task["done"] = True
                task["completed_at"] = datetime.now().isoformat()
                # Move to bottom of done section
                done_tasks = [
                    t for t in day_tasks if t.get("done") and t.get("id") != task.get("id")
                ]
                if done_tasks:
                    task["position"] = max(t.get("position", 0) for t in done_tasks) + 1
                else:
                    task["position"] = 0
                parts = dk.split("-")
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                set_tasks(ws_name, dt, day_tasks)

                if args.json:
                    print(json.dumps(task, indent=2))
                else:
                    print(f"✓ Marked as done: {task['text']}")
                found = True
                break

        if not found:
            print(f"Error: Task {args.task_id} not found", file=sys.stderr)
            sys.exit(1)


def cli_undone(args):
    """Mark a task as not done."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)

    # Search for task across all dates if needed
    if args.date:
        dt = parse_date(args.date)
        tasks = get_tasks(ws_name, dt)
        idx, task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task {args.task_id} not found on {date_key(dt)}", file=sys.stderr)
            sys.exit(1)

        task["done"] = False
        task["completed_at"] = None
        # Move to bottom of todo section
        todo_tasks = [t for t in tasks if not t.get("done") and t.get("id") != task.get("id")]
        if todo_tasks:
            task["position"] = max(t.get("position", 0) for t in todo_tasks) + 1
        else:
            task["position"] = 0
        set_tasks(ws_name, dt, tasks)

        if args.json:
            print(json.dumps(task, indent=2))
        else:
            print(f"• Marked as pending: {task['text']}")
    else:
        # Search all dates
        found = False
        all_tasks = load_all_ws_tasks(ws_name)
        for dk, day_tasks in all_tasks.items():
            idx, task = find_task(day_tasks, args.task_id)
            if task:
                task["done"] = False
                task["completed_at"] = None
                # Move to bottom of todo section
                todo_tasks = [
                    t for t in day_tasks if not t.get("done") and t.get("id") != task.get("id")
                ]
                if todo_tasks:
                    task["position"] = max(t.get("position", 0) for t in todo_tasks) + 1
                else:
                    task["position"] = 0
                parts = dk.split("-")
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                set_tasks(ws_name, dt, day_tasks)

                if args.json:
                    print(json.dumps(task, indent=2))
                else:
                    print(f"• Marked as pending: {task['text']}")
                found = True
                break

        if not found:
            print(f"Error: Task {args.task_id} not found", file=sys.stderr)
            sys.exit(1)


def cli_delete(args):
    """Delete a task."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)

    # Search for task across all dates if needed
    if args.date:
        dt = parse_date(args.date)
        tasks = get_tasks(ws_name, dt)
        idx, task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task {args.task_id} not found on {date_key(dt)}", file=sys.stderr)
            sys.exit(1)

        text = task["text"]
        tasks.pop(idx)
        set_tasks(ws_name, dt, tasks)

        if args.json:
            print(json.dumps({"deleted": True, "task_id": args.task_id, "text": text}, indent=2))
        else:
            print(f"✗ Deleted: {text}")
    else:
        # Search all dates
        found = False
        all_tasks = load_all_ws_tasks(ws_name)
        for dk, day_tasks in all_tasks.items():
            idx, task = find_task(day_tasks, args.task_id)
            if task:
                text = task["text"]
                day_tasks.pop(idx)
                parts = dk.split("-")
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                set_tasks(ws_name, dt, day_tasks)

                if args.json:
                    print(
                        json.dumps(
                            {"deleted": True, "task_id": args.task_id, "text": text}, indent=2
                        )
                    )
                else:
                    print(f"✗ Deleted: {text}")
                found = True
                break

        if not found:
            print(f"Error: Task {args.task_id} not found", file=sys.stderr)
            sys.exit(1)


def cli_edit(args):
    """Edit a task's text."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)

    # Search for task across all dates if needed
    if args.date:
        dt = parse_date(args.date)
        tasks = get_tasks(ws_name, dt)
        idx, task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task {args.task_id} not found on {date_key(dt)}", file=sys.stderr)
            sys.exit(1)

        old_text = task["text"]
        task["text"] = args.text
        set_tasks(ws_name, dt, tasks)

        if args.json:
            print(json.dumps(task, indent=2))
        else:
            print("✓ Updated task:")
            print(f"  Old: {old_text}")
            print(f"  New: {task['text']}")
    else:
        # Search all dates
        found = False
        all_tasks = load_all_ws_tasks(ws_name)
        for dk, day_tasks in all_tasks.items():
            idx, task = find_task(day_tasks, args.task_id)
            if task:
                old_text = task["text"]
                task["text"] = args.text
                parts = dk.split("-")
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                set_tasks(ws_name, dt, day_tasks)

                if args.json:
                    print(json.dumps(task, indent=2))
                else:
                    print("✓ Updated task:")
                    print(f"  Old: {old_text}")
                    print(f"  New: {task['text']}")
                found = True
                break

        if not found:
            print(f"Error: Task {args.task_id} not found", file=sys.stderr)
            sys.exit(1)


def cli_search(args):
    """Search for tasks across all dates."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    all_tasks = load_all_ws_tasks(ws_name)

    query = args.query.lower()
    results = []

    for dk in sorted(all_tasks.keys(), reverse=True):
        for task in all_tasks[dk]:
            if query in task["text"].lower():
                results.append({"date": dk, "task": task})

    if args.json:
        output = {
            "query": args.query,
            "workspace": ws_name,
            "count": len(results),
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f'No results for "{args.query}"')
        else:
            print(
                f'Found {len(results)} result{"s" if len(results) != 1 else ""} for "{args.query}":'
            )
            print()
            for r in results:
                task = r["task"]
                marker = "✓" if task.get("done") else "•"
                print(f"  {marker} [{r['date']}] [{task['id']}] {task['text']}")


def cli_stats(args):
    """Show statistics for a date range."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    today = datetime.now()

    if args.range == "week":
        start_date = today - timedelta(days=6)
        end_date = today
        title = "Last 7 days"
    elif args.range == "month":
        start_date = today - timedelta(days=29)
        end_date = today
        title = "Last 30 days"
    else:  # today
        start_date = today
        end_date = today
        title = "Today"

    # Collect stats
    total_tasks = 0
    total_done = 0
    daily_stats = []

    current = start_date
    while current <= end_date:
        tasks = get_tasks(ws_name, current)
        done_count = sum(1 for t in tasks if t.get("done"))
        todo_count = sum(1 for t in tasks if not t.get("done"))

        total_tasks += len(tasks)
        total_done += done_count

        daily_stats.append(
            {"date": date_key(current), "total": len(tasks), "done": done_count, "todo": todo_count}
        )

        current += timedelta(days=1)

    if args.json:
        output = {
            "workspace": ws_name,
            "range": title,
            "start_date": date_key(start_date),
            "end_date": date_key(end_date),
            "total_tasks": total_tasks,
            "total_done": total_done,
            "total_pending": total_tasks - total_done,
            "daily": daily_stats,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Statistics for {title} ({ws_name}):")
        print()
        print(f"Total tasks: {total_tasks}")
        print(f"Completed: {total_done}")
        print(f"Pending: {total_tasks - total_done}")
        if total_tasks > 0:
            completion_rate = (total_done / total_tasks) * 100
            print(f"Completion rate: {completion_rate:.1f}%")
        print()

        if len(daily_stats) > 1:
            print("Daily breakdown:")
            for stat in daily_stats:
                if stat["total"] > 0:
                    bar = "█" * stat["done"] + "░" * stat["todo"]
                    print(f"  {stat['date']}: {bar} ({stat['done']}/{stat['total']})")


def cli_export(args):
    """Export tasks to markdown."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    all_tasks = load_all_ws_tasks(ws_name)

    if args.date:
        dt = parse_date(args.date)
        dk = date_key(dt)
        tasks = get_tasks(ws_name, dt)

        print(f"# Tasks for {dk}\n")

        todos = [t for t in tasks if not t.get("done")]
        dones = [t for t in tasks if t.get("done")]

        if todos:
            print("## TODO\n")
            for t in sorted(todos, key=lambda x: x.get("position", 0)):
                print(f"- [ ] {t['text']}")
            print()

        if dones:
            print("## DONE\n")
            for t in sorted(dones, key=lambda x: x.get("position", 0)):
                print(f"- [x] {t['text']}")
    else:
        print(f"# Tasks for {ws_name}\n")

        for dk in sorted(all_tasks.keys(), reverse=True):
            tasks = all_tasks[dk]
            if not tasks:
                continue

            print(f"## {dk}\n")

            todos = [t for t in tasks if not t.get("done")]
            dones = [t for t in tasks if t.get("done")]

            for t in sorted(todos, key=lambda x: x.get("position", 0)):
                print(f"- [ ] {t['text']}")
            for t in sorted(dones, key=lambda x: x.get("position", 0)):
                print(f"- [x] {t['text']}")
            print()


def cli_import(args):
    """Import tasks from markdown."""
    config = load_config()
    ws_name = args.workspace or active_ws_name(config)
    dt = parse_date(args.date)

    # Read from stdin or file
    if args.file == "-":
        content = sys.stdin.read()
    else:
        try:
            with open(args.file) as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File {args.file} not found", file=sys.stderr)
            sys.exit(1)

    tasks = get_tasks(ws_name, dt)
    added = 0

    for line in content.split("\n"):
        line = line.strip()

        # Parse markdown checkbox format
        if line.startswith("- [ ] "):
            text = line[6:].strip()
            if text:
                new_task = {
                    "id": gen_id(),
                    "text": text,
                    "done": False,
                    "position": next_position(tasks),
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None,
                }
                tasks.append(new_task)
                added += 1
        elif line.startswith("- [x] ") or line.startswith("- [X] "):
            text = line[6:].strip()
            if text:
                new_task = {
                    "id": gen_id(),
                    "text": text,
                    "done": True,
                    "position": next_position(tasks),
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                }
                tasks.append(new_task)
                added += 1

    if added > 0:
        set_tasks(ws_name, dt, tasks)

        if args.json:
            print(
                json.dumps(
                    {"imported": added, "date": date_key(dt), "workspace": ws_name}, indent=2
                )
            )
        else:
            print(f"✓ Imported {added} task{'s' if added != 1 else ''} to {date_key(dt)}")
    else:
        print("No tasks found to import", file=sys.stderr)


# ── Argument parser ──────────────────────────────────────────────────────────


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="A minimal, beautiful terminal todo app",
        epilog="Run without arguments to launch the interactive TUI.",
    )

    # Global options
    parser.add_argument("-w", "--workspace", help="Workspace name")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "-d", "--date", default="today", help="Date (today, tomorrow, yesterday, or YYYY-MM-DD)"
    )

    # add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("text", help="Task text")
    add_parser.add_argument(
        "-d", "--date", default="today", help="Date (today, tomorrow, yesterday, or YYYY-MM-DD)"
    )

    # done command
    done_parser = subparsers.add_parser("done", help="Mark task as done")
    done_parser.add_argument("task_id", help="Task ID")
    done_parser.add_argument(
        "-d", "--date", help="Date (optional, will search all dates if not provided)"
    )

    # undone command
    undone_parser = subparsers.add_parser("undone", help="Mark task as not done")
    undone_parser.add_argument("task_id", help="Task ID")
    undone_parser.add_argument(
        "-d", "--date", help="Date (optional, will search all dates if not provided)"
    )

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="Task ID")
    delete_parser.add_argument(
        "-d", "--date", help="Date (optional, will search all dates if not provided)"
    )

    # edit command
    edit_parser = subparsers.add_parser("edit", help="Edit task text")
    edit_parser.add_argument("task_id", help="Task ID")
    edit_parser.add_argument("text", help="New task text")
    edit_parser.add_argument(
        "-d", "--date", help="Date (optional, will search all dates if not provided)"
    )

    # search command
    search_parser = subparsers.add_parser("search", help="Search tasks")
    search_parser.add_argument("query", help="Search query")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument(
        "-r", "--range", default="today", choices=["today", "week", "month"], help="Date range"
    )

    # export command
    export_parser = subparsers.add_parser("export", help="Export tasks to markdown")
    export_parser.add_argument("-d", "--date", help="Date (optional, exports all if not provided)")

    # import command
    import_parser = subparsers.add_parser("import", help="Import tasks from markdown")
    import_parser.add_argument("file", help="File to import (use - for stdin)")
    import_parser.add_argument("-d", "--date", default="today", help="Date to import to")

    return parser


def execute_cli_command(args):
    """Execute the appropriate CLI command based on parsed arguments."""
    try:
        if args.command == "list":
            cli_list(args)
        elif args.command == "add":
            cli_add(args)
        elif args.command == "done":
            cli_done(args)
        elif args.command == "undone":
            cli_undone(args)
        elif args.command == "delete":
            cli_delete(args)
        elif args.command == "edit":
            cli_edit(args)
        elif args.command == "search":
            cli_search(args)
        elif args.command == "stats":
            cli_stats(args)
        elif args.command == "export":
            cli_export(args)
        elif args.command == "import":
            cli_import(args)
    except KeyboardInterrupt:
        print("\nAborted", file=sys.stderr)
        sys.exit(130)


__all__ = [
    "parse_date",
    "create_parser",
    "execute_cli_command",
    "cli_list",
    "cli_add",
    "cli_done",
    "cli_undone",
    "cli_delete",
    "cli_edit",
    "cli_search",
    "cli_stats",
    "cli_export",
    "cli_import",
]
