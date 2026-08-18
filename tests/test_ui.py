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
    from coding_tutor.quiz.templates import get_editor_template
    for method in ("python", "sql", "pandas", "pyspark", "polars"):
        template = get_editor_template(method)
        assert template.strip(), f"Template for {method} must not be empty"
    assert get_editor_template("sql").lstrip().startswith("--")
    assert "import pandas" in get_editor_template("pandas")
    assert "pyspark" in get_editor_template("pyspark")
    assert "import polars" in get_editor_template("polars")


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
    import streamlit as st

    fake_state = {
        "current_question": {"id": "q1", "title": "Test"},
        "editor_content": "some code", "submit_trigger": True,
        "show_solution_trigger": False,
    }
    with patch.object(st, "session_state", fake_state):
        from coding_tutor.quiz.session import clear_question_with_confirm
        clear_question_with_confirm()
        assert fake_state["current_question"] is None
        assert fake_state["editor_content"] == ""
        assert fake_state["submit_trigger"] is False
        assert fake_state["show_solution_trigger"] is False


def test_dataset_rows_exclude_ai_and_filter_method():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.ui.main_page import _dataset_rows
    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, is_ai_generated)
           VALUES ('Dataset Python', 'algorithm', 'Easy', 'p', '["python"]', false),
                  ('AI Python', 'algorithm', 'Easy', 'p', '["python"]', true),
                  ('Dataset SQL', 'algorithm', 'Easy', 'p', '["sql"]', false)"""
    )
    rows = _dataset_rows(conn, "algorithm", "Easy", "python")
    assert [row[1] for row in rows] == ["Dataset Python"]


def test_dataset_rows_filter_selected_topic():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.ui.main_page import _dataset_rows
    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, tags)
           VALUES ('Arrays', 'algorithm', 'Easy', 'p', '["python"]', '["Array"]'),
                  ('Graphs', 'algorithm', 'Easy', 'p', '["python"]', '["Graph"]')"""
    )
    assert [row[1] for row in _dataset_rows(conn, "algorithm", "Easy", "python", "Graph")] == ["Graphs"]


def test_available_topics_come_from_matching_questions():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.ui.sidebar import _available_topics
    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, tags)
           VALUES ('A', 'algorithm', 'Easy', 'p', '["python"]', '["Array", "Hash Table"]'),
                  ('B', 'algorithm', 'Hard', 'p', '["python"]', '["Graph"]')"""
    )
    assert _available_topics(conn, "algorithm", "Easy", "python") == ["Array", "Hash Table"]


def _editor_state():
    from coding_tutor.quiz.session import initialize_session_state
    state = {}
    initialize_session_state(state)
    state.update({
        "question_type": "data_analysis", "question_type_control": "data_analysis",
        "method": "sql", "method_control": "sql",
        "current_question": {
            "id": "q1", "question_type": "data_analysis",
            "supported_methods": ["sql", "pandas", "pyspark", "polars"],
        },
        "editor_q1_sql": "SELECT * FROM t", "editor_baseline_q1_sql": "-- starter",
        "editor_content": "SELECT * FROM t",
    })
    return state


def test_dirty_method_change_requires_decision_and_keep_restores_draft():
    from coding_tutor.quiz.session import request_learning_change, resolve_pending_learning_change
    state = _editor_state()
    state["method_control"] = "pandas"
    assert request_learning_change("method", "pandas", state) is True
    assert state["method"] == "sql"
    assert state["method_control"] == "sql"
    resolve_pending_learning_change("keep", state)
    assert state["method"] == "pandas"
    assert state["editor_q1_sql"] == "SELECT * FROM t"


@pytest.mark.parametrize("decision", ["discard", "cancel"])
def test_dirty_method_change_discard_or_cancel(decision):
    from coding_tutor.quiz.session import request_learning_change, resolve_pending_learning_change
    state = _editor_state()
    request_learning_change("method", "pandas", state)
    resolve_pending_learning_change(decision, state)
    if decision == "discard":
        assert state["method"] == "pandas"
        assert state["editor_q1_sql"] == "-- starter"
    else:
        assert state["method"] == "sql"
    assert state["pending_learning_change"] is None


def test_saved_editor_changes_method_without_prompt():
    from coding_tutor.quiz.session import mark_editor_saved, request_learning_change
    state = _editor_state()
    mark_editor_saved("q1", "sql", "SELECT * FROM t", state)
    assert request_learning_change("method", "pandas", state) is False
    assert state["method"] == "pandas"


@pytest.mark.parametrize(
    ("has_dataset", "has_ai", "random_value", "expected"),
    [
        (True, True, 0.49, "ai"),
        (True, True, 0.50, "dataset"),
        (True, False, None, "dataset"),
        (False, True, None, "ai"),
        (False, False, None, None),
    ],
)
def test_choose_mixed_source(has_dataset, has_ai, random_value, expected):
    from coding_tutor.ui.main_page import _choose_mixed_source
    assert _choose_mixed_source(has_dataset, has_ai, random_value) == expected


def test_load_question_includes_dataset_provenance(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.quiz.session as session

    conn = get_test_db()
    source_id = conn.execute(
        """INSERT INTO question_sources (dataset_name, attribution, license)
           VALUES ('sample', 'Sample authors', 'MIT') RETURNING id"""
    ).fetchone()[0]
    question_id = conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, source_id)
           VALUES ('Q', 'algorithm', 'Easy', 'P', '["python"]', ?) RETURNING id""",
        [source_id],
    ).fetchone()[0]
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    fake_state = State()
    monkeypatch.setattr(session.st, "session_state", fake_state)

    session.load_question(str(question_id))

    loaded = fake_state["current_question"]
    assert loaded["source_kind"] == "dataset"
    assert loaded["dataset_name"] == "sample"
    assert loaded["attribution"] == "Sample authors"
    assert loaded["license"] == "MIT"


def test_load_question_uses_test_cases_as_example_fallback(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.quiz.session as session
    conn = get_test_db()
    question_id = conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Q', 'algorithm', 'Easy', 'P', '["python"]') RETURNING id"""
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO question_test_cases (question_id, input_data, expected_output, is_example) VALUES (?, '1', '2', true)",
        [question_id],
    )
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    fake_state = {"method": "python"}
    monkeypatch.setattr(session.st, "session_state", fake_state)
    session.load_question(str(question_id))
    assert fake_state["current_question"]["examples"] == [{"input": 1, "expected_output": 2}]


def test_app_source_control_and_conditional_topic(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.ui.main_page as main_page
    import coding_tutor.ui.sidebar as sidebar

    conn = get_test_db()
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    monkeypatch.setattr(main_page, "get_db", lambda: conn)
    monkeypatch.setattr(sidebar, "get_db", lambda: conn)

    app = AppTest.from_file("app.py", default_timeout=10).run()
    assert not app.exception
    assert app.title
    assert "Coding Tutor" in app.title[0].value
    source = next(widget for widget in app.segmented_control if widget.label == "Learning mode")
    assert source.options == ["Curated dataset", "AI generated", "Mixed"]
    assert any(widget.label == "Topic/tag" for widget in app.selectbox)
    question_type = next(widget for widget in app.selectbox if widget.label == "Question type")
    difficulty = next(widget for widget in app.selectbox if widget.label == "Difficulty")
    method = next(widget for widget in app.selectbox if widget.label == "Solution method")
    assert question_type.options == ["Algorithm", "Data Analysis"]
    assert difficulty.options == ["Beginner", "Easy", "Medium", "Hard", "Very Hard"]
    assert method.options == ["PYTHON"]

    question_type.set_value("data_analysis").run()
    assert not app.exception
    method = next(widget for widget in app.selectbox if widget.label == "Solution method")
    assert method.options == ["SQL", "PANDAS", "PYSPARK", "POLARS"]

    source = next(widget for widget in app.segmented_control if widget.label == "Learning mode")
    source.set_value("ai_generated").run()
    assert not app.exception

    provider = next(widget for widget in app.selectbox if widget.label == "Provider")
    provider.set_value("gemini").run()
    assert not app.exception
    model = next(widget for widget in app.selectbox if widget.label == "Model")
    assert model.options == ["Gemini 3.5 Flash Lite", "Gemini 3.7 Flash"]


@pytest.mark.parametrize(
    ("failure_name", "expected"),
    [
        ("PROVIDER_UNAVAILABLE", "not configured"),
        ("PROVIDER_ERROR", "provider request failed"),
        ("MALFORMED_RESPONSE", "malformed JSON"),
        ("INCOMPLETE_RESPONSE", "incomplete or invalid question"),
        ("STORAGE_ERROR", "No partial question was kept"),
    ],
)
def test_generation_failures_have_distinct_safe_messages(failure_name, expected):
    from coding_tutor.generation.generator import GenerationFailure, GenerationResult
    from coding_tutor.ui.main_page import _generation_failure_message

    result = GenerationResult(failure=getattr(GenerationFailure, failure_name))
    assert expected in _generation_failure_message(result)


def test_generation_failure_does_not_render_model_controlled_detail():
    from coding_tutor.generation.generator import GenerationFailure, GenerationResult
    from coding_tutor.ui.main_page import _generation_failure_message

    result = GenerationResult(
        failure=GenerationFailure.INCOMPLETE_RESPONSE,
        detail="sentinel-model-output",
    )
    assert "sentinel-model-output" not in _generation_failure_message(result)


def test_app_loads_question_editor_and_visible_actions(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.ui.main_page as main_page
    import coding_tutor.ui.sidebar as sidebar
    conn = get_test_db()
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, constraints,
                examples, supported_methods, tags, is_complete)
           VALUES ('Two Sum', 'algorithm', 'Easy', 'Find two values.', 'At least two values.',
                   '[{"input":"[1,2]","output":"[0,1]"}]', '["python"]', '["Array"]', true)"""
    )
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    monkeypatch.setattr(main_page, "get_db", lambda: conn)
    monkeypatch.setattr(sidebar, "get_db", lambda: conn)

    app = AppTest.from_file("app.py", default_timeout=10).run()
    load = next(button for button in app.button if button.label == "Load Question")
    load.click().run()
    assert not app.exception
    assert any("Two Sum" in markdown.value for markdown in app.markdown)
    assert app.text_area and "def solution" in app.text_area[0].value
    assert any(button.label == "✅ Done" for button in app.button)
    assert any(button.label == "💡 Show Solution" for button in app.button)


def test_provider_secrets_are_never_rendered(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.ui.main_page as main_page

    secrets = {
        "OPENAI_API_KEY": "sentinel-openai-secret",
        "OPENAI_BASE_URL": "https://sentinel-base-url.invalid/v1",
        "AGNES_API_KEY": "sentinel-agnes-secret",
        "GOOGLE_API_KEY": "sentinel-google-secret",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    conn = get_test_db()
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    monkeypatch.setattr(main_page, "get_db", lambda: conn)

    app = AppTest.from_file("app.py", default_timeout=10).run()
    assert not app.exception

    rendered_values = []
    for collection_name in (
        "caption",
        "error",
        "header",
        "info",
        "markdown",
        "subheader",
        "success",
        "text",
        "title",
        "warning",
    ):
        rendered_values.extend(
            str(element.value) for element in getattr(app, collection_name, [])
        )
    rendered = "\n".join(rendered_values)

    assert "configuration available" in rendered
    assert all(secret not in rendered for secret in secrets.values())
