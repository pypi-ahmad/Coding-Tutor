"""AI question generation: one provider call, strict validation, atomic persistence."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)

QUESTION_METHODS = {
    "algorithm": ("python",),
    "data_analysis": ("sql", "pandas", "pyspark", "polars"),
}
VALID_DIFFICULTIES = {"Beginner", "Easy", "Medium", "Hard", "Very Hard"}
MAX_TOPIC_LENGTH = 100


class GenerationFailure(str, Enum):
    INVALID_SELECTION = "invalid_selection"
    MODEL_UNAVAILABLE = "model_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_ERROR = "provider_error"
    MALFORMED_RESPONSE = "malformed_response"
    INCOMPLETE_RESPONSE = "incomplete_response"
    STORAGE_ERROR = "storage_error"


@dataclass(frozen=True)
class GenerationResult:
    question_id: str | None = None
    failure: GenerationFailure | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.question_id is not None and self.failure is None


def _failed(failure: GenerationFailure, detail: str = "") -> GenerationResult:
    return GenerationResult(failure=failure, detail=detail)


def generate_question(
    provider_name: str,
    model,
    question_type: str,
    difficulty: str,
    method: str,
    topic: str = "general",
) -> GenerationResult:
    """Generate, validate, and atomically save one question."""
    from coding_tutor.generation.prompts import (
        ALGORITHM_SYSTEM_PROMPT,
        DATA_ANALYSIS_SYSTEM_PROMPT,
        PROMPT_VERSION,
        build_algorithm_user_prompt,
        build_data_analysis_user_prompt,
    )
    from coding_tutor.generation.validator import (
        ValidationError,
        validate_algorithm_question,
        validate_data_analysis_question,
    )
    from coding_tutor.providers.base import ChatMessage
    from coding_tutor.providers.registry import get_provider

    if question_type not in QUESTION_METHODS:
        return _failed(GenerationFailure.INVALID_SELECTION, "Unsupported question type.")
    if difficulty not in VALID_DIFFICULTIES:
        return _failed(GenerationFailure.INVALID_SELECTION, "Unsupported difficulty.")
    if method not in QUESTION_METHODS[question_type]:
        return _failed(
            GenerationFailure.INVALID_SELECTION,
            "The selected method does not match the question type.",
        )
    if not isinstance(topic, str):
        return _failed(GenerationFailure.INVALID_SELECTION, "Topic must be text.")
    topic = topic.strip() or "general"
    if len(topic) > MAX_TOPIC_LENGTH:
        return _failed(
            GenerationFailure.INVALID_SELECTION,
            f"Topic must be at most {MAX_TOPIC_LENGTH} characters.",
        )
    if model is None or not model.verified:
        return _failed(GenerationFailure.MODEL_UNAVAILABLE)
    if model.provider != provider_name:
        return _failed(
            GenerationFailure.INVALID_SELECTION,
            "The selected model does not belong to the selected provider.",
        )

    try:
        provider = get_provider(provider_name)
    except KeyError:
        return _failed(GenerationFailure.INVALID_SELECTION, "Unknown provider.")
    if not provider.is_configured():
        return _failed(GenerationFailure.PROVIDER_UNAVAILABLE)

    if question_type == "algorithm":
        system_prompt = ALGORITHM_SYSTEM_PROMPT
        user_content = build_algorithm_user_prompt(difficulty, method, topic)
    else:
        system_prompt = DATA_ANALYSIS_SYSTEM_PROMPT
        user_content = build_data_analysis_user_prompt(difficulty, method, topic)

    try:
        response = provider.chat(
            messages=[ChatMessage(role="user", content=user_content)],
            model=model,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        logger.error("Question provider request failed (%s)", type(exc).__name__)
        return _failed(GenerationFailure.PROVIDER_ERROR)

    data = _parse_response(getattr(response, "content", None))
    if data is None:
        return _failed(GenerationFailure.MALFORMED_RESPONSE)

    try:
        if question_type == "algorithm":
            validate_algorithm_question(data, expected_difficulty=difficulty)
        else:
            validate_data_analysis_question(data, expected_difficulty=difficulty)
    except ValidationError as exc:
        logger.error("Generated question failed validation")
        return _failed(GenerationFailure.INCOMPLETE_RESPONSE, str(exc))

    try:
        question_id = _save_generated_question(
            data,
            question_type,
            method,
            topic,
            model,
            provider_name,
            PROMPT_VERSION,
        )
    except Exception as exc:
        logger.error("Generated question persistence failed (%s)", type(exc).__name__)
        return _failed(GenerationFailure.STORAGE_ERROR)
    return GenerationResult(question_id=question_id)


def _parse_response(content) -> dict | None:
    if not isinstance(content, str) or not content.strip():
        return None
    raw = content.strip()
    if raw.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.DOTALL)
        if not match:
            return None
        raw = match.group(1)
    try:
        data = json.loads(raw, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _reject_json_constant(value: str):
    raise ValueError(f"Invalid JSON constant: {value}")


def _save_generated_question(
    data: dict,
    question_type: str,
    method: str,
    topic: str,
    model,
    provider_name: str,
    prompt_version: str,
) -> str:
    from coding_tutor.database.connection import get_db

    conn = get_db()
    conn.execute("BEGIN TRANSACTION")
    try:
        supported_methods = list(QUESTION_METHODS[question_type])
        q_row = conn.execute(
            """INSERT INTO questions
                   (title, question_type, difficulty, problem_statement, constraints,
                    examples, supported_methods, tags, is_ai_generated, is_complete)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, true, true) RETURNING id""",
            [
                data["title"],
                question_type,
                data["difficulty"],
                data["problem_statement"],
                data.get("constraints"),
                json.dumps(data.get("examples", [])),
                json.dumps(supported_methods),
                json.dumps(data["tags"]),
            ],
        ).fetchone()
        q_id = str(q_row[0])

        if question_type == "algorithm":
            _save_algorithm_assets(conn, q_id, data)
            prompt_template = "algorithm_question"
        else:
            _save_data_analysis_assets(conn, q_id, data)
            prompt_template = "data_analysis_question"

        conn.execute(
            """INSERT INTO ai_generated_questions
                   (question_id, provider, model_id, prompt_version, generation_metadata)
               VALUES (?, ?, ?, ?, ?)""",
            [
                q_id,
                provider_name,
                model.model_id,
                prompt_version,
                json.dumps(
                    {
                        "prompt_template": prompt_template,
                        "question_type": question_type,
                        "difficulty": data["difficulty"],
                        "method": method,
                        "topic": topic,
                    }
                ),
            ],
        )
        conn.commit()
        return q_id
    except Exception:
        conn.rollback()
        raise


def _save_algorithm_assets(conn, q_id: str, data: dict) -> None:
    conn.execute(
        """INSERT INTO question_assets (question_id, asset_type, method, content)
           VALUES (?, 'starter_code', 'python', ?)""",
        [q_id, data["starter_code_python"]],
    )

    reference = data.get("reference_solution_python")
    if reference:
        conn.execute(
            """INSERT INTO reference_solutions
                   (question_id, method, code, language, is_from_dataset)
               VALUES (?, 'python', ?, 'python', false)""",
            [q_id, reference],
        )

    for test_case in data["test_cases"]:
        conn.execute(
            """INSERT INTO question_test_cases
                   (question_id, input_data, expected_output)
               VALUES (?, ?, ?)""",
            [
                q_id,
                json.dumps(test_case["input"]),
                json.dumps(test_case["expected_output"]),
            ],
        )


def _save_data_analysis_assets(conn, q_id: str, data: dict) -> None:
    conn.execute(
        """INSERT INTO question_assets
               (question_id, asset_type, method, content, content_type)
           VALUES (?, 'schema', 'shared', ?, 'sql')""",
        [q_id, data["schema_sql"]],
    )
    conn.execute(
        """INSERT INTO question_assets
               (question_id, asset_type, method, content, content_type)
           VALUES (?, 'fixture_data', 'shared', ?, 'json')""",
        [q_id, json.dumps({data["table_name"]: data["fixture_data"]})],
    )
    conn.execute(
        """INSERT INTO question_assets
               (question_id, asset_type, method, content, content_type)
           VALUES (?, 'expected_result', 'shared', ?, 'json')""",
        [q_id, json.dumps(data["expected_result"])],
    )

    for method in QUESTION_METHODS["data_analysis"]:
        conn.execute(
            """INSERT INTO question_assets
                   (question_id, asset_type, method, content)
               VALUES (?, 'starter_code', ?, ?)""",
            [q_id, method, data["starter_code"][method]],
        )
        language = "sql" if method == "sql" else "python"
        conn.execute(
            """INSERT INTO reference_solutions
                   (question_id, method, code, language, is_from_dataset)
               VALUES (?, ?, ?, ?, false)""",
            [q_id, method, data["reference_solutions"][method], language],
        )
