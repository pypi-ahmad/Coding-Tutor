"""Persistent, source-labelled solution viewer."""
from __future__ import annotations

import json

import streamlit as st

from coding_tutor.evaluation.persistence import record_solution_method
from coding_tutor.evaluation.solutions import (
    PROMPT_VERSION,
    SolutionFailure,
    SolutionBundle,
    generate_teaching_solutions,
)


def render_solution_view(question: dict, panel: dict) -> None:
    """Render stored references and explicit, validated AI generation."""
    st.subheader("💡 Solutions")
    st.caption("AI teaching solutions are generated text and are not locally executed or verified.")
    qid = str(question["id"])
    stored = _get_stored_solutions(qid)
    if question.get("question_type") == "algorithm":
        _render_method(question, panel, "python", stored.get("python", []), allow_multiple=True)
        return

    supported = _supported_methods(question)
    if not supported:
        st.info("No solution methods are available for this question.")
        return
    current = st.session_state.get("method")
    default = current if current in supported else supported[0]
    key = f"solution_method_{qid}"
    st.session_state.setdefault(key, default)
    method = st.segmented_control(
        "Method", supported, key=key, format_func=lambda value: value.upper(), width="stretch"
    )
    if method:
        st.caption("Equivalence across methods has not been deterministically executed or verified.")
        _render_method(question, panel, method, stored.get(method, []), allow_multiple=False)


def _supported_methods(question: dict) -> list[str]:
    value = question.get("supported_methods") or []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            value = []
    allowed = {"sql", "pandas", "pyspark", "polars"}
    return [method for method in value if method in allowed]


def _get_stored_solutions(question_id: str) -> dict[str, list[dict]]:
    from coding_tutor.database.connection import get_db

    rows = get_db().execute(
        """SELECT method, code, is_from_dataset, explanation
           FROM reference_solutions WHERE question_id=? ORDER BY id""",
        [question_id],
    ).fetchall()
    result: dict[str, list[dict]] = {}
    for method, code, is_dataset, explanation in rows:
        result.setdefault(method, []).append({
            "code": code, "is_from_dataset": is_dataset, "explanation": explanation,
        })
    return result


def _render_method(question: dict, panel: dict, method: str, stored: list[dict], allow_multiple: bool) -> None:
    displayed = False
    language = "sql" if method == "sql" else "python"
    for index, solution in enumerate(stored, 1):
        source = (
            "Dataset-provided reference" if solution["is_from_dataset"]
            else "Stored AI-generated reference"
        )
        with st.container(border=True):
            st.markdown(f"**{source}**" + (f" · {index}" if len(stored) > 1 else ""))
            st.code(solution["code"], language=language)
            if solution.get("explanation"):
                st.markdown(solution["explanation"])
            else:
                st.caption("Stored source artifact; no teaching explanation was provided.")
        displayed = True

    bundle = _cached_bundle(question, method)
    if bundle:
        _render_bundle(bundle, language)
        displayed = displayed or bool(bundle.solutions)

    provider = st.session_state.get("provider")
    model = st.session_state.get("model")
    label = "Generate alternative solutions" if allow_multiple else f"Generate guided {method.upper()} solution"
    if st.button(label, key=f"generate_guided_{question['id']}_{method}"):
        with st.spinner("Generating a structured teaching solution…"):
            result = generate_teaching_solutions(question, method, provider, model)
        if result.bundle:
            st.session_state[_cache_key(question, method)] = result.bundle
            st.session_state.pop(f"solution_failure_{question['id']}_{method}", None)
            st.rerun()
        else:
            st.session_state[f"solution_failure_{question['id']}_{method}"] = result.failure

    failure = st.session_state.get(f"solution_failure_{question['id']}_{method}")
    if failure:
        st.warning(_failure_message(failure))
    if displayed:
        _record_display(question, panel, method)


def _cache_key(question: dict, method: str) -> str:
    provider = st.session_state.get("provider") or "none"
    model = st.session_state.get("model")
    model_id = getattr(model, "model_id", "none")
    return f"teaching_solution_{PROMPT_VERSION}_{question['id']}_{method}_{provider}_{model_id}"


def _cached_bundle(question: dict, method: str) -> SolutionBundle | None:
    value = st.session_state.get(_cache_key(question, method))
    return value if isinstance(value, SolutionBundle) else None


def _render_bundle(bundle: SolutionBundle, language: str) -> None:
    st.markdown("**AI teaching solution**")
    if bundle.availability_note:
        st.info(bundle.availability_note)
    for solution in bundle.solutions:
        with st.container(border=True):
            st.markdown(f"#### {solution.title}")
            st.code(solution.code, language=language)
            st.markdown(solution.explanation)
            st.markdown(f"**Theory:** {solution.theory}")
            if solution.complexity:
                st.markdown(f"**Complexity:** {solution.complexity}")


def _record_display(question: dict, panel: dict, method: str) -> None:
    try:
        panel["view_id"] = record_solution_method(
            str(question["id"]), panel.get("attempt_id"), method, panel.get("view_id")
        )
        st.session_state.solution_panel = panel
    except Exception:
        st.warning("The solution is visible, but its view history could not be saved.")


def _failure_message(failure: SolutionFailure) -> str:
    return {
        SolutionFailure.UNAVAILABLE: "Configure a verified provider and model to generate a teaching solution.",
        SolutionFailure.INCOMPLETE_CONTEXT: "This data-analysis question lacks schema, fixture data, or an expected result, so a solution cannot be verified against shared context.",
        SolutionFailure.PROVIDER_ERROR: "The provider could not generate a solution. No secret or provider detail was displayed.",
        SolutionFailure.INVALID_RESPONSE: "The provider returned an incomplete or invalid structured solution. Nothing was displayed or saved.",
    }[failure]
