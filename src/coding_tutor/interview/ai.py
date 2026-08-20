"""Validated AI contracts shared by question practice and interviews."""
from __future__ import annotations

import json
from typing import Any

from coding_tutor.interview.prompts import (
    SYSTEM_PROMPT,
    adaptive_question_prompt,
    answer_evaluation_prompt,
    interview_plan_prompt,
    interview_report_prompt,
    question_prompt,
)
from coding_tutor.providers.base import ChatMessage
from coding_tutor.providers.registry import get_provider

PROMPT_VERSION = "interview-v1"
DIFFICULTIES = {"Beginner", "Easy", "Medium", "Hard", "Very Hard"}
FORMATS = {"theory", "coding", "mcq"}
STYLES = {"direct", "scenario"}


class InterviewAIError(ValueError):
    pass


def _provider(provider_name: str, model):
    if not provider_name or model is None or not getattr(model, "verified", False):
        raise InterviewAIError("Select a configured, verified AI model.")
    if model.provider != provider_name:
        raise InterviewAIError("The selected model does not belong to the provider.")
    provider = get_provider(provider_name)
    if not provider.is_configured():
        raise InterviewAIError("The selected provider credential is not configured.")
    return provider


def _parse_object(content: str) -> dict[str, Any]:
    raw = content.strip()
    if raw.startswith("```json") and raw.endswith("```"):
        raw = raw[7:-3].strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InterviewAIError("The model returned malformed JSON.") from exc
    if not isinstance(value, dict):
        raise InterviewAIError("The model returned an invalid response object.")
    return value


def _chat(provider_name: str, model, prompt: str) -> dict[str, Any]:
    provider = _provider(provider_name, model)
    response = provider.chat(
        [ChatMessage(role="user", content=prompt)],
        model,
        system_prompt=SYSTEM_PROMPT,
    )
    return _parse_object(response.content)


def generate_question(
    provider_name: str,
    model,
    *,
    domain: str,
    topic: str,
    difficulty: str,
    answer_format: str,
    prompt_style: str,
    method: str | None,
    references: list[dict],
    adaptive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    values = {
        "domain": domain, "topic": topic, "difficulty": difficulty,
        "answer_format": answer_format, "prompt_style": prompt_style,
        "method": method, "references": references,
    }
    prompt = (
        adaptive_question_prompt(**values, adaptive_context=adaptive_context)
        if adaptive_context is not None
        else question_prompt(**values)
    )
    item = _chat(provider_name, model, prompt)
    _validate_question(item, difficulty, answer_format, prompt_style)
    return item


def _validate_question(item: dict, difficulty: str, answer_format: str, prompt_style: str) -> None:
    required = {"domain", "topic", "answer_format", "prompt_style", "difficulty", "prompt",
                "reference_answer", "rubric", "method", "options", "correct_option", "tags"}
    if set(item) != required:
        raise InterviewAIError("The generated question has an invalid schema.")
    if item["difficulty"] != difficulty or difficulty not in DIFFICULTIES:
        raise InterviewAIError("The generated difficulty does not match the request.")
    if item["answer_format"] != answer_format or answer_format not in FORMATS:
        raise InterviewAIError("The generated answer format does not match the request.")
    if item["prompt_style"] != prompt_style or prompt_style not in STYLES:
        raise InterviewAIError("The generated prompt style does not match the request.")
    for key in ("domain", "topic", "prompt", "reference_answer"):
        if not isinstance(item[key], str) or not item[key].strip():
            raise InterviewAIError(f"The generated {key} is invalid.")
    if not isinstance(item["rubric"], list) or not item["rubric"]:
        raise InterviewAIError("The generated rubric is invalid.")
    if not all(isinstance(value, str) and value.strip() for value in item["rubric"]):
        raise InterviewAIError("The generated rubric is invalid.")
    if not isinstance(item["tags"], list) or not all(
        isinstance(value, str) and value.strip() for value in item["tags"]
    ):
        raise InterviewAIError("The generated tags are invalid.")
    if answer_format == "coding" and not isinstance(item.get("method"), str):
        raise InterviewAIError("The generated coding method is invalid.")
    if answer_format == "mcq":
        options = item["options"]
        valid_options = isinstance(options, list) and all(
            isinstance(option, dict)
            and isinstance(option.get("id"), str)
            and isinstance(option.get("text"), str)
            and option["text"].strip()
            for option in options
        )
        ids = [option.get("id") for option in options] if valid_options else []
        if not valid_options or len(options) != 4 or len(set(ids)) != 4 or item["correct_option"] not in ids:
            raise InterviewAIError("The generated MCQ options are invalid.")


def assess_answer(provider_name: str, model, item: dict, answer: str) -> dict[str, Any]:
    data = _chat(provider_name, model, answer_evaluation_prompt(item, answer))
    score = data.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
        raise InterviewAIError("The model returned an invalid score.")
    if not isinstance(data.get("feedback"), str):
        raise InterviewAIError("The model returned invalid feedback.")
    data["score"] = float(score)
    return data


def draft_blueprint(provider_name: str, model, *, role: str, level: str, jd: str, resume: str) -> dict:
    prompt = interview_plan_prompt(role=role, level=level, jd=jd, resume=resume)
    data = _chat(provider_name, model, prompt)
    if not isinstance(data.get("topics"), list) or not data["topics"]:
        raise InterviewAIError("The model returned an invalid interview blueprint.")
    if not isinstance(data.get("formats"), list) or not data["formats"] or not all(
        isinstance(value, str) and value in FORMATS for value in data["formats"]
    ):
        raise InterviewAIError("The model returned invalid interview formats.")
    if not isinstance(data.get("languages"), list) or not all(
        isinstance(value, str) and value.strip() for value in data["languages"]
    ):
        raise InterviewAIError("The model returned invalid interview languages.")
    return data


def final_report(provider_name: str, model, blueprint: dict, turns: list[dict]) -> dict:
    data = _chat(provider_name, model, interview_report_prompt(blueprint, turns))
    score = data.get("overall_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
        raise InterviewAIError("The model returned an invalid report score.")
    if not isinstance(data.get("summary"), str) or not all(
        isinstance(data.get(key), list) for key in ("strengths", "gaps", "recommendations")
    ):
        raise InterviewAIError("The model returned an invalid interview report.")
    data["overall_score"] = float(score)
    return data
