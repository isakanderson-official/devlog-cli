"""Shared pytest fixtures for all tests."""

import json
import pytest
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch


@pytest.fixture
def temp_devlog_home(tmp_path, monkeypatch):
    """Override devlog data directories with a temporary directory."""
    data_dir = tmp_path / ".todo-cli"
    config_file = data_dir / "config.json"
    tasks_dir = data_dir / "tasks"

    # Patch the module-level constants in persistence
    monkeypatch.setattr("devlog.core.persistence.DATA_DIR", data_dir)
    monkeypatch.setattr("devlog.core.persistence.CONFIG_FILE", config_file)
    monkeypatch.setattr("devlog.core.persistence.TASKS_DIR", tasks_dir)

    return {
        "data_dir": data_dir,
        "config_file": config_file,
        "tasks_dir": tasks_dir,
    }


@pytest.fixture
def sample_tasks():
    """Return a list of sample task dicts for testing."""
    return [
        {
            "id": "abc12345",
            "text": "Write unit tests",
            "done": False,
            "position": 0,
            "created_at": "2024-03-15T10:00:00",
            "completed_at": None,
        },
        {
            "id": "def67890",
            "text": "Review pull request",
            "done": False,
            "position": 1,
            "created_at": "2024-03-15T11:00:00",
            "completed_at": None,
        },
        {
            "id": "ghi11111",
            "text": "Deploy to staging",
            "done": True,
            "position": 0,
            "created_at": "2024-03-14T09:00:00",
            "completed_at": "2024-03-15T15:00:00",
        },
    ]


@pytest.fixture
def sample_config():
    """Return a sample config dict for testing."""
    return {
        "schema_version": 2,
        "workspaces": ["Personal", "Work", "Side Project"],
        "active_workspace": "Work",
    }


@pytest.fixture
def freezer():
    """Fixture for mocking datetime.now() and date.today()."""
    frozen_datetime = datetime(2024, 3, 15, 14, 30, 0)
    frozen_date = date(2024, 3, 15)

    def _freezer():
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = frozen_datetime
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            with patch("datetime.date") as mock_date:
                mock_date.today.return_value = frozen_date
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
                yield frozen_datetime, frozen_date

    return _freezer


@pytest.fixture
def sample_month_data(sample_tasks):
    """Return sample month data structure {date_key: [tasks]}."""
    return {
        "2024-03-14": [sample_tasks[2]],  # One completed task
        "2024-03-15": sample_tasks[:2],   # Two pending tasks
    }


@pytest.fixture
def populated_workspace(temp_devlog_home, sample_config, sample_month_data):
    """Create a workspace with sample config and tasks."""
    from devlog.core.config import save_config
    from devlog.core.persistence import save_month

    # Save config
    save_config(sample_config)

    # Save tasks for the active workspace
    ws_name = sample_config["active_workspace"]
    save_month(ws_name, 2024, 3, sample_month_data)

    return {
        "workspace": ws_name,
        "config": sample_config,
        "month_data": sample_month_data,
        **temp_devlog_home,
    }
