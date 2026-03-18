"""Integration tests for CLI commands."""

import json
import pytest
from datetime import datetime, date
from io import StringIO
from unittest.mock import patch
from devlog.cli import (
    parse_date,
    cli_list,
    cli_add,
    cli_done,
    create_parser,
)
from devlog.core.persistence import get_tasks, set_tasks
from devlog.core.config import save_config


class TestParseDate:
    """Tests for parse_date() function."""

    def test_parse_date_today(self):
        """parse_date should handle 'today' keyword."""
        result = parse_date("today")
        assert result.date() == datetime.now().date()

    def test_parse_date_now(self):
        """parse_date should handle 'now' keyword."""
        result = parse_date("now")
        assert result.date() == datetime.now().date()

    def test_parse_date_tomorrow(self):
        """parse_date should handle 'tomorrow' keyword."""
        result = parse_date("tomorrow")
        expected = (datetime.now().date() + __import__("datetime").timedelta(days=1))
        assert result.date() == expected

    def test_parse_date_yesterday(self):
        """parse_date should handle 'yesterday' keyword."""
        result = parse_date("yesterday")
        expected = (datetime.now().date() - __import__("datetime").timedelta(days=1))
        assert result.date() == expected

    def test_parse_date_yyyy_mm_dd(self):
        """parse_date should parse YYYY-MM-DD format."""
        result = parse_date("2024-03-15")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15

    def test_parse_date_case_insensitive(self):
        """parse_date should be case-insensitive."""
        assert parse_date("TODAY").date() == datetime.now().date()
        assert parse_date("Tomorrow").date() == (
            datetime.now().date() + __import__("datetime").timedelta(days=1)
        )

    def test_parse_date_invalid_format(self):
        """parse_date should exit with error for invalid format."""
        with pytest.raises(SystemExit):
            parse_date("invalid-date")

    def test_parse_date_none_returns_now(self):
        """parse_date should return now() when passed None."""
        result = parse_date(None)
        assert result.date() == datetime.now().date()

    def test_parse_date_empty_string_returns_now(self):
        """parse_date should return now() for empty string."""
        result = parse_date("")
        assert result.date() == datetime.now().date()


class TestCliList:
    """Tests for cli_list command."""

    def test_cli_list_empty(self, temp_devlog_home, capsys):
        """cli_list should handle empty task list."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "json": False,
        })()

        cli_list(args)
        captured = capsys.readouterr()
        assert "Tasks for" in captured.out
        assert "TODO" not in captured.out
        assert "DONE" not in captured.out

    def test_cli_list_with_tasks(self, populated_workspace, capsys):
        """cli_list should display tasks."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-15",
            "json": False,
        })()

        cli_list(args)
        captured = capsys.readouterr()
        assert "TODO" in captured.out
        assert "Write unit tests" in captured.out
        assert "Review pull request" in captured.out

    def test_cli_list_json_output(self, populated_workspace, capsys):
        """cli_list should produce valid JSON with --json flag."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-15",
            "json": True,
        })()

        cli_list(args)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert output["date"] == "2024-03-15"
        assert output["workspace"] == "Work"
        assert isinstance(output["tasks"], list)
        assert len(output["tasks"]) == 2

    def test_cli_list_workspace_flag(self, populated_workspace, capsys):
        """cli_list should respect -w workspace flag."""
        # Add tasks to a different workspace
        set_tasks("Personal", date(2024, 3, 15), [
            {"id": "per123", "text": "Personal task", "done": False, "position": 0}
        ])

        args = type("Args", (), {
            "workspace": "Personal",
            "date": "2024-03-15",
            "json": False,
        })()

        cli_list(args)
        captured = capsys.readouterr()
        assert "Personal task" in captured.out
        assert "Write unit tests" not in captured.out


class TestCliAdd:
    """Tests for cli_add command."""

    def test_cli_add_creates_task(self, temp_devlog_home, capsys):
        """cli_add should create a new task."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "text": "New test task",
            "json": False,
        })()

        cli_add(args)
        captured = capsys.readouterr()
        assert "Added task: New test task" in captured.out
        assert "ID:" in captured.out

        # Verify task was saved
        tasks = get_tasks("Personal", datetime.now())
        assert len(tasks) == 1
        assert tasks[0]["text"] == "New test task"
        assert tasks[0]["done"] is False

    def test_cli_add_json_output(self, temp_devlog_home, capsys):
        """cli_add should output JSON with --json flag."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "text": "JSON test task",
            "json": True,
        })()

        cli_add(args)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert output["text"] == "JSON test task"
        assert output["done"] is False
        assert "id" in output
        assert "created_at" in output

    def test_cli_add_uses_current_date_by_default(self, temp_devlog_home):
        """cli_add should use current date when none specified."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = type("Args", (), {
            "workspace": None,
            "date": None,
            "text": "Task for today",
            "json": False,
        })()

        cli_add(args)

        tasks = get_tasks("Personal", datetime.now())
        assert len(tasks) == 1

    def test_cli_add_to_specific_date(self, temp_devlog_home):
        """cli_add should create task on specified date."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = type("Args", (), {
            "workspace": None,
            "date": "2024-05-20",
            "text": "Future task",
            "json": False,
        })()

        cli_add(args)

        tasks = get_tasks("Personal", date(2024, 5, 20))
        assert len(tasks) == 1
        assert tasks[0]["text"] == "Future task"


class TestCliDone:
    """Tests for cli_done command."""

    def test_cli_done_marks_task_complete(self, populated_workspace, capsys):
        """cli_done should mark task as completed."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-15",
            "task_id": "abc12345",
            "json": False,
        })()

        cli_done(args)
        captured = capsys.readouterr()
        assert "Marked as done" in captured.out

        tasks = get_tasks("Work", date(2024, 3, 15))
        _, task = __import__("devlog.core.tasks", fromlist=["find_task"]).find_task(
            tasks, "abc12345"
        )
        assert task["done"] is True
        assert task["completed_at"] is not None

    def test_cli_done_idempotent(self, populated_workspace, capsys):
        """cli_done should succeed even if task already done."""
        # Mark as done first time
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-14",
            "task_id": "ghi11111",
            "json": False,
        })()

        cli_done(args)

        # Mark as done again (should succeed)
        cli_done(args)
        captured = capsys.readouterr()
        assert "Marked as done" in captured.out

    def test_cli_done_json_output(self, populated_workspace, capsys):
        """cli_done should output JSON with --json flag."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-15",
            "task_id": "abc12345",
            "json": True,
        })()

        cli_done(args)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert output["id"] == "abc12345"
        assert output["done"] is True
        assert output["completed_at"] is not None

    def test_cli_done_without_date_searches_all(self, populated_workspace, capsys):
        """cli_done should search all dates when --date not specified."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": None,
            "task_id": "abc12345",
            "json": False,
        })()

        cli_done(args)
        captured = capsys.readouterr()
        assert "Marked as done" in captured.out

    def test_cli_done_nonexistent_task(self, populated_workspace):
        """cli_done should exit with error for non-existent task."""
        args = type("Args", (), {
            "workspace": "Work",
            "date": "2024-03-15",
            "task_id": "nonexistent",
            "json": False,
        })()

        with pytest.raises(SystemExit):
            cli_done(args)


@pytest.mark.integration
class TestCLIEndToEnd:
    """End-to-end integration tests for CLI workflow."""

    def test_complete_workflow(self, temp_devlog_home, capsys):
        """Test complete workflow: add -> list -> done -> list."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        # Step 1: Add a task
        add_args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "text": "Complete workflow task",
            "json": True,
        })()

        cli_add(add_args)
        add_output = capsys.readouterr().out
        task = json.loads(add_output)
        task_id = task["id"]

        # Step 2: List tasks (should show as TODO)
        list_args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "json": True,
        })()

        cli_list(list_args)
        list_output = json.loads(capsys.readouterr().out)
        assert len(list_output["tasks"]) == 1
        assert list_output["tasks"][0]["done"] is False

        # Step 3: Mark as done
        done_args = type("Args", (), {
            "workspace": None,
            "date": "today",
            "task_id": task_id,
            "json": False,
        })()

        cli_done(done_args)
        capsys.readouterr()  # Clear output

        # Step 4: List again (should show as DONE)
        cli_list(list_args)
        list_output2 = json.loads(capsys.readouterr().out)
        assert list_output2["tasks"][0]["done"] is True
        assert list_output2["tasks"][0]["completed_at"] is not None

    def test_multi_workspace_isolation(self, temp_devlog_home):
        """Test that workspaces keep tasks isolated."""
        config = {
            "schema_version": 2,
            "workspaces": ["Work", "Personal"],
            "active_workspace": "Work",
        }
        save_config(config)

        # Add task to Work workspace
        work_args = type("Args", (), {
            "workspace": "Work",
            "date": "today",
            "text": "Work task",
            "json": False,
        })()
        cli_add(work_args)

        # Add task to Personal workspace
        personal_args = type("Args", (), {
            "workspace": "Personal",
            "date": "today",
            "text": "Personal task",
            "json": False,
        })()
        cli_add(personal_args)

        # Verify isolation
        work_tasks = get_tasks("Work", datetime.now())
        personal_tasks = get_tasks("Personal", datetime.now())

        assert len(work_tasks) == 1
        assert len(personal_tasks) == 1
        assert work_tasks[0]["text"] == "Work task"
        assert personal_tasks[0]["text"] == "Personal task"
