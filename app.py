"""Coding Tutor — unified Streamlit entry point."""
import os

import streamlit as st

from coding_tutor.catalog import (
    apply_catalog_profile,
    database_for_question_type,
    get_catalog_profile,
    interview_database,
)
from coding_tutor.database.connection import set_active_db
from coding_tutor.quiz.session import initialize_session_state
from coding_tutor.ui.sidebar import render_sidebar, render_pending_learning_change_dialog
from coding_tutor.ui.main_page import render_main_page


def main():
    profile = get_catalog_profile()
    st.set_page_config(
        page_title=profile.title,
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state()
    apply_catalog_profile(st.session_state, profile)

    # Top navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Coding", "Quiz", "AI Questions", "Interview", "Progress"],
        key="nav_page",
        label_visibility="collapsed",
    )

    if os.environ.get("CODING_TUTOR_DB"):
        set_active_db(os.environ["CODING_TUTOR_DB"])
    elif profile.key != "all":
        set_active_db(profile.database)
    elif page in {"Coding", "Quiz"}:
        set_active_db(database_for_question_type(st.session_state.get("question_type", "algorithm")))
    else:
        set_active_db(interview_database())

    render_sidebar(profile)

    if st.session_state.get("pending_learning_change"):
        render_pending_learning_change_dialog()

    if page == "Coding":
        render_main_page()
    elif page == "Quiz":
        from coding_tutor.ui.quiz_page import render_quiz_page
        render_quiz_page()
    elif page == "AI Questions":
        from coding_tutor.ui.ai_questions_page import render_ai_questions_page
        render_ai_questions_page()
    elif page == "Interview":
        from coding_tutor.ui.interview_page import render_interview_page
        render_interview_page()
    else:
        from coding_tutor.ui.progress_page import render_progress_page
        render_progress_page()


if __name__ == "__main__":
    main()
