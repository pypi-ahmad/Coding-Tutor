from coding_tutor.dataset.ai_engineering_qa import parse_ai_engineering_qa


def test_parse_questions_pairs_answers_and_ignores_navigation(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(
        "## Table of Contents\n- [LLM Fundamentals](#llm)\n"
        "### LLM Fundamentals\n- What is an LLM?\n"
        "  - Answer: [Explanation](https://example.test/llm)\n"
        "- Your model is wrong. How do you fix it?\n",
        encoding="utf-8",
    )
    items = parse_ai_engineering_qa(path, "revision", "run")
    assert len(items) == 2
    assert items[0].reference_answer == "Explanation (https://example.test/llm)"
    assert items[1].prompt_style == "scenario"


def test_coding_category_uses_coding_format(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(
        "### Coding and Practical Implementation\n- Implement semantic search.\n",
        encoding="utf-8",
    )
    item = parse_ai_engineering_qa(path, "revision", "run")[0]
    assert item.answer_format == "coding"
