from coding_tutor.dataset.ai_interview_questions import parse_selected_ai_questions


def test_parser_keeps_questions_and_excludes_preparation(tmp_path):
    path = tmp_path / "01-theory.md"
    path.write_text(
        "## Interview Questions\n### RAG Systems\n- What's RAG? [^source]\n"
        "## How to Prepare\n- RAG systems - build one.\n## Sources\n- source\n",
        encoding="utf-8",
    )
    items = parse_selected_ai_questions(path, "revision", "run")
    assert [item.prompt for item in items] == ["What's RAG?"]
    assert items[0].topic == "RAG Systems"


def test_parser_classifies_home_assignments_as_coding_scenarios(tmp_path):
    path = tmp_path / "06-home-assignments.md"
    path.write_text("## Assignment Examples\n### Agents\n- Build a support agent with safe tool use.\n", encoding="utf-8")
    item = parse_selected_ai_questions(path, "revision", "run")[0]
    assert (item.answer_format, item.prompt_style) == ("coding", "scenario")


def test_parser_excludes_assignment_evaluation_advice(tmp_path):
    path = tmp_path / "06-home-assignments.md"
    path.write_text(
        "## Assignment Examples\n### Evaluation Criteria Found in Assignments\n"
        "- Functional correctness - does it work?\n",
        encoding="utf-8",
    )
    assert parse_selected_ai_questions(path, "revision", "run") == []
