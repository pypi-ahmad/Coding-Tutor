"""Tests for strict question generation with mocked providers."""
import json
import logging
from unittest.mock import MagicMock, patch

import pytest


METHODS = ["sql", "pandas", "pyspark", "polars"]

VALID_ALGORITHM = {
    "question_type": "algorithm",
    "title": "Sum Array",
    "problem_statement": "Given an array, return the sum.",
    "examples": [{"input": "nums = [1,2,3]", "output": "6"}],
    "constraints": "0 <= nums.length <= 100",
    "difficulty": "Easy",
    "tags": ["Array"],
    "starter_code_python": "class Solution:\n    def solve(self, nums):\n        pass",
    "test_cases": [
        {"input": {"nums": [1, 2, 3]}, "expected_output": 6},
        {"input": {"nums": []}, "expected_output": 0},
    ],
    "reference_solution_python": (
        "class Solution:\n    def solve(self, nums):\n        return sum(nums)"
    ),
}

VALID_DATA_ANALYSIS = {
    "question_type": "data_analysis",
    "title": "Average Salary by Department",
    "problem_statement": (
        "Return each department and its average salary, ordered by department."
    ),
    "difficulty": "Easy",
    "tags": ["Aggregation"],
    "schema_sql": "CREATE TABLE emp (id INT, dept TEXT, salary DOUBLE);",
    "fixture_data": [
        {"id": 1, "dept": "Eng", "salary": 90000},
        {"id": 2, "dept": "Mkt", "salary": 70000},
    ],
    "table_name": "emp",
    "expected_result": [
        {"dept": "Eng", "avg_salary": 90000.0},
        {"dept": "Mkt", "avg_salary": 70000.0},
    ],
    "supported_methods": METHODS,
    "starter_code": {
        "sql": "SELECT dept, AVG(salary) AS avg_salary\nFROM emp",
        "pandas": "def solution(emp):\n    pass",
        "pyspark": "def solution(emp):\n    pass",
        "polars": "def solution(emp):\n    pass",
    },
    "reference_solutions": {
        "sql": (
            "SELECT dept, AVG(salary) AS avg_salary FROM emp "
            "GROUP BY dept ORDER BY dept;"
        ),
        "pandas": "def solution(emp):\n    return emp.groupby('dept').salary.mean()",
        "pyspark": "def solution(emp):\n    return emp.groupBy('dept').avg('salary')",
        "polars": "def solution(emp):\n    return emp.group_by('dept').agg(pl.mean('salary'))",
    },
}


def _make_model(*, provider="agnes", verified=True):
    from coding_tutor.providers.base import ModelOption

    return ModelOption(
        provider=provider,
        model_id="agnes-2.5-flash",
        display_name="Agnes 2.5 Flash",
        verified=verified,
    )


def _mock_provider(content: str):
    from coding_tutor.providers.base import ChatResponse

    provider = MagicMock()
    provider.is_configured.return_value = True
    provider.chat.return_value = ChatResponse(
        content=content,
        model="agnes-2.5-flash",
        provider="agnes",
    )
    return provider


def _generate(monkeypatch, content, **overrides):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    from coding_tutor.generation.generator import generate_question

    seed_context = overrides.pop("seed_context", None)
    conn = get_test_db()
    context_id = seed_context(conn) if seed_context else None
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    provider = _mock_provider(content)
    arguments = {
        "provider_name": "agnes",
        "model": _make_model(),
        "question_type": "algorithm",
        "difficulty": "Easy",
        "method": "python",
        "topic": "arrays",
    }
    arguments.update(overrides)
    with patch("coding_tutor.providers.registry.get_provider", return_value=provider):
        result = generate_question(**arguments)
    return result, conn, provider, context_id


def _seed_algorithm_context(conn):
    source_id = conn.execute(
        """INSERT INTO question_sources
               (dataset_name, source_key, source_file, attribution)
           VALUES ('TACO', 'taco-arrays', 'algorithm/taco.parquet', 'TACO')
           RETURNING id"""
    ).fetchone()[0]
    return str(conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods,
                tags, source_id, is_ai_generated, is_complete)
           VALUES ('Array rotation', 'algorithm', 'Easy',
                   'Rotate an array without changing its length.', '["python"]',
                   '["arrays"]', ?, false, true)
           RETURNING id""",
        [source_id],
    ).fetchone()[0])


def test_validate_algorithm_question_requires_requested_type_and_difficulty():
    from coding_tutor.generation.validator import validate_algorithm_question

    validate_algorithm_question(VALID_ALGORITHM, expected_difficulty="Easy")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda value: value.pop("test_cases"), "missing fields"),
        (lambda value: value.update(difficulty="Hard"), "difficulty"),
        (lambda value: value.update(question_type="data_analysis"), "question_type"),
        (lambda value: value.update(unexpected="reasoning"), "unexpected fields"),
    ],
)
def test_validate_algorithm_question_rejects_invalid_content(change, message):
    from coding_tutor.generation.validator import ValidationError, validate_algorithm_question

    data = json.loads(json.dumps(VALID_ALGORITHM))
    change(data)
    with pytest.raises(ValidationError, match=message):
        validate_algorithm_question(data, expected_difficulty="Easy")


def test_validate_data_analysis_question_requires_complete_cross_method_content():
    from coding_tutor.generation.validator import validate_data_analysis_question

    validate_data_analysis_question(VALID_DATA_ANALYSIS, expected_difficulty="Easy")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda value: value.update(fixture_data=[]), "fixture_data"),
        (lambda value: value["starter_code"].pop("polars"), "starter_code"),
        (lambda value: value["reference_solutions"].pop("pyspark"), "reference_solutions"),
        (lambda value: value.update(supported_methods=["sql"]), "supported_methods"),
        (lambda value: value.update(expected_result=[{"value": [1, 2]}]), "scalar"),
    ],
)
def test_validate_data_analysis_question_rejects_incomplete_content(change, message):
    from coding_tutor.generation.validator import (
        ValidationError,
        validate_data_analysis_question,
    )

    data = json.loads(json.dumps(VALID_DATA_ANALYSIS))
    change(data)
    with pytest.raises(ValidationError, match=message):
        validate_data_analysis_question(data, expected_difficulty="Easy")


def test_generate_algorithm_sends_selections_and_saves_provenance(monkeypatch):
    from coding_tutor.prompts import load_prompt

    result, conn, provider, _ = _generate(monkeypatch, json.dumps(VALID_ALGORITHM))

    assert result.ok
    question = conn.execute(
        "SELECT question_type, difficulty, is_ai_generated FROM questions WHERE id = ?",
        [result.question_id],
    ).fetchone()
    assert question == ("algorithm", "Easy", True)

    generated = conn.execute(
        """SELECT provider, model_id, generated_at IS NOT NULL, prompt_version, generation_metadata
           FROM ai_generated_questions WHERE question_id = ?""",
        [result.question_id],
    ).fetchone()
    assert generated[:2] == ("agnes", "agnes-2.5-flash")
    assert generated[2] is True
    assert generated[3] == "v4"
    assert json.loads(generated[4]) == {
        "prompt_template": "algorithm_question",
        "question_type": "algorithm",
        "difficulty": "Easy",
        "method": "python",
        "topic": "arrays",
        "context_sources": [],
    }

    call = provider.chat.call_args
    prompt = call.kwargs["messages"][0].content
    assert all(value in prompt for value in ["algorithm", "Easy", "python", "arrays"])
    assert prompt.startswith("Generate one new algorithm practice question.")
    assert call.kwargs["system_prompt"] == load_prompt("shared_rules.md")


def test_generate_uses_bounded_catalog_context_and_records_provenance(monkeypatch):
    result, conn, provider, context_id = _generate(
        monkeypatch,
        json.dumps(VALID_ALGORITHM),
        seed_context=_seed_algorithm_context,
    )

    assert result.ok
    prompt = provider.chat.call_args.kwargs["messages"][0].content
    assert "<reference_examples>" in prompt
    assert "Array rotation" in prompt
    assert "TACO" not in prompt
    assert len(prompt) < 20_000

    metadata = json.loads(conn.execute(
        "SELECT generation_metadata FROM ai_generated_questions WHERE question_id = ?",
        [result.question_id],
    ).fetchone()[0])
    assert metadata["context_sources"] == [
        {"question_id": context_id, "dataset_name": "TACO"}
    ]


def test_data_analysis_context_includes_incomplete_reference_assets():
    from coding_tutor.database.connection import get_test_db
    from coding_tutor.generation.context import load_generation_context

    conn = get_test_db()
    source_id = conn.execute(
        """INSERT INTO question_sources
               (dataset_name, source_key, source_file, attribution)
           VALUES ('sql-create-context', 'sql-aggregation', 'data/sql.json', 'SQL context')
           RETURNING id"""
    ).fetchone()[0]
    question_id = conn.execute(
        """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, supported_methods,
                source_id, is_ai_generated, is_complete)
           VALUES ('Department totals', 'data_analysis', 'Easy',
                   'Aggregate salary by department.',
                   '["sql", "pandas", "pyspark", "polars"]', ?, false, false)
           RETURNING id""",
        [source_id],
    ).fetchone()[0]
    conn.execute(
        """INSERT INTO question_assets
               (question_id, asset_type, content, content_type)
           VALUES (?, 'schema', 'CREATE TABLE emp(dept TEXT, salary INT);', 'sql')""",
        [question_id],
    )
    conn.execute(
        """INSERT INTO reference_solutions
               (question_id, method, code, language)
           VALUES (?, 'sql', 'SELECT dept, SUM(salary) FROM emp GROUP BY dept', 'sql')""",
        [question_id],
    )

    context = load_generation_context(
        conn, "data_analysis", "Easy", "aggregation"
    )

    assert len(context) == 1
    assert context[0]["question_id"] == str(question_id)
    assert context[0]["schema_sql"].startswith("CREATE TABLE")
    assert context[0]["reference_solution"].startswith("SELECT dept")
    assert context[0]["is_complete"] is False


def test_generate_data_analysis_saves_all_method_assets(monkeypatch):
    result, conn, provider, _ = _generate(
        monkeypatch,
        json.dumps(VALID_DATA_ANALYSIS),
        question_type="data_analysis",
        method="pandas",
        topic="aggregation",
    )

    assert result.ok
    methods = json.loads(
        conn.execute(
            "SELECT supported_methods FROM questions WHERE id = ?", [result.question_id]
        ).fetchone()[0]
    )
    starters = conn.execute(
        """SELECT method FROM question_assets
           WHERE question_id = ? AND asset_type = 'starter_code' ORDER BY method""",
        [result.question_id],
    ).fetchall()
    solutions = conn.execute(
        "SELECT method FROM reference_solutions WHERE question_id = ? ORDER BY method",
        [result.question_id],
    ).fetchall()
    shared_assets = conn.execute(
        """SELECT asset_type FROM question_assets
           WHERE question_id = ? AND asset_type != 'starter_code' ORDER BY asset_type""",
        [result.question_id],
    ).fetchall()

    assert methods == METHODS
    assert [row[0] for row in starters] == sorted(METHODS)
    assert [row[0] for row in solutions] == sorted(METHODS)
    assert [row[0] for row in shared_assets] == [
        "expected_result",
        "fixture_data",
        "schema",
    ]
    prompt = provider.chat.call_args.kwargs["messages"][0].content
    assert all(value in prompt for value in ["data_analysis", "Easy", "pandas", "aggregation"])


@pytest.mark.parametrize(
    ("content", "failure"),
    [
        ("not json at all {broken", "malformed_response"),
        (json.dumps([]), "malformed_response"),
        (json.dumps({"title": "Incomplete"}), "incomplete_response"),
        (json.dumps(VALID_ALGORITHM) + " trailing", "malformed_response"),
    ],
)
def test_invalid_provider_content_is_not_saved(monkeypatch, content, failure):
    result, conn, _, _ = _generate(monkeypatch, content)

    assert not result.ok
    assert result.failure.value == failure
    assert conn.execute("SELECT count(*) FROM questions").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM ai_generated_questions").fetchone()[0] == 0


def test_complete_fenced_json_is_accepted(monkeypatch):
    content = f"```json\n{json.dumps(VALID_ALGORITHM)}\n```"
    result, _, _, _ = _generate(monkeypatch, content)
    assert result.ok


def test_unverified_and_mismatched_models_fail_before_provider_call():
    from coding_tutor.generation.generator import GenerationFailure, generate_question

    unverified = generate_question(
        "agnes", _make_model(verified=False), "algorithm", "Easy", "python"
    )
    mismatched = generate_question(
        "openai", _make_model(provider="agnes"), "algorithm", "Easy", "python"
    )
    assert unverified.failure is GenerationFailure.MODEL_UNAVAILABLE
    assert mismatched.failure is GenerationFailure.INVALID_SELECTION


def test_provider_error_does_not_log_or_return_secret(monkeypatch, caplog):
    from coding_tutor.generation.generator import GenerationFailure, generate_question

    secret = "sentinel-secret-value"
    provider = MagicMock()
    provider.is_configured.return_value = True
    provider.chat.side_effect = RuntimeError(f"request failed with {secret}")
    with patch("coding_tutor.providers.registry.get_provider", return_value=provider):
        with caplog.at_level(logging.ERROR):
            result = generate_question(
                "agnes", _make_model(), "algorithm", "Easy", "python"
            )

    assert result.failure is GenerationFailure.PROVIDER_ERROR
    assert secret not in result.detail
    assert secret not in caplog.text


def test_mid_save_failure_rolls_back_all_rows(monkeypatch):
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as connection
    import coding_tutor.generation.generator as generator

    conn = get_test_db()
    monkeypatch.setattr(connection, "get_db", lambda: conn)
    provider = _mock_provider(json.dumps(VALID_DATA_ANALYSIS))

    def fail_assets(*_args, **_kwargs):
        raise RuntimeError("forced persistence failure")

    monkeypatch.setattr(generator, "_save_data_analysis_assets", fail_assets)
    with patch("coding_tutor.providers.registry.get_provider", return_value=provider):
        result = generator.generate_question(
            "agnes", _make_model(), "data_analysis", "Easy", "sql", "aggregation"
        )

    assert result.failure is generator.GenerationFailure.STORAGE_ERROR
    assert conn.execute("SELECT count(*) FROM questions").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM ai_generated_questions").fetchone()[0] == 0
