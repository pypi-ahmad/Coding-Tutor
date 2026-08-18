"""Main learning interface page."""
import json
import streamlit as st
from coding_tutor.database.connection import get_db
from coding_tutor.quiz.session import (
    get_current_question, load_question, clear_question_with_confirm
)


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
    source = st.session_state.get("question_source", "curated")

    if source == "curated":
        _pick_curated_question()
    else:
        _pick_generated_question()


def _pick_curated_question():
    conn = get_db()
    q_type = st.session_state.get("question_type", "algorithm")
    difficulty = st.session_state.get("difficulty", "Easy")

    rows = conn.execute(
        """SELECT id, title, difficulty, tags
           FROM questions
           WHERE question_type = ? AND difficulty = ? AND is_complete = true
           ORDER BY RANDOM() LIMIT 20""",
        [q_type, difficulty],
    ).fetchall()

    if not rows:
        st.info(
            f"No {q_type.replace('_', ' ')} questions at {difficulty} difficulty. "
            "Try a different difficulty or import datasets."
        )
        return

    options = {f"{r[1]} ({r[2]})": r[0] for r in rows}
    selected = st.selectbox("Choose a question", list(options.keys()))
    if st.button("Load Question", type="primary"):
        load_question(str(options[selected]))
        st.rerun()


def _pick_generated_question():
    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")
    if not provider_name or not model or not model.verified:
        st.warning("Select a verified AI provider and model in the sidebar to generate questions.")
        return
    st.info("AI question generation is available — click Generate to create a new question.")
    if st.button("Generate Question", type="primary"):
        from coding_tutor.generation.generator import generate_question
        with st.spinner("Generating question..."):
            q_id = generate_question(
                provider_name=provider_name,
                model=model,
                question_type=st.session_state.get("question_type", "algorithm"),
                difficulty=st.session_state.get("difficulty", "Easy"),
                method=st.session_state.get("method", "python"),
            )
        if q_id:
            load_question(q_id)
            st.rerun()


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

    tags = question.get("tags") or []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    if tags:
        st.markdown(" ".join(f"`{t}`" for t in tags[:8]))

    st.divider()

    st.markdown(question.get("problem_statement", ""))

    if question.get("question_type") == "data_analysis":
        _render_data_analysis_assets(question)

    examples = question.get("examples") or []
    if isinstance(examples, str):
        try:
            examples = json.loads(examples)
        except Exception:
            examples = []
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

    # Handle show-solution trigger
    if st.session_state.get("show_solution_trigger"):
        st.session_state.show_solution_trigger = False
        attempt_id = st.session_state.get("last_attempt_id")
        from coding_tutor.ui.solution_view import render_solution_view
        render_solution_view(question, attempt_id)


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
                    else:
                        st.code(a[2])
                except Exception:
                    st.code(a[2])

    if expected_assets:
        with st.expander("Expected Output Format"):
            for a in expected_assets:
                st.code(a[2])

    if not question.get("is_complete"):
        st.warning(
            "⚠️ This question was imported without executable fixture data. "
            "It can be used for reference study, but automated test execution is unavailable."
        )


def _render_editor(question: dict):
    method = st.session_state.get("method", "python")

    st.subheader(f"Your Solution ({method.upper()})")

    q_id = question["id"]
    editor_key = f"editor_{q_id}_{method}"
    if editor_key not in st.session_state:
        starter = _get_starter_code(q_id, method)
        st.session_state[editor_key] = starter

    code = st.text_area(
        "Code editor",
        value=st.session_state[editor_key],
        height=300,
        key=f"code_input_{q_id}_{method}",
        label_visibility="collapsed",
    )
    st.session_state[editor_key] = code
    st.session_state.editor_content = code


def _render_action_panel(question: dict):
    st.subheader("Actions")

    method = st.session_state.get("method", "python")
    q_id = question["id"]
    editor_key = f"editor_{q_id}_{method}"
    has_code = bool(st.session_state.get(editor_key, "").strip())

    if st.button("✅ Done", type="primary", disabled=not has_code, use_container_width=True):
        st.session_state.submit_trigger = True
        st.rerun()

    if st.button("💡 Show Solution", use_container_width=True):
        st.session_state.show_solution_trigger = True
        st.rerun()

    st.divider()

    if st.button("← Back to question list", use_container_width=True):
        clear_question_with_confirm()
        st.rerun()

    _render_method_switch_guard(question)


def _render_method_switch_guard(question: dict):
    """Warn before switching method if editor has unsaved content."""
    # Method switching triggers a full rerun via sidebar widget;
    # editor content is keyed per question+method so it is preserved automatically.
    pass


def _get_starter_code(question_id: str, method: str) -> str:
    """Fetch starter code from DB asset, or return a language-appropriate template."""
    conn = get_db()
    row = conn.execute(
        "SELECT content FROM question_assets WHERE question_id = ? AND asset_type = 'starter_code' AND method = ?",
        [question_id, method],
    ).fetchone()
    if row:
        return row[0]

    templates = {
        "python": "def solution():\n    # Write your solution here\n    pass\n",
        "sql": "-- Write your SQL query here\nSELECT \n",
        "pandas": (
            "import pandas as pd\n\n"
            "def solution(df: pd.DataFrame) -> pd.DataFrame:\n"
            "    # Write your Pandas solution here\n"
            "    return df\n"
        ),
        "pyspark": (
            "from pyspark.sql import DataFrame\n\n"
            "def solution(spark, df: DataFrame) -> DataFrame:\n"
            "    # Write your PySpark solution here\n"
            "    return df\n"
        ),
        "polars": (
            "import polars as pl\n\n"
            "def solution(df: pl.DataFrame) -> pl.DataFrame:\n"
            "    # Write your Polars solution here\n"
            "    return df\n"
        ),
    }
    return templates.get(method, "# Write your solution here\n")
