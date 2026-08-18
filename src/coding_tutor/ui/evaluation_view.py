"""Renders the evaluation result and teacher feedback in the UI."""
from __future__ import annotations
import streamlit as st
from typing import Optional


def render_evaluation(
    question: dict,
    run_result,
    feedback,
    attempt_id: str,
    submitted_code: str,
    method: str,
):
    """Display test results and AI teacher feedback."""
    st.subheader("📊 Evaluation Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tests Passed", f"{run_result.tests_passed}/{run_result.tests_total}")
    with col2:
        st.metric("Correctness", f"{run_result.percentage_correct:.1f}%")
    with col3:
        if feedback:
            st.metric("Marks (AI)", f"{feedback.marks:.1f}/10")

    status_icons = {"passed": "✅", "failed": "❌", "error": "⚠️", "timeout": "⏱️"}
    icon = status_icons.get(run_result.status, "❓")
    st.markdown(f"**Status:** {icon} {run_result.status.upper()}")

    if run_result.error_details:
        with st.expander("Error Details"):
            st.code(run_result.error_details, language="text")

    st.caption("Correctness % and marks are based on deterministic test execution.")

    if feedback:
        st.divider()
        st.subheader("🎓 Teacher Feedback")
        st.caption(
            f"_AI feedback from {feedback.provider}/{feedback.model_id} — "
            "this is teaching guidance, not authoritative scoring._"
        )

        if feedback.identified_mistakes:
            st.markdown("**Identified Issues:**")
            for m in feedback.identified_mistakes:
                st.markdown(f"- {m}")

        if feedback.explanation:
            st.markdown("**Explanation:**")
            st.markdown(feedback.explanation)

        if feedback.recommended_correction:
            st.markdown("**Recommendation:**")
            st.info(feedback.recommended_correction)

        if feedback.corrected_code:
            with st.expander("💡 Suggested Correction (click to apply)"):
                lang = "sql" if method == "sql" else "python"
                st.code(feedback.corrected_code, language=lang)
                if st.button("Apply Correction to Editor", key=f"apply_corr_{attempt_id}"):
                    q_id = question["id"]
                    editor_key = f"editor_{q_id}_{method}"
                    original_key = f"editor_original_{q_id}_{method}"
                    if original_key not in st.session_state:
                        st.session_state[original_key] = st.session_state.get(editor_key, "")
                    st.session_state[editor_key] = feedback.corrected_code
                    st.success("Correction applied. Your original code is preserved in session state.")
                    st.rerun()
