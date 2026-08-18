"""Tests for question generation with mocked providers."""
import json
import pytest
from unittest.mock import patch, MagicMock


VALID_ALGORITHM_RESPONSE = json.dumps({
    "title": "Sum Array",
    "problem_statement": "Given an array, return the sum.",
    "examples": [{"input": "nums = [1,2,3]", "output": "6"}],
    "constraints": "1 <= n <= 100",
    "difficulty": "Easy",
    "tags": ["Array"],
    "starter_code_python": "class Solution:\n    def solve(self, nums):\n        pass",
    "test_cases": [
        {"input": {"nums": [1, 2, 3]}, "expected_output": 6},
        {"input": {"nums": []}, "expected_output": 0},
    ],
    "reference_solution_python": "class Solution:\n    def solve(self, nums):\n        return sum(nums)",
})

VALID_DATA_ANALYSIS_RESPONSE = json.dumps({
    "title": "Average Salary by Dept",
    "problem_statement": "Find average salary per department.",
    "difficulty": "Easy",
    "tags": ["SQL", "Aggregation"],
    "schema_sql": "CREATE TABLE emp (id INT, dept TEXT, salary DOUBLE);",
    "fixture_data": [
        {"id": 1, "dept": "Eng", "salary": 90000},
        {"id": 2, "dept": "Mkt", "salary": 70000},
    ],
    "table_name": "emp",
    "expected_result": [{"dept": "Eng", "avg": 90000}, {"dept": "Mkt", "avg": 70000}],
    "supported_methods": ["sql", "pandas", "pyspark", "polars"],
    "starter_code": {"sql": "SELECT\n"},
    "reference_solutions": {"sql": "SELECT dept, AVG(salary) FROM emp GROUP BY dept;"},
})


def _make_model(verified=True):
    from coding_tutor.providers.base import ModelOption
    return ModelOption(
        provider="agnes",
        model_id="agnes-2.5-flash",
        display_name="Agnes 2.5 Flash",
        verified=verified,
    )


def test_validate_algorithm_question_valid():
    from coding_tutor.generation.validator import validate_algorithm_question
    data = json.loads(VALID_ALGORITHM_RESPONSE)
    validate_algorithm_question(data)  # should not raise


def test_validate_algorithm_question_missing_test_cases():
    from coding_tutor.generation.validator import validate_algorithm_question, ValidationError
    data = json.loads(VALID_ALGORITHM_RESPONSE)
    del data["test_cases"]
    with pytest.raises(ValidationError, match="missing fields"):
        validate_algorithm_question(data)


def test_validate_data_analysis_question_valid():
    from coding_tutor.generation.validator import validate_data_analysis_question
    data = json.loads(VALID_DATA_ANALYSIS_RESPONSE)
    validate_data_analysis_question(data)  # should not raise


def test_validate_data_analysis_question_empty_fixture():
    from coding_tutor.generation.validator import validate_data_analysis_question, ValidationError
    data = json.loads(VALID_DATA_ANALYSIS_RESPONSE)
    data["fixture_data"] = []
    with pytest.raises(ValidationError, match="fixture_data"):
        validate_data_analysis_question(data)


def test_generate_question_saves_to_db(monkeypatch):
    from coding_tutor.providers.base import ChatResponse
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as conn_mod
    import coding_tutor.generation.generator as gen_mod

    test_conn = get_test_db()
    monkeypatch.setattr(conn_mod, "get_db", lambda: test_conn)

    mock_response = ChatResponse(content=VALID_ALGORITHM_RESPONSE, model="agnes-2.5-flash", provider="agnes")

    with patch("coding_tutor.providers.registry.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = True
        mock_provider.chat.return_value = mock_response
        mock_get.return_value = mock_provider

        model = _make_model()
        q_id = gen_mod.generate_question("agnes", model, "algorithm", "Easy", "python")

    assert q_id is not None
    count = test_conn.execute("SELECT COUNT(*) FROM questions WHERE is_ai_generated = true").fetchone()[0]
    assert count == 1


def test_generate_question_rejects_malformed_json(monkeypatch):
    from coding_tutor.providers.base import ChatResponse
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as conn_mod

    test_conn = get_test_db()
    monkeypatch.setattr(conn_mod, "get_db", lambda: test_conn)

    with patch("coding_tutor.providers.registry.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = True
        mock_provider.chat.return_value = ChatResponse(
            content="not json at all {broken", model="agnes-2.5-flash", provider="agnes"
        )
        mock_get.return_value = mock_provider

        model = _make_model()
        from coding_tutor.generation.generator import generate_question
        result = generate_question("agnes", model, "algorithm", "Easy", "python")

    assert result is None


def test_generate_question_rejects_incomplete_structure(monkeypatch):
    from coding_tutor.providers.base import ChatResponse
    from coding_tutor.database.connection import get_test_db
    import coding_tutor.database.connection as conn_mod

    test_conn = get_test_db()
    monkeypatch.setattr(conn_mod, "get_db", lambda: test_conn)

    incomplete = json.dumps({"title": "Incomplete", "problem_statement": "no test cases"})

    with patch("coding_tutor.providers.registry.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = True
        mock_provider.chat.return_value = ChatResponse(
            content=incomplete, model="agnes-2.5-flash", provider="agnes"
        )
        mock_get.return_value = mock_provider

        model = _make_model()
        from coding_tutor.generation.generator import generate_question
        result = generate_question("agnes", model, "algorithm", "Easy", "python")

    assert result is None


def test_generate_question_fails_unverified_model():
    from coding_tutor.generation.generator import generate_question
    model = _make_model(verified=False)
    result = generate_question("openai", model, "algorithm", "Easy", "python")
    assert result is None
