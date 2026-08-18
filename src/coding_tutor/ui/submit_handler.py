"""Handles Done button submissions — runs evaluation and shows feedback."""
from __future__ import annotations
import streamlit as st
from typing import Optional


def handle_submit(question: dict, method: str) -> Optional[str]:
    """Run evaluation for current editor content. Returns attempt_id."""
    q_id = question["id"]
    editor_key = f"editor_{q_id}_{method}"
    code = st.session_state.get(editor_key, "").strip()

    if not code:
        st.warning("Write some code before submitting.")
        return None

    st.session_state.submit_trigger = False

    with st.spinner("Running evaluation..."):
        run_result = _run_evaluation(question, method, code)

    feedback = None
    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")
    if provider_name and model and model.verified and run_result.status != "timeout":
        with st.spinner("Getting teacher feedback..."):
            from coding_tutor.evaluation.feedback import get_teacher_feedback
            feedback = get_teacher_feedback(
                question, code, method, run_result, provider_name, model
            )

    from coding_tutor.evaluation.persistence import save_attempt
    attempt_id = save_attempt(
        question_id=q_id,
        method=method,
        submitted_code=code,
        run_result=run_result,
        feedback=feedback,
        provider=provider_name,
        model_id=model.model_id if model else None,
    )

    from coding_tutor.ui.evaluation_view import render_evaluation
    render_evaluation(question, run_result, feedback, attempt_id, code, method)

    return attempt_id


def _run_evaluation(question: dict, method: str, code: str):
    from coding_tutor.evaluation.runner import (
        run_python, run_sql, run_pandas, run_polars, run_pyspark, RunResult,
    )
    from coding_tutor.database.connection import get_db
    import json

    conn = get_db()

    if method == "python":
        test_cases = conn.execute(
            "SELECT input_data, expected_output FROM question_test_cases WHERE question_id = ?",
            [question["id"]],
        ).fetchall()
        tcs = [{"input": tc[0], "expected_output": tc[1]} for tc in test_cases]
        return run_python(code, tcs, entry_point=None)

    def _load_assets():
        return {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT asset_type, content FROM question_assets WHERE question_id = ?",
                [question["id"]],
            ).fetchall()
        }

    if method == "sql":
        assets = _load_assets()
        schema = assets.get("schema", "")
        fixture = json.loads(assets.get("fixture_data", "[]"))
        expected = json.loads(assets.get("expected_result", "[]"))
        return run_sql(code, schema, fixture, "data_table", expected)

    if method == "pandas":
        assets = _load_assets()
        fixture = json.loads(assets.get("fixture_data", "[]"))
        expected = json.loads(assets.get("expected_result", "[]"))
        return run_pandas(code, fixture, expected)

    if method == "polars":
        assets = _load_assets()
        fixture = json.loads(assets.get("fixture_data", "[]"))
        expected = json.loads(assets.get("expected_result", "[]"))
        return run_polars(code, fixture, expected)

    if method == "pyspark":
        assets = _load_assets()
        fixture = json.loads(assets.get("fixture_data", "[]"))
        expected = json.loads(assets.get("expected_result", "[]"))
        return run_pyspark(code, fixture, expected)

    return RunResult(status="error", error_details=f"Unknown method: {method}")
