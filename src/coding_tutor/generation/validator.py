"""Validates AI-generated question structures before saving."""
from __future__ import annotations


class ValidationError(Exception):
    pass


REQUIRED_ALGORITHM_FIELDS = {
    "title", "problem_statement", "examples", "constraints",
    "difficulty", "tags", "starter_code_python", "test_cases",
}

REQUIRED_DATA_ANALYSIS_FIELDS = {
    "title", "problem_statement", "difficulty",
    "schema_sql", "fixture_data", "table_name",
    "expected_result", "supported_methods",
}

VALID_DIFFICULTIES = {"Beginner", "Easy", "Medium", "Hard", "Very Hard"}
VALID_METHODS = {"sql", "pandas", "pyspark", "polars"}


def validate_algorithm_question(data: dict) -> None:
    missing = REQUIRED_ALGORITHM_FIELDS - set(data.keys())
    if missing:
        raise ValidationError(f"Algorithm question missing fields: {missing}")

    if not data.get("title", "").strip():
        raise ValidationError("title must not be empty")

    if not data.get("problem_statement", "").strip():
        raise ValidationError("problem_statement must not be empty")

    if not isinstance(data.get("test_cases"), list) or len(data["test_cases"]) == 0:
        raise ValidationError("test_cases must be a non-empty list")

    for tc in data["test_cases"]:
        if "input" not in tc or "expected_output" not in tc:
            raise ValidationError(f"test_case missing input/expected_output: {tc}")

    if not isinstance(data.get("examples"), list):
        raise ValidationError("examples must be a list")


def validate_data_analysis_question(data: dict) -> None:
    missing = REQUIRED_DATA_ANALYSIS_FIELDS - set(data.keys())
    if missing:
        raise ValidationError(f"Data analysis question missing fields: {missing}")

    if not data.get("title", "").strip():
        raise ValidationError("title must not be empty")

    if not data.get("schema_sql", "").strip():
        raise ValidationError("schema_sql must not be empty")

    if not isinstance(data.get("fixture_data"), list) or len(data["fixture_data"]) == 0:
        raise ValidationError("fixture_data must be a non-empty list")

    if not isinstance(data.get("expected_result"), list) or len(data["expected_result"]) == 0:
        raise ValidationError("expected_result must be a non-empty list")

    methods = data.get("supported_methods", [])
    if not isinstance(methods, list) or not methods:
        raise ValidationError("supported_methods must be a non-empty list")

    unknown = set(methods) - VALID_METHODS
    if unknown:
        raise ValidationError(f"Unknown supported_methods: {unknown}")
