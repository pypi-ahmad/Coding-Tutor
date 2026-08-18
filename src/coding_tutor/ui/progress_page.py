"""Progress page — shows full learner history from DuckDB."""
import streamlit as st
import pandas as pd
from coding_tutor.database.connection import get_db
from coding_tutor.database.progress import get_progress_summary, get_all_attempts


def render_progress_page():
    st.title("📈 My Progress")
    conn = get_db()

    summary = get_progress_summary(conn)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Attempts", summary["total_attempts"])
    with col2:
        st.metric("Questions Solved", summary["solved_questions"])
    with col3:
        st.metric("Questions Available", summary["total_questions"])

    st.divider()

    st.subheader("History")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        qt_filter = st.selectbox("Question Type", ["All", "algorithm", "data_analysis"])
    with col_f2:
        diff_filter = st.selectbox(
            "Difficulty", ["All", "Beginner", "Easy", "Medium", "Hard", "Very Hard"]
        )
    with col_f3:
        method_filter = st.selectbox(
            "Method", ["All", "python", "sql", "pandas", "pyspark", "polars"]
        )

    attempts = get_all_attempts(
        conn,
        question_type=None if qt_filter == "All" else qt_filter,
        difficulty=None if diff_filter == "All" else diff_filter,
        method=None if method_filter == "All" else method_filter,
    )

    if not attempts:
        st.info("No attempts yet. Go solve some questions!")
        return

    df = pd.DataFrame(attempts)
    df["attempted_at"] = pd.to_datetime(df["attempted_at"]).dt.strftime("%Y-%m-%d %H:%M")

    display_cols = [
        "title", "difficulty", "method", "test_result",
        "percentage_correct", "marks", "attempted_at",
    ]
    st.dataframe(
        df[display_cols].rename(columns={
            "title": "Question",
            "difficulty": "Difficulty",
            "method": "Method",
            "test_result": "Result",
            "percentage_correct": "% Correct",
            "marks": "Marks",
            "attempted_at": "Time",
        }),
        use_container_width=True,
    )

    if summary["by_difficulty"]:
        st.subheader("By Difficulty")
        bd = pd.DataFrame(summary["by_difficulty"])
        st.bar_chart(bd.set_index("difficulty")["avg_pct"])
