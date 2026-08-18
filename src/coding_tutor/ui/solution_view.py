"""Solution viewer — shows reference and AI-generated solutions with teaching explanations."""
from __future__ import annotations
import json
import logging
import streamlit as st
from typing import Optional

logger = logging.getLogger(__name__)


def render_solution_view(question: dict, attempt_id: Optional[str] = None):
    """Render the solution panel when learner clicks 'Show Solution'."""
    st.subheader("💡 Solutions")

    q_id = question["id"]
    q_type = question.get("question_type", "algorithm")
    supported = question.get("supported_methods") or []
    if isinstance(supported, str):
        try:
            supported = json.loads(supported)
        except Exception:
            supported = []

    methods_viewed = []
    dataset_solutions = _get_dataset_solutions(q_id)

    if q_type == "algorithm":
        methods_viewed = _show_algorithm_solutions(question, dataset_solutions)
    else:
        methods_viewed = _show_data_analysis_solutions(question, dataset_solutions, supported)

    _record_solution_view(q_id, attempt_id, methods_viewed)

    provider_name = st.session_state.get("provider")
    model = st.session_state.get("model")
    if provider_name and model and model.verified:
        with st.expander("🤖 AI Teaching Explanation", expanded=False):
            _render_ai_explanation(question)


def _get_dataset_solutions(question_id: str) -> dict:
    from coding_tutor.database.connection import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT method, code, is_from_dataset, explanation FROM reference_solutions WHERE question_id = ?",
        [question_id],
    ).fetchall()
    return {r[0]: {"code": r[1], "is_from_dataset": r[2], "explanation": r[3]} for r in rows}


def _show_algorithm_solutions(question: dict, dataset_solutions: dict) -> list[str]:
    methods_viewed = []

    if "python" in dataset_solutions:
        sol = dataset_solutions["python"]
        tag = "📚 Dataset Reference" if sol["is_from_dataset"] else "🤖 AI Generated"
        st.markdown(f"#### Python Solution {tag}")
        st.code(sol["code"], language="python")
        if sol.get("explanation"):
            st.info(sol["explanation"])
        methods_viewed.append("python")
    else:
        provider_name = st.session_state.get("provider")
        model = st.session_state.get("model")
        if provider_name and model and model.verified:
            st.markdown("#### Python Solution (AI Generated)")
            _fetch_and_show_ai_solution(question, "python")
            methods_viewed.append("python")
        else:
            st.info("No reference solution available. Configure an AI provider to generate one.")

    return methods_viewed


def _show_data_analysis_solutions(question: dict, dataset_solutions: dict, supported: list) -> list[str]:
    methods_viewed = []

    method_tabs = st.tabs([m.upper() for m in supported]) if supported else []

    for tab, method in zip(method_tabs, supported):
        with tab:
            if method in dataset_solutions:
                sol = dataset_solutions[method]
                tag = "📚 Dataset Reference" if sol["is_from_dataset"] else "🤖 AI Generated"
                st.markdown(f"**{tag}**")
                lang = "sql" if method == "sql" else "python"
                st.code(sol["code"], language=lang)
                if sol.get("explanation"):
                    st.info(sol["explanation"])
                methods_viewed.append(method)
            else:
                provider_name = st.session_state.get("provider")
                model = st.session_state.get("model")
                if provider_name and model and model.verified:
                    _fetch_and_show_ai_solution(question, method)
                    methods_viewed.append(method)
                else:
                    st.info(f"No {method.upper()} reference solution available.")

    return methods_viewed


def _fetch_and_show_ai_solution(question: dict, method: str):
    """Call AI to generate a solution and show it."""
    cache_key = f"ai_solution_{question['id']}_{method}"
    if cache_key not in st.session_state:
        provider_name = st.session_state.get("provider")
        model = st.session_state.get("model")
        if not provider_name or not model or not model.verified:
            st.warning("Configure a verified AI provider to generate solutions.")
            return

        with st.spinner(f"Generating {method.upper()} solution..."):
            from coding_tutor.providers.registry import get_provider
            from coding_tutor.providers.base import ChatMessage

            provider = get_provider(provider_name)
            prompt = _build_solution_prompt(question, method)
            try:
                response = provider.chat(
                    messages=[ChatMessage(role="user", content=prompt)],
                    model=model,
                    system_prompt=_solution_system_prompt(method),
                )
                st.session_state[cache_key] = response.content
            except Exception as exc:
                st.error(f"Failed to generate solution: {exc}")
                return

    content = st.session_state.get(cache_key, "")
    if content:
        lang = "sql" if method == "sql" else "python"
        if "```" in content:
            import re
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
            for block in code_blocks:
                st.code(block.strip(), language=lang)
            explanation = re.sub(r"```(?:\w+)?\n.*?```", "", content, flags=re.DOTALL).strip()
            if explanation:
                st.markdown(explanation)
        else:
            st.markdown(content)


def _solution_system_prompt(method: str) -> str:
    return (
        f"You are a patient, experienced coding teacher. "
        f"Provide a well-commented {method.upper()} solution with step-by-step explanation. "
        f"Teach the reasoning, not just the code. Do not expose internal chain-of-thought."
    )


def _build_solution_prompt(question: dict, method: str) -> str:
    from coding_tutor.database.connection import get_db
    conn = get_db()

    schema = ""
    row = conn.execute(
        "SELECT content FROM question_assets WHERE question_id = ? AND asset_type = 'schema' LIMIT 1",
        [question["id"]],
    ).fetchone()
    if row:
        schema = f"\n\nSchema:\n{row[0]}"

    return (
        f"Problem: {question['title']}\n\n"
        f"{question.get('problem_statement', '')}"
        f"{schema}\n\n"
        f"Provide a complete, well-commented {method.upper()} solution with a teaching explanation. "
        f"Explain the approach, key steps, and complexity where relevant."
    )


def _render_ai_explanation(question: dict):
    cache_key = f"ai_explain_{question['id']}"
    if cache_key not in st.session_state:
        provider_name = st.session_state.get("provider")
        model = st.session_state.get("model")
        if not provider_name or not model:
            return

        with st.spinner("Generating explanation..."):
            from coding_tutor.providers.registry import get_provider
            from coding_tutor.providers.base import ChatMessage

            provider = get_provider(provider_name)
            prompt = (
                f"Explain the key concepts and approaches for solving this problem. "
                f"Act as a teacher. Do not show code — focus on theory and reasoning.\n\n"
                f"Problem: {question['title']}\n{question.get('problem_statement','')[:500]}"
            )
            try:
                response = provider.chat(
                    messages=[ChatMessage(role="user", content=prompt)],
                    model=model,
                    system_prompt="You are a coding teacher. Explain concepts clearly and concisely.",
                )
                st.session_state[cache_key] = response.content
            except Exception as exc:
                st.warning(f"Explanation unavailable: {exc}")
                return

    content = st.session_state.get(cache_key, "")
    if content:
        st.markdown(content)


def _record_solution_view(question_id: str, attempt_id: Optional[str], methods_viewed: list):
    if not methods_viewed:
        return
    try:
        import json
        from coding_tutor.database.connection import get_db
        conn = get_db()
        conn.execute(
            """INSERT INTO solution_views (question_id, attempt_id, methods_viewed)
               VALUES (?, ?, ?)""",
            [question_id, attempt_id, json.dumps(methods_viewed)],
        )
        conn.commit()
    except Exception as exc:
        logger.warning("Failed to record solution view: %s", exc)
