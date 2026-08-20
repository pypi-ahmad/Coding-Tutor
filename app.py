"""Coding Tutor — main Streamlit entry point."""
import streamlit as st

from coding_tutor.catalog import apply_catalog_profile, get_catalog_profile
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
        ["🎓 Practice", "🧠 Quiz", "📈 Progress"],
        key="nav_page",
        label_visibility="collapsed",
    )

    render_sidebar(profile)

    if st.session_state.get("pending_learning_change"):
        render_pending_learning_change_dialog()

    if page == "🎓 Practice":
        render_main_page()
    elif page == "🧠 Quiz":
        from coding_tutor.ui.quiz_page import render_quiz_page
        render_quiz_page()
    else:
        from coding_tutor.ui.progress_page import render_progress_page
        render_progress_page()


if __name__ == "__main__":
    main()
