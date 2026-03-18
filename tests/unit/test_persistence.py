"""Unit tests for devlog.core.persistence module."""

import json
import pytest
from pathlib import Path
from datetime import datetime, date
from devlog.core.persistence import (
    _atomic_write,
    _read_json,
    _month_file,
    date_key,
    load_month,
    save_month,
    get_tasks,
    set_tasks,
    load_all_ws_tasks,
)


class TestAtomicWrite:
    """Tests for _atomic_write() function."""

    def test_atomic_write_creates_file(self, temp_devlog_home):
        """_atomic_write should create file with correct data."""
        test_file = temp_devlog_home["data_dir"] / "test.json"
        data = {"key": "value", "number": 42}

        _atomic_write(test_file, data)

        assert test_file.exists()
        with open(test_file) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_atomic_write_creates_parent_dirs(self, temp_devlog_home):
        """_atomic_write should create parent directories if missing."""
        test_file = temp_devlog_home["data_dir"] / "nested" / "deep" / "file.json"
        data = {"test": True}

        _atomic_write(test_file, data)

        assert test_file.exists()
        assert test_file.parent.exists()

    def test_atomic_write_overwrites_existing(self, temp_devlog_home):
        """_atomic_write should overwrite existing file."""
        test_file = temp_devlog_home["data_dir"] / "test.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Write initial data
        _atomic_write(test_file, {"version": 1})
        # Overwrite with new data
        _atomic_write(test_file, {"version": 2})

        with open(test_file) as f:
            loaded = json.load(f)
        assert loaded == {"version": 2}

    def test_atomic_write_uses_temp_file(self, temp_devlog_home):
        """_atomic_write should use temporary file for safety."""
        test_file = temp_devlog_home["data_dir"] / "test.json"
        temp_file = test_file.with_suffix(".tmp")

        _atomic_write(test_file, {"data": "test"})

        # Temp file should be gone after successful write
        assert not temp_file.exists()
        assert test_file.exists()


class TestReadJson:
    """Tests for _read_json() function."""

    def test_read_json_valid_file(self, temp_devlog_home):
        """_read_json should load valid JSON file."""
        test_file = temp_devlog_home["data_dir"] / "valid.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"key": "value", "list": [1, 2, 3]}

        with open(test_file, "w") as f:
            json.dump(data, f)

        loaded = _read_json(test_file)
        assert loaded == data

    def test_read_json_missing_file(self, temp_devlog_home):
        """_read_json should return None for missing file."""
        test_file = temp_devlog_home["data_dir"] / "missing.json"
        assert _read_json(test_file) is None

    def test_read_json_invalid_json(self, temp_devlog_home):
        """_read_json should return None for invalid JSON."""
        test_file = temp_devlog_home["data_dir"] / "invalid.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        with open(test_file, "w") as f:
            f.write("{invalid json content")

        assert _read_json(test_file) is None

    def test_read_json_empty_file(self, temp_devlog_home):
        """_read_json should return None for empty file."""
        test_file = temp_devlog_home["data_dir"] / "empty.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        assert _read_json(test_file) is None


class TestMonthFile:
    """Tests for _month_file() function."""

    def test_month_file_path_construction(self, temp_devlog_home):
        """_month_file should construct correct path."""
        path = _month_file("Work", 2024, 3)
        expected = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert path == expected

    def test_month_file_single_digit_month(self, temp_devlog_home):
        """_month_file should zero-pad single-digit months."""
        path = _month_file("Personal", 2024, 1)
        assert path.name == "2024-01.json"

    def test_month_file_december(self, temp_devlog_home):
        """_month_file should handle December correctly."""
        path = _month_file("Personal", 2024, 12)
        assert path.name == "2024-12.json"


class TestDateKey:
    """Tests for date_key() function."""

    def test_date_key_from_datetime(self):
        """date_key should format datetime objects correctly."""
        dt = datetime(2024, 3, 15, 14, 30, 0)
        assert date_key(dt) == "2024-03-15"

    def test_date_key_from_date(self):
        """date_key should format date objects correctly."""
        d = date(2024, 3, 15)
        assert date_key(d) == "2024-03-15"

    def test_date_key_single_digit_month(self):
        """date_key should zero-pad single-digit months."""
        d = date(2024, 1, 5)
        assert date_key(d) == "2024-01-05"

    def test_date_key_single_digit_day(self):
        """date_key should zero-pad single-digit days."""
        d = date(2024, 12, 3)
        assert date_key(d) == "2024-12-03"


class TestLoadMonth:
    """Tests for load_month() function."""

    def test_load_month_empty_month(self, temp_devlog_home):
        """load_month should return empty dict for non-existent month."""
        result = load_month("Work", 2024, 3)
        assert result == {}

    def test_load_month_existing_data(self, temp_devlog_home, sample_month_data):
        """load_month should load existing month data."""
        # Save data first
        save_month("Work", 2024, 3, sample_month_data)

        # Load it back
        result = load_month("Work", 2024, 3)
        assert result == sample_month_data

    def test_load_month_different_workspaces(self, temp_devlog_home, sample_month_data):
        """load_month should isolate data by workspace."""
        save_month("Work", 2024, 3, sample_month_data)
        save_month("Personal", 2024, 3, {"2024-03-01": []})

        work_data = load_month("Work", 2024, 3)
        personal_data = load_month("Personal", 2024, 3)

        assert work_data != personal_data
        assert work_data == sample_month_data


class TestSaveMonth:
    """Tests for save_month() function."""

    def test_save_month_creates_file(self, temp_devlog_home, sample_month_data):
        """save_month should create month file."""
        save_month("Work", 2024, 3, sample_month_data)

        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert month_file.exists()

    def test_save_month_updates_existing(self, temp_devlog_home):
        """save_month should update existing month file."""
        data_v1 = {"2024-03-15": [{"id": "a"}]}
        data_v2 = {"2024-03-15": [{"id": "b"}], "2024-03-16": [{"id": "c"}]}

        save_month("Work", 2024, 3, data_v1)
        save_month("Work", 2024, 3, data_v2)

        loaded = load_month("Work", 2024, 3)
        assert loaded == data_v2

    def test_save_month_deletes_when_empty(self, temp_devlog_home):
        """save_month should delete file when data is empty."""
        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"

        # Create file with data
        save_month("Work", 2024, 3, {"2024-03-15": []})
        assert month_file.exists()

        # Save empty data
        save_month("Work", 2024, 3, {})
        assert not month_file.exists()

    def test_save_month_handles_empty_dict(self, temp_devlog_home):
        """save_month should not create file for empty dict."""
        save_month("Work", 2024, 3, {})

        month_file = temp_devlog_home["tasks_dir"] / "Work" / "2024-03.json"
        assert not month_file.exists()


class TestGetTasks:
    """Tests for get_tasks() function."""

    def test_get_tasks_missing_date(self, temp_devlog_home):
        """get_tasks should return empty list for missing date."""
        result = get_tasks("Work", date(2024, 3, 15))
        assert result == []

    def test_get_tasks_existing_date(self, temp_devlog_home, sample_tasks):
        """get_tasks should return tasks for existing date."""
        month_data = {"2024-03-15": sample_tasks}
        save_month("Work", 2024, 3, month_data)

        result = get_tasks("Work", date(2024, 3, 15))
        assert result == sample_tasks

    def test_get_tasks_with_datetime(self, temp_devlog_home, sample_tasks):
        """get_tasks should work with datetime objects."""
        month_data = {"2024-03-15": sample_tasks}
        save_month("Work", 2024, 3, month_data)

        result = get_tasks("Work", datetime(2024, 3, 15, 14, 30))
        assert result == sample_tasks

    def test_get_tasks_different_dates_same_month(self, temp_devlog_home):
        """get_tasks should distinguish between dates in same month."""
        month_data = {
            "2024-03-15": [{"id": "a"}],
            "2024-03-16": [{"id": "b"}],
        }
        save_month("Work", 2024, 3, month_data)

        tasks_15 = get_tasks("Work", date(2024, 3, 15))
        tasks_16 = get_tasks("Work", date(2024, 3, 16))

        assert len(tasks_15) == 1
        assert tasks_15[0]["id"] == "a"
        assert len(tasks_16) == 1
        assert tasks_16[0]["id"] == "b"


class TestSetTasks:
    """Tests for set_tasks() function."""

    def test_set_tasks_creates_new(self, temp_devlog_home, sample_tasks):
        """set_tasks should create new date entry."""
        set_tasks("Work", date(2024, 3, 15), sample_tasks)

        loaded = get_tasks("Work", date(2024, 3, 15))
        assert len(loaded) == len(sample_tasks)

    def test_set_tasks_updates_existing(self, temp_devlog_home):
        """set_tasks should update existing date entry."""
        initial = [{"id": "a", "done": False, "position": 0}]
        updated = [{"id": "b", "done": False, "position": 0}]

        set_tasks("Work", date(2024, 3, 15), initial)
        set_tasks("Work", date(2024, 3, 15), updated)

        loaded = get_tasks("Work", date(2024, 3, 15))
        assert len(loaded) == 1
        assert loaded[0]["id"] == "b"

    def test_set_tasks_deletes_when_empty(self, temp_devlog_home):
        """set_tasks should remove date entry when tasks list is empty."""
        set_tasks("Work", date(2024, 3, 15), [{"id": "a", "done": False, "position": 0}])
        set_tasks("Work", date(2024, 3, 15), [])

        loaded = get_tasks("Work", date(2024, 3, 15))
        assert loaded == []

    def test_set_tasks_calls_reposition(self, temp_devlog_home):
        """set_tasks should call reposition on tasks."""
        tasks = [
            {"id": "a", "done": False, "position": 100},
            {"id": "b", "done": False, "position": 50},
        ]

        set_tasks("Work", date(2024, 3, 15), tasks)
        loaded = get_tasks("Work", date(2024, 3, 15))

        # Positions should be normalized to 0, 1
        positions = [t["position"] for t in loaded]
        assert sorted(positions) == [0, 1]

    def test_set_tasks_preserves_other_dates(self, temp_devlog_home):
        """set_tasks should not affect other dates in same month."""
        set_tasks("Work", date(2024, 3, 15), [{"id": "a", "done": False, "position": 0}])
        set_tasks("Work", date(2024, 3, 16), [{"id": "b", "done": False, "position": 0}])

        tasks_15 = get_tasks("Work", date(2024, 3, 15))
        tasks_16 = get_tasks("Work", date(2024, 3, 16))

        assert len(tasks_15) == 1
        assert len(tasks_16) == 1
        assert tasks_15[0]["id"] != tasks_16[0]["id"]


class TestLoadAllWsTasks:
    """Tests for load_all_ws_tasks() function."""

    def test_load_all_ws_tasks_empty_workspace(self, temp_devlog_home):
        """load_all_ws_tasks should return empty dict for non-existent workspace."""
        result = load_all_ws_tasks("NonExistent")
        assert result == {}

    def test_load_all_ws_tasks_single_month(self, temp_devlog_home, sample_month_data):
        """load_all_ws_tasks should load single month."""
        save_month("Work", 2024, 3, sample_month_data)

        result = load_all_ws_tasks("Work")
        assert result == sample_month_data

    def test_load_all_ws_tasks_multiple_months(self, temp_devlog_home):
        """load_all_ws_tasks should aggregate multiple months."""
        march_data = {"2024-03-15": [{"id": "a"}]}
        april_data = {"2024-04-10": [{"id": "b"}]}

        save_month("Work", 2024, 3, march_data)
        save_month("Work", 2024, 4, april_data)

        result = load_all_ws_tasks("Work")

        assert "2024-03-15" in result
        assert "2024-04-10" in result
        assert result["2024-03-15"][0]["id"] == "a"
        assert result["2024-04-10"][0]["id"] == "b"

    def test_load_all_ws_tasks_handles_missing_workspace_dir(self, temp_devlog_home):
        """load_all_ws_tasks should handle missing workspace directory."""
        result = load_all_ws_tasks("NonExistent")
        assert result == {}

    def test_load_all_ws_tasks_skips_invalid_files(self, temp_devlog_home):
        """load_all_ws_tasks should skip corrupted JSON files."""
        ws_dir = temp_devlog_home["tasks_dir"] / "Work"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # Create valid file
        valid_file = ws_dir / "2024-03.json"
        with open(valid_file, "w") as f:
            json.dump({"2024-03-15": [{"id": "valid"}]}, f)

        # Create invalid file
        invalid_file = ws_dir / "2024-04.json"
        with open(invalid_file, "w") as f:
            f.write("{invalid json")

        result = load_all_ws_tasks("Work")

        # Should load valid file and skip invalid
        assert "2024-03-15" in result
        assert result["2024-03-15"][0]["id"] == "valid"
