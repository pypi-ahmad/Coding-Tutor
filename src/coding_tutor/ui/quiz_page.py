"""Resumable Quiz Mode UI with delayed feedback."""
from __future__ import annotations

import json

import streamlit as st

from coding_tutor.methods import syntax_language

from coding_tutor.quiz import persistence
from coding_tutor.quiz.service import QuizError, evaluate_quiz, retry_preparation, start_quiz


def _save_widget_draft(item_id: str, answer_format: str, key: str) -> None:
    persistence.save_draft(item_id, answer_format, st.session_state.get(key))


def _active_attempt_id() -> str | None:
    attempt_id = st.session_state.get("active_quiz_attempt_id")
    if attempt_id and persistence.load_quiz(attempt_id):
        return attempt_id
    attempt_id = persistence.latest_unfinished_quiz()
    st.session_state["active_quiz_attempt_id"] = attempt_id
    return attempt_id


def render_quiz_page() -> None:
    st.title("🧠 Quiz mode")
    attempt_id = _active_attempt_id()
    if not attempt_id:
        _render_start()
        return
    loaded = persistence.load_quiz(attempt_id)
    if not loaded:
        st.session_state["active_quiz_attempt_id"] = None
        st.error("The quiz attempt could not be loaded.")
        return
    attempt, items = loaded
    if attempt["status"] in {"preparing", "preparation_error"}:
        _render_preparation(attempt, items)
    elif attempt["status"] == "completed":
        _render_completed(attempt, items)
    else:
        _render_answering(attempt, items)


def _render_start() -> None:
    st.markdown("### Start a new quiz")
    st.write(
        "Questions are randomly drawn at the selected difficulty. Answers are saved locally, "
        "and feedback stays hidden until the whole quiz is scored."
    )
    total = int(st.session_state.get("quiz_total_items", 1))
    coding = min(int(st.session_state.get("quiz_coding_items", 1)), total)
    mcq = total - coding
    st.info(f"{total} questions: {coding} coding and {mcq} multiple choice.")
    st.caption("Starting may make billable AI calls for generated questions or MCQ preparation.")
    if st.button("Start quiz", type="primary"):
        model = st.session_state.get("model")
        settings = {
            "question_source": st.session_state.get("question_source", "dataset"),
            "question_type": st.session_state.get("question_type", "algorithm"),
            "difficulty": st.session_state.get("difficulty", "Easy"),
            "topic": st.session_state.get("topic", "general"),
            "method": st.session_state.get("method", "python"),
            "total_items": total, "coding_items": coding, "mcq_items": mcq,
            "provider": st.session_state.get("provider"),
            "model_id": getattr(model, "model_id", None),
            "web_enabled": bool(st.session_state.get("web_research_enabled", False)),
        }
        try:
            with st.spinner("Preparing quiz questions…"):
                attempt_id = start_quiz(settings, model)
        except QuizError as exc:
            st.error(str(exc))
            return
        st.session_state["active_quiz_attempt_id"] = attempt_id
        st.rerun()


def _render_preparation(attempt: dict, items: list[dict]) -> None:
    st.subheader("Quiz preparation")
    if attempt["status"] == "preparing":
        st.info("Quiz preparation is in progress. Reload to continue if this state persists.")
    else:
        st.warning(attempt.get("error_details") or "Quiz preparation needs to be retried.")
    st.caption(f"Prepared question records: {len(items)} of {attempt['total_items']}")
    if st.button("Retry quiz creation", type="primary"):
        with st.spinner("Retrying quiz preparation…"):
            retry_preparation(attempt["id"], st.session_state.get("model"))
        st.rerun()


def _render_answering(attempt: dict, items: list[dict]) -> None:
    st.subheader(f"Quiz · {attempt['difficulty']} · {attempt['method'].upper()}")
    st.caption(
        f"Question source: {attempt['question_source']} · Untimed · "
        "feedback appears only after all items are scored"
    )
    if attempt["status"] == "evaluation_error":
        st.warning(attempt.get("error_details") or "Some coding items need assessment retry.")

    for item in items:
        with st.container(border=True):
            st.markdown(f"### {item['position']}. {item['title']}")
            disabled = item["item_status"] == "scored"
            if item["answer_format"] == "coding":
                st.markdown(item["problem_statement"])
                if item.get("constraints"):
                    with st.expander("Constraints"):
                        st.markdown(item["constraints"])
                key = f"quiz_answer_{item['id']}"
                st.session_state.setdefault(key, item.get("answer_text") or "")
                st.text_area(
                    f"Coding answer {item['position']}", key=key, height=220,
                    disabled=disabled, on_change=_save_widget_draft,
                    args=(item["id"], "coding", key),
                )
            else:
                st.markdown(item["prompt_snapshot"])
                options = item.get("options") or []
                option_ids = [option["id"] for option in options]
                option_text = {option["id"]: option["text"] for option in options}
                key = f"quiz_answer_{item['id']}"
                st.session_state.setdefault(key, item.get("selected_option_id"))
                st.radio(
                    f"Answer {item['position']}", option_ids,
                    format_func=lambda value, mapping=option_text: mapping[value],
                    index=None, key=key, disabled=disabled,
                    on_change=_save_widget_draft, args=(item["id"], "mcq", key),
                )

    label = "Retry assessment" if attempt["status"] == "evaluation_error" else "Submit quiz"
    if st.button(label, type="primary"):
        with st.spinner("Scoring quiz…"):
            complete = evaluate_quiz(
                attempt["id"], st.session_state.get("provider"), st.session_state.get("model")
            )
        if not complete:
            st.warning("Some AI assessments failed. Your answers and completed assessments were preserved.")
        st.rerun()


def _render_completed(attempt: dict, items: list[dict]) -> None:
    st.subheader("Quiz result")
    left, right = st.columns(2)
    left.metric("Score", f"{attempt['percentage_correct']:.1f}%")
    right.metric("Result", "Passed" if attempt["passed"] else "Not passed")
    st.caption("Pass threshold: 80%. Coding scores are AI estimates; learner code was not executed.")
    for item in items:
        with st.container(border=True):
            st.markdown(f"### {item['position']}. {item['title']} · {item['percentage_correct']:.1f}%")
            if item["answer_format"] == "mcq":
                options = {option["id"]: option["text"] for option in item.get("options") or []}
                chosen = item.get("selected_option_id")
                st.write(f"Your answer: {options.get(chosen, 'Unanswered')}")
                st.success(f"Correct answer: {options.get(item['correct_option_id'], item['correct_option_id'])}")
                st.info(item.get("explanation") or "No explanation was provided.")
            else:
                st.code(
                    item.get("answer_text") or "// Unanswered",
                    language=syntax_language(item["method"]),
                )
                feedback = item.get("ai_feedback")
                if isinstance(feedback, str):
                    try:
                        feedback = json.loads(feedback)
                    except json.JSONDecodeError:
                        feedback = None
                if feedback:
                    st.markdown(feedback.get("explanation", ""))
                    for mistake in feedback.get("identified_mistakes", []):
                        st.warning(mistake)
                    if feedback.get("suggested_correction"):
                        st.info(feedback["suggested_correction"])
    if st.button("New quiz"):
        st.session_state["active_quiz_attempt_id"] = None
        for key in [key for key in st.session_state if key.startswith("quiz_answer_")]:
            del st.session_state[key]
        st.rerun()
