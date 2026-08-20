"""Phase 8 tests for immutable attempts, filtered progress, and migrations."""
from __future__ import annotations

from contextlib import nullcontext
import json

import duckdb
import pytest


def _question(conn, title, question_type="algorithm", difficulty="Easy", methods='["python"]'):
    return str(conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES (?, ?, ?, 'Solve it.', ?) RETURNING id""",
        [title, question_type, difficulty, methods],
    ).fetchone()[0])


def test_repeated_attempts_are_distinct_and_preserve_each_submission(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.evaluation.persistence as persistence

    conn = get_test_db()
    question_id = _question(conn, "Repeated")
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    first = persistence.create_attempt(question_id, "python", "# first", "openai", "model")
    second = persistence.create_attempt(question_id, "python", "# second", "openai", "model")

    rows = conn.execute(
        """SELECT id, submitted_code, deterministic_test_result
           FROM attempts WHERE question_id=? ORDER BY submitted_code""",
        [question_id],
    ).fetchall()
    assert first != second
    assert [(row[1], row[2]) for row in rows] == [("# first", "not_run"), ("# second", "not_run")]


def test_unconfigured_provider_attempt_is_saved_with_error(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.evaluation.persistence as persistence
    import coding_tutor.quiz.session as session
    import coding_tutor.ui.submit_handler as submit_handler

    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    class FakeStreamlit:
        def __init__(self, state):
            self.session_state = state
            self.warnings = []
            self.errors = []

        def warning(self, message): self.warnings.append(message)
        def error(self, message): self.errors.append(message)
        def spinner(self, _message): return nullcontext()

    conn = get_test_db()
    question_id = _question(conn, "No provider")
    state = State({
        f"editor_{question_id}_python": "return 1",
        "provider": None, "model": None, "submit_trigger": True,
    })
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    monkeypatch.setattr(submit_handler, "st", FakeStreamlit(state))
    monkeypatch.setattr(session, "mark_editor_saved", lambda *args, **kwargs: None)

    attempt_id = submit_handler.handle_submit(
        {"id": question_id, "supported_methods": ["python"]}, "python"
    )
    row = conn.execute(
        """SELECT assessment_status, deterministic_test_result, provider, model_id, error_details
           FROM attempts WHERE id=?""",
        [attempt_id],
    ).fetchone()
    assert row[:4] == ("error", "not_run", None, None)
    assert "verified model" in row[4]


def test_progress_summary_counts_solved_and_applies_all_filters():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.database.progress import get_all_attempts, get_progress_summary

    conn = get_test_db()
    algorithm = _question(conn, "Algorithm", difficulty="Easy")
    analysis = _question(
        conn, "Analysis", question_type="data_analysis", difficulty="Hard",
        methods='["sql","pandas","pyspark","polars"]',
    )
    rows = [
        (algorithm, "python", "a", "completed", 79, 7.9),
        (algorithm, "python", "b", "completed", 80, 8.0),
        (analysis, "sql", "c", "completed", 90, 9.0),
        (analysis, "pandas", "d", "error", None, None),
    ]
    conn.executemany(
        """INSERT INTO attempts
               (question_id, method, submitted_code, assessment_status,
                percentage_correct, marks)
           VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )

    all_summary = get_progress_summary(conn)
    assert all_summary["total_attempts"] == 4
    assert all_summary["attempted_questions"] == 2
    assert all_summary["solved_questions"] == 2

    python_summary = get_progress_summary(conn, method="python")
    assert python_summary["total_attempts"] == 2
    assert python_summary["solved_questions"] == 1
    assert len(python_summary["recent_attempts"]) == 2

    hard_sql = get_progress_summary(
        conn, question_type="data_analysis", difficulty="Hard", method="sql"
    )
    assert hard_sql["total_attempts"] == 1
    assert hard_sql["solved_questions"] == 1

    attempts = get_all_attempts(conn, question_type="algorithm")
    assert len(attempts) == 2
    assert {attempt["marks"] for attempt in attempts} == {7.9, 8.0}


def test_file_backed_progress_survives_reopen(tmp_path):
    from coding_tutor.database.migrations import run_migrations

    path = tmp_path / "progress.duckdb"
    conn = duckdb.connect(str(path))
    run_migrations(conn)
    question_id = _question(conn, "Persistent")
    conn.execute(
        "INSERT INTO attempts (question_id, method, submitted_code) VALUES (?, 'python', 'saved')",
        [question_id],
    )
    conn.close()

    reopened = duckdb.connect(str(path))
    run_migrations(reopened)
    assert reopened.execute("SELECT submitted_code FROM attempts").fetchone()[0] == "saved"
    reopened.close()


def test_v4_migration_preserves_legacy_attempt(monkeypatch):
    import coding_tutor.database.migrations as migrations
    from coding_tutor.database.schema import SCHEMA_SQL

    conn = duckdb.connect(":memory:")
    legacy_schema = SCHEMA_SQL.replace(
        "    deterministic_test_result TEXT NOT NULL DEFAULT 'not_run',\n", ""
    )
    conn.execute(legacy_schema)
    conn.execute("ALTER TABLE attempts ADD COLUMN assessment_status TEXT")
    conn.executemany(
        "INSERT INTO schema_versions (version, description) VALUES (?, 'legacy')",
        [(1,), (2,), (3,)],
    )
    question_id = _question(conn, "Legacy")
    conn.execute(
        "INSERT INTO attempts (question_id, method, submitted_code) VALUES (?, 'python', 'keep me')",
        [question_id],
    )
    migrations.run_migrations(conn)
    assert migrations.get_schema_version(conn) == 8
    assert conn.execute(
        "SELECT submitted_code, deterministic_test_result FROM attempts"
    ).fetchone() == ("keep me", "not_run")


def test_v8_migration_expands_only_curated_algorithm_languages():
    import coding_tutor.database.migrations as migrations
    from coding_tutor.database.schema import SCHEMA_SQL
    from coding_tutor.methods import ALGORITHM_METHODS

    conn = duckdb.connect(":memory:")
    conn.execute(SCHEMA_SQL)
    conn.executemany(
        "INSERT INTO schema_versions (version, description) VALUES (?, 'legacy')",
        [(version,) for version in range(1, 8)],
    )
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement,
                supported_methods, is_ai_generated)
           VALUES ('Curated', 'algorithm', 'Easy', 'Solve it.', '["python"]', false),
                  ('Generated', 'algorithm', 'Easy', 'Solve it.', '["python"]', true)"""
    )

    migrations.run_migrations(conn)

    rows = conn.execute(
        "SELECT title, supported_methods FROM questions ORDER BY title"
    ).fetchall()
    assert rows == [
        ("Curated", json.dumps(list(ALGORITHM_METHODS), separators=(",", ":"))),
        ("Generated", '["python"]'),
    ]


def test_failed_migration_rolls_back_schema_and_version(monkeypatch):
    import coding_tutor.database.migrations as migrations
    from coding_tutor.database.connection import get_test_db

    conn = get_test_db()
    broken = (
        999,
        "broken migration",
        "ALTER TABLE attempts ADD COLUMN rollback_probe TEXT; SELECT * FROM missing_table;",
    )
    monkeypatch.setattr(migrations, "MIGRATIONS", [*migrations.MIGRATIONS, broken])
    with pytest.raises(Exception):
        migrations.run_migrations(conn)
    columns = {row[0] for row in conn.execute("DESCRIBE attempts").fetchall()}
    assert "rollback_probe" not in columns
    assert conn.execute(
        "SELECT COUNT(*) FROM schema_versions WHERE version=999"
    ).fetchone()[0] == 0
