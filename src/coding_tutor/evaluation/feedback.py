"""AI teacher feedback for code submissions."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Optional
from coding_tutor.evaluation.runner import RunResult

logger = logging.getLogger(__name__)


@dataclass
class TeacherFeedback:
    percentage_correct: float  # from deterministic test result (authoritative)
    marks: float               # e.g. tests_passed / tests_total * 10
    identified_mistakes: list[str]
    explanation: str
    recommended_correction: str
    corrected_code: Optional[str] = None  # if AI provides corrected code
    model_id: Optional[str] = None
    provider: Optional[str] = None


def get_teacher_feedback(
    question: dict,
    submitted_code: str,
    method: str,
    run_result: RunResult,
    provider_name: str,
    model,
) -> Optional[TeacherFeedback]:
    """Call AI provider for teacher-style feedback on a submission."""
    if not model or not model.verified:
        return None

    from coding_tutor.providers.registry import get_provider
    from coding_tutor.providers.base import ChatMessage

    provider = get_provider(provider_name)
    if not provider.is_configured():
        return None

    system_prompt = (
        "You are a patient, expert coding teacher. Analyze the learner's solution and give constructive, "
        "educational feedback. Identify specific mistakes. Suggest improvements with a corrected version. "
        "Return a JSON object. Do not expose internal reasoning or chain of thought."
    )

    prompt = _build_feedback_prompt(question, submitted_code, method, run_result)

    try:
        response = provider.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model,
            system_prompt=system_prompt,
        )
        return _parse_feedback(response.content, run_result, model.model_id, provider_name)
    except Exception as exc:
        logger.error("Feedback generation failed: %s", exc)
        return None


def _build_feedback_prompt(question: dict, code: str, method: str, run_result: RunResult) -> str:
    test_summary = (
        f"Test results: {run_result.tests_passed}/{run_result.tests_total} passed "
        f"({run_result.percentage_correct:.1f}%). Status: {run_result.status}."
    )
    if run_result.error_details:
        test_summary += f"\nError: {run_result.error_details[:500]}"

    return f"""Problem: {question['title']}

Problem statement: {question.get('problem_statement', '')[:600]}

Learner's {method.upper()} code:
```
{code[:2000]}
```

{test_summary}

Return a JSON object with these exact keys:
{{
  "identified_mistakes": ["list of specific mistakes"],
  "explanation": "clear teaching explanation of what went wrong and why",
  "recommended_correction": "specific advice on how to fix it",
  "corrected_code": "corrected code if a fix is straightforward, else null"
}}"""


def _parse_feedback(
    content: str,
    run_result: RunResult,
    model_id: str,
    provider_name: str,
) -> TeacherFeedback:
    raw = content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "identified_mistakes": [],
            "explanation": content[:1000],
            "recommended_correction": "",
            "corrected_code": None,
        }

    marks = round((run_result.percentage_correct / 100) * 10, 1)

    return TeacherFeedback(
        percentage_correct=run_result.percentage_correct,
        marks=marks,
        identified_mistakes=data.get("identified_mistakes", []),
        explanation=data.get("explanation", ""),
        recommended_correction=data.get("recommended_correction", ""),
        corrected_code=data.get("corrected_code"),
        model_id=model_id,
        provider=provider_name,
    )
