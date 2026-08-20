"""Quiz preparation and scoring rules explicitly approved for Phase 9."""
from __future__ import annotations

import json
import random

from coding_tutor.database.connection import get_db
from coding_tutor.prompts import load_prompt, render_prompt
from coding_tutor.quiz import persistence


class QuizError(ValueError):
    """A safe, user-displayable quiz workflow error."""


def _provider(provider_name, model):
    if not provider_name or not model or not model.verified or model.provider != provider_name:
        raise QuizError("Select a configured, verified model before starting a quiz.")
    from coding_tutor.providers.registry import get_provider
    try:
        provider = get_provider(provider_name)
    except KeyError as exc:
        raise QuizError("The selected AI provider is unavailable.") from exc
    if not provider.is_configured():
        raise QuizError("The selected provider is not configured in the system environment.")
    if not any(option.verified and option.model_id == model.model_id for option in provider.get_model_options()):
        raise QuizError("The selected model is not a verified provider option.")
    return provider


def start_quiz(settings: dict, model) -> str:
    """Create the durable attempt immediately, then prepare its questions and MCQs."""
    if not 1 <= settings["total_items"] <= 10:
        raise QuizError("Quiz size must be between 1 and 10 questions.")
    if not 0 <= settings["coding_items"] <= settings["total_items"]:
        raise QuizError("Coding question count must fit within the quiz size.")
    settings = dict(settings)
    settings["mcq_items"] = settings["total_items"] - settings["coding_items"]
    _provider(settings.get("provider"), model)
    attempt_id = persistence.create_quiz_attempt(settings)
    try:
        _prepare_attempt(attempt_id, settings, model)
    except QuizError as exc:
        persistence.set_quiz_error(attempt_id, "preparation_error", str(exc))
    except Exception:
        persistence.set_quiz_error(
            attempt_id, "preparation_error",
            "Quiz preparation failed. Retry after checking provider access and local data.",
        )
    return attempt_id


def retry_preparation(attempt_id: str, model) -> None:
    loaded = persistence.load_quiz(attempt_id)
    if not loaded:
        raise QuizError("Quiz attempt not found.")
    attempt, items = loaded
    settings = dict(attempt)
    settings["provider"] = attempt["provider"]
    settings["model_id"] = attempt["model_id"]
    try:
        if not items:
            _prepare_attempt(attempt_id, settings, model)
        else:
            _prepare_mcqs(attempt_id, items, attempt["provider"], model)
    except QuizError as exc:
        persistence.set_quiz_error(attempt_id, "preparation_error", str(exc))
    except Exception:
        persistence.set_quiz_error(attempt_id, "preparation_error", "Quiz preparation failed. Retry is available.")


def _prepare_attempt(attempt_id: str, settings: dict, model) -> None:
    questions = _select_questions(settings, model)
    persistence.insert_quiz_items(attempt_id, questions, settings["coding_items"], settings["method"])
    loaded = persistence.load_quiz(attempt_id)
    if settings["mcq_items"]:
        _prepare_mcqs(attempt_id, loaded[1], settings["provider"], model)
    else:
        persistence.mark_ready(attempt_id)


def _curated_candidates(settings: dict, limit: int) -> list[dict]:
    conn = get_db()
    topic = settings.get("topic") or "general"
    rows = conn.execute(
        """SELECT id, title, problem_statement, constraints, examples, tags
           FROM questions
           WHERE question_type=? AND difficulty=? AND is_complete=true
             AND is_ai_generated=false
             AND json_contains(supported_methods, to_json(?))
             AND (?='general' OR json_contains(tags, to_json(?)))
           ORDER BY random() LIMIT ?""",
        [settings["question_type"], settings["difficulty"], settings["method"], topic, topic, limit],
    ).fetchall()
    return [_row_to_question(row) for row in rows]


def _row_to_question(row) -> dict:
    examples = row[4]
    tags = row[5]
    for value_name, value in (("examples", examples), ("tags", tags)):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = []
            if value_name == "examples": examples = parsed
            else: tags = parsed
    return {"id": str(row[0]), "title": row[1], "problem_statement": row[2],
            "constraints": row[3], "examples": examples or [], "tags": tags or []}


def _load_question(question_id: str) -> dict:
    row = get_db().execute(
        "SELECT id,title,problem_statement,constraints,examples,tags FROM questions WHERE id=?",
        [question_id],
    ).fetchone()
    if not row:
        raise QuizError("A generated quiz question could not be loaded.")
    return _row_to_question(row)


def _generate_question(settings: dict, model) -> dict:
    from coding_tutor.generation.generator import generate_question
    result = generate_question(
        settings["provider"], model, settings["question_type"], settings["difficulty"],
        settings["method"], settings.get("topic") or "general",
        web_enabled=bool(settings.get("web_enabled")),
    )
    if not result.ok:
        raise QuizError("The provider could not generate a valid quiz question.")
    return _load_question(result.question_id)


def _select_questions(settings: dict, model) -> list[dict]:
    total = settings["total_items"]
    source = settings["question_source"]
    if source == "dataset":
        questions = _curated_candidates(settings, total)
        if len(questions) < total:
            raise QuizError(f"Only {len(questions)} matching curated questions are available; {total} are required.")
        return questions
    if source == "ai_generated":
        return [_generate_question(settings, model) for _ in range(total)]
    if source != "mixed":
        raise QuizError("Unsupported quiz question source.")

    curated = _curated_candidates(settings, total)
    questions = []
    for _ in range(total):
        use_ai = not curated or random.random() < 0.5
        questions.append(_generate_question(settings, model) if use_ai else curated.pop())
    return questions


def _prepare_mcqs(attempt_id: str, items: list[dict], provider_name: str, model) -> None:
    mcq_items = [item for item in items if item["answer_format"] == "mcq"]
    if not mcq_items:
        persistence.mark_ready(attempt_id)
        return
    provider = _provider(provider_name, model)
    contexts = [{
        "question_id": item["question_id"], "title": item["title"],
        "problem_statement": item["problem_statement"][:8000],
        "constraints": (item.get("constraints") or "")[:3000],
        "examples": (item.get("examples") or [])[:5], "method": item["method"],
    } for item in mcq_items]
    prompt = render_prompt(
        "quiz_generator.md",
        question_contexts=json.dumps(contexts, ensure_ascii=False),
    )
    from coding_tutor.providers.base import ChatMessage
    try:
        response = provider.chat(
            [ChatMessage(role="user", content=prompt)], model,
            system_prompt=load_prompt("shared_rules.md"),
        )
    except Exception as exc:
        raise QuizError("The provider could not generate quiz choices. Retry is available.") from exc
    content = _validate_mcq_response(response.content, {item["question_id"] for item in mcq_items})
    for value in content.values():
        value["provider"], value["model_id"] = provider_name, model.model_id
    persistence.save_mcq_content(attempt_id, content)


def _validate_mcq_response(raw: str, expected_ids: set[str]) -> dict[str, dict]:
    try:
        data = json.loads(raw.strip())
    except (AttributeError, json.JSONDecodeError) as exc:
        raise QuizError("The provider returned malformed quiz JSON.") from exc
    if not isinstance(data, dict) or set(data) != {"status", "questions"} or data["status"] != "ok":
        raise QuizError("The provider returned an invalid quiz response.")
    questions = data["questions"]
    if not isinstance(questions, list) or len(questions) != len(expected_ids):
        raise QuizError("The provider returned an incomplete quiz response.")
    result = {}
    for question in questions:
        if not isinstance(question, dict) or set(question) != {
            "question_id", "prompt", "options", "correct_option_id", "explanation"
        }:
            raise QuizError("The provider returned an invalid MCQ schema.")
        qid = question["question_id"]
        options = question["options"]
        if qid not in expected_ids or qid in result or not isinstance(options, list) or len(options) != 4:
            raise QuizError("The provider returned invalid MCQ questions or options.")
        if not all(isinstance(option, dict) and set(option) == {"id", "text"}
                   and isinstance(option["id"], str) and option["id"].strip()
                   and isinstance(option["text"], str) and option["text"].strip()
                   for option in options):
            raise QuizError("The provider returned invalid MCQ options.")
        option_ids = [option["id"] for option in options]
        option_text = [option["text"].casefold() for option in options]
        if len(set(option_ids)) != 4 or len(set(option_text)) != 4 or question["correct_option_id"] not in option_ids:
            raise QuizError("The provider returned duplicate options or an invalid correct answer.")
        if not all(isinstance(question[key], str) and question[key].strip() for key in ("prompt", "explanation")):
            raise QuizError("The provider returned incomplete MCQ teaching content.")
        result[qid] = question
    if set(result) != expected_ids:
        raise QuizError("The provider response did not match the selected questions.")
    return result


def evaluate_quiz(attempt_id: str, provider_name: str, model) -> bool:
    """Score all items; return False and retain retryable state on any AI failure."""
    persistence.begin_evaluation(attempt_id)
    loaded = persistence.load_quiz(attempt_id)
    if not loaded:
        raise QuizError("Quiz attempt not found.")
    attempt, items = loaded
    failed = False
    needs_ai = any(
        item["answer_format"] == "coding"
        and item["item_status"] != "scored"
        and (item.get("answer_text") or "").strip()
        for item in items
    )
    if needs_ai and (
        provider_name != attempt.get("provider")
        or getattr(model, "model_id", None) != attempt.get("model_id")
    ):
        persistence.set_quiz_error(
            attempt_id, "evaluation_error",
            "Select the same provider and model used when this quiz was started, then retry.",
        )
        return False
    for item in items:
        if item["item_status"] == "scored":
            continue
        if item["answer_format"] == "mcq":
            percentage = 100.0 if item.get("selected_option_id") == item.get("correct_option_id") else 0.0
            persistence.score_item(item["id"], percentage)
            continue
        if not (item.get("answer_text") or "").strip():
            persistence.score_item(item["id"], 0.0, {"explanation": "No coding answer was submitted."})
            continue
        question = {
            "id": item["question_id"], "title": item["title"],
            "question_type": attempt["question_type"], "difficulty": attempt["difficulty"],
            "problem_statement": item["problem_statement"], "constraints": item.get("constraints"),
            "examples": item.get("examples") or [], "supported_methods": [item["method"]],
        }
        try:
            from coding_tutor.evaluation.feedback import assess_solution
            assessment = assess_solution(question, item["answer_text"], item["method"], provider_name, model)
            feedback = {
                "identified_mistakes": assessment.identified_mistakes,
                "explanation": assessment.explanation,
                "suggested_correction": assessment.suggested_correction,
                "corrected_code": assessment.corrected_code,
            }
            persistence.score_item(
                item["id"], assessment.estimated_percentage_correct, feedback,
                provider_name, getattr(model, "model_id", None),
            )
        except Exception:
            failed = True
            persistence.fail_item(item["id"], "AI assessment failed. Retry is available.")
    if failed:
        persistence.set_quiz_error(attempt_id, "evaluation_error", "One or more coding assessments failed. Retry to finish scoring.")
        return False
    _, scored = persistence.load_quiz(attempt_id)
    percentage = sum(float(item["percentage_correct"]) for item in scored) / len(scored)
    persistence.complete_quiz(attempt_id, round(percentage, 2))
    return True
