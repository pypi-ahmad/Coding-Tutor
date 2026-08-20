"""Timed adaptive technical interview UI."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from coding_tutor.interview.ai import draft_blueprint
from coding_tutor.interview.documents import DocumentError, extract_document
from coding_tutor.interview import service
from coding_tutor.methods import INTERVIEW_LANGUAGES, method_label

DURATIONS = [30, 45, 60, 90]
LANGUAGES = list(INTERVIEW_LANGUAGES)
FORMATS = ["theory", "coding", "mcq"]


def _deadline(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace(" ", "T"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _remaining_seconds(value: str) -> int:
    return max(0, int((_deadline(value) - datetime.now(timezone.utc)).total_seconds()))


@st.fragment(run_every=1)
def _render_timer(value: str) -> None:
    remaining = _remaining_seconds(value)
    minutes, seconds = divmod(remaining, 60)
    st.metric("Time remaining", f"{minutes:02d}:{seconds:02d}")
    if remaining == 0:
        st.warning(
            "Time is up. Submit this final answer or finish without answering; "
            "no new question will be asked."
        )


def _current_item(turns: list[dict]) -> dict | None:
    pending = next((turn for turn in reversed(turns) if turn["status"] == "pending"), None)
    return service.get_item(pending["interview_item_id"]) if pending else None


def _answer_widget(item: dict, key: str) -> str:
    if item["answer_format"] == "mcq":
        options = item.get("options") or []
        mapping = {str(option["id"]): str(option["text"]) for option in options}
        return st.radio("Answer", list(mapping), format_func=mapping.get, index=None, key=key) or ""
    return st.text_area(
        "Code answer" if item["answer_format"] == "coding" else "Your answer",
        key=key, height=260 if item["answer_format"] == "coding" else 180,
    )


def _setup() -> None:
    st.subheader("Create an interview plan")
    with st.form("interview_plan_inputs"):
        interview_type = st.segmented_control(
            "Interview type", ["tech", "jd"],
            format_func=lambda value: "Tech interview" if value == "tech" else "JD-based interview",
            default="tech", required=True,
        )
        role = st.text_input("Target role", placeholder="AI Engineer")
        level = st.selectbox("Level", ["Junior", "Mid", "Senior", "Staff"])
        jd_text = st.text_area("Job description", disabled=interview_type != "jd")
        resume_text = st.text_area("Resume (optional)", disabled=interview_type != "jd")
        jd_file = st.file_uploader("Job description file", type=["pdf", "docx", "txt"], disabled=interview_type != "jd")
        resume_file = st.file_uploader("Resume file (optional)", type=["pdf", "docx", "txt"], disabled=interview_type != "jd")
        create = st.form_submit_button("Create interview plan", type="primary")
    if create:
        try:
            if jd_file:
                jd_text = extract_document(jd_file.name, jd_file.getvalue())
            if resume_file:
                resume_text = extract_document(resume_file.name, resume_file.getvalue())
            if interview_type == "jd" and not jd_text.strip():
                raise DocumentError("A job description is required for a JD-based interview.")
            blueprint = draft_blueprint(
                st.session_state.get("provider"), st.session_state.get("model"),
                role=role or "AI Engineer", level=level, jd=jd_text, resume=resume_text,
            )
            st.session_state["interview_draft"] = {
                "interview_type": interview_type, "blueprint": blueprint,
            }
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _review_plan(draft: dict) -> None:
    blueprint = draft["blueprint"]
    suggested_formats = [value for value in blueprint.get("formats", []) if value in FORMATS] or FORMATS
    suggested_languages = [value for value in blueprint.get("languages", []) if value in LANGUAGES] or ["python"]
    st.subheader("Review interview plan")
    st.caption("The JD and resume are not stored. Only this editable plan and interview results are saved locally.")
    with st.form("interview_plan_review"):
        role = st.text_input("Role", value=str(blueprint.get("role", "AI Engineer")))
        level = st.selectbox(
            "Level", ["Junior", "Mid", "Senior", "Staff"],
            index=["Junior", "Mid", "Senior", "Staff"].index(blueprint.get("level"))
            if blueprint.get("level") in ["Junior", "Mid", "Senior", "Staff"] else 1,
        )
        topics_text = st.text_area("Topics", value=", ".join(blueprint.get("topics") or ["RAG", "LLMs"]))
        formats = st.pills("Answer formats", FORMATS, default=suggested_formats, selection_mode="multi")
        languages = st.pills(
            "Coding languages", LANGUAGES, default=suggested_languages,
            selection_mode="multi", format_func=method_label,
        )
        duration = st.segmented_control("Time window", DURATIONS, default=45, format_func=lambda x: f"{x} min", required=True)
        source_mode = st.segmented_control(
            "Question source", ["local", "ai", "mixed"], default="mixed", required=True,
            format_func=lambda x: {"local": "Local catalog", "ai": "AI generated", "mixed": "Mixed"}[x],
        )
        web_enabled = st.toggle("Web research", value=False, disabled=source_mode == "local")
        start = st.form_submit_button("Start interview", type="primary")
    if start:
        try:
            final_blueprint = {
                **blueprint, "role": role, "level": level,
                "topics": [value.strip() for value in topics_text.split(",") if value.strip()],
                "formats": list(formats or ["theory"]), "languages": list(languages or ["python"]),
            }
            session_id = service.start_interview(
                draft["interview_type"], int(duration), source_mode, final_blueprint,
                web_enabled, st.session_state.get("provider"), st.session_state.get("model"),
            )
            _, warning = service.add_interview_turn(
                session_id, st.session_state.get("provider"), st.session_state.get("model")
            )
            st.session_state["active_interview_session_id"] = session_id
            st.session_state.pop("interview_draft", None)
            if warning:
                st.session_state["interview_warning"] = warning
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _completed(session: dict, turns: list[dict]) -> None:
    report = session.get("report") or {}
    st.subheader("Interview report")
    st.metric("Overall AI-estimated score", f"{report.get('overall_score', 0):.0f}%")
    st.write(report.get("summary", ""))
    for title, key in (("Strengths", "strengths"), ("Gaps", "gaps"), ("Recommendations", "recommendations")):
        st.markdown(f"### {title}")
        for value in report.get(key, []):
            st.markdown(f"- {value}")
    with st.expander("Question-by-question feedback"):
        for turn in turns:
            st.markdown(f"**{turn['position']}. {turn['prompt']}**")
            st.write(turn.get("answer_text") or turn.get("selected_option") or "Skipped")
            if turn.get("feedback"):
                st.caption(f"Score: {turn.get('score', 0):.0f}%")
                st.write(turn["feedback"].get("feedback", ""))
    if st.button("New interview"):
        st.session_state.pop("active_interview_session_id", None)
        st.rerun()


def _active(session: dict, turns: list[dict]) -> None:
    remaining = _remaining_seconds(session["deadline_at"])
    _render_timer(session["deadline_at"])
    warning = st.session_state.pop("interview_warning", None)
    if warning:
        st.warning(warning)
    for turn in turns:
        if turn["status"] == "pending":
            continue
        with st.chat_message("assistant"):
            st.write(turn["prompt"])
        with st.chat_message("user"):
            st.write(turn.get("answer_text") or turn.get("selected_option") or "Skipped")
    item = _current_item(turns)
    if not item:
        st.error("The active interview has no pending question.")
        return
    with st.chat_message("assistant"):
        st.write(item["prompt"])
    key = f"interview_answer_{session['id']}_{len(turns)}"
    answer = _answer_widget(item, key)
    with st.container(horizontal=True):
        if st.button("Submit answer", type="primary", disabled=not bool(answer.strip())):
            try:
                service.submit_interview_answer(
                    session["id"], item, answer, st.session_state.get("provider"), st.session_state.get("model")
                )
                if _remaining_seconds(session["deadline_at"]) == 0:
                    service.finish_interview(
                        session["id"], st.session_state.get("provider"), st.session_state.get("model")
                    )
                else:
                    _, warning = service.add_interview_turn(
                        session["id"], st.session_state.get("provider"), st.session_state.get("model")
                    )
                    if warning:
                        st.session_state["interview_warning"] = warning
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if st.button("Finish interview early" if remaining else "Finish without answering"):
            try:
                service.skip_pending_turn(session["id"])
                service.finish_interview(
                    session["id"], st.session_state.get("provider"), st.session_state.get("model")
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def render_interview_page() -> None:
    st.title(":material/record_voice_over: Interview")
    st.caption("A timed adaptive technical interview. Feedback is revealed only in the final report.")
    session_id = st.session_state.get("active_interview_session_id")
    if session_id:
        loaded = service.load_interview(session_id)
        if loaded:
            session, turns = loaded
            if session["status"] == "completed":
                _completed(session, turns)
            else:
                _active(session, turns)
            return
        st.session_state.pop("active_interview_session_id", None)
    draft = st.session_state.get("interview_draft")
    _review_plan(draft) if draft else _setup()
