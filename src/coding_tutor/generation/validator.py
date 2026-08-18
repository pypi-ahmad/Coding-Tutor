"""Strict validation for AI-generated question structures."""
from __future__ import annotations

import math
from collections.abc import Mapping


class ValidationError(ValueError):
    """The generated question does not satisfy the accepted schema."""


VALID_DIFFICULTIES = {"Beginner", "Easy", "Medium", "Hard", "Very Hard"}
VALID_METHODS = ("sql", "pandas", "pyspark", "polars")

REQUIRED_ALGORITHM_FIELDS = {
    "question_type",
    "title",
    "problem_statement",
    "examples",
    "constraints",
    "difficulty",
    "tags",
    "starter_code_python",
    "test_cases",
}
ALLOWED_ALGORITHM_FIELDS = REQUIRED_ALGORITHM_FIELDS | {"reference_solution_python"}

REQUIRED_DATA_ANALYSIS_FIELDS = {
    "question_type",
    "title",
    "problem_statement",
    "difficulty",
    "tags",
    "schema_sql",
    "fixture_data",
    "table_name",
    "expected_result",
    "supported_methods",
    "starter_code",
    "reference_solutions",
}


def _require_object(data, label: str) -> Mapping:
    if not isinstance(data, Mapping):
        raise ValidationError(f"{label} must be a JSON object")
    return data


def _validate_fields(data: Mapping, required: set[str], allowed: set[str], label: str) -> None:
    missing = required - set(data)
    if missing:
        raise ValidationError(f"{label} missing fields: {sorted(missing)}")
    unexpected = set(data) - allowed
    if unexpected:
        raise ValidationError(f"{label} has unexpected fields: {sorted(unexpected)}")


def _non_empty_string(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value


def _validate_common(data: Mapping, question_type: str, expected_difficulty: str) -> None:
    if expected_difficulty not in VALID_DIFFICULTIES:
        raise ValidationError(f"Unsupported requested difficulty: {expected_difficulty}")
    if data["question_type"] != question_type:
        raise ValidationError(f"question_type must be {question_type}")
    if data["difficulty"] != expected_difficulty:
        raise ValidationError(f"difficulty must match requested {expected_difficulty}")
    _non_empty_string(data["title"], "title")
    _non_empty_string(data["problem_statement"], "problem_statement")
    tags = data["tags"]
    if not isinstance(tags, list) or not tags or not all(
        isinstance(tag, str) and tag.strip() for tag in tags
    ):
        raise ValidationError("tags must be a non-empty list of strings")


def validate_algorithm_question(data: dict, *, expected_difficulty: str) -> None:
    data = _require_object(data, "Algorithm question")
    _validate_fields(
        data,
        REQUIRED_ALGORITHM_FIELDS,
        ALLOWED_ALGORITHM_FIELDS,
        "Algorithm question",
    )
    _validate_common(data, "algorithm", expected_difficulty)
    _non_empty_string(data["constraints"], "constraints")
    _non_empty_string(data["starter_code_python"], "starter_code_python")

    examples = data["examples"]
    if not isinstance(examples, list) or not examples:
        raise ValidationError("examples must be a non-empty list")
    for example in examples:
        if not isinstance(example, dict) or "input" not in example or not (
            "output" in example or "expected_output" in example
        ):
            raise ValidationError("each example needs input and output")

    test_cases = data["test_cases"]
    if not isinstance(test_cases, list) or not test_cases:
        raise ValidationError("test_cases must be a non-empty list")
    for test_case in test_cases:
        if not isinstance(test_case, dict) or not {
            "input",
            "expected_output",
        }.issubset(test_case):
            raise ValidationError("each test_case needs input and expected_output")

    if "reference_solution_python" in data:
        _non_empty_string(data["reference_solution_python"], "reference_solution_python")


def _is_json_scalar(value) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _validate_rows(value, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{field} must be a non-empty list")
    expected_columns = None
    for row in value:
        if not isinstance(row, dict) or not row:
            raise ValidationError(f"{field} rows must be non-empty objects")
        if not all(isinstance(column, str) and column for column in row):
            raise ValidationError(f"{field} column names must be non-empty strings")
        columns = set(row)
        if expected_columns is None:
            expected_columns = columns
        elif columns != expected_columns:
            raise ValidationError(f"{field} rows must use consistent columns")
        if not all(_is_json_scalar(cell) for cell in row.values()):
            raise ValidationError(f"{field} cells must be JSON scalar values")


def _validate_method_map(value, field: str) -> None:
    if not isinstance(value, dict) or set(value) != set(VALID_METHODS):
        raise ValidationError(f"{field} must contain exactly {list(VALID_METHODS)}")
    for method in VALID_METHODS:
        _non_empty_string(value[method], f"{field}.{method}")


def validate_data_analysis_question(data: dict, *, expected_difficulty: str) -> None:
    data = _require_object(data, "Data analysis question")
    _validate_fields(
        data,
        REQUIRED_DATA_ANALYSIS_FIELDS,
        REQUIRED_DATA_ANALYSIS_FIELDS,
        "Data analysis question",
    )
    _validate_common(data, "data_analysis", expected_difficulty)

    schema_sql = _non_empty_string(data["schema_sql"], "schema_sql")
    table_name = _non_empty_string(data["table_name"], "table_name")
    if "create table" not in schema_sql.casefold():
        raise ValidationError("schema_sql must contain CREATE TABLE")
    if table_name.casefold() not in schema_sql.casefold():
        raise ValidationError("table_name must appear in schema_sql")

    _validate_rows(data["fixture_data"], "fixture_data")
    _validate_rows(data["expected_result"], "expected_result")

    methods = data["supported_methods"]
    if (
        not isinstance(methods, list)
        or not all(isinstance(method, str) for method in methods)
        or set(methods) != set(VALID_METHODS)
        or len(methods) != len(VALID_METHODS)
    ):
        raise ValidationError(
            f"supported_methods must contain exactly {list(VALID_METHODS)}"
        )
    _validate_method_map(data["starter_code"], "starter_code")
    _validate_method_map(data["reference_solutions"], "reference_solutions")
