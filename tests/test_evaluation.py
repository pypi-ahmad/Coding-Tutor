"""Tests for strict AI assessment parsing and persistence."""
from contextlib import nullcontext
import json
import pytest


def test_parse_assessment_derives_marks():
    from coding_tutor.evaluation.feedback import _parse_assessment
    result = _parse_assessment(json.dumps({
        "estimated_percentage_correct": 83,
        "identified_mistakes": ["edge case"],
        "explanation": "Mostly correct.",
        "suggested_correction": "Handle empty input.",
        "corrected_code": None,
    }), "model", "provider")
    assert result.estimated_percentage_correct == 83
    assert result.marks == 8.3


def test_parse_assessment_rejects_malformed_json():
    from coding_tutor.evaluation.feedback import AssessmentError, _parse_assessment
    with pytest.raises(AssessmentError, match="malformed"):
        _parse_assessment("not json", "model", "provider")


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {
            "estimated_percentage_correct": 101,
            "identified_mistakes": [],
            "explanation": "Explanation",
            "suggested_correction": "",
            "corrected_code": None,
        },
        {
            "estimated_percentage_correct": 50,
            "identified_mistakes": ["issue"] * 21,
            "explanation": "Explanation",
            "suggested_correction": "",
            "corrected_code": None,
        },
        {
            "estimated_percentage_correct": 50,
            "identified_mistakes": [],
            "explanation": "",
            "suggested_correction": "",
            "corrected_code": None,
        },
        {
            "estimated_percentage_correct": 50,
            "identified_mistakes": [],
            "explanation": "x" * 8_001,
            "suggested_correction": "",
            "corrected_code": None,
        },
    ],
)
def test_parse_assessment_rejects_invalid_or_unbounded_payloads(payload):
    from coding_tutor.evaluation.feedback import AssessmentError, _parse_assessment

    with pytest.raises(AssessmentError):
        _parse_assessment(json.dumps(payload), "model", "provider")


def test_assessment_prompt_contains_verbatim_submission_and_question_context(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.providers.registry as registry
    from coding_tutor.evaluation.feedback import assess_solution
    from coding_tutor.providers.base import ChatResponse, ModelOption

    conn = get_test_db()
    question_id = str(conn.execute(
        """INSERT INTO questions
           (title, question_type, difficulty, problem_statement, constraints,
            examples, supported_methods, tags)
           VALUES ('Q', 'algorithm', 'Easy', 'Solve it.', 'Keep order.',
                   '[{\"input\": [1]}]', '[\"python\"]', '[\"arrays\"]')
           RETURNING id"""
    ).fetchone()[0])
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    model = ModelOption("openai", "verified-model", "Verified", True)

    class Provider:
        captured = None
        captured_system = None

        def is_configured(self):
            return True

        def get_model_options(self):
            return [model]

        def chat(self, messages, selected_model, system_prompt=None):
            self.captured = messages[0].content
            self.captured_system = system_prompt
            return ChatResponse(
                json.dumps({
                    "estimated_percentage_correct": 75,
                    "identified_mistakes": ["Missing an edge case."],
                    "explanation": "The main approach is sound.",
                    "suggested_correction": "Handle empty input.",
                    "corrected_code": None,
                }),
                selected_model.model_id,
                "openai",
            )

    provider = Provider()
    monkeypatch.setattr(registry, "get_provider", lambda _name: provider)
    question = {
        "id": question_id,
        "title": "Q",
        "question_type": "algorithm",
        "difficulty": "Easy",
        "problem_statement": "Solve it.",
        "constraints": "Keep order.",
        "examples": [{"input": [1]}],
        "tags": ["arrays"],
        "supported_methods": ["python"],
    }
    submitted = "\n  def solution():\n      return 1\n"

    assess_solution(question, submitted, "python", "openai", model)

    def prompt_value(name):
        marked = provider.captured.split(f"<{name}>\n", 1)[1].split(
            f"\n</{name}>", 1
        )[0]
        return json.loads(marked)

    assert prompt_value("learner_submission") == submitted
    assert prompt_value("selected_method") == "python"
    question_context = prompt_value("question")
    assert question_context["constraints"] == "Keep order."
    assert question_context["examples"] == [{"input": [1]}]
    assert "static analysis only" in provider.captured
    assert "AI-estimated correctness" in provider.captured_system


def test_attempt_lifecycle_preserves_original(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.evaluation.persistence as persistence_mod
    from coding_tutor.evaluation.feedback import AIAssessment
    from coding_tutor.evaluation.persistence import create_attempt, complete_attempt
    conn = get_test_db()
    q_id = str(conn.execute("INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods) VALUES ('Q','algorithm','Easy','P','[\"python\"]') RETURNING id").fetchone()[0])
    monkeypatch.setattr(persistence_mod, "get_db", lambda: conn)
    attempt_id = create_attempt(q_id, "python", "\n  original  \n", "openai", "model")
    complete_attempt(attempt_id, AIAssessment(90, 9, [], "ok", "none", "replacement", "model", "openai"))
    row = conn.execute("SELECT submitted_code, assessment_status, percentage_correct FROM attempts WHERE id=?", [attempt_id]).fetchone()
    assert row == ("\n  original  \n", "completed", 90.0)


def test_provider_failure_is_sanitized_in_ui_and_database(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.evaluation.persistence as persistence
    import coding_tutor.providers.registry as registry
    import coding_tutor.ui.submit_handler as submit_handler
    from coding_tutor.providers.base import ModelOption

    class State(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__

    class FakeStreamlit:
        def __init__(self, state):
            self.session_state = state
            self.errors = []
            self.warnings = []

        def error(self, message):
            self.errors.append(message)

        def warning(self, message):
            self.warnings.append(message)

        def spinner(self, _message):
            return nullcontext()

    conn = get_test_db()
    question_id = str(conn.execute(
        """INSERT INTO questions
           (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Q', 'algorithm', 'Easy', 'P', '[\"python\"]') RETURNING id"""
    ).fetchone()[0])
    model = ModelOption("openai", "verified-model", "Verified", True)
    secret = "sentinel-provider-secret"

    class Provider:
        def is_configured(self):
            return True

        def get_model_options(self):
            return [model]

        def chat(self, *_args, **_kwargs):
            raise RuntimeError(f"request failed with {secret}")

    state = State({
        f"editor_{question_id}_python": "\n  original  \n",
        "provider": "openai",
        "model": model,
        "submit_trigger": True,
    })
    fake_st = FakeStreamlit(state)
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    monkeypatch.setattr(registry, "get_provider", lambda _name: Provider())
    monkeypatch.setattr(submit_handler, "st", fake_st)

    attempt_id = submit_handler.handle_submit(
        {
            "id": question_id,
            "supported_methods": ["python"],
            "title": "Q",
            "problem_statement": "P",
        },
        "python",
    )

    row = conn.execute(
        "SELECT submitted_code, assessment_status, error_details FROM attempts WHERE id=?",
        [attempt_id],
    ).fetchone()
    rendered = "\n".join(fake_st.errors + fake_st.warnings)
    assert row[0] == "\n  original  \n"
    assert row[1] == "error"
    assert secret not in row[2]
    assert secret not in rendered


def test_correction_can_be_applied_and_restored(monkeypatch):
    import coding_tutor.ui.evaluation_view as evaluation_view

    state = {
        "editor_question_python": "original",
    }
    monkeypatch.setattr(evaluation_view.st, "session_state", state)

    evaluation_view._apply_correction(
        "editor_question_python", "backup", "applied", "corrected"
    )
    assert state["editor_question_python"] == "corrected"
    assert state["backup"] == "original"
    assert state["applied"] is True

    evaluation_view._restore_correction(
        "editor_question_python", "backup", "applied"
    )
    assert state["editor_question_python"] == "original"
    assert state["applied"] is False


def test_active_assessment_is_rendered_again_after_rerun(monkeypatch):
    import coding_tutor.ui.evaluation_view as evaluation_view
    import coding_tutor.ui.main_page as main_page
    from coding_tutor.evaluation.feedback import AIAssessment

    assessment = AIAssessment(
        80, 8, [], "Explanation", "Suggestion", None, "model", "openai"
    )
    state = {
        "method": "python",
        "active_assessment": {
            "question_id": "question",
            "method": "python",
            "attempt_id": "attempt",
            "assessment": assessment,
        },
    }
    rendered = []
    monkeypatch.setattr(main_page.st, "session_state", state)
    monkeypatch.setattr(
        evaluation_view,
        "render_evaluation",
        lambda *args: rendered.append(args),
    )

    main_page._render_active_assessment({"id": "question"})
    main_page._render_active_assessment({"id": "question"})

    assert len(rendered) == 2
    assert rendered[0][1] is assessment


def test_progress_summary_empty_db():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.database.progress import get_progress_summary
    summary = get_progress_summary(get_test_db())
    assert summary["total_attempts"] == 0
    assert summary["assessed_questions"] == 0
