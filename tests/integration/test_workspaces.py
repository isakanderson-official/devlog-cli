"""Integration tests for workspace management."""

import pytest
from datetime import date
from devlog.core.persistence import get_tasks, set_tasks, load_all_ws_tasks
from devlog.core.config import load_config, save_config, active_ws_name


class TestWorkspaceIsolation:
    """Tests for workspace task isolation."""

    def test_tasks_isolated_between_workspaces(self, temp_devlog_home):
        """Tasks in one workspace should not appear in another."""
        # Create tasks in Work workspace
        work_tasks = [
            {"id": "work1", "text": "Work task 1", "done": False, "position": 0},
            {"id": "work2", "text": "Work task 2", "done": False, "position": 1},
        ]
        set_tasks("Work", date(2024, 3, 15), work_tasks)

        # Create tasks in Personal workspace
        personal_tasks = [
            {"id": "pers1", "text": "Personal task 1", "done": False, "position": 0},
        ]
        set_tasks("Personal", date(2024, 3, 15), personal_tasks)

        # Verify isolation
        loaded_work = get_tasks("Work", date(2024, 3, 15))
        loaded_personal = get_tasks("Personal", date(2024, 3, 15))

        assert len(loaded_work) == 2
        assert len(loaded_personal) == 1
        assert all(t["id"].startswith("work") for t in loaded_work)
        assert all(t["id"].startswith("pers") for t in loaded_personal)

    def test_same_task_id_different_workspaces(self, temp_devlog_home):
        """Same task ID in different workspaces should be independent."""
        same_id = "abc12345"

        # Create task with same ID in different workspaces
        set_tasks("Work", date(2024, 3, 15), [
            {"id": same_id, "text": "Work version", "done": False, "position": 0}
        ])
        set_tasks("Personal", date(2024, 3, 15), [
            {"id": same_id, "text": "Personal version", "done": False, "position": 0}
        ])

        # Each workspace should have its own version
        work_tasks = get_tasks("Work", date(2024, 3, 15))
        personal_tasks = get_tasks("Personal", date(2024, 3, 15))

        assert work_tasks[0]["text"] == "Work version"
        assert personal_tasks[0]["text"] == "Personal version"

    def test_modifying_one_workspace_preserves_others(self, temp_devlog_home):
        """Modifying tasks in one workspace should not affect others."""
        # Setup tasks in both workspaces
        set_tasks("Work", date(2024, 3, 15), [
            {"id": "work1", "text": "Original", "done": False, "position": 0}
        ])
        set_tasks("Personal", date(2024, 3, 15), [
            {"id": "pers1", "text": "Original", "done": False, "position": 0}
        ])

        # Modify Work workspace
        work_tasks = get_tasks("Work", date(2024, 3, 15))
        work_tasks[0]["text"] = "Modified"
        work_tasks[0]["done"] = True
        set_tasks("Work", date(2024, 3, 15), work_tasks)

        # Personal should be unchanged
        personal_tasks = get_tasks("Personal", date(2024, 3, 15))
        assert personal_tasks[0]["text"] == "Original"
        assert personal_tasks[0]["done"] is False


class TestSwitchWorkspace:
    """Tests for switching active workspaces."""

    def test_switching_active_workspace(self, temp_devlog_home):
        """Changing active workspace should load correct tasks."""
        config = {
            "schema_version": 2,
            "workspaces": ["Work", "Personal", "Side Project"],
            "active_workspace": "Work",
        }
        save_config(config)

        # Create tasks in different workspaces
        set_tasks("Work", date(2024, 3, 15), [
            {"id": "work1", "text": "Work task", "done": False, "position": 0}
        ])
        set_tasks("Personal", date(2024, 3, 15), [
            {"id": "pers1", "text": "Personal task", "done": False, "position": 0}
        ])

        # Verify initial active workspace
        assert active_ws_name(config) == "Work"

        # Switch to Personal
        config["active_workspace"] = "Personal"
        save_config(config)

        reloaded = load_config()
        assert active_ws_name(reloaded) == "Personal"

    def test_fallback_to_first_workspace(self, temp_devlog_home):
        """Should fallback to first workspace if active not in list."""
        config = {
            "schema_version": 2,
            "workspaces": ["Work", "Personal"],
            "active_workspace": "NonExistent",
        }
        save_config(config)

        loaded = load_config()
        assert active_ws_name(loaded) == "Work"

    def test_handles_empty_workspace_list(self, temp_devlog_home):
        """Should handle empty workspace list gracefully."""
        config = {
            "schema_version": 2,
            "workspaces": [],
            "active_workspace": "Work",
        }
        save_config(config)

        loaded = load_config()
        assert active_ws_name(loaded) == "Personal"  # Default fallback


class TestMultipleWorkspaces:
    """Tests for operating on multiple workspaces."""

    def test_three_independent_workspaces(self, temp_devlog_home):
        """Three workspaces should operate independently."""
        config = {
            "schema_version": 2,
            "workspaces": ["Work", "Personal", "Side Project"],
            "active_workspace": "Work",
        }
        save_config(config)

        # Create unique tasks in each
        set_tasks("Work", date(2024, 3, 15), [
            {"id": "w1", "text": "Work task", "done": False, "position": 0}
        ])
        set_tasks("Personal", date(2024, 3, 15), [
            {"id": "p1", "text": "Personal task", "done": False, "position": 0}
        ])
        set_tasks("Side Project", date(2024, 3, 15), [
            {"id": "s1", "text": "Side project task", "done": False, "position": 0}
        ])

        # Verify each workspace has correct tasks
        work = get_tasks("Work", date(2024, 3, 15))
        personal = get_tasks("Personal", date(2024, 3, 15))
        side = get_tasks("Side Project", date(2024, 3, 15))

        assert len(work) == 1
        assert len(personal) == 1
        assert len(side) == 1

        assert work[0]["text"] == "Work task"
        assert personal[0]["text"] == "Personal task"
        assert side[0]["text"] == "Side project task"

    def test_workspace_with_special_characters(self, temp_devlog_home):
        """Workspace names with special characters should work."""
        ws_names = [
            "Client: Acme Corp",
            "Project-X",
            "Team_Alpha",
            "Q1 2024",
        ]

        for ws in ws_names:
            set_tasks(ws, date(2024, 3, 15), [
                {"id": f"task_{ws[:5]}", "text": f"Task for {ws}", "done": False, "position": 0}
            ])

        # All should be retrievable
        for ws in ws_names:
            tasks = get_tasks(ws, date(2024, 3, 15))
            assert len(tasks) == 1
            assert ws in tasks[0]["text"]

    def test_load_all_tasks_per_workspace(self, temp_devlog_home):
        """load_all_ws_tasks should only return tasks for specified workspace."""
        # Create tasks across multiple months in multiple workspaces
        for month in [1, 2, 3]:
            set_tasks("Work", date(2024, month, 15), [
                {"id": f"work_m{month}", "done": False, "position": 0}
            ])
            set_tasks("Personal", date(2024, month, 15), [
                {"id": f"pers_m{month}", "done": False, "position": 0}
            ])

        # Load all for Work
        work_all = load_all_ws_tasks("Work")
        assert len(work_all) == 3
        assert all("work" in tasks[0]["id"] for tasks in work_all.values())

        # Load all for Personal
        personal_all = load_all_ws_tasks("Personal")
        assert len(personal_all) == 3
        assert all("pers" in tasks[0]["id"] for tasks in personal_all.values())


class TestWorkspaceCreation:
    """Tests for creating new workspaces."""

    def test_creating_workspace_on_demand(self, temp_devlog_home):
        """New workspaces should be created automatically when used."""
        # No config yet, just use a new workspace name
        set_tasks("BrandNewWorkspace", date(2024, 3, 15), [
            {"id": "new1", "text": "First task", "done": False, "position": 0}
        ])

        # Should be retrievable
        tasks = get_tasks("BrandNewWorkspace", date(2024, 3, 15))
        assert len(tasks) == 1
        assert tasks[0]["text"] == "First task"

        # Directory should exist
        ws_dir = temp_devlog_home["tasks_dir"] / "BrandNewWorkspace"
        assert ws_dir.exists()

    def test_workspace_persists_after_creation(self, temp_devlog_home):
        """Workspace should persist after initial creation."""
        ws_name = "NewWorkspace"

        # Create with first task
        set_tasks(ws_name, date(2024, 3, 1), [
            {"id": "task1", "done": False, "position": 0}
        ])

        # Add more tasks later
        set_tasks(ws_name, date(2024, 3, 15), [
            {"id": "task2", "done": False, "position": 0}
        ])

        # Both dates should be accessible
        all_tasks = load_all_ws_tasks(ws_name)
        assert "2024-03-01" in all_tasks
        assert "2024-03-15" in all_tasks


class TestWorkspaceDeletion:
    """Tests for workspace cleanup."""

    def test_empty_workspace_directory_remains(self, temp_devlog_home):
        """Empty workspace directory should remain even after all tasks deleted."""
        ws_name = "TempWorkspace"

        # Create and then delete all tasks
        set_tasks(ws_name, date(2024, 3, 15), [
            {"id": "temp", "done": False, "position": 0}
        ])
        set_tasks(ws_name, date(2024, 3, 15), [])

        # Directory should still exist (empty but present)
        ws_dir = temp_devlog_home["tasks_dir"] / ws_name
        assert ws_dir.exists()
        assert len(list(ws_dir.glob("*.json"))) == 0

    def test_removing_all_months_from_workspace(self, temp_devlog_home):
        """Removing all month files should leave empty workspace directory."""
        ws_name = "CleanedWorkspace"

        # Add tasks to multiple months
        set_tasks(ws_name, date(2024, 1, 15), [{"id": "jan", "done": False, "position": 0}])
        set_tasks(ws_name, date(2024, 2, 15), [{"id": "feb", "done": False, "position": 0}])
        set_tasks(ws_name, date(2024, 3, 15), [{"id": "mar", "done": False, "position": 0}])

        # Remove all
        set_tasks(ws_name, date(2024, 1, 15), [])
        set_tasks(ws_name, date(2024, 2, 15), [])
        set_tasks(ws_name, date(2024, 3, 15), [])

        # No JSON files should remain
        ws_dir = temp_devlog_home["tasks_dir"] / ws_name
        json_files = list(ws_dir.glob("*.json"))
        assert len(json_files) == 0


class TestWorkspaceNaming:
    """Tests for workspace name handling."""

    def test_case_sensitive_workspace_names(self, temp_devlog_home):
        """Workspace names should be case-sensitive."""
        set_tasks("Work", date(2024, 3, 15), [
            {"id": "upper", "text": "Upper", "done": False, "position": 0}
        ])
        set_tasks("work", date(2024, 3, 15), [
            {"id": "lower", "text": "Lower", "done": False, "position": 0}
        ])

        # Should be separate
        upper_tasks = get_tasks("Work", date(2024, 3, 15))
        lower_tasks = get_tasks("work", date(2024, 3, 15))

        assert upper_tasks[0]["text"] == "Upper"
        assert lower_tasks[0]["text"] == "Lower"

    def test_workspace_name_with_unicode(self, temp_devlog_home):
        """Workspace names with unicode characters should work."""
        ws_name = "プロジェクト"  # Japanese "Project"

        set_tasks(ws_name, date(2024, 3, 15), [
            {"id": "unicode1", "text": "Unicode task", "done": False, "position": 0}
        ])

        tasks = get_tasks(ws_name, date(2024, 3, 15))
        assert len(tasks) == 1

    def test_very_long_workspace_name(self, temp_devlog_home):
        """Very long workspace names should work."""
        ws_name = "A" * 200  # 200 character name

        set_tasks(ws_name, date(2024, 3, 15), [
            {"id": "long1", "done": False, "position": 0}
        ])

        tasks = get_tasks(ws_name, date(2024, 3, 15))
        assert len(tasks) == 1
