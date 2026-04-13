"""Configuration management."""

from datetime import datetime, timedelta

from .persistence import CONFIG_FILE, SCHEMA_VERSION, _atomic_write, _read_json

DEFAULT_WORKSPACES = ["Personal"]
# Monday=0 through Sunday=6 (matches datetime.weekday())
DEFAULT_WORKDAYS = [0, 1, 2, 3, 4]


def load_config() -> dict:
    """Load configuration from disk."""
    d = _read_json(CONFIG_FILE)
    if d and d.get("schema_version") == SCHEMA_VERSION:
        return dict(d)
    # Return default config
    return {
        "schema_version": SCHEMA_VERSION,
        "workspaces": list(DEFAULT_WORKSPACES),
        "active_workspace": "Personal",
    }


def save_config(config: dict):
    """Save configuration to disk."""
    _atomic_write(CONFIG_FILE, config)


def active_ws_name(config) -> str:
    """Get the active workspace name from config."""
    name = str(config.get("active_workspace", "Personal"))
    wsl = config.get("workspaces", DEFAULT_WORKSPACES)
    if name in wsl:
        return name
    return str(wsl[0]) if wsl else "Personal"


def get_workdays(config) -> list:
    """Get active workdays from config (list of weekday ints, 0=Mon..6=Sun)."""
    return config.get("workdays", list(DEFAULT_WORKDAYS))


def previous_workday(dt, workdays) -> datetime:
    """Find the most recent workday before dt. Falls back to yesterday if no workdays set."""
    if not workdays:
        return dt - timedelta(days=1)
    d = dt - timedelta(days=1)
    for _ in range(7):
        if d.weekday() in workdays:
            return d
        d -= timedelta(days=1)
    # All days checked, just return yesterday
    return dt - timedelta(days=1)


__all__ = [
    "DEFAULT_WORKDAYS",
    "DEFAULT_WORKSPACES",
    "load_config",
    "save_config",
    "active_ws_name",
    "get_workdays",
    "previous_workday",
]
