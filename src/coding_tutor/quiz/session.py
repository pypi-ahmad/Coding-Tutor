"""Session-state management for the learning flow and editor drafts."""
from __future__ import annotations

import json
from collections.abc import MutableMapping
from typing import Any, Optional

import streamlit as st


METHODS_BY_QUESTION_TYPE = {
    "algorithm": ("python",),
    "data_analysis": ("sql", "pandas", "pyspark", "polars"),
}

_DEFAULT_STATE = {
    "initialized": True,
    "provider": None,
    "model": None,
    "current_question": None,
    "editor_content": "",
    "question_type": "algorithm",
    "question_type_control": "algorithm",
    "method": "python",
    "method_control": "python",
    "difficulty": "Easy",
    "question_source": "dataset",
    "topic": "general",
    "pending_learning_change": None,
    "submit_trigger": False,
    "show_solution_trigger": False,
    "quiz_total_items": 1,
    "quiz_coding_items": 1,
    "active_quiz_attempt_id": None,
}


def _state(state: MutableMapping[str, Any] | None = None) -> MutableMapping[str, Any]:
    return state if state is not None else st.session_state


def initialize_session_state(state: MutableMapping[str, Any] | None = None) -> None:
    target = _state(state)
    queued_controls = target.pop("_queued_control_updates", {})
    for key, value in queued_controls.items():
        target[key] = value
    for key, value in _DEFAULT_STATE.items():
        target.setdefault(key, value)
    target.setdefault("question_type_control", target["question_type"])
    target.setdefault("method_control", target["method"])


def editor_key(question_id: str, method: str) -> str:
    return f"editor_{question_id}_{method}"


def editor_baseline_key(question_id: str, method: str) -> str:
    return f"editor_baseline_{question_id}_{method}"


def has_unsaved_editor_content(state: MutableMapping[str, Any] | None = None) -> bool:
    target = _state(state)
    question = target.get("current_question")
    if not question:
        return False
    method = target.get("method", "python")
    content_key = editor_key(str(question["id"]), method)
    baseline_key = editor_baseline_key(str(question["id"]), method)
    content = target.get(content_key, target.get("editor_content", ""))
    baseline = target.get(baseline_key, "")
    return content != baseline


def _clear_active_question(target: MutableMapping[str, Any]) -> None:
    target["current_question"] = None
    target["editor_content"] = ""
    target["submit_trigger"] = False
    target["show_solution_trigger"] = False


def _set_control(target: MutableMapping[str, Any], key: str, value: str,
                 defer_controls: bool) -> None:
    if defer_controls:
        target.setdefault("_queued_control_updates", {})[key] = value
    else:
        target[key] = value


def _commit_learning_change(target: MutableMapping[str, Any], setting: str, value: str,
                            defer_controls: bool = False) -> None:
    if setting == "question_type":
        target["question_type"] = value
        _set_control(target, "question_type_control", value, defer_controls)
        methods = METHODS_BY_QUESTION_TYPE[value]
        if target.get("method") not in methods:
            target["method"] = methods[0]
        _set_control(target, "method_control", target["method"], defer_controls)
        question = target.get("current_question")
        if question and question.get("question_type") != value:
            _clear_active_question(target)
        return

    if setting == "method":
        target["method"] = value
        _set_control(target, "method_control", value, defer_controls)
        question = target.get("current_question")
        if question and value not in question.get("supported_methods", []):
            _clear_active_question(target)
        return

    raise ValueError(f"Unsupported learning setting: {setting}")


def request_learning_change(setting: str, value: str,
                            state: MutableMapping[str, Any] | None = None) -> bool:
    """Request a type/method change; return True when confirmation is required."""
    target = _state(state)
    current = target.get(setting)
    if value == current:
        return False
    if has_unsaved_editor_content(target):
        question = target["current_question"]
        method = target.get("method", "python")
        target["pending_learning_change"] = {
            "setting": setting,
            "value": value,
            "editor_key": editor_key(str(question["id"]), method),
            "baseline_key": editor_baseline_key(str(question["id"]), method),
        }
        target[f"{setting}_control"] = current
        return True
    _commit_learning_change(target, setting, value)
    return False


def resolve_pending_learning_change(decision: str,
                                    state: MutableMapping[str, Any] | None = None,
                                    defer_controls: bool = False) -> None:
    """Resolve a pending change with keep, discard, or cancel."""
    target = _state(state)
    pending = target.get("pending_learning_change")
    if not pending:
        return
    if decision == "cancel":
        _set_control(
            target, f"{pending['setting']}_control", target[pending["setting"]],
            defer_controls,
        )
    elif decision in {"keep", "discard"}:
        if decision == "discard":
            target[pending["editor_key"]] = target.get(pending["baseline_key"], "")
        _commit_learning_change(
            target, pending["setting"], pending["value"], defer_controls,
        )
    else:
        raise ValueError(f"Unknown pending-change decision: {decision}")
    target["pending_learning_change"] = None


def mark_editor_saved(question_id: str, method: str, content: str,
                      state: MutableMapping[str, Any] | None = None) -> None:
    target = _state(state)
    target[editor_baseline_key(question_id, method)] = content


def get_current_question() -> Optional[dict]:
    return st.session_state.get("current_question")


def _json_value(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def load_question(question_id: str) -> None:
    """Load a normalized question and its display examples into session state."""
    from coding_tutor.database.connection import get_db
    conn = get_db()
    row = conn.execute(
        """SELECT q.id, q.title, q.question_type, q.difficulty, q.problem_statement,
                  q.constraints, q.examples, q.supported_methods, q.tags, q.is_complete, q.is_ai_generated, q.source_id,
                  qs.dataset_name, qs.attribution, qs.license, ag.provider, ag.model_id
           FROM questions q
           LEFT JOIN question_sources qs ON q.source_id = qs.id
           LEFT JOIN ai_generated_questions ag ON q.id = ag.question_id
           WHERE q.id = ?""",
        [question_id],
    ).fetchone()

    if not row:
        st.error(f"Question {question_id} not found.")
        return

    examples = _json_value(row[6], [])
    if not examples:
        case_rows = conn.execute(
            """SELECT input_data, expected_output
               FROM question_test_cases WHERE question_id = ?
               ORDER BY is_example DESC, id LIMIT 3""",
            [question_id],
        ).fetchall()
        examples = [
            {"input": _json_value(case[0], case[0]), "expected_output": _json_value(case[1], case[1])}
            for case in case_rows
        ]

    question = {
        "id": str(row[0]), "title": row[1], "question_type": row[2],
        "difficulty": row[3], "problem_statement": row[4], "constraints": row[5],
        "examples": examples, "supported_methods": _json_value(row[7], []),
        "tags": _json_value(row[8], []), "is_complete": row[9],
        "is_ai_generated": row[10], "source_id": str(row[11]) if row[11] else None,
        "source_kind": "ai_generated" if row[10] else "dataset",
        "dataset_name": row[12], "attribution": row[13], "license": row[14],
        "generation_provider": row[15], "generation_model": row[16],
    }

    supported = question["supported_methods"]
    current_method = st.session_state.get("method", "python")
    if supported and current_method not in supported:
        current_method = supported[0]
        st.session_state["method"] = current_method
    st.session_state.setdefault("_queued_control_updates", {})["method_control"] = current_method
    st.session_state["current_question"] = question
    st.session_state["submit_trigger"] = False
    st.session_state["show_solution_trigger"] = False


def clear_question_with_confirm() -> None:
    """Return to the question list while retaining keyed editor drafts."""
    _clear_active_question(st.session_state)
