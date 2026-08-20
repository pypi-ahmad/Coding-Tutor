"""Load and render version-controlled Markdown prompts."""
from __future__ import annotations

import re
from importlib.resources import files


PROMPT_NAMES = frozenset(
    {
        "algorithm_question_generator.md",
        "adaptive_interview_question_generator.md",
        "ai_answer_evaluator.md",
        "ai_question_generator.md",
        "data_analysis_question_generator.md",
        "dataset_record_converter.md",
        "final_interview_report.md",
        "interview_plan_generator.md",
        "quiz_generator.md",
        "shared_rules.md",
        "solution_teacher.md",
        "static_code_reviewer.md",
    }
)
_PLACEHOLDER = re.compile(r"{{([a-z][a-z0-9_]*)}}")


def load_prompt(name: str) -> str:
    """Read one known prompt without allowing arbitrary file access."""
    if name not in PROMPT_NAMES:
        raise ValueError(f"Unknown prompt: {name}")
    return files(__package__).joinpath(name).read_text(encoding="utf-8")


def render_prompt(name: str, **values: str) -> str:
    """Render one prompt and reject missing, extra, or non-text values."""
    template = load_prompt(name)
    expected = frozenset(_PLACEHOLDER.findall(template))
    provided = frozenset(values)
    if expected != provided or not all(isinstance(value, str) for value in values.values()):
        raise ValueError(
            f"Prompt values for {name} must be exactly: {sorted(expected)}"
        )
    return _PLACEHOLDER.sub(lambda match: values[match.group(1)], template)
