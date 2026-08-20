from __future__ import annotations

from types import SimpleNamespace


def _generated_question(**overrides):
    value = {
        "domain": "AI Engineering", "topic": "RAG", "answer_format": "theory",
        "prompt_style": "scenario", "difficulty": "Medium",
        "prompt": "How would you debug retrieval quality?",
        "reference_answer": "Measure retrieval separately from generation.",
        "rubric": ["Separates retrieval and generation"], "method": None,
        "options": [], "correct_option": None, "tags": ["rag"],
    }
    value.update(overrides)
    return value


def test_generated_ai_question_is_promoted_and_attempt_is_scored(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.interview import service

    conn = get_test_db()
    monkeypatch.setattr(service, "connection", lambda: conn)
    monkeypatch.setattr(service, "generate_question", lambda *args, **kwargs: _generated_question())
    monkeypatch.setattr(
        service, "assess_answer",
        lambda *args, **kwargs: {"score": 80.0, "strengths": ["Good"], "gaps": [],
                                "feedback": "Solid", "next_focus": "evaluation"},
    )
    model = SimpleNamespace(model_id="model", provider="openai", verified=True)
    filters = {
        "source_mode": "ai", "domain": "AI Engineering", "topic": "RAG",
        "difficulty": "Medium", "answer_format": "theory", "prompt_style": "scenario",
        "method": None, "web_enabled": False,
    }

    session_id = service.create_ai_session(filters, "openai", model)
    item, warning = service.next_ai_question(session_id, "openai", model)
    result = service.submit_ai_answer(session_id, item, "I would measure recall.", "openai", model)

    assert warning is None
    assert result["score"] == 80.0
    assert conn.execute("SELECT COUNT(*) FROM interview_items").fetchone()[0] == 1
    assert conn.execute("SELECT origin FROM interview_item_generation").fetchone()[0] == "ai"
    assert conn.execute("SELECT status FROM ai_question_items").fetchone()[0] == "scored"


def test_local_mode_never_generates(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.interview import service

    conn = get_test_db()
    monkeypatch.setattr(service, "connection", lambda: conn)
    conn.execute("INSERT INTO question_sources (dataset_name, source_key) VALUES ('test','one')")
    source_id = conn.execute("SELECT id FROM question_sources").fetchone()[0]
    conn.execute(
        """INSERT INTO interview_items
           (source_id, domain, topic, answer_format, prompt_style, difficulty, prompt, content_hash)
           VALUES (?, 'AI Engineering', 'RAG', 'theory', 'scenario', 'Medium', 'Local question?', 'local')""",
        [source_id],
    )
    monkeypatch.setattr(service, "generate_question", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    filters = {
        "source_mode": "local", "domain": "AI Engineering", "topic": "RAG",
        "difficulty": "Medium", "answer_format": "theory", "prompt_style": "scenario",
        "method": None, "web_enabled": False,
    }
    session_id = service.create_ai_session(filters, None, None)
    item, _ = service.next_ai_question(session_id, None, None)
    assert item["prompt"] == "Local question?"


def test_interview_timer_and_report_persist_without_documents(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.interview import service

    conn = get_test_db()
    monkeypatch.setattr(service, "connection", lambda: conn)
    monkeypatch.setattr(service, "generate_question", lambda *args, **kwargs: _generated_question())
    monkeypatch.setattr(
        service, "final_report",
        lambda *args, **kwargs: {"overall_score": 0.0, "summary": "Done", "strengths": [],
                                 "gaps": [], "recommendations": []},
    )
    model = SimpleNamespace(model_id="model", provider="openai", verified=True)
    blueprint = {"role": "AI Engineer", "level": "Mid", "topics": ["RAG"],
                 "formats": ["theory"], "languages": ["python"]}
    session_id = service.start_interview("jd", 30, "ai", blueprint, False, "openai", model)
    service.add_interview_turn(session_id, "openai", model)
    service.skip_pending_turn(session_id)
    report = service.finish_interview(session_id, "openai", model)
    loaded, turns = service.load_interview(session_id)

    assert report["summary"] == "No answers were submitted."
    assert loaded["status"] == "completed"
    assert turns[0]["status"] == "skipped"
    columns = {row[0] for row in conn.execute("DESCRIBE interview_sessions").fetchall()}
    assert not {"jd", "resume", "document_text"} & columns


def test_generated_interview_question_uses_last_three_scored_turns(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.interview import service

    conn = get_test_db()
    monkeypatch.setattr(service, "connection", lambda: conn)
    captured = []

    def generate(*args, **kwargs):
        captured.append(kwargs.get("adaptive_context"))
        return _generated_question(prompt=f"Question {len(captured)}?")

    monkeypatch.setattr(service, "generate_question", generate)
    monkeypatch.setattr(
        service, "assess_answer",
        lambda *args, **kwargs: {"score": 70.0, "strengths": [], "gaps": ["depth"],
                                "feedback": "More detail", "next_focus": "trade-offs"},
    )
    model = SimpleNamespace(model_id="model", provider="openai", verified=True)
    blueprint = {"role": "AI Engineer", "level": "Mid", "topics": ["RAG"],
                 "formats": ["theory"], "languages": ["python"]}
    session_id = service.start_interview("tech", 30, "ai", blueprint, False, "openai", model)

    for position in range(4):
        item, _ = service.add_interview_turn(session_id, "openai", model)
        service.submit_interview_answer(session_id, item, f"Answer {position + 1}", "openai", model)
    service.add_interview_turn(session_id, "openai", model)

    assert captured[0] == {"blueprint": blueprint, "recent_scored_turns": []}
    recent = captured[-1]["recent_scored_turns"]
    assert [turn["answer"] for turn in recent] == ["Answer 2", "Answer 3", "Answer 4"]
    assert all(turn["gaps"] == ["depth"] for turn in recent)


def test_text_document_extraction_is_bounded():
    from coding_tutor.interview.documents import extract_document

    assert extract_document("resume.txt", b"AI engineer") == "AI engineer"


def test_navigation_exposes_ai_questions_and_interview(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.interview import service

    conn = get_test_db()
    monkeypatch.setattr(service, "connection", lambda: conn)
    app = AppTest.from_file("app.py", default_timeout=10).run()
    navigation = next(widget for widget in app.radio if widget.label == "Navigation")
    assert navigation.options == ["Coding", "Quiz", "AI Questions", "Interview", "Progress"]

    navigation.set_value("AI Questions").run()
    assert not app.exception
    assert any("AI Questions" in title.value for title in app.title)

    navigation = next(widget for widget in app.radio if widget.label == "Navigation")
    navigation.set_value("Interview").run()
    assert not app.exception
    assert any("Interview" in title.value for title in app.title)


def test_firecrawl_payload_parser_handles_nested_web_results():
    from coding_tutor.web_research import _rows

    payload = {"success": True, "data": {"web": [
        {"title": "Docs", "url": "https://example.com", "description": "Reference"}
    ]}}
    assert _rows(payload)[0]["title"] == "Docs"


def test_firecrawl_access_mode_never_returns_key(monkeypatch):
    from coding_tutor.web_research import firecrawl_access_mode

    monkeypatch.setenv("FIRECRAWL_API_KEY", "secret-value")
    assert firecrawl_access_mode() == "authenticated"
