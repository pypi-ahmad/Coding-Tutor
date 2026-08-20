"""Persist the immutable learner attempt and its later AI assessment."""
from __future__ import annotations
import json
import uuid
from coding_tutor.database.connection import get_db
from coding_tutor.methods import ALL_METHODS


def create_attempt(
    question_id: str,
    method: str,
    submitted_code: str,
    provider: str | None = None,
    model_id: str | None = None,
) -> str:
    """Insert one immutable submission; repeated attempts always receive a new ID."""
    conn = get_db()
    row = conn.execute(
        """INSERT INTO attempts
               (question_id, method, submitted_code, deterministic_test_result,
                assessment_status, provider, model_id)
           VALUES (?, ?, ?, 'not_run', 'pending', ?, ?) RETURNING id""",
        [question_id, method, submitted_code, provider, model_id],
    ).fetchone()
    conn.commit()
    return str(row[0])


def complete_attempt(attempt_id: str, assessment) -> None:
    payload = json.dumps({"identified_mistakes": assessment.identified_mistakes, "explanation": assessment.explanation, "suggested_correction": assessment.suggested_correction, "corrected_code": assessment.corrected_code})
    conn = get_db()
    conn.execute("UPDATE attempts SET assessment_status='completed', percentage_correct=?, marks=?, ai_feedback=?, error_details=NULL WHERE id=?", [assessment.estimated_percentage_correct, assessment.marks, payload, attempt_id])
    conn.commit()


def fail_attempt(attempt_id: str, error: str) -> None:
    conn = get_db()
    conn.execute("UPDATE attempts SET assessment_status='error', error_details=? WHERE id=?", [error[:2000], attempt_id])
    conn.commit()


def mark_solution_viewed(attempt_id: str) -> None:
    conn = get_db()
    conn.execute("UPDATE attempts SET solution_viewed=true WHERE id=?", [attempt_id])
    conn.commit()


def record_solution_method(
    question_id: str, attempt_id: str | None, method: str, view_id: str | None = None
) -> str:
    """Record one panel opening and append each actually displayed method once."""
    if method not in ALL_METHODS:
        raise ValueError("Unsupported solution method")
    conn = get_db()
    linked_attempt = None
    if attempt_id:
        row = conn.execute("SELECT question_id FROM attempts WHERE id=?", [attempt_id]).fetchone()
        if row and str(row[0]) == str(question_id):
            linked_attempt = attempt_id

    existing = None
    if view_id:
        existing = conn.execute(
            "SELECT methods_viewed FROM solution_views WHERE id=? AND question_id=?",
            [view_id, question_id],
        ).fetchone()
    if existing:
        try:
            methods = json.loads(existing[0]) if isinstance(existing[0], str) else existing[0]
        except (TypeError, json.JSONDecodeError):
            methods = []
        methods = methods if isinstance(methods, list) else []
        if method not in methods:
            methods.append(method)
            conn.execute("UPDATE solution_views SET methods_viewed=? WHERE id=?", [json.dumps(methods), view_id])
        result = str(view_id)
    else:
        result = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO solution_views (id, question_id, attempt_id, methods_viewed) VALUES (?, ?, ?, ?)",
            [result, question_id, linked_attempt, json.dumps([method])],
        )
    if linked_attempt:
        conn.execute("UPDATE attempts SET solution_viewed=true WHERE id=?", [linked_attempt])
    conn.commit()
    return result
