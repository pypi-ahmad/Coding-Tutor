"""Global provider and learning controls for the practice interface."""
from __future__ import annotations

import streamlit as st

from coding_tutor.catalog import CatalogProfile, get_catalog_profile
from coding_tutor.database.connection import get_db
from coding_tutor.methods import METHODS_BY_QUESTION_TYPE, method_label
from coding_tutor.providers.config import get_models_for_provider
from coding_tutor.providers.registry import PROVIDERS, PROVIDER_DISPLAY_NAMES
from coding_tutor.quiz.session import request_learning_change, resolve_pending_learning_change

QUESTION_TYPES = ["algorithm", "data_analysis"]
DIFFICULTIES = ["Beginner", "Easy", "Medium", "Hard", "Very Hard"]
ALGORITHM_METHODS = list(METHODS_BY_QUESTION_TYPE["algorithm"])
DATA_ANALYSIS_METHODS = list(METHODS_BY_QUESTION_TYPE["data_analysis"])


def _available_topics(conn, question_type: str, difficulty: str, method: str) -> list[str]:
    rows = conn.execute(
        """SELECT DISTINCT unnest(json_extract_string(tags, '$[*]')) AS topic
           FROM questions
           WHERE question_type = ? AND difficulty = ? AND is_complete = true
             AND is_ai_generated = false
             AND json_contains(supported_methods, to_json(?))
           ORDER BY topic""",
        [question_type, difficulty, method],
    ).fetchall()
    return [str(row[0]) for row in rows if row[0] is not None]


def _format_topic(value) -> str:
    return "Any topic" if value == "general" else str(value)


def _available_difficulties(conn, question_type: str, method: str) -> list[str]:
    rows = conn.execute(
        """SELECT DISTINCT difficulty
           FROM questions
           WHERE question_type = ? AND is_complete = true
             AND is_ai_generated = false
             AND json_contains(supported_methods, to_json(?))""",
        [question_type, method],
    ).fetchall()
    available = {row[0] for row in rows}
    return [difficulty for difficulty in DIFFICULTIES if difficulty in available]


def _learning_modes(
    conn, profile: CatalogProfile, question_type: str, method: str,
) -> tuple[str, ...]:
    if question_type != "data_analysis" or profile.learning_modes == ("ai_generated",):
        return profile.learning_modes
    curated_exists = conn.execute(
        """SELECT 1 FROM questions
           WHERE question_type = 'data_analysis' AND is_complete = true
             AND is_ai_generated = false
             AND json_contains(supported_methods, to_json(?))
           LIMIT 1""",
        [method],
    ).fetchone()
    return profile.learning_modes if curated_exists else ("ai_generated",)


def _on_question_type_change() -> None:
    request_learning_change("question_type", st.session_state["question_type_control"])


def _on_method_change() -> None:
    request_learning_change("method", st.session_state["method_control"])


@st.dialog("Unsaved code", dismissible=False, icon=":material/warning:")
def render_pending_learning_change_dialog() -> None:
    pending = st.session_state.get("pending_learning_change")
    if not pending:
        return
    label = pending["setting"].replace("_", " ")
    st.write(
        f"Changing {label} will replace the active editor. "
        "Keep the draft for this question and method, or discard it explicitly."
    )
    if st.button("Keep draft and switch", type="primary", width="stretch"):
        resolve_pending_learning_change("keep", defer_controls=True)
        st.rerun()
    if st.button("Discard draft and switch", width="stretch"):
        resolve_pending_learning_change("discard", defer_controls=True)
        st.rerun()
    if st.button("Cancel", width="stretch"):
        resolve_pending_learning_change("cancel", defer_controls=True)
        st.rerun()


def render_sidebar(profile: CatalogProfile | None = None):
    profile = profile or get_catalog_profile()
    with st.sidebar:
        st.header(":material/settings: Settings")

        st.subheader("AI provider")
        provider_name = st.selectbox(
            "Provider", options=list(PROVIDERS),
            format_func=lambda key: PROVIDER_DISPLAY_NAMES[key],
            key="selected_provider_name",
        )
        provider = PROVIDERS[provider_name]
        if provider.is_configured():
            st.success(f"{PROVIDER_DISPLAY_NAMES[provider_name]} configuration available.")
        else:
            st.warning(
                f"{PROVIDER_DISPLAY_NAMES[provider_name]} configuration unavailable. "
                "Set its API key in the system environment and restart the app."
            )

        models = get_models_for_provider(provider_name)
        verified_models = [model for model in models if model.verified]
        if verified_models:
            selected_index = st.selectbox(
                "Model", options=range(len(verified_models)),
                format_func=lambda index: verified_models[index].display_name,
                key="selected_model_idx",
            )
            selected_model = verified_models[selected_index]
        else:
            st.info("No verified models are available for this provider.")
            selected_model = None

        for unavailable_model in (model for model in models if not model.verified):
            st.warning(
                f"**{unavailable_model.display_name} is unavailable.** "
                f"{unavailable_model.unverified_reason} "
                f"[Official model documentation]({unavailable_model.documentation_url})"
            )
        st.session_state["provider"] = provider_name
        st.session_state["model"] = selected_model

        from coding_tutor.web_research import firecrawl_access_mode

        web_mode = firecrawl_access_mode()
        st.caption(
            "Web research: authenticated Firecrawl MCP"
            if web_mode == "authenticated"
            else "Web research: keyless Firecrawl MCP (limited)"
        )

        page = st.session_state.get("nav_page", "Coding")
        if page not in {"Coding", "Quiz"}:
            st.divider()
            st.caption("AI Questions and Interview use the interview catalog.")
            return

        st.divider()
        st.subheader("Learning")
        if profile.question_type is None:
            st.selectbox(
                "Question type", QUESTION_TYPES,
                format_func=lambda value: value.replace("_", " ").title(),
                key="question_type_control", on_change=_on_question_type_change,
            )
            question_type = st.session_state.get("question_type", "algorithm")
        else:
            question_type = profile.question_type
            st.caption(f"Catalog: {question_type.replace('_', ' ').title()}")
        methods = list(METHODS_BY_QUESTION_TYPE[question_type])
        if st.session_state.get("method_control") not in methods:
            candidate = st.session_state.get("method", methods[0])
            st.session_state["method_control"] = candidate if candidate in methods else methods[0]
        method = st.session_state.get("method", methods[0])
        st.selectbox(
            "Language or method", methods, format_func=method_label,
            key="method_control", on_change=_on_method_change,
        )
        method = st.session_state.get("method", methods[0])

        learning_modes = _learning_modes(get_db(), profile, question_type, method)
        if st.session_state.get("question_source") not in learning_modes:
            st.session_state["question_source"] = learning_modes[0]
        if len(learning_modes) == 1:
            source = learning_modes[0]
            st.caption("Learning mode: AI generated")
        else:
            source = st.segmented_control(
                "Learning mode", options=list(learning_modes),
                format_func=lambda value: {
                    "dataset": "Curated questions", "ai_generated": "AI generated", "mixed": "Mixed",
                }[value],
                key="question_source", required=True, width="stretch",
            )

        difficulty_options = DIFFICULTIES
        if source in {"dataset", "curated"}:
            available = _available_difficulties(get_db(), question_type, method)
            if available:
                difficulty_options = available
        if st.session_state.get("difficulty") not in difficulty_options:
            st.session_state["difficulty"] = difficulty_options[0]
        st.selectbox("Difficulty", difficulty_options, key="difficulty")

        topics = _available_topics(
            get_db(), question_type, st.session_state.get("difficulty", "Easy"),
            st.session_state.get("method", methods[0]),
        )
        topic_options = ["general", *topics]
        topic_key = f"topic_control_{source}"
        current_topic = st.session_state.get("topic", "general")
        if topic_key not in st.session_state:
            st.session_state[topic_key] = current_topic if current_topic in topic_options else "general"
        elif source == "dataset" and st.session_state[topic_key] not in topic_options:
            st.session_state[topic_key] = "general"
        selected_topic = st.selectbox(
            "Topic", topic_options, key=topic_key,
            format_func=_format_topic,
            accept_new_options=source in {"ai_generated", "mixed"},
            help="Choose an imported tag or type a custom topic when AI generation is available.",
        )
        st.session_state["topic"] = selected_topic or "general"

        st.toggle(
            "Web research",
            value=False,
            key="web_research_enabled",
            disabled=source in {"dataset", "curated"},
            help="When enabled, AI generation can use Firecrawl if local references do not cover the topic.",
        )

        if st.session_state.get("nav_page") == "Quiz":
            st.divider()
            st.subheader("Quiz setup")
            st.number_input(
                "Total questions", min_value=1, max_value=10, step=1,
                key="quiz_total_items",
            )
            total = int(st.session_state.get("quiz_total_items", 1))
            if int(st.session_state.get("quiz_coding_items", 1)) > total:
                st.session_state["quiz_coding_items"] = total
            st.number_input(
                "Coding questions", min_value=0, max_value=total, step=1,
                key="quiz_coding_items",
            )
            coding = int(st.session_state.get("quiz_coding_items", 1))
            st.caption(f"Multiple-choice questions: {total - coding}")
            st.caption("Untimed · equal weighting · pass at 80% · no negative marking")
