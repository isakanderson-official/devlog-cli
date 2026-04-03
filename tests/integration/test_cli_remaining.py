"""Integration tests for remaining CLI commands: undone, delete, edit, search, stats, export, import."""

import json
import pytest
from datetime import datetime, date
from io import StringIO
from unittest.mock import patch
from devlog.cli import (
    cli_undone,
    cli_delete,
    cli_edit,
    cli_search,
    cli_stats,
    cli_export,
    cli_import,
    execute_cli_command,
    create_parser,
)
from devlog.core.persistence import get_tasks, set_tasks
from devlog.core.config import save_config


def _args(**kwargs):
    """Helper to create a mock args object."""
    return type("Args", (), kwargs)()


class TestCliUndone:
    """Tests for cli_undone command."""

    def test_undone_with_date(self, populated_workspace, capsys):
        """cli_undone should mark a done task as pending."""
        args = _args(workspace="Work", date="2024-03-14", task_id="ghi11111", json=False)
        cli_undone(args)
        captured = capsys.readouterr()
        assert "Marked as pending" in captured.out

        tasks = get_tasks("Work", date(2024, 3, 14))
        from devlog.core.tasks import find_task
        _, task = find_task(tasks, "ghi11111")
        assert task["done"] is False
        assert task["completed_at"] is None

    def test_undone_json_output(self, populated_workspace, capsys):
        """cli_undone should output JSON with --json flag."""
        args = _args(workspace="Work", date="2024-03-14", task_id="ghi11111", json=True)
        cli_undone(args)
        output = json.loads(capsys.readouterr().out)
        assert output["done"] is False

    def test_undone_without_date(self, populated_workspace, capsys):
        """cli_undone should search all dates when --date not specified."""
        args = _args(workspace="Work", date=None, task_id="ghi11111", json=False)
        cli_undone(args)
        assert "Marked as pending" in capsys.readouterr().out

    def test_undone_nonexistent(self, populated_workspace):
        """cli_undone should exit with error for non-existent task."""
        args = _args(workspace="Work", date="2024-03-14", task_id="nonexistent", json=False)
        with pytest.raises(SystemExit):
            cli_undone(args)

    def test_undone_without_date_nonexistent(self, populated_workspace):
        """cli_undone should exit when task not found across all dates."""
        args = _args(workspace="Work", date=None, task_id="nonexistent", json=False)
        with pytest.raises(SystemExit):
            cli_undone(args)

    def test_undone_without_date_json(self, populated_workspace, capsys):
        """cli_undone without date should support JSON output."""
        args = _args(workspace="Work", date=None, task_id="ghi11111", json=True)
        cli_undone(args)
        output = json.loads(capsys.readouterr().out)
        assert output["done"] is False


class TestCliDelete:
    """Tests for cli_delete command."""

    def test_delete_with_date(self, populated_workspace, capsys):
        """cli_delete should remove a task."""
        args = _args(workspace="Work", date="2024-03-15", task_id="abc12345", json=False)
        cli_delete(args)
        assert "Deleted" in capsys.readouterr().out

        tasks = get_tasks("Work", date(2024, 3, 15))
        assert len(tasks) == 1  # was 2, now 1

    def test_delete_json_output(self, populated_workspace, capsys):
        """cli_delete should output JSON with --json flag."""
        args = _args(workspace="Work", date="2024-03-15", task_id="abc12345", json=True)
        cli_delete(args)
        output = json.loads(capsys.readouterr().out)
        assert output["deleted"] is True
        assert output["task_id"] == "abc12345"

    def test_delete_without_date(self, populated_workspace, capsys):
        """cli_delete should search all dates when --date not specified."""
        args = _args(workspace="Work", date=None, task_id="abc12345", json=False)
        cli_delete(args)
        assert "Deleted" in capsys.readouterr().out

    def test_delete_without_date_json(self, populated_workspace, capsys):
        """cli_delete without date should support JSON output."""
        args = _args(workspace="Work", date=None, task_id="abc12345", json=True)
        cli_delete(args)
        output = json.loads(capsys.readouterr().out)
        assert output["deleted"] is True

    def test_delete_nonexistent(self, populated_workspace):
        """cli_delete should exit with error for non-existent task."""
        args = _args(workspace="Work", date="2024-03-15", task_id="nonexistent", json=False)
        with pytest.raises(SystemExit):
            cli_delete(args)

    def test_delete_without_date_nonexistent(self, populated_workspace):
        """cli_delete should exit when task not found across all dates."""
        args = _args(workspace="Work", date=None, task_id="nonexistent", json=False)
        with pytest.raises(SystemExit):
            cli_delete(args)


class TestCliEdit:
    """Tests for cli_edit command."""

    def test_edit_with_date(self, populated_workspace, capsys):
        """cli_edit should update task text."""
        args = _args(workspace="Work", date="2024-03-15", task_id="abc12345", text="Updated text", json=False)
        cli_edit(args)
        captured = capsys.readouterr()
        assert "Updated task" in captured.out
        assert "Updated text" in captured.out

        tasks = get_tasks("Work", date(2024, 3, 15))
        from devlog.core.tasks import find_task
        _, task = find_task(tasks, "abc12345")
        assert task["text"] == "Updated text"

    def test_edit_json_output(self, populated_workspace, capsys):
        """cli_edit should output JSON with --json flag."""
        args = _args(workspace="Work", date="2024-03-15", task_id="abc12345", text="New text", json=True)
        cli_edit(args)
        output = json.loads(capsys.readouterr().out)
        assert output["text"] == "New text"

    def test_edit_without_date(self, populated_workspace, capsys):
        """cli_edit should search all dates when --date not specified."""
        args = _args(workspace="Work", date=None, task_id="abc12345", text="Edited", json=False)
        cli_edit(args)
        assert "Updated task" in capsys.readouterr().out

    def test_edit_without_date_json(self, populated_workspace, capsys):
        """cli_edit without date should support JSON output."""
        args = _args(workspace="Work", date=None, task_id="abc12345", text="Edited", json=True)
        cli_edit(args)
        output = json.loads(capsys.readouterr().out)
        assert output["text"] == "Edited"

    def test_edit_nonexistent(self, populated_workspace):
        """cli_edit should exit with error for non-existent task."""
        args = _args(workspace="Work", date="2024-03-15", task_id="nonexistent", text="X", json=False)
        with pytest.raises(SystemExit):
            cli_edit(args)

    def test_edit_without_date_nonexistent(self, populated_workspace):
        """cli_edit should exit when task not found across all dates."""
        args = _args(workspace="Work", date=None, task_id="nonexistent", text="X", json=False)
        with pytest.raises(SystemExit):
            cli_edit(args)


class TestCliSearch:
    """Tests for cli_search command."""

    def test_search_finds_tasks(self, populated_workspace, capsys):
        """cli_search should find matching tasks."""
        args = _args(workspace="Work", query="unit tests", json=False)
        cli_search(args)
        captured = capsys.readouterr()
        assert "Write unit tests" in captured.out

    def test_search_no_results(self, populated_workspace, capsys):
        """cli_search should handle no results."""
        args = _args(workspace="Work", query="nonexistent query xyz", json=False)
        cli_search(args)
        assert "No results" in capsys.readouterr().out

    def test_search_json_output(self, populated_workspace, capsys):
        """cli_search should output JSON with --json flag."""
        args = _args(workspace="Work", query="unit", json=True)
        cli_search(args)
        output = json.loads(capsys.readouterr().out)
        assert output["count"] >= 1
        assert output["query"] == "unit"

    def test_search_case_insensitive(self, populated_workspace, capsys):
        """cli_search should be case-insensitive."""
        args = _args(workspace="Work", query="UNIT TESTS", json=True)
        cli_search(args)
        output = json.loads(capsys.readouterr().out)
        assert output["count"] >= 1


class TestCliStats:
    """Tests for cli_stats command."""

    def test_stats_today(self, populated_workspace, capsys):
        """cli_stats should show stats for today."""
        args = _args(workspace="Work", range="today", json=False)
        cli_stats(args)
        captured = capsys.readouterr()
        assert "Statistics" in captured.out
        assert "Today" in captured.out

    def test_stats_week(self, populated_workspace, capsys):
        """cli_stats should show stats for the week."""
        args = _args(workspace="Work", range="week", json=False)
        cli_stats(args)
        captured = capsys.readouterr()
        assert "Last 7 days" in captured.out

    def test_stats_month(self, populated_workspace, capsys):
        """cli_stats should show stats for the month."""
        args = _args(workspace="Work", range="month", json=False)
        cli_stats(args)
        assert "Last 30 days" in capsys.readouterr().out

    def test_stats_json_output(self, populated_workspace, capsys):
        """cli_stats should output JSON with --json flag."""
        args = _args(workspace="Work", range="today", json=True)
        cli_stats(args)
        output = json.loads(capsys.readouterr().out)
        assert "total_tasks" in output
        assert "total_done" in output
        assert "daily" in output

    def test_stats_with_tasks(self, temp_devlog_home, capsys):
        """cli_stats should compute correct numbers."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        today = datetime.now()
        set_tasks("Personal", today, [
            {"id": "t1", "text": "Task 1", "done": False, "position": 0},
            {"id": "t2", "text": "Task 2", "done": True, "position": 0,
             "completed_at": today.isoformat()},
        ])

        args = _args(workspace="Personal", range="today", json=True)
        cli_stats(args)
        output = json.loads(capsys.readouterr().out)
        assert output["total_tasks"] == 2
        assert output["total_done"] == 1
        assert output["total_pending"] == 1


class TestCliExport:
    """Tests for cli_export command."""

    def test_export_with_date(self, populated_workspace, capsys):
        """cli_export should export tasks for a specific date."""
        args = _args(workspace="Work", date="2024-03-15", json=False)
        cli_export(args)
        captured = capsys.readouterr()
        assert "- [ ] Write unit tests" in captured.out
        assert "- [ ] Review pull request" in captured.out

    def test_export_all_dates(self, populated_workspace, capsys):
        """cli_export without date should export all tasks."""
        args = _args(workspace="Work", date=None, json=False)
        cli_export(args)
        captured = capsys.readouterr()
        assert "Tasks for Work" in captured.out
        assert "2024-03-15" in captured.out

    def test_export_done_tasks(self, populated_workspace, capsys):
        """cli_export should show done tasks with [x]."""
        args = _args(workspace="Work", date="2024-03-14", json=False)
        cli_export(args)
        captured = capsys.readouterr()
        assert "- [x] Deploy to staging" in captured.out


class TestCliImport:
    """Tests for cli_import command."""

    def test_import_from_file(self, temp_devlog_home, tmp_path, capsys):
        """cli_import should import tasks from a markdown file."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        md_file = tmp_path / "tasks.md"
        md_file.write_text("- [ ] Task one\n- [x] Task two\n- [ ] Task three\n")

        args = _args(workspace="Personal", date="2024-06-01", file=str(md_file), json=False)
        cli_import(args)
        captured = capsys.readouterr()
        assert "Imported 3" in captured.out

        tasks = get_tasks("Personal", date(2024, 6, 1))
        assert len(tasks) == 3

    def test_import_json_output(self, temp_devlog_home, tmp_path, capsys):
        """cli_import should output JSON with --json flag."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        md_file = tmp_path / "tasks.md"
        md_file.write_text("- [ ] Task one\n")

        args = _args(workspace="Personal", date="2024-06-01", file=str(md_file), json=True)
        cli_import(args)
        output = json.loads(capsys.readouterr().out)
        assert output["imported"] == 1

    def test_import_no_tasks(self, temp_devlog_home, tmp_path, capsys):
        """cli_import should handle file with no tasks."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        md_file = tmp_path / "empty.md"
        md_file.write_text("# Just a header\nSome text\n")

        args = _args(workspace="Personal", date="2024-06-01", file=str(md_file), json=False)
        cli_import(args)
        captured = capsys.readouterr()
        assert "No tasks found" in captured.err

    def test_import_file_not_found(self, temp_devlog_home):
        """cli_import should exit with error for missing file."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        args = _args(workspace="Personal", date="2024-06-01", file="/nonexistent/file.md", json=False)
        with pytest.raises(SystemExit):
            cli_import(args)

    def test_import_from_stdin(self, temp_devlog_home, capsys):
        """cli_import should read from stdin when file is '-'."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        with patch("sys.stdin", StringIO("- [ ] Stdin task\n- [x] Done stdin task\n")):
            args = _args(workspace="Personal", date="2024-06-01", file="-", json=False)
            cli_import(args)

        captured = capsys.readouterr()
        assert "Imported 2" in captured.out


class TestExecuteCliCommand:
    """Tests for execute_cli_command dispatcher."""

    def test_execute_list(self, populated_workspace, capsys):
        """execute_cli_command should dispatch to cli_list."""
        parser = create_parser()
        args = parser.parse_args(["--workspace", "Work", "list", "--date", "2024-03-15"])
        execute_cli_command(args)
        assert "TODO" in capsys.readouterr().out

    def test_execute_add(self, temp_devlog_home, capsys):
        """execute_cli_command should dispatch to cli_add."""
        config = {"schema_version": 2, "workspaces": ["Personal"], "active_workspace": "Personal"}
        save_config(config)

        parser = create_parser()
        args = parser.parse_args(["add", "Test task"])
        execute_cli_command(args)
        assert "Added task" in capsys.readouterr().out

    def test_execute_search(self, populated_workspace, capsys):
        """execute_cli_command should dispatch to cli_search."""
        parser = create_parser()
        args = parser.parse_args(["--workspace", "Work", "search", "unit"])
        execute_cli_command(args)
        assert "unit tests" in capsys.readouterr().out.lower()

    def test_execute_stats(self, populated_workspace, capsys):
        """execute_cli_command should dispatch to cli_stats."""
        parser = create_parser()
        args = parser.parse_args(["--workspace", "Work", "stats"])
        execute_cli_command(args)
        assert "Statistics" in capsys.readouterr().out

    def test_execute_export(self, populated_workspace, capsys):
        """execute_cli_command should dispatch to cli_export."""
        parser = create_parser()
        args = parser.parse_args(["--workspace", "Work", "export", "--date", "2024-03-15"])
        execute_cli_command(args)
        assert "[ ]" in capsys.readouterr().out
