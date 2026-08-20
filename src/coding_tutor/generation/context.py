"""Bounded DuckDB retrieval for AI question-generation reference context."""
from __future__ import annotations

import json

import duckdb


MAX_REFERENCES = 3
MAX_CONTEXT_CHARS = 6_000


def _clip(value: object, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def load_generation_context(
    conn: duckdb.DuckDBPyConnection,
    question_type: str,
    difficulty: str,
    topic: str,
    limit: int = MAX_REFERENCES,
) -> list[dict]:
    """Return relevant imported questions, including incomplete reference-only rows."""
    rows = conn.execute(
        """SELECT CAST(q.id AS VARCHAR), s.dataset_name, q.title, q.difficulty,
                  q.problem_statement, CAST(q.tags AS VARCHAR), q.is_complete,
                  (SELECT content FROM question_assets a
                   WHERE a.question_id = q.id AND a.asset_type = 'schema'
                   LIMIT 1) AS schema_sql,
                  (SELECT code FROM reference_solutions r
                   WHERE r.question_id = q.id AND r.method = 'sql'
                   LIMIT 1) AS reference_solution
           FROM questions q
           JOIN question_sources s ON s.id = q.source_id
           WHERE q.question_type = ? AND q.is_ai_generated = false
           ORDER BY
               (CASE WHEN q.difficulty = ? THEN 2 ELSE 0 END
                + CASE WHEN ? = 'general' THEN 0
                       WHEN lower(q.title || ' ' || q.problem_statement || ' ' ||
                                  CAST(q.tags AS VARCHAR)) LIKE '%' || lower(?) || '%'
                       THEN 4 ELSE 0 END) DESC,
               q.title, q.id
           LIMIT ?""",
        [question_type, difficulty, topic, topic, limit],
    ).fetchall()

    context = []
    for row in rows:
        try:
            tags = json.loads(row[5]) if row[5] else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        context.append({
            "question_id": row[0],
            "dataset_name": row[1],
            "title": _clip(row[2], 120),
            "difficulty": row[3],
            "problem_statement": _clip(row[4], 600),
            "tags": [_clip(tag, 40) for tag in tags[:8]],
            "is_complete": bool(row[6]),
            "schema_sql": _clip(row[7], 400),
            "reference_solution": _clip(row[8], 300),
        })
    return context


def prompt_reference_context(references: list[dict]) -> str:
    """Serialize only catalog-level reference content within a fixed prompt budget."""
    selected: list[dict] = []
    for reference in references[:MAX_REFERENCES]:
        public = {
            key: value for key, value in reference.items()
            if key not in {"question_id", "dataset_name", "is_complete"} and value
        }
        candidate = [*selected, public]
        if len(json.dumps(candidate, ensure_ascii=False)) > MAX_CONTEXT_CHARS:
            break
        selected = candidate
    return json.dumps(selected, ensure_ascii=False)
