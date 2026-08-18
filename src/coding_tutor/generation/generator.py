"""AI question generation — calls provider, validates, persists."""
from __future__ import annotations
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_question(
    provider_name: str,
    model,  # ModelOption
    question_type: str,
    difficulty: str,
    method: str,
    topic: str = "general",
) -> Optional[str]:
    """
    Generate a question via AI, validate it, save to DB, and return question ID.
    Returns None if generation or validation fails.
    """
    from coding_tutor.providers.registry import get_provider
    from coding_tutor.providers.base import ChatMessage
    from coding_tutor.generation.prompts import (
        ALGORITHM_SYSTEM_PROMPT, ALGORITHM_USER_PROMPT,
        DATA_ANALYSIS_SYSTEM_PROMPT, DATA_ANALYSIS_USER_PROMPT,
        PROMPT_VERSION,
    )
    from coding_tutor.generation.validator import (
        validate_algorithm_question, validate_data_analysis_question, ValidationError
    )

    if not model.verified:
        logger.error("Cannot generate with unverified model: %s", model.model_id)
        return None

    provider = get_provider(provider_name)
    if not provider.is_configured():
        logger.error("Provider %s is not configured", provider_name)
        return None

    if question_type == "algorithm":
        system_prompt = ALGORITHM_SYSTEM_PROMPT
        user_content = ALGORITHM_USER_PROMPT.format(difficulty=difficulty, topic=topic)
    else:
        system_prompt = DATA_ANALYSIS_SYSTEM_PROMPT
        user_content = DATA_ANALYSIS_USER_PROMPT.format(difficulty=difficulty, topic=topic)

    try:
        response = provider.chat(
            messages=[ChatMessage(role="user", content=user_content)],
            model=model,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        logger.error("Provider chat error: %s", exc)
        return None

    raw = response.content.strip()

    # Extract JSON from response (model may wrap in markdown)
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from model response: %s", exc)
        return None

    try:
        if question_type == "algorithm":
            validate_algorithm_question(data)
        else:
            validate_data_analysis_question(data)
    except ValidationError as exc:
        logger.error("Generated question failed validation: %s", exc)
        return None

    return _save_generated_question(
        data, question_type, model, provider_name, PROMPT_VERSION
    )


def _save_generated_question(
    data: dict,
    question_type: str,
    model,
    provider_name: str,
    prompt_version: str,
) -> Optional[str]:
    import json
    from coding_tutor.database.connection import get_db

    conn = get_db()
    try:
        difficulty = data.get("difficulty", "Medium")
        valid_diffs = {"Beginner", "Easy", "Medium", "Hard", "Very Hard"}
        if difficulty not in valid_diffs:
            difficulty = "Medium"

        supported_methods = (
            ["python"] if question_type == "algorithm"
            else data.get("supported_methods", ["sql", "pandas", "pyspark", "polars"])
        )

        q_row = conn.execute(
            """INSERT INTO questions
                   (title, question_type, difficulty, problem_statement, constraints,
                    examples, supported_methods, tags, is_ai_generated, is_complete)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, true, true) RETURNING id""",
            [
                data["title"],
                question_type,
                difficulty,
                data["problem_statement"],
                data.get("constraints"),
                json.dumps(data.get("examples", [])),
                json.dumps(supported_methods),
                json.dumps(data.get("tags", [])),
            ],
        ).fetchone()
        q_id = str(q_row[0])

        if question_type == "algorithm":
            _save_algorithm_assets(conn, q_id, data)
        else:
            _save_data_analysis_assets(conn, q_id, data)

        conn.execute(
            """INSERT INTO ai_generated_questions
                   (question_id, provider, model_id, prompt_version, generation_metadata)
               VALUES (?, ?, ?, ?, ?)""",
            [
                q_id, provider_name, model.model_id, prompt_version,
                json.dumps({"question_type": question_type}),
            ],
        )
        conn.commit()
        return q_id

    except Exception as exc:
        logger.error("Failed to save generated question: %s", exc)
        conn.rollback()
        return None


def _save_algorithm_assets(conn, q_id: str, data: dict):
    import json
    starter = data.get("starter_code_python", "")
    if starter:
        conn.execute(
            "INSERT INTO question_assets (question_id, asset_type, method, content) VALUES (?, 'starter_code', 'python', ?)",
            [q_id, starter],
        )

    ref_sol = data.get("reference_solution_python", "")
    if ref_sol:
        conn.execute(
            """INSERT INTO reference_solutions (question_id, method, code, language, is_from_dataset)
               VALUES (?, 'python', ?, 'python', false)""",
            [q_id, ref_sol],
        )

    for tc in data.get("test_cases", []):
        conn.execute(
            "INSERT INTO question_test_cases (question_id, input_data, expected_output) VALUES (?, ?, ?)",
            [q_id, json.dumps(tc.get("input")), json.dumps(tc.get("expected_output"))],
        )


def _save_data_analysis_assets(conn, q_id: str, data: dict):
    import json
    if data.get("schema_sql"):
        conn.execute(
            "INSERT INTO question_assets (question_id, asset_type, content, content_type) VALUES (?, 'schema', ?, 'sql')",
            [q_id, data["schema_sql"]],
        )

    if data.get("fixture_data"):
        conn.execute(
            "INSERT INTO question_assets (question_id, asset_type, content, content_type) VALUES (?, 'fixture_data', ?, 'json')",
            [q_id, json.dumps(data["fixture_data"])],
        )

    if data.get("expected_result"):
        conn.execute(
            "INSERT INTO question_assets (question_id, asset_type, content, content_type) VALUES (?, 'expected_result', ?, 'json')",
            [q_id, json.dumps(data["expected_result"])],
        )

    starter_codes = data.get("starter_code", {})
    for method, code in starter_codes.items():
        conn.execute(
            "INSERT INTO question_assets (question_id, asset_type, method, content) VALUES (?, 'starter_code', ?, ?)",
            [q_id, method, code],
        )

    ref_solutions = data.get("reference_solutions", {})
    for method, code in ref_solutions.items():
        lang = "sql" if method == "sql" else "python"
        conn.execute(
            """INSERT INTO reference_solutions (question_id, method, code, language, is_from_dataset)
               VALUES (?, ?, ?, ?, false)""",
            [q_id, method, code, lang],
        )
