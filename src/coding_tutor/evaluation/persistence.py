"""Save and retrieve attempt records."""
from __future__ import annotations
import json
import logging
from typing import Optional
from coding_tutor.evaluation.runner import RunResult
from coding_tutor.evaluation.feedback import TeacherFeedback

logger = logging.getLogger(__name__)


def save_attempt(
    question_id: str,
    method: str,
    submitted_code: str,
    run_result: RunResult,
    feedback: Optional[TeacherFeedback],
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
) -> str:
    """Insert attempt record and return its ID."""
    from coding_tutor.database.connection import get_db
    conn = get_db()

    ai_feedback_text = None
    if feedback:
        ai_feedback_text = json.dumps({
            "explanation": feedback.explanation,
            "identified_mistakes": feedback.identified_mistakes,
            "recommended_correction": feedback.recommended_correction,
        })

    row = conn.execute(
        """INSERT INTO attempts
               (question_id, method, submitted_code, test_result,
                tests_passed, tests_total, percentage_correct, marks,
                ai_feedback, error_details, provider, model_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [
            question_id, method, submitted_code,
            run_result.status,
            run_result.tests_passed, run_result.tests_total,
            run_result.percentage_correct,
            feedback.marks if feedback else None,
            ai_feedback_text,
            run_result.error_details,
            provider, model_id,
        ],
    ).fetchone()
    conn.commit()
    return str(row[0])


def mark_solution_viewed(attempt_id: str) -> None:
    from coding_tutor.database.connection import get_db
    conn = get_db()
    conn.execute(
        "UPDATE attempts SET solution_viewed = true WHERE id = ?",
        [attempt_id],
    )
    conn.commit()
