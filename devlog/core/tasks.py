"""Task model and utilities."""

import uuid


def gen_id() -> str:
    return uuid.uuid4().hex[:8]


def find_task(tasks, task_id):
    """Return (index, task) for the given ID, or (None, None)."""
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            return i, t
    return None, None


def next_position(tasks) -> int:
    if not tasks:
        return 0
    return max(t.get("position", 0) for t in tasks) + 1


def reposition(tasks):
    """Normalize positions to 0, 1, 2, ... within each done/todo group."""
    todos = sorted([t for t in tasks if not t.get("done")], key=lambda t: t.get("position", 0))
    dones = sorted([t for t in tasks if t.get("done")], key=lambda t: t.get("position", 0))
    for i, t in enumerate(todos):
        t["position"] = i
    for i, t in enumerate(dones):
        t["position"] = i


def nav_order(tasks):
    """Return task IDs in display order: todos first (by position), then dones (by position)."""
    todos = sorted([t for t in tasks if not t.get("done")], key=lambda t: t.get("position", 0))
    dones = sorted([t for t in tasks if t.get("done")], key=lambda t: t.get("position", 0))
    return [t["id"] for t in todos + dones]


__all__ = ["gen_id", "find_task", "next_position", "reposition", "nav_order"]
