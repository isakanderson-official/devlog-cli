"""Unit tests for devlog.core.config module."""

import pytest
from devlog.core.config import (
    DEFAULT_WORKSPACES,
    load_config,
    save_config,
    active_ws_name,
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
