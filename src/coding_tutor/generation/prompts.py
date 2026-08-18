"""Versioned, file-backed prompt builders for question generation."""
from __future__ import annotations

import json

from coding_tutor.prompts import load_prompt, render_prompt


PROMPT_VERSION = "v3"
ALGORITHM_SYSTEM_PROMPT = load_prompt("shared_rules.md")
DATA_ANALYSIS_SYSTEM_PROMPT = ALGORITHM_SYSTEM_PROMPT


def build_algorithm_user_prompt(difficulty: str, method: str, topic: str) -> str:
    return render_prompt(
        "algorithm_question_generator.md",
        difficulty=json.dumps(difficulty, ensure_ascii=False),
        topic=json.dumps(topic, ensure_ascii=False),
        selected_method=json.dumps(method, ensure_ascii=False),
    )


def build_data_analysis_user_prompt(difficulty: str, method: str, topic: str) -> str:
    return render_prompt(
        "data_analysis_question_generator.md",
        difficulty=json.dumps(difficulty, ensure_ascii=False),
        topic=json.dumps(topic, ensure_ascii=False),
        selected_method=json.dumps(method, ensure_ascii=False),
    )
