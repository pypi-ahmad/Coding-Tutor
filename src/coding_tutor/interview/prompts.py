"""Render file-backed prompts for AI Questions and Interview modes."""
from __future__ import annotations

import json
from typing import Any

from coding_tutor.prompts import load_prompt, render_prompt


SYSTEM_PROMPT = load_prompt("shared_rules.md")


def _encoded(value: Any, limit: int) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)[:limit]


def question_prompt(
    *, domain: str, topic: str, difficulty: str, answer_format: str,
    prompt_style: str, method: str | None, references: list[dict],
) -> str:
    return render_prompt(
        "ai_question_generator.md",
        domain=_encoded(domain or "AI engineering", 1000),
        topic=_encoded(topic or "general", 1000),
        difficulty=_encoded(difficulty, 100),
        answer_format=_encoded(answer_format, 100),
        prompt_style=_encoded(prompt_style, 100),
        method=_encoded(method, 1000),
        reference_material=_encoded(references, 24000),
    )


def adaptive_question_prompt(
    *, domain: str, topic: str, difficulty: str, answer_format: str,
    prompt_style: str, method: str | None, references: list[dict],
    adaptive_context: dict[str, Any],
) -> str:
    return render_prompt(
        "adaptive_interview_question_generator.md",
        domain=_encoded(domain or "AI engineering", 1000),
        topic=_encoded(topic or "general", 1000),
        difficulty=_encoded(difficulty, 100),
        answer_format=_encoded(answer_format, 100),
        prompt_style=_encoded(prompt_style, 100),
        method=_encoded(method, 1000),
        adaptive_context=_encoded(adaptive_context, 12000),
        reference_material=_encoded(references, 24000),
    )


def answer_evaluation_prompt(item: dict, answer: str) -> str:
    return render_prompt(
        "ai_answer_evaluator.md",
        question_and_rubric=_encoded(item, 18000),
        candidate_answer=_encoded(answer, 12000),
    )


def interview_plan_prompt(*, role: str, level: str, jd: str, resume: str) -> str:
    return render_prompt(
        "interview_plan_generator.md",
        role=_encoded(role, 300),
        level=_encoded(level, 100),
        job_description=_encoded(jd, 30000),
        resume=_encoded(resume, 30000),
    )


def interview_report_prompt(blueprint: dict, turns: list[dict]) -> str:
    return render_prompt(
        "final_interview_report.md",
        interview_blueprint=_encoded(blueprint, 12000),
        scored_turns=_encoded(turns, 30000),
    )
