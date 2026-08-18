"""TACO Parquet importer."""
from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from coding_tutor.dataset.catalog import SPECS_BY_KEY, DatasetSpec
from coding_tutor.dataset.importer import DATASET_ROOT, ImportResult
from coding_tutor.dataset.inspection import InspectedFile
from coding_tutor.dataset.normalization import (
    Asset, NormalizedQuestion, Solution, SourceMetadata, TestCase,
    persist_question, relative_source_file, stable_source_key,
)

logger = logging.getLogger(__name__)
SPEC = SPECS_BY_KEY["taco"]
DATASET_NAME = SPEC.dataset_name
_DIFFICULTY_MAP = {"easy": "Easy", "medium": "Medium", "hard": "Hard", "very hard": "Very Hard", "beginner": "Beginner"}


def _decode(value, default):
    if not isinstance(value, str):
        return value if value is not None else default
    for decoder in (json.loads, ast.literal_eval):
        try:
            return decoder(value)
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue
    return default


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        parquet = pq.ParquetFile(source.path)
        index = 0
        for batch in parquet.iter_batches(batch_size=100):
            for record in batch.to_pylist():
                try:
                    ok, was_skipped = _upsert_question(conn, record, run_id, str(source.path), index, dataset_root, source.revision, spec)
                    imported += int(ok and not was_skipped)
                    skipped += int(was_skipped)
                except Exception as exc:
                    logger.warning("Skipping TACO record %s in %s: %s", index, source.path, exc)
                    skipped += 1
                index += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _upsert_question(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str,
                     source_file: str, record_index: int = 0,
                     dataset_root: Path = DATASET_ROOT, revision: str | None = None,
                     spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    original_id = str(record.get("url") or record.get("problem_id") or record.get("id") or "")
    statement = record.get("question") or ""
    if not original_id or not statement:
        return False, True
    path = Path(source_file)
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, original_id),
        relative_source_file(path, dataset_root), original_id, revision, record_index,
        spec.license, spec.attribution, run_id, original_id,
    )
    difficulty_key = str(record.get("difficulty") or "medium").lower().replace("_", " ")
    tags_value = _decode(record.get("tags") or record.get("raw_tags"), [])
    tags = tuple(str(item) for item in tags_value) if isinstance(tags_value, list) else ()
    io_data = _decode(record.get("input_output"), {})
    inputs = io_data.get("inputs", []) if isinstance(io_data, dict) else []
    outputs = io_data.get("outputs", []) if isinstance(io_data, dict) else []
    cases = tuple(TestCase(inp, out) for inp, out in zip(inputs[:50], outputs[:50]))
    solutions_value = _decode(record.get("solutions"), [])
    solutions = tuple(Solution("python", item, "python") for item in solutions_value[:3] if isinstance(item, str) and item.strip()) if isinstance(solutions_value, list) else ()
    starter = record.get("starter_code") or ""
    assets = (Asset("starter_code", starter, "python"),) if starter else ()
    question = NormalizedQuestion(
        record.get("name") or "TACO Problem", spec.question_type,
        _DIFFICULTY_MAP.get(difficulty_key, "Medium"), statement,
        spec.supported_methods, source, tags, assets=assets,
        solutions=solutions, test_cases=cases,
    )
    return persist_question(conn, question)
