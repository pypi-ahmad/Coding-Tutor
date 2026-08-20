"""Business rules and persistence for AI Questions and Interview modes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import duckdb

from coding_tutor.catalog import interview_database
from coding_tutor.database.connection import get_db
from coding_tutor.interview.ai import (
    PROMPT_VERSION,
    InterviewAIError,
    assess_answer,
    final_report,
    generate_question,
)
from coding_tutor.web_research import WebResearchError, research_web


def connection() -> duckdb.DuckDBPyConnection:
    return get_db(interview_database())


def _json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def catalog_facets(conn: duckdb.DuckDBPyConnection | None = None) -> dict[str, list[str]]:
    conn = conn or connection()
    return {
        "domains": [row[0] for row in conn.execute(
            "SELECT DISTINCT domain FROM interview_items WHERE is_complete ORDER BY domain"
        ).fetchall()],
        "topics": [row[0] for row in conn.execute(
            "SELECT DISTINCT topic FROM interview_items WHERE is_complete ORDER BY topic"
        ).fetchall()],
    }


def _row_item(row) -> dict:
    columns = ["id", "domain", "topic", "answer_format", "prompt_style", "difficulty",
               "prompt", "reference_answer", "rubric", "method", "options", "correct_option", "tags"]
    item = dict(zip(columns, row))
    item["id"] = str(item["id"])
    for key, default in (("rubric", []), ("options", []), ("tags", [])):
        item[key] = _json(item[key], default)
    return item


def get_item(item_id: str, conn: duckdb.DuckDBPyConnection | None = None) -> dict | None:
    conn = conn or connection()
    row = conn.execute(
        """SELECT id, domain, topic, answer_format, prompt_style, difficulty, prompt,
                  reference_answer, rubric, method, options, correct_option, tags
           FROM interview_items WHERE id=?""", [item_id]
    ).fetchone()
    return _row_item(row) if row else None


def _local_item(filters: dict, used_ids: list[str], conn: duckdb.DuckDBPyConnection) -> dict | None:
    clauses = ["is_complete=true", "answer_format=?", "prompt_style=?", "difficulty=?"]
    params: list[Any] = [filters["answer_format"], filters["prompt_style"], filters["difficulty"]]
    if filters.get("domain"):
        clauses.append("domain=?")
        params.append(filters["domain"])
    if filters.get("topic"):
        clauses.append("topic=?")
        params.append(filters["topic"])
    if used_ids:
        placeholders = ",".join("?" for _ in used_ids)
        clauses.append(f"CAST(id AS VARCHAR) NOT IN ({placeholders})")
        params.extend(used_ids)
    row = conn.execute(
        f"""SELECT id, domain, topic, answer_format, prompt_style, difficulty, prompt,
                   reference_answer, rubric, method, options, correct_option, tags
            FROM interview_items WHERE {' AND '.join(clauses)} ORDER BY random() LIMIT 1""",
        params,
    ).fetchone()
    return _row_item(row) if row else None


def _references(filters: dict, conn: duckdb.DuckDBPyConnection) -> list[dict]:
    clauses = ["is_complete=true", "difficulty=?", "answer_format=?"]
    params: list[Any] = [filters["difficulty"], filters["answer_format"]]
    if filters.get("domain"):
        clauses.append("domain=?")
        params.append(filters["domain"])
    if filters.get("topic"):
        clauses.append("topic=?")
        params.append(filters["topic"])
    rows = conn.execute(
        f"""SELECT prompt, reference_answer, domain, topic FROM interview_items
            WHERE {' AND '.join(clauses)} LIMIT 3""",
        params,
    ).fetchall()
    return [
        {"prompt": row[0], "reference_answer": row[1], "domain": row[2], "topic": row[3]}
        for row in rows
    ]


def _persist_generated(
    item: dict,
    *,
    origin: str,
    provider_name: str,
    model_id: str,
    web_sources: list[dict],
    conn: duckdb.DuckDBPyConnection,
) -> dict:
    normalized = " ".join(item["prompt"].split()).casefold()
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    source_key = f"runtime:{content_hash}"
    conn.execute("BEGIN")
    try:
        source = conn.execute(
            """INSERT INTO question_sources
               (dataset_name, original_id, source_key, source_file, license, attribution)
               VALUES ('runtime-generated-interview', ?, ?, ?, NULL, ?)
               ON CONFLICT (dataset_name, source_key) DO NOTHING RETURNING id""",
            [content_hash, source_key, web_sources[0]["url"] if web_sources else "AI generated",
             "AI-generated interview question; web citations stored separately."],
        ).fetchone()
        if source:
            source_id = source[0]
        else:
            source_id = conn.execute(
                "SELECT id FROM question_sources WHERE dataset_name='runtime-generated-interview' AND source_key=?",
                [source_key],
            ).fetchone()[0]
        inserted = conn.execute(
            """INSERT INTO interview_items
               (source_id, domain, topic, answer_format, prompt_style, difficulty, prompt,
                reference_answer, rubric, method, options, correct_option, tags, content_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (content_hash) DO NOTHING RETURNING id""",
            [source_id, item["domain"], item["topic"], item["answer_format"], item["prompt_style"],
             item["difficulty"], item["prompt"], item["reference_answer"], json.dumps(item["rubric"]),
             item.get("method"), json.dumps(item.get("options") or []), item.get("correct_option"),
             json.dumps(item.get("tags") or []), content_hash],
        ).fetchone()
        item_id = inserted[0] if inserted else conn.execute(
            "SELECT id FROM interview_items WHERE content_hash=?", [content_hash]
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO interview_item_generation
               (interview_item_id, origin, provider, model_id, prompt_version, web_sources)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT (interview_item_id) DO NOTHING""",
            [item_id, origin, provider_name, model_id, PROMPT_VERSION, json.dumps(web_sources)],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return get_item(str(item_id), conn)


def _generated_item(filters: dict, provider_name: str, model, web_enabled: bool, tailored: str, conn) -> tuple[dict, list[dict], str | None]:
    references = _references(filters, conn)
    web_sources: list[dict] = []
    warning = None
    if web_enabled and len(references) < 3:
        try:
            query = f"{filters.get('domain') or 'AI engineering'} {filters.get('topic') or ''} interview question official documentation"
            web_sources = [source.as_dict() for source in research_web(query)]
            references.extend({"title": s["title"], "url": s["url"], "excerpt": s["excerpt"]} for s in web_sources)
        except WebResearchError as exc:
            warning = str(exc)
    item = generate_question(
        provider_name, model, domain=filters.get("domain") or "AI Engineering",
        topic=filters.get("topic") or "General", difficulty=filters["difficulty"],
        answer_format=filters["answer_format"], prompt_style=filters["prompt_style"],
        method=filters.get("method"), references=references,
        tailored_context=(
            "Use this only to select relevant skills. The question must stand alone and must not mention "
            "a company, candidate, employer, project name, or identifying detail. " + tailored
        ) if tailored else "",
    )
    item = _persist_generated(
        item, origin="web" if web_sources else "ai", provider_name=provider_name,
        model_id=model.model_id, web_sources=web_sources, conn=conn,
    )
    return item, web_sources, warning


def create_ai_session(filters: dict, provider_name: str | None, model) -> str:
    row = connection().execute(
        """INSERT INTO ai_question_sessions
           (source_mode, domain, topic, difficulty, answer_format, prompt_style, method,
            web_enabled, provider, model_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [filters["source_mode"], filters.get("domain"), filters.get("topic"), filters["difficulty"],
         filters["answer_format"], filters["prompt_style"], filters.get("method"),
         bool(filters.get("web_enabled")), provider_name, getattr(model, "model_id", None)],
    ).fetchone()
    return str(row[0])


def next_ai_question(session_id: str, provider_name: str | None, model) -> tuple[dict, str | None]:
    conn = connection()
    session = conn.execute(
        """SELECT source_mode, domain, topic, difficulty, answer_format, prompt_style, method,
                  web_enabled FROM ai_question_sessions WHERE id=? AND status='active'""", [session_id]
    ).fetchone()
    if not session:
        raise ValueError("The AI Questions session is not active.")
    keys = ["source_mode", "domain", "topic", "difficulty", "answer_format", "prompt_style", "method", "web_enabled"]
    filters = dict(zip(keys, session))
    existing = conn.execute(
        "SELECT CAST(interview_item_id AS VARCHAR) FROM ai_question_items WHERE session_id=?", [session_id]
    ).fetchall()
    used = [row[0] for row in existing]
    position = len(used) + 1
    use_local = filters["source_mode"] == "local" or (filters["source_mode"] == "mixed" and position % 2 == 1)
    item = _local_item(filters, used, conn) if use_local else None
    warning = None
    sources: list[dict] = []
    if item is None:
        if filters["source_mode"] == "local":
            raise ValueError("No unused local question matches these filters.")
        item, sources, warning = _generated_item(filters, provider_name or "", model, bool(filters["web_enabled"]), "", conn)
    conn.execute(
        """INSERT INTO ai_question_items
           (session_id, position, interview_item_id, prompt_snapshot, options, correct_option, web_sources)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [session_id, position, item["id"], item["prompt"], json.dumps(item.get("options") or []),
         item.get("correct_option"), json.dumps(sources)],
    )
    item["position"] = position
    item["web_sources"] = sources
    return item, warning


def pending_ai_question(session_id: str) -> dict | None:
    row = connection().execute(
        """SELECT interview_item_id, position, web_sources FROM ai_question_items
           WHERE session_id=? AND status='pending' ORDER BY position DESC LIMIT 1""", [session_id]
    ).fetchone()
    if not row:
        return None
    item = get_item(str(row[0]))
    item["position"] = row[1]
    item["web_sources"] = _json(row[2], [])
    return item


def submit_ai_answer(session_id: str, item: dict, answer: str, provider_name: str | None, model) -> dict:
    if not answer.strip():
        raise ValueError("Enter an answer before submitting.")
    if item["answer_format"] == "mcq":
        score = 100.0 if answer == item["correct_option"] else 0.0
        feedback = {"score": score, "strengths": [], "gaps": [],
                    "feedback": item.get("reference_answer") or "Review the correct option.", "next_focus": item["topic"]}
        selected, text = answer, None
    else:
        feedback = assess_answer(provider_name or "", model, item, answer)
        score = feedback["score"]
        selected, text = None, answer
    connection().execute(
        """UPDATE ai_question_items SET answer_text=?, selected_option=?, score=?, feedback=?,
                  status='scored', answered_at=now()
           WHERE session_id=? AND interview_item_id=? AND status='pending'""",
        [text, selected, score, json.dumps(feedback), session_id, item["id"]],
    )
    return feedback


def start_interview(interview_type: str, duration: int, source_mode: str, blueprint: dict,
                    web_enabled: bool, provider_name: str, model) -> str:
    deadline = datetime.now(timezone.utc) + timedelta(minutes=duration)
    row = connection().execute(
        """INSERT INTO interview_sessions
           (interview_type, duration_minutes, source_mode, blueprint, web_enabled,
            provider, model_id, deadline_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [interview_type, duration, source_mode, json.dumps(blueprint), web_enabled,
         provider_name, model.model_id, deadline],
    ).fetchone()
    return str(row[0])


def load_interview(session_id: str) -> tuple[dict, list[dict]] | None:
    conn = connection()
    row = conn.execute(
        """SELECT id, interview_type, duration_minutes, source_mode, blueprint, web_enabled,
                  provider, model_id, status, CAST(started_at AS VARCHAR),
                  CAST(deadline_at AS VARCHAR), overall_score, report, error_details
           FROM interview_sessions WHERE id=?""", [session_id]
    ).fetchone()
    if not row:
        return None
    keys = ["id", "interview_type", "duration_minutes", "source_mode", "blueprint", "web_enabled",
            "provider", "model_id", "status", "started_at", "deadline_at", "overall_score", "report", "error_details"]
    session = dict(zip(keys, row))
    session["id"] = str(session["id"])
    session["blueprint"] = _json(session["blueprint"], {})
    session["report"] = _json(session["report"], None)
    rows = conn.execute(
        """SELECT position, interview_item_id, prompt_snapshot, answer_format, method, options,
                  correct_option, answer_text, selected_option, score, feedback, web_sources, status
           FROM interview_turns WHERE session_id=? ORDER BY position""", [session_id]
    ).fetchall()
    turn_keys = ["position", "interview_item_id", "prompt", "answer_format", "method", "options",
                 "correct_option", "answer_text", "selected_option", "score", "feedback", "web_sources", "status"]
    turns = []
    for value in rows:
        turn = dict(zip(turn_keys, value))
        turn["interview_item_id"] = str(turn["interview_item_id"])
        turn["options"] = _json(turn["options"], [])
        turn["feedback"] = _json(turn["feedback"], None)
        turn["web_sources"] = _json(turn["web_sources"], [])
        turns.append(turn)
    return session, turns


def add_interview_turn(session_id: str, provider_name: str, model, tailored_context: str = "") -> tuple[dict, str | None]:
    loaded = load_interview(session_id)
    if not loaded:
        raise ValueError("Interview session not found.")
    session, turns = loaded
    if session["status"] != "active" or any(turn["status"] == "pending" for turn in turns):
        raise ValueError("The interview cannot create another question yet.")
    blueprint = session["blueprint"]
    position = len(turns) + 1
    formats = blueprint.get("formats") or ["theory", "coding", "mcq"]
    topics = blueprint.get("topics") or ["AI engineering"]
    answer_format = formats[(position - 1) % len(formats)]
    topic = topics[(position - 1) % len(topics)]
    languages = blueprint.get("languages") or ["python"]
    filters = {
        "source_mode": session["source_mode"], "domain": None, "topic": topic,
        "difficulty": {"junior": "Easy", "senior": "Hard", "staff": "Very Hard"}.get(
            str(blueprint.get("level", "")).casefold(), "Medium"),
        "answer_format": answer_format, "prompt_style": "scenario",
        "method": languages[(position - 1) % len(languages)] if answer_format == "coding" else None,
        "web_enabled": session["web_enabled"],
    }
    used = [turn["interview_item_id"] for turn in turns]
    use_local = session["source_mode"] == "local" or (session["source_mode"] == "mixed" and position % 2 == 1)
    item = _local_item(filters, used, connection()) if use_local else None
    warning = None
    sources: list[dict] = []
    if item is None:
        if session["source_mode"] == "local":
            # Relax topic while preserving format, difficulty, and local-only provenance.
            filters["topic"] = None
            item = _local_item(filters, used, connection())
            if item is None:
                raise ValueError("No unused local interview question matches the plan.")
        else:
            item, sources, warning = _generated_item(
                filters, provider_name, model, bool(session["web_enabled"]), tailored_context, connection()
            )
    connection().execute(
        """INSERT INTO interview_turns
           (session_id, position, interview_item_id, prompt_snapshot, answer_format, method,
            options, correct_option, web_sources)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [session_id, position, item["id"], item["prompt"], item["answer_format"], item.get("method"),
         json.dumps(item.get("options") or []), item.get("correct_option"), json.dumps(sources)],
    )
    item["position"] = position
    item["web_sources"] = sources
    return item, warning


def submit_interview_answer(session_id: str, item: dict, answer: str,
                            provider_name: str, model) -> dict:
    if not answer.strip():
        raise ValueError("Enter an answer or choose Finish without answering.")
    if item["answer_format"] == "mcq":
        score = 100.0 if answer == item["correct_option"] else 0.0
        result = {"score": score, "strengths": [], "gaps": [],
                  "feedback": item.get("reference_answer") or "Review the correct option.", "next_focus": item["topic"]}
        selected, text = answer, None
    else:
        result = assess_answer(provider_name, model, item, answer)
        score = result["score"]
        selected, text = None, answer
    connection().execute(
        """UPDATE interview_turns SET answer_text=?, selected_option=?, score=?, feedback=?,
                  status='scored', answered_at=now()
           WHERE session_id=? AND interview_item_id=? AND status='pending'""",
        [text, selected, score, json.dumps(result), session_id, item["id"]],
    )
    return result


def skip_pending_turn(session_id: str) -> None:
    connection().execute(
        """UPDATE interview_turns SET status='skipped', score=0, answered_at=now()
           WHERE session_id=? AND status='pending'""",
        [session_id],
    )


def finish_interview(session_id: str, provider_name: str, model) -> dict:
    loaded = load_interview(session_id)
    if not loaded:
        raise ValueError("Interview session not found.")
    session, turns = loaded
    scored = [turn for turn in turns if turn["status"] == "scored"]
    report = final_report(provider_name, model, session["blueprint"], scored) if scored else {
        "overall_score": 0.0, "summary": "No answers were submitted.", "strengths": [],
        "gaps": ["No assessed answers"], "recommendations": ["Start another interview and submit answers."],
    }
    connection().execute(
        """UPDATE interview_sessions SET status='completed', completed_at=now(),
                  overall_score=?, report=? WHERE id=?""",
        [report["overall_score"], json.dumps(report), session_id],
    )
    return report
