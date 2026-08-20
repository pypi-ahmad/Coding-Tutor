"""Render explicitly labelled AI-estimated assessment results."""
import streamlit as st


def _apply_correction(
    editor_key: str, backup_key: str, applied_key: str, code: str
) -> None:
    st.session_state[backup_key] = st.session_state.get(editor_key, "")
    st.session_state[editor_key] = code
    st.session_state[applied_key] = True


def _restore_correction(editor_key: str, backup_key: str, applied_key: str) -> None:
    if backup_key in st.session_state:
        st.session_state[editor_key] = st.session_state[backup_key]
    st.session_state[applied_key] = False


def render_evaluation(question: dict, assessment, attempt_id: str, method: str) -> None:
    st.subheader("📊 AI Teacher Assessment")
    left, right = st.columns(2)
    left.metric("AI-estimated correctness", f"{assessment.estimated_percentage_correct:.1f}%")
    right.metric("AI-estimated marks", f"{assessment.marks:.1f}/10")
    st.caption(f"Static AI review by {assessment.provider}/{assessment.model_id}. No code or tests were executed.")
    if assessment.identified_mistakes:
        st.markdown("**Identified issues**")
        for mistake in assessment.identified_mistakes:
            st.markdown(f"- {mistake}")
    st.markdown("**Explanation**")
    st.markdown(assessment.explanation)
    if assessment.suggested_correction:
        st.info(assessment.suggested_correction)
    if assessment.corrected_code:
        st.code(assessment.corrected_code, language="sql" if method == "sql" else "python")
        editor_key = f"editor_{question['id']}_{method}"
        backup_key = f"editor_pre_correction_{attempt_id}"
        applied_key = f"correction_applied_{attempt_id}"
        applied = st.session_state.get(applied_key, False)
        current_code = st.session_state.get(editor_key, "")

        if applied:
            if current_code == assessment.corrected_code:
                st.success("AI correction applied. Your submitted attempt remains saved unchanged.")
                restore_label = "Restore pre-correction code"
            else:
                st.warning(
                    "You edited the AI correction. Restoring will replace those newer editor changes."
                )
                restore_label = "Restore pre-correction code and replace current edits"
            st.button(
                restore_label,
                key=f"restore_corr_{attempt_id}",
                on_click=_restore_correction,
                args=(editor_key, backup_key, applied_key),
            )
        else:
            st.button(
                "Apply suggested correction",
                key=f"apply_corr_{attempt_id}",
                on_click=_apply_correction,
                args=(editor_key, backup_key, applied_key, assessment.corrected_code),
            )
