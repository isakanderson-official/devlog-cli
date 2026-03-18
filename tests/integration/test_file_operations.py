"""Integration tests for filesystem operations and edge cases."""

import json
import pytest
from pathlib import Path
from datetime import date
from devlog.core.persistence import (
    get_tasks,
    set_tasks,
    load_month,
    save_month,
    load_all_ws_tasks,
)


class TestCorruptedFileRecovery:
    """Tests for handling corrupted or invalid files."""

    def test_corrupted_json_returns_empty(self, temp_devlog_home):
        """load_month should return empty dict for corrupted JSON."""
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        corrupt_file = ws_dir / "2024-03.json"
        with open(corrupt_file, "w") as f:
            f.write("{invalid json content [}")

        # Should return empty dict instead of crashing
        result = load_month("Work", 2024, 3)
        assert result == {}

    def test_corrupted_task_file_allows_recovery(self, temp_devlog_home):
        """get_tasks should allow recovery from corrupted files."""
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted file
        corrupt_file = ws_dir / "2024-03.json"
        with open(corrupt_file, "w") as f:
            f.write("not valid json at all")

        # Getting tasks should return empty
        tasks = get_tasks("Work", date(2024, 3, 15))
        assert tasks == []

        # Should be able to write new tasks (recovery)
        new_tasks = [{"id": "recover1", "text": "Recovered", "done": False, "position": 0}]
        set_tasks("Work", date(2024, 3, 15), new_tasks)

        # Verify recovery worked
        loaded = get_tasks("Work", date(2024, 3, 15))
        assert len(loaded) == 1
        assert loaded[0]["id"] == "recover1"

    def test_partial_corruption_in_multi_month(self, temp_devlog_home):
        """load_all_ws_tasks should skip corrupted files and load valid ones."""
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # Valid March file
        save_month("Work", 2024, 3, {"2024-03-15": [{"id": "valid1"}]})

        # Corrupted April file
        april_file = ws_dir / "2024-04.json"
        with open(april_file, "w") as f:
            f.write("{corrupt}")

        # Valid May file
        save_month("Work", 2024, 5, {"2024-05-10": [{"id": "valid2"}]})

        # Should load valid files and skip corrupted
        all_tasks = load_all_ws_tasks("Work")
        assert "2024-03-15" in all_tasks
        assert "2024-05-10" in all_tasks
        # April should not be present
        assert not any("2024-04" in k for k in all_tasks.keys())


class TestDirectoryCreation:
    """Tests for automatic directory creation."""

    def test_creates_workspace_directory(self, temp_devlog_home):
        """set_tasks should create workspace directory if missing."""
        assert not (temp_devlog_home["tasks_dir"] / "NewWorkspace").exists()

        tasks = [{"id": "test1", "text": "Test", "done": False, "position": 0}]
        set_tasks("NewWorkspace", date(2024, 3, 15), tasks)

        assert (temp_devlog_home["tasks_dir"] / "NewWorkspace").exists()

    def test_creates_nested_structure(self, temp_devlog_home):
        """save_month should create full directory tree."""
        # Verify nothing exists yet
        assert not temp_devlog_home["tasks_dir"].exists()

        save_month("Work", 2024, 3, {"2024-03-15": []})

        # Verify full path created
        expected_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert expected_file.exists()

    def test_handles_existing_directories(self, temp_devlog_home):
        """Directory creation should handle existing directories gracefully."""
        # Pre-create directories
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # Should not fail when directories exist
        save_month("Work", 2024, 3, {"2024-03-15": []})

        # Should succeed
        assert (ws_dir / "2024-03.json").exists()


class TestMonthlyPartitioning:
    """Tests for monthly file partitioning."""

    def test_tasks_route_to_correct_month(self, temp_devlog_home):
        """Tasks should be saved to correct month files."""
        # Add tasks to different months
        set_tasks("Work", date(2024, 3, 15), [{"id": "mar1", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 4, 10), [{"id": "apr1", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 5, 20), [{"id": "may1", "position": 0, "done": False}])

        # Verify separate files created
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        assert (ws_dir / "2024-03.json").exists()
        assert (ws_dir / "2024-04.json").exists()
        assert (ws_dir / "2024-05.json").exists()

    def test_same_month_different_dates(self, temp_devlog_home):
        """Multiple dates in same month should share one file."""
        set_tasks("Work", date(2024, 3, 1), [{"id": "day1", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 3, 15), [{"id": "day15", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 3, 31), [{"id": "day31", "position": 0, "done": False}])

        # Should only have one March file
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        march_files = list(ws_dir.glob("2024-03*.json"))
        assert len(march_files) == 1

        # Verify all dates present in file
        month_data = load_month("Work", 2024, 3)
        assert "2024-03-01" in month_data
        assert "2024-03-15" in month_data
        assert "2024-03-31" in month_data

    def test_year_boundary_handling(self, temp_devlog_home):
        """Tasks across year boundary should create separate files."""
        set_tasks("Work", date(2023, 12, 31), [{"id": "2023", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 1, 1), [{"id": "2024", "position": 0, "done": False}])

        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        assert (ws_dir / "2023-12.json").exists()
        assert (ws_dir / "2024-01.json").exists()


class TestEmptyMonthCleanup:
    """Tests for cleaning up empty month files."""

    def test_deletes_file_when_no_tasks_remain(self, temp_devlog_home):
        """save_month should delete file when all tasks removed."""
        # Create file with data
        save_month("Work", 2024, 3, {"2024-03-15": [{"id": "task1"}]})

        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert month_file.exists()

        # Save empty data
        save_month("Work", 2024, 3, {})

        # File should be deleted
        assert not month_file.exists()

    def test_deletes_when_all_dates_cleared(self, temp_devlog_home):
        """Month file should be deleted when all dates cleared."""
        # Create with multiple dates
        set_tasks("Work", date(2024, 3, 10), [{"id": "task1", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 3, 20), [{"id": "task2", "position": 0, "done": False}])

        # Clear both dates
        set_tasks("Work", date(2024, 3, 10), [])
        set_tasks("Work", date(2024, 3, 20), [])

        # File should be deleted
        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert not month_file.exists()

    def test_preserves_file_with_remaining_dates(self, temp_devlog_home):
        """Month file should remain if any dates have tasks."""
        set_tasks("Work", date(2024, 3, 10), [{"id": "task1", "position": 0, "done": False}])
        set_tasks("Work", date(2024, 3, 20), [{"id": "task2", "position": 0, "done": False}])

        # Clear only one date
        set_tasks("Work", date(2024, 3, 10), [])

        # File should still exist
        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert month_file.exists()

        # Should only have March 20 tasks
        month_data = load_month("Work", 2024, 3)
        assert "2024-03-10" not in month_data
        assert "2024-03-20" in month_data


class TestAtomicOperations:
    """Tests for atomic write operations."""

    def test_atomic_write_prevents_partial_writes(self, temp_devlog_home):
        """Writes should be atomic (temp file then rename)."""
        tasks = [{"id": f"task{i}", "position": i, "done": False} for i in range(100)]

        # Write should complete atomically
        set_tasks("Work", date(2024, 3, 15), tasks)

        # Verify complete write
        loaded = get_tasks("Work", date(2024, 3, 15))
        assert len(loaded) == 100

    def test_no_temp_files_left_behind(self, temp_devlog_home):
        """Temporary files should be cleaned up after write."""
        set_tasks("Work", date(2024, 3, 15), [{"id": "task1", "position": 0, "done": False}])

        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        temp_files = list(ws_dir.glob("*.tmp"))

        assert len(temp_files) == 0

    def test_concurrent_writes_safe(self, temp_devlog_home):
        """Multiple writes to different dates should be safe."""
        # Simulate concurrent writes to different dates
        for day in range(1, 11):
            set_tasks("Work", date(2024, 3, day), [
                {"id": f"task_day_{day}", "position": 0, "done": False}
            ])

        # All should be present
        month_data = load_month("Work", 2024, 3)
        assert len(month_data) == 10

        for day in range(1, 11):
            date_key = f"2024-03-{day:02d}"
            assert date_key in month_data


class TestLargeDatasets:
    """Tests for handling large amounts of data."""

    def test_many_tasks_in_single_date(self, temp_devlog_home):
        """Should handle hundreds of tasks in one date."""
        tasks = [
            {
                "id": f"task{i:04d}",
                "text": f"Task number {i}",
                "done": i % 3 == 0,
                "position": i,
            }
            for i in range(500)
        ]

        set_tasks("Work", date(2024, 3, 15), tasks)
        loaded = get_tasks("Work", date(2024, 3, 15))

        assert len(loaded) == 500

    def test_many_dates_in_workspace(self, temp_devlog_home):
        """Should handle many dates across multiple months."""
        # Create tasks for every day in Q1 2024
        for month in [1, 2, 3]:
            days_in_month = [31, 29, 31][month - 1]  # 2024 is leap year
            for day in range(1, days_in_month + 1):
                set_tasks("Work", date(2024, month, day), [
                    {"id": f"m{month}d{day}", "position": 0, "done": False}
                ])

        # Load all should work
        all_tasks = load_all_ws_tasks("Work")
        assert len(all_tasks) == 31 + 29 + 31  # Jan + Feb + Mar

    def test_many_workspaces(self, temp_devlog_home):
        """Should handle many workspaces."""
        for i in range(50):
            ws_name = f"Workspace{i}"
            set_tasks(ws_name, date(2024, 3, 15), [
                {"id": f"task_ws{i}", "position": 0, "done": False}
            ])

        # All workspace directories should exist
        workspace_dirs = list(temp_devlog_home["tasks_dir"].glob("Workspace*"))
        assert len(workspace_dirs) == 50
