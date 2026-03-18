"""Unit tests for devlog.core.tasks module."""

import pytest
from devlog.core.tasks import gen_id, find_task, next_position, reposition, nav_order


class TestGenId:
    """Tests for gen_id() function."""

    def test_generates_8_char_hex(self):
        """gen_id should return an 8-character hexadecimal string."""
        task_id = gen_id()
        assert len(task_id) == 8
        assert all(c in "0123456789abcdef" for c in task_id)

    def test_generates_unique_ids(self):
        """gen_id should generate unique IDs across multiple calls."""
        ids = [gen_id() for _ in range(100)]
        assert len(set(ids)) == 100, "IDs should be unique"


class TestFindTask:
    """Tests for find_task() function."""

    def test_find_existing_task(self, sample_tasks):
        """find_task should return (index, task) for existing task."""
        idx, task = find_task(sample_tasks, "abc12345")
        assert idx == 0
        assert task["id"] == "abc12345"
        assert task["text"] == "Write unit tests"

    def test_find_middle_task(self, sample_tasks):
        """find_task should find task in the middle of list."""
        idx, task = find_task(sample_tasks, "def67890")
        assert idx == 1
        assert task["id"] == "def67890"

    def test_find_last_task(self, sample_tasks):
        """find_task should find task at end of list."""
        idx, task = find_task(sample_tasks, "ghi11111")
        assert idx == 2
        assert task["id"] == "ghi11111"

    def test_find_nonexistent_task(self, sample_tasks):
        """find_task should return (None, None) for non-existent task."""
        idx, task = find_task(sample_tasks, "nonexistent")
        assert idx is None
        assert task is None

    def test_find_in_empty_list(self):
        """find_task should return (None, None) for empty list."""
        idx, task = find_task([], "any_id")
        assert idx is None
        assert task is None


class TestNextPosition:
    """Tests for next_position() function."""

    def test_next_position_empty_list(self):
        """next_position should return 0 for empty list."""
        assert next_position([]) == 0

    def test_next_position_with_tasks(self, sample_tasks):
        """next_position should return max position + 1."""
        assert next_position(sample_tasks) == 2  # max is 1, so next is 2

    def test_next_position_single_task(self):
        """next_position should work with single task."""
        tasks = [{"position": 0}]
        assert next_position(tasks) == 1

    def test_next_position_handles_missing_position(self):
        """next_position should treat missing position as 0."""
        tasks = [{"id": "a"}, {"id": "b", "position": 3}]
        assert next_position(tasks) == 4

    def test_next_position_with_gaps(self):
        """next_position should return max + 1 even with position gaps."""
        tasks = [{"position": 0}, {"position": 5}, {"position": 2}]
        assert next_position(tasks) == 6


class TestReposition:
    """Tests for reposition() function."""

    def test_reposition_all_todos(self):
        """reposition should normalize positions for todos."""
        tasks = [
            {"id": "a", "done": False, "position": 5},
            {"id": "b", "done": False, "position": 10},
            {"id": "c", "done": False, "position": 3},
        ]
        reposition(tasks)

        # Should be renormalized to 0, 1, 2 based on original order
        assert tasks[0]["position"] == 1  # was 5, middle
        assert tasks[1]["position"] == 2  # was 10, highest
        assert tasks[2]["position"] == 0  # was 3, lowest

    def test_reposition_all_dones(self):
        """reposition should normalize positions for completed tasks."""
        tasks = [
            {"id": "a", "done": True, "position": 7},
            {"id": "b", "done": True, "position": 2},
            {"id": "c", "done": True, "position": 15},
        ]
        reposition(tasks)

        assert tasks[0]["position"] == 1  # was 7, middle
        assert tasks[1]["position"] == 0  # was 2, lowest
        assert tasks[2]["position"] == 2  # was 15, highest

    def test_reposition_mixed_todos_and_dones(self):
        """reposition should handle mixed todos and completed tasks."""
        tasks = [
            {"id": "a", "done": False, "position": 8},
            {"id": "b", "done": True, "position": 5},
            {"id": "c", "done": False, "position": 2},
            {"id": "d", "done": True, "position": 10},
        ]
        reposition(tasks)

        # Todos normalized within their group
        assert tasks[0]["position"] == 1  # todo: was 8
        assert tasks[2]["position"] == 0  # todo: was 2

        # Dones normalized within their group
        assert tasks[1]["position"] == 0  # done: was 5
        assert tasks[3]["position"] == 1  # done: was 10

    def test_reposition_with_gaps(self):
        """reposition should close position gaps."""
        tasks = [
            {"id": "a", "done": False, "position": 0},
            {"id": "b", "done": False, "position": 100},
            {"id": "c", "done": False, "position": 50},
        ]
        reposition(tasks)

        assert tasks[0]["position"] == 0
        assert tasks[1]["position"] == 2
        assert tasks[2]["position"] == 1

    def test_reposition_empty_list(self):
        """reposition should handle empty list without error."""
        tasks = []
        reposition(tasks)  # Should not raise
        assert tasks == []

    def test_reposition_with_negative_positions(self):
        """reposition should handle negative positions."""
        tasks = [
            {"id": "a", "done": False, "position": -5},
            {"id": "b", "done": False, "position": 3},
            {"id": "c", "done": False, "position": 0},
        ]
        reposition(tasks)

        assert tasks[0]["position"] == 0  # was -5, lowest
        assert tasks[1]["position"] == 2  # was 3, highest
        assert tasks[2]["position"] == 1  # was 0, middle


class TestNavOrder:
    """Tests for nav_order() function."""

    def test_nav_order_empty(self):
        """nav_order should return empty list for empty tasks."""
        assert nav_order([]) == []

    def test_nav_order_only_todos(self):
        """nav_order should return todos sorted by position."""
        tasks = [
            {"id": "c", "done": False, "position": 2},
            {"id": "a", "done": False, "position": 0},
            {"id": "b", "done": False, "position": 1},
        ]
        assert nav_order(tasks) == ["a", "b", "c"]

    def test_nav_order_only_dones(self):
        """nav_order should return dones sorted by position."""
        tasks = [
            {"id": "z", "done": True, "position": 2},
            {"id": "x", "done": True, "position": 0},
            {"id": "y", "done": True, "position": 1},
        ]
        assert nav_order(tasks) == ["x", "y", "z"]

    def test_nav_order_mixed_todos_first(self):
        """nav_order should return todos before dones."""
        tasks = [
            {"id": "done1", "done": True, "position": 0},
            {"id": "todo1", "done": False, "position": 0},
            {"id": "done2", "done": True, "position": 1},
            {"id": "todo2", "done": False, "position": 1},
        ]
        assert nav_order(tasks) == ["todo1", "todo2", "done1", "done2"]

    def test_nav_order_preserves_position_order(self):
        """nav_order should respect position values within groups."""
        tasks = [
            {"id": "d1", "done": True, "position": 5},
            {"id": "t1", "done": False, "position": 10},
            {"id": "d2", "done": True, "position": 2},
            {"id": "t2", "done": False, "position": 3},
        ]
        # Todos: t2 (pos 3), t1 (pos 10)
        # Dones: d2 (pos 2), d1 (pos 5)
        assert nav_order(tasks) == ["t2", "t1", "d2", "d1"]

    def test_nav_order_handles_missing_position(self):
        """nav_order should treat missing position as 0."""
        tasks = [
            {"id": "a", "done": False, "position": 5},
            {"id": "b", "done": False},  # missing position
            {"id": "c", "done": False, "position": 2},
        ]
        # b should be treated as position 0
        assert nav_order(tasks) == ["b", "c", "a"]
