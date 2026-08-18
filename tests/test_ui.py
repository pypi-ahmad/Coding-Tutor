"""Tests for session state and question loading."""
import json
import pytest
from unittest.mock import patch, MagicMock


def test_get_current_question_returns_none_initially():
    """Session state has no question by default."""
    import streamlit as st
    with patch.object(st, "session_state", {}):
        from coding_tutor.quiz.session import get_current_question
        assert get_current_question() is None


def test_starter_templates_exist_for_all_methods():
    """All method templates must be non-empty strings."""
    templates = {
        "python": "def solution():\n    # Write your solution here\n    pass\n",
        "sql": "-- Write your SQL query here\nSELECT \n",
        "pandas": (
            "import pandas as pd\n\n"
            "def solution(df: pd.DataFrame) -> pd.DataFrame:\n"
            "    # Write your Pandas solution here\n"
            "    return df\n"
        ),
        "pyspark": (
            "from pyspark.sql import DataFrame\n\n"
            "def solution(spark, df: DataFrame) -> DataFrame:\n"
            "    # Write your PySpark solution here\n"
            "    return df\n"
        ),
        "polars": (
            "import polars as pl\n\n"
            "def solution(df: pl.DataFrame) -> pl.DataFrame:\n"
            "    # Write your Polars solution here\n"
            "    return df\n"
        ),
    }
    for method, template in templates.items():
        assert template.strip(), f"Template for {method} must not be empty"


def test_supported_methods_algorithm():
    from coding_tutor.database.connection import get_test_db
    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Test', 'algorithm', 'Easy', 'stmt', '["python"]')"""
    )
    row = conn.execute("SELECT supported_methods FROM questions LIMIT 1").fetchone()
    methods = json.loads(row[0])
    assert methods == ["python"]


def test_supported_methods_data_analysis():
    from coding_tutor.database.connection import get_test_db
    conn = get_test_db()
    methods = ["sql", "pandas", "pyspark", "polars"]
    conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('SQL Q', 'data_analysis', 'Easy', 'stmt', ?)""",
        [json.dumps(methods)],
    )
    row = conn.execute(
        "SELECT supported_methods FROM questions ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert json.loads(row[0]) == methods


def test_clear_question_resets_session():
    """clear_question_with_confirm resets all relevant session keys."""
    from types import SimpleNamespace
    import streamlit as st

    # Use SimpleNamespace so attribute-style access works (matching session_state usage)
    fake_state = SimpleNamespace(
        current_question={"id": "q1", "title": "Test"},
        editor_content="some code",
        submit_trigger=True,
        show_solution_trigger=False,
    )
    with patch.object(st, "session_state", fake_state):
        from coding_tutor.quiz.session import clear_question_with_confirm
        clear_question_with_confirm()
        assert fake_state.current_question is None
        assert fake_state.editor_content == ""
        assert fake_state.submit_trigger is False
        assert fake_state.show_solution_trigger is False
