"""One-question-at-a-time AI engineering practice UI."""
from __future__ import annotations

import json

import streamlit as st

from coding_tutor.interview import service

DIFFICULTIES = ["Beginner", "Easy", "Medium", "Hard", "Very Hard"]
FORMATS = ["theory", "coding", "mcq"]
STYLES = ["scenario", "direct"]
LANGUAGES = ["python", "javascript/typescript", "java", "cpp", "sql"]


def _source_label(value: str) -> str:
    return {"local": "Local catalog", "ai": "AI generated", "mixed": "Mixed"}[value]


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander("Web sources"):
        for source in sources:
            st.markdown(f"- [{source.get('title') or source['url']}]({source['url']})")


def _answer_widget(item: dict, key: str) -> str:
    if item["answer_format"] == "mcq":
        options = item.get("options") or []
        mapping = {str(option["id"]): str(option["text"]) for option in options}
        return st.radio("Answer", list(mapping), format_func=mapping.get, index=None, key=key) or ""
    label = "Code answer" if item["answer_format"] == "coding" else "Your answer"
    return st.text_area(label, key=key, height=260 if item["answer_format"] == "coding" else 180)


def render_ai_questions_page() -> None:
    st.title(":material/psychology: AI Questions")
    st.caption("Practice AI engineering theory, scenarios, coding, and MCQs. Code is reviewed but never executed.")
    session_id = st.session_state.get("active_ai_question_session_id")
    if not session_id:
        facets = service.catalog_facets()
        with st.form("ai_question_setup"):
            source_mode = st.segmented_control(
                "Question source", ["local", "ai", "mixed"], format_func=_source_label,
                default="local", required=True,
            )
            col1, col2 = st.columns(2)
            domain = col1.selectbox("Domain", ["", *facets["domains"]], format_func=lambda x: x or "Any domain")
            topic = col2.selectbox(
                "Topic", ["", *facets["topics"]], format_func=lambda x: x or "Any topic",
                accept_new_options=source_mode in {"ai", "mixed"},
            )
            col3, col4, col5 = st.columns(3)
            difficulty = col3.selectbox("Difficulty", DIFFICULTIES, index=2)
            answer_format = col4.selectbox("Answer format", FORMATS, format_func=str.title)
            prompt_style = col5.selectbox("Question style", STYLES, format_func=str.title)
            method = st.selectbox("Coding language", LANGUAGES) if answer_format == "coding" else None
            web_enabled = st.toggle(
                "Web research", value=False, disabled=source_mode == "local",
                help="Used only when local references cannot cover an AI-generated question.",
            )
            start = st.form_submit_button("Start practice", type="primary")
        if start:
            try:
                filters = {
                    "source_mode": source_mode, "domain": domain or None, "topic": topic or None,
                    "difficulty": difficulty, "answer_format": answer_format,
                    "prompt_style": prompt_style, "method": method, "web_enabled": web_enabled,
                }
                session_id = service.create_ai_session(
                    filters, st.session_state.get("provider"), st.session_state.get("model")
                )
                _, warning = service.next_ai_question(
                    session_id, st.session_state.get("provider"), st.session_state.get("model")
                )
                st.session_state["active_ai_question_session_id"] = session_id
                if warning:
                    st.session_state["ai_question_warning"] = warning
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        return

    warning = st.session_state.pop("ai_question_warning", None)
    if warning:
        st.warning(warning)
    item = service.pending_ai_question(session_id)
    feedback = st.session_state.get("ai_question_feedback")
    if feedback:
        st.metric("AI-estimated score", f"{feedback['score']:.0f}%")
        st.write(feedback.get("feedback", ""))
        for gap in feedback.get("gaps", []):
            st.warning(gap)
        with st.container(horizontal=True):
            if st.button("Next question", type="primary"):
                try:
                    _, warning = service.next_ai_question(
                        session_id, st.session_state.get("provider"), st.session_state.get("model")
                    )
                    st.session_state.pop("ai_question_feedback", None)
                    if warning:
                        st.session_state["ai_question_warning"] = warning
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if st.button("New practice session"):
                st.session_state.pop("active_ai_question_session_id", None)
                st.session_state.pop("ai_question_feedback", None)
                st.rerun()
        return
    if not item:
        st.info("This session has no pending question.")
        if st.button("New practice session"):
            st.session_state.pop("active_ai_question_session_id", None)
            st.rerun()
        return

    st.subheader(f"Question {item['position']} · {item['topic']}")
    st.markdown(item["prompt"])
    _render_sources(item.get("web_sources") or [])
    key = f"ai_question_answer_{session_id}_{item['position']}"
    answer = _answer_widget(item, key)
    if st.button("Submit answer", type="primary", disabled=not bool(answer.strip())):
        try:
            result = service.submit_ai_answer(
                session_id, item, answer, st.session_state.get("provider"), st.session_state.get("model")
            )
            st.session_state["ai_question_feedback"] = result
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
