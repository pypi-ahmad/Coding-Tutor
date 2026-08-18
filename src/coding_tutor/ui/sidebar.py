import streamlit as st
from coding_tutor.providers.registry import PROVIDERS, PROVIDER_DISPLAY_NAMES
from coding_tutor.providers.config import get_models_for_provider

QUESTION_TYPES = ["algorithm", "data_analysis"]
DIFFICULTIES = ["Beginner", "Easy", "Medium", "Hard", "Very Hard"]
ALGORITHM_METHODS = ["python"]
DATA_ANALYSIS_METHODS = ["sql", "pandas", "pyspark", "polars"]


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Settings")

        # Provider selection
        st.subheader("AI Provider")
        provider_name = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            format_func=lambda k: PROVIDER_DISPLAY_NAMES[k],
            key="selected_provider_name",
        )
        provider = PROVIDERS[provider_name]
        configured = provider.is_configured()
        if configured:
            st.success(f"{PROVIDER_DISPLAY_NAMES[provider_name]} configured ✓")
        else:
            st.warning(f"{PROVIDER_DISPLAY_NAMES[provider_name]}: API key not set")

        # Model selection
        models = get_models_for_provider(provider_name)
        verified_models = [m for m in models if m.verified]
        unverified_models = [m for m in models if not m.verified]

        model_options = [m.display_name for m in verified_models]
        disabled_display = [f"⚠️ {m.display_name} (unverified)" for m in unverified_models]

        all_display = model_options + disabled_display
        all_models = verified_models + unverified_models

        if not all_display:
            st.info("No models available for this provider.")
            selected_model = None
        else:
            selected_idx = st.selectbox(
                "Model",
                options=range(len(all_display)),
                format_func=lambda i: all_display[i],
                key="selected_model_idx",
            )
            selected_model = all_models[selected_idx]
            if not selected_model.verified:
                st.error(f"Unverified: {selected_model.unverified_reason}")

        st.session_state.provider = provider_name
        st.session_state.model = selected_model

        st.divider()

        # Learning settings
        st.subheader("Learning")
        q_type = st.selectbox(
            "Question Type",
            options=QUESTION_TYPES,
            format_func=lambda t: t.replace("_", " ").title(),
            key="question_type",
        )

        st.selectbox("Difficulty", DIFFICULTIES, key="difficulty")

        if q_type == "algorithm":
            st.selectbox("Method", ALGORITHM_METHODS, format_func=str.upper, key="method")
        else:
            st.selectbox("Method", DATA_ANALYSIS_METHODS, format_func=str.upper, key="method")

        st.divider()
        st.subheader("Question Source")
        st.radio(
            "Source",
            options=["curated", "ai_generated"],
            format_func=lambda s: "Curated Dataset" if s == "curated" else "AI Generated",
            key="question_source",
            index=0,
        )
