"""Filter-aware learner progress dashboard backed entirely by DuckDB."""
import pandas as pd
import streamlit as st

from coding_tutor.database.connection import get_db
from coding_tutor.database.progress import (
    get_all_attempts,
    get_progress_summary,
    get_quiz_progress,
    get_solution_view_history,
)


def render_progress_page():
    st.title("📈 My progress")
    conn = get_db()

    st.subheader("Filters")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        qt_filter = st.selectbox("Question type", ["All", "algorithm", "data_analysis"])
    with col_f2:
        diff_filter = st.selectbox(
            "Difficulty", ["All", "Beginner", "Easy", "Medium", "Hard", "Very Hard"]
        )
    with col_f3:
        method_filter = st.selectbox(
            "Method", ["All", "python", "sql", "pandas", "pyspark", "polars"]
        )
    filters = {
        "question_type": None if qt_filter == "All" else qt_filter,
        "difficulty": None if diff_filter == "All" else diff_filter,
        "method": None if method_filter == "All" else method_filter,
    }

    summary = get_progress_summary(conn, **filters)
    attempts = get_all_attempts(conn, **filters)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total attempts", summary["total_attempts"])
    with col2:
        st.metric("Attempted questions", summary["attempted_questions"])
    with col3:
        st.metric(
            f"AI-estimated solved (≥{summary['solved_threshold']:.0f}%)",
            summary["solved_questions"],
        )
    st.caption(
        "Learner code is not executed. Deterministic test status is recorded as ‘not run’; "
        "solved status comes only from AI-estimated correctness."
    )

    st.divider()
    st.subheader("Recent attempts")
    if summary["recent_attempts"]:
        recent = pd.DataFrame(summary["recent_attempts"])
        recent["attempted_at"] = pd.to_datetime(recent["attempted_at"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            recent[["title", "difficulty", "method", "assessment_status",
                    "deterministic_test_result", "percentage_correct", "marks", "attempted_at"]]
            .rename(columns={
                "title": "Question", "difficulty": "Difficulty", "method": "Method",
                "assessment_status": "Assessment", "deterministic_test_result": "Deterministic test",
                "percentage_correct": "AI-estimated %", "marks": "AI-estimated marks",
                "attempted_at": "Time",
            }),
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No attempts match these filters.")

    if attempts:
        frame = pd.DataFrame(attempts)
        frame["attempted_at"] = pd.to_datetime(frame["attempted_at"]).dt.strftime("%Y-%m-%d %H:%M")
        frame["attempt_id"] = frame["id"].str.slice(0, 8)

        st.subheader("Question-wise marks")
        marks = frame[frame["marks"].notna()]
        if marks.empty:
            st.info("No AI-estimated marks are available for these attempts.")
        else:
            st.caption("Every row is a separate attempt; marks are never averaged or overwritten.")
            st.dataframe(
                marks[["title", "attempt_id", "method", "marks", "percentage_correct", "attempted_at"]]
                .rename(columns={
                    "title": "Question", "attempt_id": "Attempt", "method": "Method",
                    "marks": "AI-estimated marks", "percentage_correct": "AI-estimated %",
                    "attempted_at": "Time",
                }),
                hide_index=True,
                width="stretch",
            )

        st.subheader("Attempts grouped by question")
        for (_, title), group in frame.groupby(["question_id", "title"], sort=True):
            solved = bool(
                ((group["assessment_status"] == "completed")
                 & (group["percentage_correct"] >= summary["solved_threshold"])).any()
            )
            label = f"{title} · {len(group)} attempt{'s' if len(group) != 1 else ''} · {'Solved' if solved else 'Not solved'}"
            with st.expander(label):
                st.dataframe(
                    group[["attempt_id", "attempted_at", "method", "deterministic_test_result",
                           "assessment_status", "percentage_correct", "marks", "solution_viewed",
                           "provider", "model_id", "error_details"]]
                    .rename(columns={
                        "attempt_id": "Attempt", "attempted_at": "Time", "method": "Method",
                        "deterministic_test_result": "Deterministic test",
                        "assessment_status": "Assessment", "percentage_correct": "AI-estimated %",
                        "marks": "AI-estimated marks", "solution_viewed": "Solution viewed",
                        "provider": "Provider", "model_id": "Model", "error_details": "Error",
                    }),
                    hide_index=True,
                    width="stretch",
                )

    if summary["by_difficulty"]:
        st.subheader("Attempts by difficulty")
        by_difficulty = pd.DataFrame(summary["by_difficulty"])
        st.bar_chart(by_difficulty.set_index("difficulty")["attempts"])

    st.divider()
    st.subheader("Quiz progress")
    quiz = get_quiz_progress(conn, **filters)
    quiz_cols = st.columns(3)
    quiz_cols[0].metric("Quiz attempts", quiz["total_attempts"])
    quiz_cols[1].metric("Completed quizzes", quiz["completed_attempts"])
    quiz_cols[2].metric("Passed quizzes", quiz["passed_attempts"])
    if quiz["attempts"]:
        quiz_frame = pd.DataFrame(quiz["attempts"])
        quiz_frame["started_at"] = pd.to_datetime(quiz_frame["started_at"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            quiz_frame[["started_at", "status", "question_source", "difficulty", "method",
                        "total_items", "coding_items", "mcq_items", "percentage_correct", "passed"]]
            .rename(columns={
                "started_at": "Started", "status": "Status", "question_source": "Source",
                "difficulty": "Difficulty", "method": "Method", "total_items": "Questions",
                "coding_items": "Coding", "mcq_items": "MCQ",
                "percentage_correct": "Score %", "passed": "Passed",
            }),
            hide_index=True, width="stretch",
        )
    else:
        st.info("No quiz attempts match these filters.")

    st.subheader("Solution views")
    views = get_solution_view_history(conn, **filters)
    if not views:
        st.info("No solution views match these filters.")
    else:
        view_frame = pd.DataFrame(views)
        view_frame["Methods"] = view_frame["methods"].apply(lambda values: ", ".join(values))
        view_frame["Time"] = pd.to_datetime(view_frame["viewed_at"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            view_frame[["title", "Methods", "Time"]].rename(columns={"title": "Question"}),
            hide_index=True,
            width="stretch",
        )
