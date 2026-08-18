"""Shared normalized question contract and atomic DuckDB persistence."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb


DATA_ANALYSIS_METHODS = ("sql", "pandas", "pyspark", "polars")


@dataclass(frozen=True)
class SourceMetadata:
    dataset_name: str
    source_key: str
    source_file: str
    original_id: str | None
    source_revision: str | None
    source_record_index: int | None
    license: str | None
    attribution: str
    import_run_id: str | None = None
    legacy_original_id: str | None = None


@dataclass(frozen=True)
class Asset:
    asset_type: str
    content: str
    method: str | None = None
    content_type: str = "text"


@dataclass(frozen=True)
class Solution:
    method: str
    code: str
    language: str


@dataclass(frozen=True)
class TestCase:
    input_data: Any
    expected_output: Any
    is_example: bool = False


@dataclass(frozen=True)
class NormalizedQuestion:
    title: str
    question_type: str
    difficulty: str
    problem_statement: str
    supported_methods: tuple[str, ...]
    source: SourceMetadata
    tags: tuple[str, ...] = ()
    constraints: str | None = None
    examples: Any = None
    assets: tuple[Asset, ...] = ()
    solutions: tuple[Solution, ...] = ()
    test_cases: tuple[TestCase, ...] = ()
    is_complete: bool = True


def stable_source_key(dataset_name: str, *identity: object) -> str:
    payload = json.dumps([dataset_name, *identity], ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relative_source_file(path: Path, dataset_root: Path) -> str:
    try:
        return path.resolve().relative_to(dataset_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix() if not path.is_absolute() else path.name


def _legacy_source_exists(conn: duckdb.DuckDBPyConnection, source: SourceMetadata) -> bool:
    if source.legacy_original_id is None:
        return False
    rows = conn.execute(
        "SELECT source_file FROM question_sources WHERE dataset_name=? AND original_id=?",
        [source.dataset_name, source.legacy_original_id],
    ).fetchall()
    basename = Path(source.source_file).name.lower()
    return any(Path(str(row[0]).replace("\\", "/")).name.lower() == basename for row in rows if row[0])


def persist_question(conn: duckdb.DuckDBPyConnection, question: NormalizedQuestion) -> tuple[bool, bool]:
    """Persist one normalized question atomically; return (inserted, skipped)."""
    if not question.problem_statement.strip():
        return False, True
    if question.question_type == "algorithm" and question.supported_methods != ("python",):
        raise ValueError("Algorithm questions must support Python only")
    if question.question_type == "data_analysis" and question.supported_methods != DATA_ANALYSIS_METHODS:
        raise ValueError("Data-analysis questions must expose all supported methods")

    asset_types = {asset.asset_type for asset in question.assets}
    is_complete = question.is_complete
    if question.question_type == "data_analysis":
        is_complete = {"schema", "fixture_data", "expected_result"}.issubset(asset_types)

    if conn.execute(
        "SELECT 1 FROM question_sources WHERE dataset_name=? AND source_key=?",
        [question.source.dataset_name, question.source.source_key],
    ).fetchone() or _legacy_source_exists(conn, question.source):
        return True, True

    conn.begin()
    try:
        source_row = conn.execute(
            """INSERT INTO question_sources
               (dataset_name, original_id, source_key, source_file, source_revision,
                source_record_index, license, attribution, import_run_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (dataset_name, source_key) DO NOTHING
               RETURNING id""",
            [question.source.dataset_name, question.source.original_id, question.source.source_key,
             question.source.source_file, question.source.source_revision,
             question.source.source_record_index, question.source.license,
             question.source.attribution, question.source.import_run_id],
        ).fetchone()
        if source_row is None:
            conn.rollback()
            return True, True

        q_row = conn.execute(
            """INSERT INTO questions
               (title, question_type, difficulty, problem_statement, constraints, examples,
                supported_methods, tags, source_id, is_complete)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
            [question.title, question.question_type, question.difficulty, question.problem_statement,
             question.constraints, json.dumps(question.examples) if question.examples is not None else None,
             json.dumps(question.supported_methods), json.dumps(question.tags), source_row[0], is_complete],
        ).fetchone()
        question_id = q_row[0]

        for asset in question.assets:
            conn.execute(
                "INSERT INTO question_assets (question_id, asset_type, method, content, content_type) VALUES (?, ?, ?, ?, ?)",
                [question_id, asset.asset_type, asset.method, asset.content, asset.content_type],
            )
        for solution in question.solutions:
            conn.execute(
                "INSERT INTO reference_solutions (question_id, method, code, language, is_from_dataset) VALUES (?, ?, ?, ?, true)",
                [question_id, solution.method, solution.code, solution.language],
            )
        for case in question.test_cases:
            conn.execute(
                "INSERT INTO question_test_cases (question_id, input_data, expected_output, is_example) VALUES (?, ?, ?, ?)",
                [question_id, json.dumps(case.input_data), json.dumps(case.expected_output), case.is_example],
            )
        conn.commit()
        return True, False
    except Exception:
        conn.rollback()
        raise
