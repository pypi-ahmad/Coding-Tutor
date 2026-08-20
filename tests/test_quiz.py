"""Phase 9 Quiz Mode navigation, validation, scoring, and persistence."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _question(conn, title, difficulty="Easy"):
    return str(conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, tags)
           VALUES (?, 'algorithm', ?, 'Solve this.', '[\"python\"]', '[\"arrays\"]')
           RETURNING id""",
        [title, difficulty],
    ).fetchone()[0])


def _settings(**overrides):
    value = {
        "question_source": "dataset", "question_type": "algorithm",
        "difficulty": "Easy", "topic": "general", "method": "python",
        "total_items": 2, "coding_items": 1, "mcq_items": 1,
        "provider": "openai", "model_id": "model",
    }
    value.update(overrides)
    return value


def test_quiz_tables_are_separate_and_share_question_provenance(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.quiz.persistence as persistence

    conn = get_test_db()
    question_ids = [_question(conn, "One"), _question(conn, "Two")]
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    attempt_id = persistence.create_quiz_attempt(_settings())
    persistence.insert_quiz_items(
        attempt_id,
        [{"id": qid, "problem_statement": "Solve this."} for qid in question_ids],
        1, "python",
    )
    assert conn.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM quiz_items").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
    assert {str(row[0]) for row in conn.execute("SELECT question_id FROM quiz_items").fetchall()} == set(question_ids)
    assert persistence.latest_unfinished_quiz() == attempt_id


def test_curated_quiz_selection_respects_difficulty_topic_and_has_no_duplicates(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.quiz.service as service

    conn = get_test_db()
    expected = {_question(conn, "A"), _question(conn, "B")}
    _question(conn, "Hard", "Hard")
    conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods, tags)
           VALUES ('Other topic', 'algorithm', 'Easy', 'P', '[\"python\"]', '[\"graphs\"]')"""
    )
    monkeypatch.setattr(service, "get_db", lambda: conn)
    selected = service._select_questions(_settings(topic="arrays"), model=None)
    assert {item["id"] for item in selected} == expected
    assert len({item["id"] for item in selected}) == 2


def test_mcq_validator_requires_exact_ids_four_unique_options_and_one_correct():
    from coding_tutor.quiz.service import QuizError, _validate_mcq_response

    valid = {
        "status": "ok",
        "questions": [{
            "question_id": "q1", "prompt": "What is correct?",
            "options": [{"id": key, "text": f"Option {key}"} for key in "abcd"],
            "correct_option_id": "b", "explanation": "B follows the requirement.",
        }],
    }
    assert _validate_mcq_response(json.dumps(valid), {"q1"})["q1"]["correct_option_id"] == "b"

    for mutation in (
        lambda data: data["questions"][0].update(question_id="wrong"),
        lambda data: data["questions"][0]["options"].pop(),
        lambda data: data["questions"][0]["options"][1].update(text="Option a"),
        lambda data: data["questions"][0].update(correct_option_id="missing"),
    ):
        broken = json.loads(json.dumps(valid))
        mutation(broken)
        with pytest.raises(QuizError):
            _validate_mcq_response(json.dumps(broken), {"q1"})


def test_mcq_generation_uses_file_backed_prompt_and_shared_rules(monkeypatch):
    from coding_tutor.providers.base import ChatResponse
    import coding_tutor.quiz.service as service

    captured = {}

    class Provider:
        def chat(self, messages, model, system_prompt=None):
            captured["prompt"] = messages[0].content
            captured["system_prompt"] = system_prompt
            payload = {
                "status": "ok",
                "questions": [{
                    "question_id": "q1",
                    "prompt": "Which option is correct?",
                    "options": [
                        {"id": key, "text": f"Option {key}"} for key in "abcd"
                    ],
                    "correct_option_id": "a",
                    "explanation": "A follows the question requirements.",
                }],
            }
            return ChatResponse(json.dumps(payload), model.model_id, "openai")

    saved = {}
    monkeypatch.setattr(service, "_provider", lambda *_args: Provider())
    monkeypatch.setattr(
        service.persistence,
        "save_mcq_content",
        lambda attempt_id, content: saved.update(content),
    )
    model = SimpleNamespace(model_id="model")
    service._prepare_mcqs("attempt", [{
        "answer_format": "mcq",
        "question_id": "q1",
        "title": "Question",
        "problem_statement": "Solve this.",
        "constraints": "",
        "examples": [],
        "method": "python",
    }], "openai", model)

    assert captured["prompt"].startswith(
        "Create one four-option, single-answer multiple-choice item"
    )
    assert "AI-estimated correctness" in captured["system_prompt"]
    assert saved["q1"]["model_id"] == "model"


def test_quiz_scoring_equal_weights_and_delays_completion_until_ai_succeeds(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.evaluation.feedback import AIAssessment
    import coding_tutor.evaluation.feedback as feedback
    import coding_tutor.quiz.persistence as persistence
    import coding_tutor.quiz.service as service

    conn = get_test_db()
    q1, q2 = _question(conn, "Code"), _question(conn, "Choice")
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    monkeypatch.setattr(service, "get_db", lambda: conn)
    attempt_id = persistence.create_quiz_attempt(_settings())
    persistence.insert_quiz_items(
        attempt_id,
        [{"id": q1, "problem_statement": "Solve this."}, {"id": q2, "problem_statement": "Solve this."}],
        1, "python",
    )
    persistence.save_mcq_content(attempt_id, {q2: {
        "prompt": "Pick B", "options": [{"id": key, "text": key.upper()} for key in "abcd"],
        "correct_option_id": "b", "explanation": "B is correct.",
        "provider": "openai", "model_id": "model",
    }})
    _, items = persistence.load_quiz(attempt_id)
    persistence.save_draft(items[0]["id"], "coding", "return 1")
    persistence.save_draft(items[1]["id"], "mcq", "b")

    calls = MagicMock(side_effect=RuntimeError("temporary"))
    monkeypatch.setattr(feedback, "assess_solution", calls)
    selected_model = SimpleNamespace(model_id="model")
    assert service.evaluate_quiz(attempt_id, "openai", selected_model) is False
    attempt, failed_items = persistence.load_quiz(attempt_id)
    assert attempt["status"] == "evaluation_error"
    assert failed_items[1]["item_status"] == "scored"

    monkeypatch.setattr(
        feedback, "assess_solution",
        lambda *args, **kwargs: AIAssessment(80, 8, [], "Good", "", None, "model", "openai"),
    )
    assert service.evaluate_quiz(attempt_id, "openai", selected_model) is True
    attempt, scored = persistence.load_quiz(attempt_id)
    assert attempt["status"] == "completed"
    assert attempt["percentage_correct"] == 90.0
    assert attempt["passed"] is True
    assert [item["percentage_correct"] for item in scored] == [80.0, 100.0]


def test_blank_coding_answer_scores_zero_without_ai_call(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.evaluation.feedback as feedback
    import coding_tutor.quiz.persistence as persistence
    import coding_tutor.quiz.service as service

    conn = get_test_db()
    qid = _question(conn, "Blank")
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    monkeypatch.setattr(service, "get_db", lambda: conn)
    attempt_id = persistence.create_quiz_attempt(_settings(total_items=1, coding_items=1, mcq_items=0))
    persistence.insert_quiz_items(attempt_id, [{"id": qid, "problem_statement": "Solve this."}], 1, "python")
    persistence.mark_ready(attempt_id)
    called = MagicMock()
    monkeypatch.setattr(feedback, "assess_solution", called)
    assert service.evaluate_quiz(attempt_id, "openai", object()) is True
    assert called.call_count == 0
    attempt, items = persistence.load_quiz(attempt_id)
    assert attempt["percentage_correct"] == 0.0
    assert attempt["passed"] is False
    assert items[0]["percentage_correct"] == 0.0


def test_quiz_progress_is_filtered_and_separate(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.database.progress import get_quiz_progress
    import coding_tutor.quiz.persistence as persistence

    conn = get_test_db()
    monkeypatch.setattr(persistence, "get_db", lambda: conn)
    first = persistence.create_quiz_attempt(_settings())
    second = persistence.create_quiz_attempt(_settings(difficulty="Hard"))
    persistence.complete_quiz(first, 80)
    persistence.complete_quiz(second, 70)
    summary = get_quiz_progress(conn)
    assert summary["total_attempts"] == 2
    assert summary["completed_attempts"] == 2
    assert summary["passed_attempts"] == 1
    assert get_quiz_progress(conn, difficulty="Hard")["passed_attempts"] == 0


def test_quiz_navigation_and_setup_controls(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.quiz.persistence as persistence
    import coding_tutor.quiz.service as service
    import coding_tutor.ui.main_page as main_page
    import coding_tutor.ui.sidebar as sidebar

    conn = get_test_db()
    for module in (connection, persistence, service, main_page, sidebar):
        if hasattr(module, "get_db"):
            monkeypatch.setattr(module, "get_db", lambda: conn)
    app = AppTest.from_file("app.py", default_timeout=10).run()
    navigation = next(widget for widget in app.radio if widget.label == "Navigation")
    assert "Quiz" in navigation.options
    navigation.set_value("Quiz").run()
    assert not app.exception
    assert any(title.value == "🧠 Quiz mode" for title in app.title)
    assert any(widget.label == "Total questions" for widget in app.number_input)
    assert any(widget.label == "Coding questions" for widget in app.number_input)
