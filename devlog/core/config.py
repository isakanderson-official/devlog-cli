"""Configuration management."""

from .persistence import CONFIG_FILE, SCHEMA_VERSION, _read_json, _atomic_write

DEFAULT_WORKSPACES = ["Personal"]


def load_config() -> dict:
    """Load configuration from disk."""
    d = _read_json(CONFIG_FILE)
    if d and d.get("schema_version") == SCHEMA_VERSION:
        return d
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
    name = config.get("active_workspace", "Personal")
    wsl = config.get("workspaces", DEFAULT_WORKSPACES)
    if name in wsl:
        return name
    return wsl[0] if wsl else "Personal"


__all__ = [
    'DEFAULT_WORKSPACES', 'load_config',
    'save_config', 'active_ws_name'
]
