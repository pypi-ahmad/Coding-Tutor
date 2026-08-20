"""DuckDB persistence for quiz attempts, kept separate from practice attempts."""
from __future__ import annotations

import json
from typing import Any

from coding_tutor.database.connection import get_db

UNFINISHED_STATUSES = ("preparing", "preparation_error", "in_progress", "evaluating", "evaluation_error")


def create_quiz_attempt(settings: dict[str, Any]) -> str:
    conn = get_db()
    row = conn.execute(
        """INSERT INTO quiz_attempts
                (question_source, question_type, difficulty, topic, method,
                total_items, coding_items, mcq_items, provider, model_id, web_enabled)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [settings[key] for key in (
            "question_source", "question_type", "difficulty", "topic", "method",
            "total_items", "coding_items", "mcq_items", "provider", "model_id",
        )] + [bool(settings.get("web_enabled"))],
    ).fetchone()
    conn.commit()
    return str(row[0])


def insert_quiz_items(attempt_id: str, questions: list[dict], coding_count: int, method: str) -> None:
    conn = get_db()
    conn.execute("BEGIN TRANSACTION")
    try:
        for position, question in enumerate(questions, 1):
            answer_format = "coding" if position <= coding_count else "mcq"
            conn.execute(
                """INSERT INTO quiz_items
                       (quiz_attempt_id, position, question_id, answer_format, method, prompt_snapshot)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [attempt_id, position, question["id"], answer_format, method, question["problem_statement"]],
            )
        conn.execute("UPDATE quiz_attempts SET status='preparing', error_details=NULL WHERE id=?", [attempt_id])
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def save_mcq_content(attempt_id: str, content: dict[str, dict]) -> None:
    conn = get_db()
    conn.execute("BEGIN TRANSACTION")
    try:
        for question_id, item in content.items():
            conn.execute(
                """UPDATE quiz_items
                   SET prompt_snapshot=?, options=?, correct_option_id=?, explanation=?,
                       provider=?, model_id=?, error_details=NULL
                   WHERE quiz_attempt_id=? AND question_id=? AND answer_format='mcq'""",
                [item["prompt"], json.dumps(item["options"]), item["correct_option_id"],
                 item["explanation"], item["provider"], item["model_id"], attempt_id, question_id],
            )
        conn.execute("UPDATE quiz_attempts SET status='in_progress', error_details=NULL WHERE id=?", [attempt_id])
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def mark_ready(attempt_id: str) -> None:
    conn = get_db()
    conn.execute("UPDATE quiz_attempts SET status='in_progress', error_details=NULL WHERE id=?", [attempt_id])
    conn.commit()


def set_quiz_error(attempt_id: str, status: str, message: str) -> None:
    if status not in {"preparation_error", "evaluation_error"}:
        raise ValueError("Invalid quiz error status")
    conn = get_db()
    conn.execute("UPDATE quiz_attempts SET status=?, error_details=? WHERE id=?", [status, message[:2000], attempt_id])
    conn.commit()


def save_draft(item_id: str, answer_format: str, value: str | None) -> None:
    conn = get_db()
    column = "answer_text" if answer_format == "coding" else "selected_option_id"
    conn.execute(f"UPDATE quiz_items SET {column}=? WHERE id=?", [value, item_id])
    conn.commit()


def load_quiz(attempt_id: str) -> tuple[dict, list[dict]] | None:
    conn = get_db()
    attempt_row = conn.execute(
        """SELECT id, CAST(started_at AS VARCHAR), CAST(completed_at AS VARCHAR), status,
                  question_source, question_type, difficulty, topic, method, total_items,
                  coding_items, mcq_items, percentage_correct, marks, passed,
                  provider, model_id, web_enabled, error_details
           FROM quiz_attempts WHERE id=?""",
        [attempt_id],
    ).fetchone()
    if not attempt_row:
        return None
    attempt_cols = ["id", "started_at", "completed_at", "status", "question_source",
                    "question_type", "difficulty", "topic", "method", "total_items",
                    "coding_items", "mcq_items", "percentage_correct", "marks", "passed",
                    "provider", "model_id", "web_enabled", "error_details"]
    attempt = dict(zip(attempt_cols, attempt_row))
    attempt["id"] = str(attempt["id"])
    rows = conn.execute(
        """SELECT qi.id, qi.position, qi.question_id, qi.answer_format, qi.method,
                  qi.prompt_snapshot, qi.options, qi.correct_option_id, qi.explanation,
                  qi.answer_text, qi.selected_option_id, qi.item_status,
                  qi.percentage_correct, qi.marks, qi.ai_feedback, qi.error_details,
                  q.title, q.problem_statement, q.constraints, q.examples
           FROM quiz_items qi JOIN questions q ON q.id=qi.question_id
           WHERE qi.quiz_attempt_id=? ORDER BY qi.position""",
        [attempt_id],
    ).fetchall()
    cols = ["id", "position", "question_id", "answer_format", "method", "prompt_snapshot",
            "options", "correct_option_id", "explanation", "answer_text", "selected_option_id",
            "item_status", "percentage_correct", "marks", "ai_feedback", "error_details",
            "title", "problem_statement", "constraints", "examples"]
    items = []
    for row in rows:
        item = dict(zip(cols, row))
        item["id"], item["question_id"] = str(item["id"]), str(item["question_id"])
        for key in ("options", "examples"):
            if isinstance(item[key], str):
                try:
                    item[key] = json.loads(item[key])
                except json.JSONDecodeError:
                    item[key] = []
        items.append(item)
    return attempt, items


def latest_unfinished_quiz() -> str | None:
    conn = get_db()
    placeholders = ",".join("?" for _ in UNFINISHED_STATUSES)
    row = conn.execute(
        f"SELECT id FROM quiz_attempts WHERE status IN ({placeholders}) ORDER BY started_at DESC LIMIT 1",
        list(UNFINISHED_STATUSES),
    ).fetchone()
    return str(row[0]) if row else None


def score_item(
    item_id: str,
    percentage: float,
    feedback: dict | None = None,
    provider: str | None = None,
    model_id: str | None = None,
) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE quiz_items SET item_status='scored', percentage_correct=?, marks=?,
                  ai_feedback=?, provider=COALESCE(?, provider), model_id=COALESCE(?, model_id),
                  error_details=NULL WHERE id=?""",
        [percentage, percentage, json.dumps(feedback) if feedback is not None else None,
         provider, model_id, item_id],
    )
    conn.commit()


def fail_item(item_id: str, message: str) -> None:
    conn = get_db()
    conn.execute("UPDATE quiz_items SET item_status='error', error_details=? WHERE id=?", [message[:2000], item_id])
    conn.commit()


def begin_evaluation(attempt_id: str) -> None:
    conn = get_db()
    conn.execute("UPDATE quiz_attempts SET status='evaluating', error_details=NULL WHERE id=?", [attempt_id])
    conn.commit()


def complete_quiz(attempt_id: str, percentage: float) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE quiz_attempts SET status='completed', completed_at=now(),
                  percentage_correct=?, marks=?, passed=?, error_details=NULL WHERE id=?""",
        [percentage, percentage, percentage >= 80.0, attempt_id],
    )
    conn.commit()
