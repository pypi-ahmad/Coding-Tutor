"""Structured, AI-estimated assessment of learner submissions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from coding_tutor.prompts import load_prompt, render_prompt


MAX_SUBMISSION_CHARS = 12_000
MAX_MISTAKES = 20
MAX_MISTAKE_CHARS = 1_000
MAX_EXPLANATION_CHARS = 8_000
MAX_SUGGESTION_CHARS = 4_000
MAX_CORRECTED_CODE_CHARS = 12_000


class AssessmentError(ValueError):
    """The provider response was not a valid assessment."""


@dataclass(frozen=True)
class AIAssessment:
    estimated_percentage_correct: float
    marks: float
    identified_mistakes: list[str]
    explanation: str
    suggested_correction: str
    corrected_code: Optional[str]
    model_id: str
    provider: str


def _clip_context(value: object, limit: int) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n[context truncated by Coding Tutor]"


def validate_assessment_request(
    question: dict,
    submitted_code: str,
    method: str,
    provider_name: str,
    model,
):
    """Validate a submission and return its configured provider."""
    if not isinstance(submitted_code, str) or not submitted_code.strip():
        raise AssessmentError("Enter a solution before submitting.")
    if len(submitted_code) > MAX_SUBMISSION_CHARS:
        raise AssessmentError(
            f"The solution is too long. Keep it within {MAX_SUBMISSION_CHARS:,} characters."
        )
    if method not in question.get("supported_methods", []):
        raise AssessmentError("The selected method is not supported by this question.")
    if not provider_name or not model or not model.verified:
        raise AssessmentError("Select a configured, verified model before submitting.")
    if model.provider != provider_name:
        raise AssessmentError("The selected model does not belong to the selected provider.")

    from coding_tutor.providers.registry import get_provider

    try:
        provider = get_provider(provider_name)
    except KeyError as exc:
        raise AssessmentError("The selected AI provider is unavailable.") from exc
    verified = any(
        option.model_id == model.model_id and option.verified
        for option in provider.get_model_options()
    )
    if not verified:
        raise AssessmentError("The selected model is not a verified provider option.")
    if not provider.is_configured():
        raise AssessmentError(
            "The selected provider credential is not configured in the system environment."
        )
    return provider


def assess_solution(question: dict, submitted_code: str, method: str, provider_name: str, model) -> AIAssessment:
    """Ask one verified provider to estimate correctness without executing code."""
    from coding_tutor.database.connection import get_db
    from coding_tutor.providers.base import ChatMessage

    provider = validate_assessment_request(
        question, submitted_code, method, provider_name, model
    )

    conn = get_db()
    solution = conn.execute(
        "SELECT code FROM reference_solutions WHERE question_id = ? AND method = ? LIMIT 1",
        [question["id"], method],
    ).fetchone()
    assets = conn.execute(
        """SELECT asset_type, method, content FROM question_assets
           WHERE question_id = ?
             AND asset_type IN ('schema','fixture_data','expected_result')
             AND (method IS NULL OR method = 'shared' OR method = ?)
           LIMIT 10""",
        [question["id"], method],
    ).fetchall()
    cases = conn.execute(
        "SELECT input_data, expected_output FROM question_test_cases WHERE question_id = ? LIMIT 10",
        [question["id"]],
    ).fetchall()
    context = {
        "question": {
            "title": question.get("title", ""),
            "question_type": question.get("question_type", ""),
            "difficulty": question.get("difficulty", ""),
            "problem_statement": _clip_context(
                question.get("problem_statement", ""), 6_000
            ),
            "constraints": _clip_context(question.get("constraints") or "", 3_000),
            "examples": question.get("examples") or [],
            "tags": question.get("tags") or [],
        },
        "method": method,
        "submitted_code": submitted_code,
        "reference_solution": _clip_context(solution[0], 12_000) if solution else None,
        "assets": [
            {
                "type": row[0],
                "method": row[1],
                "content": _clip_context(row[2], 4_000),
            }
            for row in assets
        ],
        "reference_cases": [{"input": row[0], "expected_output": row[1]} for row in cases],
    }
    exercise_data = {
        "reference_solution": context["reference_solution"],
        "assets": context["assets"],
        "reference_cases": context["reference_cases"],
    }
    prompt = render_prompt(
        "static_code_reviewer.md",
        question=json.dumps(context["question"], ensure_ascii=False, default=str),
        selected_method=json.dumps(method, ensure_ascii=False),
        exercise_data=json.dumps(exercise_data, ensure_ascii=False, default=str),
        learner_submission=json.dumps(submitted_code, ensure_ascii=False),
    )
    response = provider.chat(
        [ChatMessage(role="user", content=prompt)], model,
        system_prompt=load_prompt("shared_rules.md"),
    )
    return _parse_assessment(response.content, model.model_id, provider_name)


def _parse_assessment(content: str, model_id: str, provider_name: str) -> AIAssessment:
    if not isinstance(content, str):
        raise AssessmentError("The model returned malformed assessment JSON.")
    raw = content.strip()
    if raw.startswith("```json") and raw.endswith("```"):
        raw = raw[7:-3].strip()
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AssessmentError("The model returned malformed assessment JSON.") from exc
    required = {"estimated_percentage_correct", "identified_mistakes", "explanation", "suggested_correction", "corrected_code"}
    if not isinstance(data, dict) or set(data) != required:
        raise AssessmentError("The model returned an invalid assessment schema.")
    mistakes = data["identified_mistakes"]
    if (
        not isinstance(mistakes, list)
        or len(mistakes) > MAX_MISTAKES
        or not all(
            isinstance(item, str)
            and bool(item.strip())
            and len(item) <= MAX_MISTAKE_CHARS
            for item in mistakes
        )
    ):
        raise AssessmentError("The model returned invalid assessment mistakes.")
    explanation = data["explanation"]
    suggestion = data["suggested_correction"]
    corrected_code = data["corrected_code"]
    if (
        not isinstance(explanation, str)
        or not explanation.strip()
        or len(explanation) > MAX_EXPLANATION_CHARS
        or not isinstance(suggestion, str)
        or len(suggestion) > MAX_SUGGESTION_CHARS
        or not (corrected_code is None or isinstance(corrected_code, str))
        or (isinstance(corrected_code, str) and len(corrected_code) > MAX_CORRECTED_CODE_CHARS)
    ):
        raise AssessmentError("The model returned invalid assessment field types.")
    percentage = data["estimated_percentage_correct"]
    if isinstance(percentage, bool) or not isinstance(percentage, (int, float)) or not 0 <= percentage <= 100:
        raise AssessmentError("The model returned an invalid correctness estimate.")
    return AIAssessment(
        float(percentage),
        round(float(percentage) / 10, 1),
        mistakes,
        explanation,
        suggestion,
        corrected_code,
        model_id,
        provider_name,
    )
