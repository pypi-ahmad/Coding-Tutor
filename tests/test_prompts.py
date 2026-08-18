"""Regression tests for file-backed AI prompt templates."""

import pytest


PROMPT_VALUES = {
    "algorithm_question_generator.md": {
        "difficulty": '"Easy"',
        "topic": '"arrays"',
        "selected_method": '"python"',
    },
    "data_analysis_question_generator.md": {
        "difficulty": '"Medium"',
        "topic": '"aggregation"',
        "selected_method": '"sql"',
    },
    "dataset_record_converter.md": {
        "dataset_metadata": '{"name": "fixture"}',
        "raw_record": '{"id": 1}',
    },
    "quiz_generator.md": {"question_contexts": "[]"},
    "shared_rules.md": {},
    "solution_teacher.md": {
        "question": '{"title": "Sum"}',
        "question_type": '"algorithm"',
        "requested_method": '"python"',
        "exercise_data": "{}",
    },
    "static_code_reviewer.md": {
        "question": '{"title": "Sum"}',
        "selected_method": '"python"',
        "exercise_data": "{}",
        "learner_submission": '"return 1"',
    },
}


def test_every_prompt_is_file_backed_and_fully_renderable():
    from coding_tutor.prompts import PROMPT_NAMES, load_prompt, render_prompt

    assert PROMPT_NAMES == frozenset(PROMPT_VALUES)
    for name, values in PROMPT_VALUES.items():
        assert load_prompt(name).strip()
        assert "{{" not in render_prompt(name, **values)


def test_prompt_loader_rejects_unknown_files_and_placeholder_mismatches():
    from coding_tutor.prompts import load_prompt, render_prompt

    with pytest.raises(ValueError, match="Unknown prompt"):
        load_prompt("../shared_rules.md")
    with pytest.raises(ValueError, match="Prompt values"):
        render_prompt("algorithm_question_generator.md", difficulty='"Easy"')
