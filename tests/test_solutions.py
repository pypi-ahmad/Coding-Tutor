"""Phase 7 structured solution generation and view persistence."""
import json

import pytest

from coding_tutor.database.connection import get_test_db
from coding_tutor.providers.base import ChatResponse
from coding_tutor.providers.config import OPENAI_MODELS


def _payload(count=1, comment="# explanation"):
    return {
        "multiple_approaches_meaningful": count > 1,
        "availability_note": None,
        "solutions": [
            {
                "title": f"Approach {index}",
                "code": f"{comment}\nprint({index})",
                "explanation": "This applies the required transformation.",
                "theory": "Use a direct deterministic transformation.",
                "complexity": "O(n) time.",
            }
            for index in range(count)
        ],
    }


def test_validate_algorithm_allows_multiple_commented_approaches():
    from coding_tutor.evaluation.solutions import _validate_payload

    solutions, meaningful, note = _validate_payload(_payload(2), "python", "algorithm")
    assert len(solutions) == 2
    assert meaningful is True
    assert note is None


@pytest.mark.parametrize("method", ["javascript/typescript", "java", "cpp"])
def test_validate_algorithm_allows_c_style_comments(method):
    from coding_tutor.evaluation.solutions import _validate_payload

    solutions, _, _ = _validate_payload(
        _payload(comment="// explanation"), method, "algorithm"
    )
    assert len(solutions) == 1


@pytest.mark.parametrize("method,comment", [("sql", "-- note"), ("pandas", "# note"), ("pyspark", "# note"), ("polars", "# note")])
def test_validate_data_solution_for_each_method(method, comment):
    from coding_tutor.evaluation.solutions import _validate_payload

    solutions, _, _ = _validate_payload(_payload(comment=comment), method, "data_analysis")
    assert len(solutions) == 1


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {**_payload(), "extra": True},
        {**_payload(3)},
        {**_payload(), "solutions": [{**_payload()["solutions"][0], "code": "print(1)"}]},
        {"multiple_approaches_meaningful": False, "availability_note": None, "solutions": []},
    ],
)
def test_validator_rejects_malformed_or_incomplete_data_payload(payload):
    from coding_tutor.evaluation.solutions import _validate_payload

    with pytest.raises((TypeError, ValueError)):
        _validate_payload(payload, "pandas", "data_analysis")


def test_generation_uses_context_and_does_not_leak_provider_error(monkeypatch):
    import coding_tutor.evaluation.solutions as module

    conn = get_test_db()
    qid = str(conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Two Sum', 'algorithm', 'Easy', 'Find indices.', '[\"python\"]') RETURNING id"""
    ).fetchone()[0])
    monkeypatch.setattr(module, "get_db", lambda: conn)
    captured = {}

    class Provider:
        def is_configured(self): return True
        def chat(self, messages, model, system_prompt=None):
            captured["prompt"] = messages[0].content
            captured["system_prompt"] = system_prompt
            return ChatResponse(json.dumps(_payload()), model.model_id, "openai")

    monkeypatch.setattr(module, "get_provider", lambda name: Provider())
    result = module.generate_teaching_solutions(
        {"id": qid, "title": "Two Sum", "question_type": "algorithm", "problem_statement": "Find indices."},
        "python", "openai", OPENAI_MODELS[0],
    )
    assert result.bundle is not None
    assert "Find indices." in captured["prompt"]
    assert captured["prompt"].startswith("Teach learner how to solve")
    assert "AI-estimated correctness" in captured["system_prompt"]

    class Broken(Provider):
        def chat(self, *args, **kwargs): raise RuntimeError("SECRET-SENTINEL")

    monkeypatch.setattr(module, "get_provider", lambda name: Broken())
    failed = module.generate_teaching_solutions(
        {"id": qid, "question_type": "algorithm"}, "python", "openai", OPENAI_MODELS[0]
    )
    assert failed.failure == module.SolutionFailure.PROVIDER_ERROR
    assert "SECRET-SENTINEL" not in repr(failed)


def test_incomplete_data_context_never_calls_provider(monkeypatch):
    import coding_tutor.evaluation.solutions as module

    conn = get_test_db()
    qid = str(conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Analysis', 'data_analysis', 'Easy', 'Aggregate.', '[\"sql\"]') RETURNING id"""
    ).fetchone()[0])
    monkeypatch.setattr(module, "get_db", lambda: conn)
    monkeypatch.setattr(module, "get_provider", lambda name: (_ for _ in ()).throw(AssertionError("called")))
    result = module.generate_teaching_solutions(
        {"id": qid, "question_type": "data_analysis"}, "sql", "openai", OPENAI_MODELS[0]
    )
    assert result.failure == module.SolutionFailure.INCOMPLETE_CONTEXT


def test_solution_view_event_appends_once_and_links_only_matching_attempt(monkeypatch):
    import coding_tutor.evaluation.persistence as persistence
    from coding_tutor.database.progress import get_solution_view_history

    conn = get_test_db()
    qids = [str(conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES (?, 'algorithm', 'Easy', 'Solve.', '[\"python\"]') RETURNING id""", [title]
    ).fetchone()[0]) for title in ("One", "Two")]
    attempt = str(conn.execute(
        """INSERT INTO attempts (question_id, method, submitted_code) VALUES (?, 'python', 'pass') RETURNING id""",
        [qids[0]],
    ).fetchone()[0])
    monkeypatch.setattr(persistence, "get_db", lambda: conn)

    view_id = persistence.record_solution_method(qids[0], attempt, "python")
    persistence.record_solution_method(qids[0], attempt, "python", view_id)
    persistence.record_solution_method(qids[0], attempt, "sql", view_id)
    row = conn.execute("SELECT methods_viewed, attempt_id FROM solution_views WHERE id=?", [view_id]).fetchone()
    assert json.loads(row[0]) == ["python", "sql"]
    assert str(row[1]) == attempt
    assert conn.execute("SELECT solution_viewed FROM attempts WHERE id=?", [attempt]).fetchone()[0] is True

    other = persistence.record_solution_method(qids[1], attempt, "python")
    assert conn.execute("SELECT attempt_id FROM solution_views WHERE id=?", [other]).fetchone()[0] is None
    assert get_solution_view_history(conn)[0]["methods"] == ["python"]


def test_stored_solution_query_preserves_duplicates(monkeypatch):
    import coding_tutor.database.connection as connection
    from coding_tutor.ui.solution_view import _get_stored_solutions

    conn = get_test_db()
    qid = str(conn.execute(
        """INSERT INTO questions (title, question_type, difficulty, problem_statement, supported_methods)
           VALUES ('Q', 'algorithm', 'Easy', 'Solve.', '[\"python\"]') RETURNING id"""
    ).fetchone()[0])
    for code in ("# first", "# second"):
        conn.execute("INSERT INTO reference_solutions (question_id, method, code) VALUES (?, 'python', ?)", [qid, code])
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    assert len(_get_stored_solutions(qid)["python"]) == 2
