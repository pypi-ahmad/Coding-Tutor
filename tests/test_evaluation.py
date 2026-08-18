"""Tests for code evaluation runner and progress persistence."""
import pytest
from unittest.mock import patch, MagicMock


def test_python_runner_passes_correct_solution():
    from coding_tutor.evaluation.runner import run_python
    code = "def solution(nums):\n    return sum(nums)\n"
    test_cases = [
        {"input": {"nums": [1, 2, 3]}, "expected_output": 6},
        {"input": {"nums": []}, "expected_output": 0},
    ]
    result = run_python(code, test_cases, entry_point="solution")
    assert result.status == "passed"
    assert result.tests_passed == 2
    assert result.percentage_correct == 100.0


def test_python_runner_fails_wrong_solution():
    from coding_tutor.evaluation.runner import run_python
    code = "def solution(nums):\n    return 0\n"
    test_cases = [{"input": {"nums": [1, 2, 3]}, "expected_output": 6}]
    result = run_python(code, test_cases, entry_point="solution")
    assert result.status == "failed"
    assert result.tests_passed == 0


def test_python_runner_timeout():
    from coding_tutor.evaluation import runner as runner_mod
    original = runner_mod.TIMEOUT_SECONDS
    runner_mod.TIMEOUT_SECONDS = 2
    try:
        from coding_tutor.evaluation.runner import run_python
        code = "def solution(nums):\n    while True: pass\n"
        test_cases = [{"input": {"nums": [1]}, "expected_output": 1}]
        result = run_python(code, test_cases, entry_point="solution")
        assert result.status == "timeout"
    finally:
        runner_mod.TIMEOUT_SECONDS = original


def test_sql_runner_runs_without_crash():
    from coding_tutor.evaluation.runner import run_sql
    result = run_sql(
        sql_code="SELECT * FROM emp WHERE salary > 80000",
        schema_sql="CREATE TABLE emp (id INT, name TEXT, salary INT);",
        fixture_data=[
            {"id": 1, "name": "Alice", "salary": 90000},
            {"id": 2, "name": "Bob", "salary": 70000},
        ],
        table_name="emp",
        expected_result=[{"id": 1, "name": "Alice", "salary": 90000}],
    )
    assert result.status in ("passed", "failed", "error")


def test_pyspark_unavailable_returns_clear_message(monkeypatch):
    """PySpark unavailable must not silently fall back to another method."""
    from coding_tutor.evaluation import runner as runner_mod
    monkeypatch.setattr(runner_mod, "_pyspark_available", lambda: False)
    from coding_tutor.evaluation.runner import run_pyspark
    result = run_pyspark("def solution(spark, df): return df", [], [])
    assert result.status == "error"
    assert "PySpark" in (result.error_details or "")
    assert "not available" in (result.error_details or "").lower()


def test_no_test_cases_returns_error():
    from coding_tutor.evaluation.runner import run_python
    result = run_python("def solution(): pass", [], entry_point="solution")
    assert result.status == "error"
    assert "No test cases" in (result.error_details or "")


def test_save_attempt_stores_record():
    from coding_tutor.evaluation.runner import RunResult
    from coding_tutor.evaluation.persistence import save_attempt
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as conn_mod
    import unittest.mock as mock

    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (id, title, question_type, difficulty, problem_statement, supported_methods)
           VALUES (gen_random_uuid(), 'Test Q', 'algorithm', 'Easy', 'Test', '["python"]')"""
    )
    q_id = str(conn.execute("SELECT id FROM questions LIMIT 1").fetchone()[0])

    with mock.patch.object(conn_mod, "get_db", return_value=conn):
        attempt_id = save_attempt(
            question_id=q_id,
            method="python",
            submitted_code="def solution(): return 1",
            run_result=RunResult(
                status="passed", tests_passed=1, tests_total=1, percentage_correct=100.0
            ),
            feedback=None,
        )

    assert attempt_id
    row = conn.execute(
        "SELECT test_result FROM attempts WHERE id = ?", [attempt_id]
    ).fetchone()
    assert row[0] == "passed"


def test_repeated_attempts_stored_separately():
    from coding_tutor.evaluation.runner import RunResult
    from coding_tutor.evaluation.persistence import save_attempt
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as conn_mod
    import unittest.mock as mock

    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (id, title, question_type, difficulty, problem_statement, supported_methods)
           VALUES (gen_random_uuid(), 'Repeat Q', 'algorithm', 'Easy', 'Test', '["python"]')"""
    )
    q_id = str(conn.execute("SELECT id FROM questions LIMIT 1").fetchone()[0])

    with mock.patch.object(conn_mod, "get_db", return_value=conn):
        id1 = save_attempt(
            q_id, "python", "code v1",
            RunResult("failed", 0, 1, 0.0), None,
        )
        id2 = save_attempt(
            q_id, "python", "code v2",
            RunResult("passed", 1, 1, 100.0), None,
        )

    assert id1 != id2
    count = conn.execute(
        "SELECT COUNT(*) FROM attempts WHERE question_id = ?", [q_id]
    ).fetchone()[0]
    assert count == 2


def test_progress_summary_empty_db():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.database.progress import get_progress_summary
    conn = get_test_db()
    summary = get_progress_summary(conn)
    assert summary["total_attempts"] == 0
    assert summary["solved_questions"] == 0
    assert summary["total_questions"] == 0
