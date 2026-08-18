"""Tests for dataset import pipeline using fixture files."""
import pytest
from pathlib import Path
from coding_tutor.database.connection import get_test_db
from coding_tutor.dataset.importer import _start_run, _finish_run

FIXTURES = Path(__file__).parent / "fixtures"


def test_leetcode_import_fixture():
    """Import sample LeetCode fixture and verify idempotency.

    Uses actual field names from LeetCodeDataset inspection:
    task_id, problem_description, tags (list of strings), starter_code (string).
    """
    from coding_tutor.dataset.leetcode import _upsert_question
    conn = get_test_db()
    run_id = _start_run(conn, "LeetCodeDataset")

    record = {
        "task_id": "two-sum",
        "question_id": 1,
        "problem_description": "Given nums and target, return indices of two numbers that add to target.",
        "difficulty": "Easy",
        "tags": ["Array", "Hash Table"],
        "starter_code": "class Solution:\n    def twoSum(self, nums, target):\n        pass",
        "completion": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
        "input_output": [{"input": "nums=[1,2], target=3", "output": "[0,1]"}],
    }

    ok, skipped = _upsert_question(conn, record, run_id, "fixture.jsonl")
    assert ok and not skipped

    # Second call must skip (idempotent)
    ok2, skipped2 = _upsert_question(conn, record, run_id, "fixture.jsonl")
    assert skipped2

    count = conn.execute("SELECT COUNT(*) FROM questions WHERE question_type='algorithm'").fetchone()[0]
    assert count == 1


def test_sql_create_context_import_fixture():
    """Import sql-create-context fixture and check incompleteness flag."""
    from coding_tutor.dataset.sql_create_context import _upsert_question
    conn = get_test_db()
    run_id = _start_run(conn, "sql-create-context")

    record = {
        "question": "Find employees with salary > 50000",
        "context": "CREATE TABLE employees (id INT, name TEXT, salary INT);",
        "answer": "SELECT * FROM employees WHERE salary > 50000;",
    }

    ok, skipped = _upsert_question(conn, record, run_id, "fixture.json", 0)
    assert ok and not skipped

    row = conn.execute("SELECT is_complete, question_type FROM questions ORDER BY created_at LIMIT 1").fetchone()
    assert row[0] is False  # no fixture rows → incomplete
    assert row[1] == "data_analysis"


def test_import_sets_correct_question_type():
    from coding_tutor.dataset.leetcode import _upsert_question
    conn = get_test_db()
    run_id = _start_run(conn, "LeetCodeDataset")
    # Use actual field names from dataset inspection
    record = {
        "task_id": "sort-array",
        "problem_description": "Sort the array in ascending order.",
        "difficulty": "Easy",
    }
    ok, skipped = _upsert_question(conn, record, run_id, "test.jsonl")
    assert ok and not skipped
    qt = conn.execute("SELECT question_type FROM questions ORDER BY created_at LIMIT 1").fetchone()[0]
    assert qt == "algorithm"


def test_start_finish_run():
    conn = get_test_db()
    run_id = _start_run(conn, "test_dataset")
    assert run_id
    _finish_run(conn, run_id, 5, 2, "completed")
    row = conn.execute(
        "SELECT records_imported, records_skipped, status FROM import_runs WHERE id = ?",
        [run_id],
    ).fetchone()
    assert row == (5, 2, "completed")
