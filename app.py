"""Coding Tutor — main Streamlit entry point."""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads .env if present locally; safe if file absent

from coding_tutor.ui.sidebar import render_sidebar
from coding_tutor.ui.main_page import render_main_page


def main():
    st.set_page_config(
        page_title="Coding Tutor",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.provider = None
        st.session_state.model = None
        st.session_state.current_question = None
        st.session_state.editor_content = ""
        st.session_state.question_type = "algorithm"
        st.session_state.method = "python"
        st.session_state.difficulty = "Easy"
        st.session_state.question_source = "curated"
        st.session_state.submit_trigger = False
        st.session_state.show_solution_trigger = False

    # Top navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🎓 Practice", "📈 Progress"],
        key="nav_page",
        label_visibility="collapsed",
    )

    render_sidebar()

    if page == "🎓 Practice":
        render_main_page()
    else:
        from coding_tutor.ui.progress_page import render_progress_page
        render_progress_page()


if __name__ == "__main__":
    main()
