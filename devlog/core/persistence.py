"""Data persistence layer - file I/O and monthly task file management."""

import json
from datetime import datetime
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

DATA_DIR = Path.home() / ".todo-cli"
CONFIG_FILE = DATA_DIR / "config.json"
TASKS_DIR = DATA_DIR / "tasks"
SCHEMA_VERSION = 2


# ── Helper functions ─────────────────────────────────────────────────────────


def _atomic_write(path, data):
    """Write JSON atomically via temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def _read_json(path):
    """Read JSON file, return None on failure."""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return None


# ── Monthly task files ───────────────────────────────────────────────────────


def _month_file(ws_name, year, month) -> Path:
    return TASKS_DIR / ws_name / f"{year}-{month:02d}.json"


def load_month(ws_name, year, month) -> dict:
    """Load a monthly task file. Returns {date_key: [tasks]}."""
    data = _read_json(_month_file(ws_name, year, month))
    return data if data else {}


def save_month(ws_name, year, month, month_data: dict):
    path = _month_file(ws_name, year, month)
    if month_data:
        _atomic_write(path, month_data)
    elif path.exists():
        path.unlink()


def date_key(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def _dt_year_month(dt):
    if isinstance(dt, datetime):
        return dt.year, dt.month
    return dt.year, dt.month


def get_tasks(ws_name, dt) -> list:
    year, month = _dt_year_month(dt)
    md = load_month(ws_name, year, month)
    return md.get(date_key(dt), [])


def set_tasks(ws_name, dt, tasks):
    from .tasks import reposition

    year, month = _dt_year_month(dt)
    md = load_month(ws_name, year, month)
    k = date_key(dt)
    if tasks:
        reposition(tasks)
        md[k] = tasks
    elif k in md:
        del md[k]
    save_month(ws_name, year, month, md)


def load_all_ws_tasks(ws_name) -> dict:
    """Load all monthly files for a workspace. Returns {date_key: [tasks]}."""
    ws_dir = TASKS_DIR / ws_name
    all_tasks = {}
    if ws_dir.exists():
        for f in sorted(ws_dir.glob("*.json")):
            data = _read_json(f)
            if data:
                all_tasks.update(data)
    return all_tasks


__all__ = [
    "DATA_DIR",
    "TASKS_DIR",
    "SCHEMA_VERSION",
    "CONFIG_FILE",
    "get_tasks",
    "set_tasks",
    "load_all_ws_tasks",
    "date_key",
    "load_month",
    "save_month",
]
