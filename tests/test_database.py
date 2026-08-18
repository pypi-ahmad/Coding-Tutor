"""Tests for DuckDB schema and migrations."""
import pytest
from coding_tutor.database.connection import get_test_db
from coding_tutor.database.migrations import get_schema_version, run_migrations


def test_migrations_create_all_tables():
    conn = get_test_db()
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    expected = {
        "schema_versions", "import_runs", "question_sources",
        "questions", "question_assets", "reference_solutions",
        "question_test_cases", "ai_generated_questions",
        "attempts", "solution_views",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_migrations_idempotent():
    conn = get_test_db()
    v1 = get_schema_version(conn)
    run_migrations(conn)  # run again
    v2 = get_schema_version(conn)
    assert v1 == v2


def test_schema_version_is_positive():
    conn = get_test_db()
    assert get_schema_version(conn) >= 1


def test_insert_question():
    conn = get_test_db()
    conn.execute(
        "INSERT INTO question_sources (id, dataset_name, original_id) VALUES (gen_random_uuid(), 'test', 'q1')"
    )
    src_id = conn.execute("SELECT id FROM question_sources WHERE original_id='q1'").fetchone()[0]
    conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods, source_id)
           VALUES ('Test Q', 'algorithm', 'Easy', 'Test statement', '["python"]', ?)""",
        [src_id],
    )
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    assert count == 1
