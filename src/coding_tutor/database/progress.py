"""Filter-aware progress queries over immutable learner attempts."""
from __future__ import annotations

import json
from typing import Optional

import duckdb

SOLVED_THRESHOLD = 80.0


def _attempt_where(
    question_type: Optional[str], difficulty: Optional[str], method: Optional[str]
) -> tuple[str, list[str]]:
    filters = ["1=1"]
    params: list[str] = []
    if question_type:
        filters.append("q.question_type = ?")
        params.append(question_type)
    if difficulty:
        filters.append("q.difficulty = ?")
        params.append(difficulty)
    if method:
        filters.append("a.method = ?")
        params.append(method)
    return " AND ".join(filters), params


def get_all_attempts(
    conn: duckdb.DuckDBPyConnection,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    method: Optional[str] = None,
) -> list[dict]:
    """Return every matching attempt separately, newest first within each question."""
    where, params = _attempt_where(question_type, difficulty, method)
    rows = conn.execute(
        f"""SELECT a.id, a.question_id, q.title, q.question_type, q.difficulty,
                   a.method, CAST(a.attempted_at AS VARCHAR), a.assessment_status,
                   a.deterministic_test_result, a.percentage_correct, a.marks,
                   a.solution_viewed, a.provider, a.model_id, a.submitted_code,
                   a.ai_feedback, a.error_details
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE {where}
            ORDER BY q.title, a.attempted_at DESC, a.id DESC""",
        params,
    ).fetchall()
    cols = [
        "id", "question_id", "title", "question_type", "difficulty", "method",
        "attempted_at", "assessment_status", "deterministic_test_result",
        "percentage_correct", "marks", "solution_viewed", "provider", "model_id",
        "submitted_code", "ai_feedback", "error_details",
    ]
    return [dict(zip(cols, row)) for row in rows]


def get_progress_summary(
    conn: duckdb.DuckDBPyConnection,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    method: Optional[str] = None,
) -> dict:
    """Return metrics and recent attempts for the same filtered attempt set."""
    where, params = _attempt_where(question_type, difficulty, method)
    aggregate = conn.execute(
        f"""SELECT COUNT(*), COUNT(DISTINCT a.question_id),
                   COUNT(DISTINCT CASE
                       WHEN a.assessment_status = 'completed'
                        AND a.percentage_correct >= ? THEN a.question_id END),
                   COUNT(DISTINCT CASE
                       WHEN a.percentage_correct IS NOT NULL THEN a.question_id END)
            FROM attempts a JOIN questions q ON q.id = a.question_id
            WHERE {where}""",
        [SOLVED_THRESHOLD, *params],
    ).fetchone()
    recent = conn.execute(
        f"""SELECT a.id, q.title, q.difficulty, a.method, a.assessment_status,
                   a.deterministic_test_result, a.percentage_correct, a.marks,
                   CAST(a.attempted_at AS VARCHAR)
            FROM attempts a JOIN questions q ON q.id = a.question_id
            WHERE {where}
            ORDER BY a.attempted_at DESC, a.id DESC LIMIT 5""",
        params,
    ).fetchall()
    by_difficulty = conn.execute(
        f"""SELECT q.difficulty, COUNT(*), AVG(a.percentage_correct)
            FROM attempts a JOIN questions q ON q.id = a.question_id
            WHERE {where}
            GROUP BY q.difficulty ORDER BY q.difficulty""",
        params,
    ).fetchall()
    return {
        "total_attempts": aggregate[0],
        "attempted_questions": aggregate[1],
        "solved_questions": aggregate[2],
        "assessed_questions": aggregate[3],
        "solved_threshold": SOLVED_THRESHOLD,
        "recent_attempts": [
            {
                "id": str(row[0]), "title": row[1], "difficulty": row[2],
                "method": row[3], "assessment_status": row[4],
                "deterministic_test_result": row[5], "percentage_correct": row[6],
                "marks": row[7], "attempted_at": row[8],
            }
            for row in recent
        ],
        "by_difficulty": [
            {"difficulty": row[0], "attempts": row[1], "avg_pct": row[2]}
            for row in by_difficulty
        ],
    }


def get_question_attempts(conn: duckdb.DuckDBPyConnection, question_id: str) -> list[dict]:
    """Return all attempts for one question without collapsing repeated submissions."""
    rows = conn.execute(
        """SELECT id, method, CAST(attempted_at AS VARCHAR), assessment_status,
                  deterministic_test_result, percentage_correct, marks, solution_viewed,
                  provider, model_id, submitted_code, ai_feedback, error_details
           FROM attempts WHERE question_id = ?
           ORDER BY attempted_at DESC, id DESC""",
        [question_id],
    ).fetchall()
    cols = [
        "id", "method", "attempted_at", "assessment_status",
        "deterministic_test_result", "percentage_correct", "marks", "solution_viewed",
        "provider", "model_id", "submitted_code", "ai_feedback", "error_details",
    ]
    return [dict(zip(cols, row)) for row in rows]


def get_solution_view_history(
    conn: duckdb.DuckDBPyConnection,
    limit: int = 100,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    method: Optional[str] = None,
) -> list[dict]:
    """Return recent solution views using the active progress filters."""
    filters = ["1=1"]
    params: list[object] = []
    if question_type:
        filters.append("q.question_type = ?")
        params.append(question_type)
    if difficulty:
        filters.append("q.difficulty = ?")
        params.append(difficulty)
    if method:
        filters.append("json_contains(sv.methods_viewed, to_json(?))")
        params.append(method)
    params.append(limit)
    rows = conn.execute(
        f"""SELECT sv.id, sv.question_id, q.title, sv.methods_viewed,
                   CAST(sv.viewed_at AS VARCHAR), sv.attempt_id
            FROM solution_views sv JOIN questions q ON q.id=sv.question_id
            WHERE {' AND '.join(filters)}
            ORDER BY sv.viewed_at DESC LIMIT ?""",
        params,
    ).fetchall()
    result = []
    for view_id, question_id, title, raw_methods, viewed_at, attempt_id in rows:
        try:
            methods = json.loads(raw_methods) if isinstance(raw_methods, str) else raw_methods
        except (TypeError, json.JSONDecodeError):
            methods = []
        result.append({
            "id": str(view_id), "question_id": str(question_id), "title": title,
            "methods": methods if isinstance(methods, list) else [], "viewed_at": viewed_at,
            "attempt_id": str(attempt_id) if attempt_id else None,
        })
    return result


def get_quiz_progress(
    conn: duckdb.DuckDBPyConnection,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    method: Optional[str] = None,
) -> dict:
    """Return quiz-only progress; normal practice attempts are never mixed in."""
    filters = ["1=1"]
    params: list[str] = []
    for column, value in (
        ("question_type", question_type), ("difficulty", difficulty), ("method", method)
    ):
        if value:
            filters.append(f"{column}=?")
            params.append(value)
    where = " AND ".join(filters)
    aggregate = conn.execute(
        f"""SELECT COUNT(*),
                   COUNT(CASE WHEN status='completed' THEN 1 END),
                   COUNT(CASE WHEN status='completed' AND passed=true THEN 1 END)
            FROM quiz_attempts WHERE {where}""",
        params,
    ).fetchone()
    rows = conn.execute(
        f"""SELECT id, CAST(started_at AS VARCHAR), CAST(completed_at AS VARCHAR), status,
                   question_source, question_type, difficulty, method, total_items,
                   coding_items, mcq_items, percentage_correct, marks, passed
            FROM quiz_attempts WHERE {where}
            ORDER BY started_at DESC, id DESC""",
        params,
    ).fetchall()
    cols = ["id", "started_at", "completed_at", "status", "question_source",
            "question_type", "difficulty", "method", "total_items", "coding_items",
            "mcq_items", "percentage_correct", "marks", "passed"]
    attempts = []
    for row in rows:
        value = dict(zip(cols, row))
        value["id"] = str(value["id"])
        attempts.append(value)
    return {
        "total_attempts": aggregate[0], "completed_attempts": aggregate[1],
        "passed_attempts": aggregate[2], "attempts": attempts,
    }
