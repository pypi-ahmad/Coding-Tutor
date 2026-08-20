"""Handle Submit solution actions through AI review only; no learner code is executed."""
from __future__ import annotations
import streamlit as st


def _store_failure(attempt_id: str, message: str) -> None:
    try:
        from coding_tutor.evaluation.persistence import fail_attempt

        fail_attempt(attempt_id, message)
    except Exception:
        pass


def handle_submit(question: dict, method: str):
    editor_key = f"editor_{question['id']}_{method}"
    code = st.session_state.get(editor_key, "")
    st.session_state.submit_trigger = False
    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")

    if not isinstance(code, str) or not code.strip():
        st.warning("Enter a solution before submitting.")
        return None
    if method not in question.get("supported_methods", []):
        st.error("The selected method is not supported by this question.")
        return None

    from coding_tutor.evaluation.persistence import create_attempt, complete_attempt

    try:
        attempt_id = create_attempt(
            question["id"], method, code, provider_name, getattr(model, "model_id", None)
        )
    except Exception:
        st.error("The original attempt could not be saved locally. Assessment was not requested.")
        return None

    st.session_state.last_attempt_id = attempt_id
    st.session_state.pop("active_assessment", None)
    from coding_tutor.quiz.session import mark_editor_saved

    mark_editor_saved(question["id"], method, code)
    from coding_tutor.evaluation.feedback import (
        AssessmentError,
        validate_assessment_request,
    )

    try:
        validate_assessment_request(question, code, method, provider_name, model)
    except AssessmentError as exc:
        message = str(exc)
        _store_failure(attempt_id, message)
        st.warning(message)
        return attempt_id
    except Exception:
        message = "The assessment configuration could not be validated."
        _store_failure(attempt_id, message)
        st.error(message)
        return attempt_id

    try:
        with st.spinner("Getting AI teacher assessment..."):
            from coding_tutor.evaluation.feedback import assess_solution

            assessment = assess_solution(question, code, method, provider_name, model)
    except AssessmentError as exc:
        message = str(exc)
        _store_failure(attempt_id, message)
        st.error(f"AI assessment failed: {message}")
        return attempt_id
    except Exception:
        message = "The AI provider could not complete the assessment. Check configuration, connectivity, quota, and model access, then try again."
        _store_failure(attempt_id, message)
        st.error(message)
        return attempt_id

    try:
        complete_attempt(attempt_id, assessment)
    except Exception:
        message = "The AI assessment was returned but could not be saved locally."
        _store_failure(attempt_id, message)
        st.error(message)
        return attempt_id

    st.session_state.active_assessment = {
        "question_id": str(question["id"]),
        "method": method,
        "attempt_id": attempt_id,
        "assessment": assessment,
    }
    return attempt_id
