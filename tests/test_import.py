"""Tests for dataset import pipeline using only small local fixtures."""
import io
import json
import tarfile
import pytest
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from coding_tutor.database.connection import get_test_db
from coding_tutor.dataset.importer import _start_run, _finish_run, run_import

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
    """Schema-only SQL retains provenance but is not a complete task."""
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
    assert row[0] is False
    assert row[1] == "data_analysis"
    methods = conn.execute("SELECT supported_methods FROM questions").fetchone()[0]
    assert json.loads(methods) == ["sql", "pandas", "pyspark", "polars"]


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


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_apps_import_scopes_reused_ids_by_source_file_and_retains_revision(tmp_path):
    root = tmp_path / "Dataset"
    dataset_dir = root / "algorithm_problems" / "apps"
    base = {"id": 0, "difficulty": "interview", "solutions": "[]", "input_output": "{}", "starter_code": ""}
    _write_jsonl(dataset_dir / "train.jsonl", [{**base, "question": "Train problem"}])
    _write_jsonl(dataset_dir / "test.jsonl", [{**base, "question": "Test problem"}])
    metadata_dir = dataset_dir / ".cache" / "huggingface" / "download"
    metadata_dir.mkdir(parents=True)
    (metadata_dir / "train.jsonl.metadata").write_text("revision-train\nobject\ntime\n", encoding="utf-8")
    (metadata_dir / "test.jsonl.metadata").write_text("revision-test\nobject\ntime\n", encoding="utf-8")

    conn = get_test_db()
    first = run_import(conn, ["apps"], root)[0]
    second = run_import(conn, ["apps"], root)[0]

    assert (first.imported, first.skipped) == (2, 0)
    assert (second.imported, second.skipped) == (0, 2)
    rows = conn.execute(
        "SELECT original_id, source_file, source_revision, license FROM question_sources ORDER BY source_file"
    ).fetchall()
    assert rows == [
        ("0", "algorithm_problems/apps/test.jsonl", "revision-test", "MIT"),
        ("0", "algorithm_problems/apps/train.jsonl", "revision-train", "MIT"),
    ]


def test_querypls_duplicate_records_are_idempotent_across_splits(tmp_path):
    root = tmp_path / "Dataset"
    data_dir = root / "data_analysis_problems" / "querypls-prompt2sql-dataset" / "data"
    data_dir.mkdir(parents=True)
    table = pa.table({
        "context": ["CREATE TABLE t (id INT)"],
        "answer": ["SELECT id FROM t"],
        "autotrain_text": ["Return every id"],
    })
    pq.write_table(table, data_dir / "train.parquet")
    pq.write_table(table, data_dir / "validation.parquet")

    conn = get_test_db()
    result = run_import(conn, ["querypls"], root)[0]
    assert (result.imported, result.skipped) == (1, 1)
    row = conn.execute("SELECT is_complete, supported_methods FROM questions").fetchone()
    assert row[0] is False
    assert json.loads(row[1]) == ["sql", "pandas", "pyspark", "polars"]
    assert conn.execute("SELECT count(*) FROM reference_solutions WHERE method='sql'").fetchone()[0] == 1


def test_taco_normalizes_string_tags_starter_and_very_hard(tmp_path):
    from coding_tutor.dataset.taco import _upsert_question
    root = tmp_path / "Dataset"
    path = root / "algorithm_problems" / "TACO" / "ALL" / "test.parquet"
    path.parent.mkdir(parents=True)
    conn = get_test_db()
    run_id = _start_run(conn, "TACO")
    record = {
        "url": "https://example.test/problem/1", "question": "Solve it", "name": "Problem",
        "difficulty": "VERY_HARD", "tags": "['Graph', 'DP']", "starter_code": "def solve(): pass",
        "input_output": '{"inputs":["1"],"outputs":["2"]}', "solutions": '["print(2)"]',
    }
    ok, skipped = _upsert_question(conn, record, run_id, str(path), 0, root)
    assert ok and not skipped
    difficulty, tags = conn.execute("SELECT difficulty, tags FROM questions").fetchone()
    assert difficulty == "Very Hard"
    assert json.loads(tags) == ["Graph", "DP"]
    assert conn.execute("SELECT count(*) FROM question_assets WHERE asset_type='starter_code'").fetchone()[0] == 1


def _codecontests_archive() -> bytes:
    buffer = io.BytesIO()
    members = {
        "instruction.md": b"# Add One\nReturn the input plus one.",
        "task.toml": b'[metadata]\ndifficulty="medium"\ntags=["math"]\n',
        "tests/test_data.json": b'{"inputs":["1"],"outputs":["2"]}',
    }
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_codecontests_duplicate_is_reported_as_skipped(tmp_path):
    from coding_tutor.dataset.codecontests import _upsert
    root = tmp_path / "Dataset"
    path = root / "algorithm_problems" / "CodeContests" / "tasks.parquet"
    path.parent.mkdir(parents=True)
    conn = get_test_db()
    run_id = _start_run(conn, "CodeContests")
    record = {"path": "code_contests-0000", "task_binary": _codecontests_archive()}
    assert _upsert(conn, record, run_id, str(path), 0, root) == (True, False)
    assert _upsert(conn, record, run_id, str(path), 0, root) == (True, True)


def test_inspection_rejects_missing_required_fields(tmp_path):
    root = tmp_path / "Dataset"
    _write_jsonl(root / "algorithm_problems" / "apps" / "train.jsonl", [{"id": 1}])
    conn = get_test_db()
    result = run_import(conn, ["apps"], root)[0]
    assert result.status == "failed"
    assert "missing required fields" in result.error
    assert conn.execute("SELECT count(*) FROM questions").fetchone()[0] == 0
