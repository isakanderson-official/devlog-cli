"""Unit tests for devlog.core.config module."""

from datetime import datetime

import pytest
from devlog.core.config import (
    DEFAULT_WORKDAYS,
    DEFAULT_WORKSPACES,
    active_ws_name,
    get_workdays,
    load_config,
    previous_workday,
    save_config,
)


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_config_missing_file(self, temp_devlog_home):
        """load_config should return default config when file missing."""
        config = load_config()

        assert config["schema_version"] == 2
        assert config["workspaces"] == list(DEFAULT_WORKSPACES)
        assert config["active_workspace"] == "Personal"

    def test_load_config_existing_file(self, temp_devlog_home, sample_config):
        """load_config should load existing config from disk."""
        save_config(sample_config)

        loaded = load_config()

        assert loaded == sample_config
        assert loaded["active_workspace"] == "Work"
        assert "Side Project" in loaded["workspaces"]

    def test_load_config_wrong_schema_version(self, temp_devlog_home):
        """load_config should return default for wrong schema version."""
        old_config = {
            "schema_version": 1,  # Wrong version
            "workspaces": ["Old"],
            "active_workspace": "Old",
        }
        save_config(old_config)

        loaded = load_config()

        # Should return default, not old config
        assert loaded["schema_version"] == 2
        assert loaded["workspaces"] == list(DEFAULT_WORKSPACES)
        assert loaded["active_workspace"] == "Personal"

    def test_load_config_corrupted_file(self, temp_devlog_home):
        """load_config should return default for corrupted file."""
        config_file = temp_devlog_home["config_file"]
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        with open(config_file, "w") as f:
            f.write("{invalid json content")

        loaded = load_config()

        assert loaded["schema_version"] == 2
        assert loaded["workspaces"] == list(DEFAULT_WORKSPACES)


class TestSaveConfig:
    """Tests for save_config() function."""

    def test_save_config_creates_file(self, temp_devlog_home, sample_config):
        """save_config should create config file."""
        save_config(sample_config)

        assert temp_devlog_home["config_file"].exists()

    def test_save_config_persists_data(self, temp_devlog_home, sample_config):
        """save_config should persist data correctly."""
        save_config(sample_config)

        loaded = load_config()
        assert loaded == sample_config

    def test_save_config_overwrites_existing(self, temp_devlog_home):
        """save_config should overwrite existing config."""
        config_v1 = {
            "schema_version": 2,
            "workspaces": ["A"],
            "active_workspace": "A",
        }
        config_v2 = {
            "schema_version": 2,
            "workspaces": ["B", "C"],
            "active_workspace": "B",
        }

        save_config(config_v1)
        save_config(config_v2)

        loaded = load_config()
        assert loaded == config_v2
        assert "A" not in loaded["workspaces"]

    def test_save_config_creates_parent_dirs(self, temp_devlog_home):
        """save_config should create parent directories if missing."""
        # Ensure directory doesn't exist
        assert not temp_devlog_home["config_file"].parent.exists()

        save_config({"schema_version": 2, "workspaces": [], "active_workspace": "default"})

        assert temp_devlog_home["config_file"].exists()


class TestActiveWsName:
    """Tests for active_ws_name() function."""

    def test_active_ws_name_valid(self, sample_config):
        """active_ws_name should return active workspace if valid."""
        name = active_ws_name(sample_config)
        assert name == "Work"

    def test_active_ws_name_missing_key(self):
        """active_ws_name should fallback if active_workspace key missing."""
        config = {
            "workspaces": ["Personal", "Work"],
            # missing active_workspace key
        }

        name = active_ws_name(config)
        assert name == "Personal"  # Default fallback

    def test_active_ws_name_not_in_list(self):
        """active_ws_name should fallback if active workspace not in list."""
        config = {
            "workspaces": ["Personal", "Work"],
            "active_workspace": "NonExistent",
        }

        name = active_ws_name(config)
        assert name == "Personal"  # First in list

    def test_active_ws_name_empty_workspaces(self):
        """active_ws_name should return 'Personal' if workspaces list empty."""
        config = {
            "workspaces": [],
            "active_workspace": "Something",
        }

        name = active_ws_name(config)
        assert name == "Personal"

    def test_active_ws_name_missing_workspaces_key(self):
        """active_ws_name should handle missing workspaces key."""
        config = {
            "active_workspace": "Work",
            # missing workspaces key
        }

        name = active_ws_name(config)
        assert name == "Personal"  # Uses DEFAULT_WORKSPACES

    def test_active_ws_name_returns_first_if_multiple(self):
        """active_ws_name should return first workspace if active not found."""
        config = {
            "workspaces": ["First", "Second", "Third"],
            "active_workspace": "NotFound",
        }

        name = active_ws_name(config)
        assert name == "First"

    def test_active_ws_name_case_sensitive(self):
        """active_ws_name should be case-sensitive."""
        config = {
            "workspaces": ["Work", "personal"],
            "active_workspace": "work",  # lowercase
        }

        name = active_ws_name(config)
        # Should not match "Work" (uppercase), fallback to first
        assert name == "Work"


class TestGetWorkdays:
    """Tests for get_workdays() function."""

    def test_returns_default_when_not_set(self):
        assert get_workdays({}) == DEFAULT_WORKDAYS

    def test_returns_config_value(self):
        config = {"workdays": [0, 1, 2]}
        assert get_workdays(config) == [0, 1, 2]

    def test_returns_empty_list(self):
        config = {"workdays": []}
        assert get_workdays(config) == []


class TestPreviousWorkday:
    """Tests for previous_workday() function."""

    def test_friday_to_thursday_weekdays_only(self):
        """Friday should go back to Thursday with Mon-Fri workdays."""
        # 2026-04-10 is a Friday
        fri = datetime(2026, 4, 10)
        result = previous_workday(fri, [0, 1, 2, 3, 4])
        assert result.weekday() == 3  # Thursday

    def test_monday_skips_weekend(self):
        """Monday should go back to Friday when weekends are off."""
        # 2026-04-13 is a Monday
        mon = datetime(2026, 4, 13)
        result = previous_workday(mon, [0, 1, 2, 3, 4])
        assert result.weekday() == 4  # Friday
        assert result.day == 10

    def test_all_days_active(self):
        """With all days active, previous workday is just yesterday."""
        mon = datetime(2026, 4, 13)
        result = previous_workday(mon, [0, 1, 2, 3, 4, 5, 6])
        assert result.day == 12  # Sunday

    def test_empty_workdays_falls_back_to_yesterday(self):
        """Empty workdays list should fall back to yesterday."""
        mon = datetime(2026, 4, 13)
        result = previous_workday(mon, [])
        assert result.day == 12

    def test_only_mondays_active(self):
        """With only Monday active, Tuesday goes back to Monday."""
        tue = datetime(2026, 4, 14)  # Tuesday
        result = previous_workday(tue, [0])  # Only Monday
        assert result.weekday() == 0  # Monday
        assert result.day == 13
