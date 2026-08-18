"""Main learning interface page."""
import json
import streamlit as st
from coding_tutor.database.connection import get_db
from coding_tutor.quiz.session import (
    clear_question_with_confirm, editor_baseline_key, editor_key,
    get_current_question, load_question,
)
from coding_tutor.quiz.templates import get_editor_template


def render_main_page():
    st.title("🎓 Coding Tutor")

    question = get_current_question()

    col_main, col_side = st.columns([3, 1])

    with col_main:
        if question is None:
            _render_question_picker()
        else:
            _render_question(question)

    with col_side:
        if question:
            _render_action_panel(question)


def _render_question_picker():
    st.subheader("Select a Question")
    source = st.session_state.get("question_source", "dataset")

    if source in {"dataset", "curated"}:
        _pick_dataset_question()
    elif source == "ai_generated":
        _pick_generated_question()
    else:
        _pick_mixed_question()


def _dataset_rows(conn, question_type: str, difficulty: str, method: str,
                  topic: str = "general", limit: int = 20):
    return conn.execute(
        """SELECT id, title, difficulty, tags
           FROM questions
           WHERE question_type = ? AND difficulty = ? AND is_complete = true
             AND is_ai_generated = false
             AND json_contains(supported_methods, to_json(?))
             AND (? = 'general' OR json_contains(tags, to_json(?)))
           ORDER BY title, id LIMIT ?""",
        [question_type, difficulty, method, topic, topic, limit],
    ).fetchall()


def _dataset_count(conn, question_type: str, difficulty: str, method: str,
                   topic: str = "general") -> int:
    return conn.execute(
        """SELECT COUNT(*) FROM questions
           WHERE question_type = ? AND difficulty = ? AND is_complete = true
             AND is_ai_generated = false
             AND json_contains(supported_methods, to_json(?))
             AND (? = 'general' OR json_contains(tags, to_json(?)))""",
        [question_type, difficulty, method, topic, topic],
    ).fetchone()[0]


def _ai_unavailable_reason(provider_name, model) -> str | None:
    if not provider_name:
        return "Select an AI provider."
    if not model:
        return "The selected provider has no verified model available."
    if not model.verified:
        return "The selected model is not verified for API use."
    from coding_tutor.providers.registry import get_provider
    try:
        provider = get_provider(provider_name)
    except KeyError:
        return "The selected AI provider is unavailable."
    if not provider.is_configured():
        return "The selected provider is not configured. Set its API key in the system environment."
    return None


def _ai_available(provider_name, model) -> bool:
    return _ai_unavailable_reason(provider_name, model) is None


def _choose_mixed_source(has_dataset: bool, has_ai: bool, random_value=None):
    if has_dataset and has_ai:
        if random_value is None:
            import random
            random_value = random.random()
        return "ai" if random_value < 0.5 else "dataset"
    if has_ai:
        return "ai"
    if has_dataset:
        return "dataset"
    return None


def _generate_selected_question(provider_name, model, question_type, difficulty, method, topic):
    from coding_tutor.generation.generator import generate_question
    return generate_question(
        provider_name=provider_name,
        model=model,
        question_type=question_type,
        difficulty=difficulty,
        method=method,
        topic=topic.strip() or "general",
    )


def _generation_failure_message(result) -> str:
    from coding_tutor.generation.generator import GenerationFailure

    messages = {
        GenerationFailure.INVALID_SELECTION: "The generation settings are invalid. Reselect them and try again.",
        GenerationFailure.MODEL_UNAVAILABLE: "Select a verified model before generating a question.",
        GenerationFailure.PROVIDER_UNAVAILABLE: "The selected provider is not configured. Set its API key in the system environment.",
        GenerationFailure.PROVIDER_ERROR: "The provider request failed. Check network access, credentials, quota, and model access.",
        GenerationFailure.MALFORMED_RESPONSE: "The provider returned malformed JSON. Nothing was saved.",
        GenerationFailure.INCOMPLETE_RESPONSE: "The provider returned an incomplete or invalid question. Nothing was saved.",
        GenerationFailure.STORAGE_ERROR: "The valid question could not be saved locally. No partial question was kept.",
    }
    return messages.get(result.failure, "Question generation failed. Nothing was saved.")


def _pick_dataset_question():
    conn = get_db()
    q_type = st.session_state.get("question_type", "algorithm")
    difficulty = st.session_state.get("difficulty", "Easy")
    method = st.session_state.get("method", "python")
    topic = st.session_state.get("topic", "general")

    rows = _dataset_rows(conn, q_type, difficulty, method, topic)

    if not rows:
        st.info(
            f"No curated {q_type.replace('_', ' ')} questions for {method.upper()} at {difficulty} difficulty. "
            "Try a different difficulty or import datasets."
        )
        return

    options = {str(r[0]): f"{r[1]} ({r[2]})" for r in rows}
    selected = st.selectbox("Choose a question", list(options), format_func=options.get)
    if st.button("Load Question", type="primary"):
        load_question(selected)
        st.rerun()


def _pick_generated_question():
    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")
    unavailable_reason = _ai_unavailable_reason(provider_name, model)
    if unavailable_reason:
        st.warning(unavailable_reason)
        return
    st.info("AI question generation is available — click Generate to create a new question.")
    if st.button("Generate Question", type="primary"):
        with st.spinner("Generating question..."):
            result = _generate_selected_question(
                provider_name, model,
                st.session_state.get("question_type", "algorithm"),
                st.session_state.get("difficulty", "Easy"),
                st.session_state.get("method", "python"),
                st.session_state.get("topic", "general"),
            )
        if result.ok:
            load_question(result.question_id)
            st.rerun()
        else:
            st.error(_generation_failure_message(result))


def _pick_mixed_question():
    conn = get_db()
    q_type = st.session_state.get("question_type", "algorithm")
    difficulty = st.session_state.get("difficulty", "Easy")
    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")

    method = st.session_state.get("method", "python")
    topic = st.session_state.get("topic", "general")
    unavailable_reason = _ai_unavailable_reason(provider_name, model)
    has_ai = unavailable_reason is None
    dataset_count = _dataset_count(conn, q_type, difficulty, method, topic)

    if not has_ai and not dataset_count:
        st.warning(
            "Mixed mode needs either imported curated questions or a verified AI provider. "
            "Import datasets or configure an API key in the sidebar."
        )
        return

    if has_ai and dataset_count:
        st.info("Mixed mode chooses a dataset or fresh AI question with equal probability.")
    elif dataset_count:
        st.info(f"Mixed mode is using curated questions. {unavailable_reason}")
    else:
        st.info("🎲 Mixed mode — using AI generation (no curated questions at this difficulty).")

    if st.button("Get Question", type="primary"):
        use_ai = _choose_mixed_source(bool(dataset_count), has_ai) == "ai"
        if use_ai:
            with st.spinner("Generating question..."):
                result = _generate_selected_question(
                    provider_name, model, q_type, difficulty, method, topic
                )
            q_id = result.question_id
        else:
            row = conn.execute(
                """SELECT id FROM questions
                   WHERE question_type = ? AND difficulty = ? AND is_complete = true
                     AND is_ai_generated = false
                     AND json_contains(supported_methods, to_json(?))
                     AND (? = 'general' OR json_contains(tags, to_json(?)))
                   ORDER BY RANDOM() LIMIT 1""",
                [q_type, difficulty, method, topic, topic],
            ).fetchone()
            q_id = str(row[0]) if row else None

        if q_id:
            load_question(q_id)
            st.rerun()
        elif use_ai:
            st.error(_generation_failure_message(result))


def _render_question(question: dict):
    diff_colors = {
        "Beginner": "🟢", "Easy": "🟢", "Medium": "🟡",
        "Hard": "🔴", "Very Hard": "🟣",
    }
    icon = diff_colors.get(question.get("difficulty", "Medium"), "⚪")
    st.markdown(f"## {question['title']}")
    st.markdown(
        f"{icon} **{question.get('difficulty', 'Medium')}** · "
        f"`{question.get('question_type','').replace('_',' ').title()}`"
    )
    if question.get("source_kind") == "dataset":
        source = question.get("dataset_name") or "Local dataset"
        details = " · ".join(x for x in [question.get("attribution"), question.get("license")] if x)
        st.caption(f"Source: {source}" + (f" · {details}" if details else ""))
    elif question.get("source_kind") == "ai_generated":
        st.caption(f"Source: AI generated · {question.get('generation_provider', 'unknown')}/{question.get('generation_model', 'unknown')}")

    tags = question.get("tags") or []
    if tags:
        st.markdown(" ".join(f"`{t}`" for t in tags[:8]))

    st.divider()

    st.markdown(question.get("problem_statement", ""))

    if question.get("question_type") == "data_analysis":
        _render_data_analysis_assets(question)

    examples = question.get("examples") or []
    if examples:
        with st.expander("Examples", expanded=True):
            for i, ex in enumerate(examples[:3], 1):
                if isinstance(ex, dict):
                    st.markdown(f"**Example {i}:**")
                    if "input" in ex:
                        st.code(f"Input: {ex['input']}", language="text")
                    if "output" in ex or "expected_output" in ex:
                        st.code(
                            f"Output: {ex.get('output', ex.get('expected_output', ''))}",
                            language="text",
                        )
                elif isinstance(ex, str):
                    st.code(ex, language="text")

    if question.get("constraints"):
        with st.expander("Constraints"):
            st.markdown(question["constraints"])

    st.divider()
    _render_editor(question)

    # Handle submit trigger (Done button)
    if st.session_state.get("submit_trigger"):
        method = st.session_state.get("method", "python")
        from coding_tutor.ui.submit_handler import handle_submit
        handle_submit(question, method)

    _render_active_assessment(question)

    panel = st.session_state.get("solution_panel")
    if isinstance(panel, dict) and panel.get("question_id") == str(question["id"]):
        from coding_tutor.ui.solution_view import render_solution_view
        render_solution_view(question, panel)


def _render_active_assessment(question: dict) -> None:
    active = st.session_state.get("active_assessment")
    method = st.session_state.get("method", "python")
    if (
        not isinstance(active, dict)
        or active.get("question_id") != str(question["id"])
        or active.get("method") != method
    ):
        return

    from coding_tutor.ui.evaluation_view import render_evaluation

    render_evaluation(
        question,
        active["assessment"],
        active["attempt_id"],
        method,
    )


def _render_data_analysis_assets(question: dict):
    conn = get_db()
    q_id = question["id"]
    assets = conn.execute(
        "SELECT asset_type, method, content, content_type FROM question_assets WHERE question_id = ?",
        [q_id],
    ).fetchall()

    schema_assets = [a for a in assets if a[0] == "schema" and (a[1] is None or a[1] == "shared")]
    fixture_assets = [a for a in assets if a[0] == "fixture_data"]
    expected_assets = [a for a in assets if a[0] == "expected_result"]

    if schema_assets:
        with st.expander("Schema", expanded=True):
            for a in schema_assets:
                lang = "sql" if a[3] == "sql" else "text"
                st.code(a[2], language=lang)

    if fixture_assets:
        with st.expander("Sample Data"):
            for a in fixture_assets:
                try:
                    import pandas as pd
                    data = json.loads(a[2])
                    if isinstance(data, list) and data:
                        st.dataframe(pd.DataFrame(data).head(5))
                    elif isinstance(data, dict) and data:
                        for table_name, rows in data.items():
                            st.markdown(f"**{table_name}**")
                            st.dataframe(pd.DataFrame(rows).head(5))
                    else:
                        st.code(a[2])
                except Exception:
                    st.code(a[2])

    if expected_assets:
        with st.expander("Expected Output Format"):
            for a in expected_assets:
                st.code(a[2])

    if not question.get("is_complete"):
        st.info("This imported question has limited reference context; AI assessment is still available.")


def _render_editor(question: dict):
    method = st.session_state.get("method", "python")

    st.subheader(f"Your Solution ({method.upper()})")

    q_id = question["id"]
    content_key = editor_key(q_id, method)
    baseline_key = editor_baseline_key(q_id, method)
    starter = _get_starter_code(q_id, method)
    st.session_state.setdefault(content_key, starter)
    st.session_state.setdefault(baseline_key, starter)

    code = st.text_area(
        "Code editor",
        height=300,
        key=content_key,
        label_visibility="collapsed",
    )
    st.session_state.editor_content = code


def _render_action_panel(question: dict):
    st.subheader("Actions")

    method = st.session_state.get("method", "python")
    q_id = question["id"]
    content_key = editor_key(q_id, method)
    has_code = bool(st.session_state.get(content_key, "").strip())

    if st.button("✅ Done", type="primary", disabled=not has_code, width="stretch"):
        st.session_state.submit_trigger = True
        st.rerun()

    panel = st.session_state.get("solution_panel")
    panel_open = isinstance(panel, dict) and panel.get("question_id") == str(q_id)
    if st.button("Hide Solutions" if panel_open else "💡 Show Solution", width="stretch"):
        if panel_open:
            st.session_state.pop("solution_panel", None)
        else:
            st.session_state.solution_panel = {
                "question_id": str(q_id),
                "attempt_id": st.session_state.get("last_attempt_id"),
                "view_id": None,
            }
        st.rerun()

    st.divider()

    if st.button("← Back to question list", width="stretch"):
        clear_question_with_confirm()
        st.rerun()

def _get_starter_code(question_id: str, method: str) -> str:
    """Fetch starter code from DB asset, or return a language-appropriate template."""
    conn = get_db()
    row = conn.execute(
        "SELECT content FROM question_assets WHERE question_id = ? AND asset_type = 'starter_code' AND method = ?",
        [question_id, method],
    ).fetchone()
    if row:
        return row[0]

    return get_editor_template(method)
