"""Session state management for quiz/learning flow."""
import json
import streamlit as st
from typing import Optional


def get_current_question() -> Optional[dict]:
    return st.session_state.get("current_question")


def load_question(question_id: str) -> None:
    """Load a question from DB into session state."""
    from coding_tutor.database.connection import get_db
    conn = get_db()
    row = conn.execute(
        """SELECT id, title, question_type, difficulty, problem_statement,
                  constraints, examples, supported_methods, tags, is_complete, is_ai_generated, source_id
           FROM questions WHERE id = ?""",
        [question_id],
    ).fetchone()

    if not row:
        st.error(f"Question {question_id} not found.")
        return

    q = {
        "id": str(row[0]),
        "title": row[1],
        "question_type": row[2],
        "difficulty": row[3],
        "problem_statement": row[4],
        "constraints": row[5],
        "examples": row[6],
        "supported_methods": json.loads(row[7]) if row[7] else [],
        "tags": json.loads(row[8]) if row[8] else [],
        "is_complete": row[9],
        "is_ai_generated": row[10],
        "source_id": str(row[11]) if row[11] else None,
    }

    # Auto-select a valid method for this question if current selection isn't supported
    supported = q["supported_methods"]
    current_method = st.session_state.get("method", "python")
    if supported and current_method not in supported:
        st.session_state.method = supported[0]

    st.session_state.current_question = q
    st.session_state.submit_trigger = False
    st.session_state.show_solution_trigger = False


def clear_question_with_confirm() -> None:
    """Clear current question from session state."""
    st.session_state.current_question = None
    st.session_state.editor_content = ""
    st.session_state.submit_trigger = False
    st.session_state.show_solution_trigger = False
