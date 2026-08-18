"""Progress queries — all learner history from DuckDB."""
from __future__ import annotations
from typing import Optional
import duckdb


def get_all_attempts(
    conn: duckdb.DuckDBPyConnection,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    method: Optional[str] = None,
) -> list[dict]:
    """Return all attempts, optionally filtered."""
    filters = ["1=1"]
    params = []

    if question_type:
        filters.append("q.question_type = ?")
        params.append(question_type)
    if difficulty:
        filters.append("q.difficulty = ?")
        params.append(difficulty)
    if method:
        filters.append("a.method = ?")
        params.append(method)

    where = " AND ".join(filters)
    rows = conn.execute(
        f"""SELECT a.id, a.question_id, q.title, q.question_type, q.difficulty,
                   a.method, a.attempted_at, a.test_result, a.tests_passed, a.tests_total,
                   a.percentage_correct, a.marks, a.solution_viewed, a.provider, a.model_id
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE {where}
            ORDER BY a.attempted_at DESC""",
        params,
    ).fetchall()

    cols = [
        "id", "question_id", "title", "question_type", "difficulty",
        "method", "attempted_at", "test_result", "tests_passed", "tests_total",
        "percentage_correct", "marks", "solution_viewed", "provider", "model_id",
    ]
    return [dict(zip(cols, r)) for r in rows]


def get_progress_summary(conn: duckdb.DuckDBPyConnection) -> dict:
    """High-level summary statistics."""
    total_attempts = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    solved_questions = conn.execute(
        "SELECT COUNT(DISTINCT question_id) FROM attempts WHERE test_result = 'passed'"
    ).fetchone()[0]
    total_questions = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    recent = conn.execute(
        """SELECT q.title, a.test_result, a.percentage_correct, a.attempted_at
           FROM attempts a JOIN questions q ON a.question_id = q.id
           ORDER BY a.attempted_at DESC LIMIT 5"""
    ).fetchall()

    by_difficulty = conn.execute(
        """SELECT q.difficulty, COUNT(*) as attempts,
                  AVG(a.percentage_correct) as avg_pct
           FROM attempts a JOIN questions q ON a.question_id = q.id
           GROUP BY q.difficulty ORDER BY q.difficulty"""
    ).fetchall()

    return {
        "total_attempts": total_attempts,
        "solved_questions": solved_questions,
        "total_questions": total_questions,
        "recent_attempts": [
            {"title": r[0], "result": r[1], "pct": r[2], "at": str(r[3])}
            for r in recent
        ],
        "by_difficulty": [
            {"difficulty": r[0], "attempts": r[1], "avg_pct": r[2]}
            for r in by_difficulty
        ],
    }


def get_question_attempts(conn: duckdb.DuckDBPyConnection, question_id: str) -> list[dict]:
    """All attempts for a single question, newest first."""
    rows = conn.execute(
        """SELECT id, method, attempted_at, test_result, tests_passed, tests_total,
                  percentage_correct, marks, solution_viewed
           FROM attempts WHERE question_id = ?
           ORDER BY attempted_at DESC""",
        [question_id],
    ).fetchall()
    cols = [
        "id", "method", "attempted_at", "test_result", "tests_passed", "tests_total",
        "percentage_correct", "marks", "solution_viewed",
    ]
    return [dict(zip(cols, r)) for r in rows]
