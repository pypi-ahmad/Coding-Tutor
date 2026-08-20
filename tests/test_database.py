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
        "attempts", "solution_views", "quiz_attempts", "quiz_items",
        "interview_items",
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


def test_source_identity_is_unique_per_dataset():
    conn = get_test_db()
    conn.execute("INSERT INTO question_sources (dataset_name, source_key) VALUES ('one', 'same')")
    with pytest.raises(Exception):
        conn.execute("INSERT INTO question_sources (dataset_name, source_key) VALUES ('one', 'same')")
    conn.execute("INSERT INTO question_sources (dataset_name, source_key) VALUES ('two', 'same')")


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


def test_interview_items_have_separate_formats():
    conn = get_test_db()
    conn.execute("INSERT INTO question_sources (dataset_name, source_key) VALUES ('test', 'interview')")
    source_id = conn.execute("SELECT id FROM question_sources WHERE source_key='interview'").fetchone()[0]
    conn.execute(
        """INSERT INTO interview_items
           (source_id, domain, topic, answer_format, prompt_style, difficulty, prompt, content_hash)
           VALUES (?, 'llm', 'rag', 'theory', 'scenario', 'Medium', 'Design a RAG evaluator.', 'hash')""",
        [source_id],
    )
    assert conn.execute("SELECT answer_format, prompt_style FROM interview_items").fetchone() == ("theory", "scenario")
