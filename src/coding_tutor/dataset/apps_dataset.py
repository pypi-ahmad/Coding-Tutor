"""APPS JSONL importer."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb

from coding_tutor.dataset.catalog import SPECS_BY_KEY, DatasetSpec
from coding_tutor.dataset.importer import DATASET_ROOT, ImportResult
from coding_tutor.dataset.inspection import InspectedFile
from coding_tutor.dataset.normalization import (
    Asset, NormalizedQuestion, Solution, SourceMetadata, TestCase,
    persist_question, relative_source_file, stable_source_key,
)

logger = logging.getLogger(__name__)
SPEC = SPECS_BY_KEY["apps"]
DATASET_NAME = SPEC.dataset_name
_DIFFICULTY_MAP = {"introductory": "Easy", "interview": "Medium", "competition": "Hard"}


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        with source.path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream):
                if not line.strip():
                    continue
                try:
                    ok, was_skipped = _upsert_question(conn, json.loads(line), run_id, str(source.path), index, dataset_root, source.revision, spec)
                    imported += int(ok and not was_skipped)
                    skipped += int(was_skipped)
                except Exception as exc:
                    logger.warning("Skipping APPS record %s in %s: %s", index, source.path, exc)
                    skipped += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _decode(value, default):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value if value is not None else default


def _upsert_question(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str,
                     source_file: str, line_idx: int,
                     dataset_root: Path = DATASET_ROOT, revision: str | None = None,
                     spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    raw_id = record.get("problem_id", record.get("id"))
    original_id = str(raw_id) if raw_id is not None else None
    statement = record.get("question") or record.get("problem") or ""
    if not statement:
        return False, True
    path = Path(source_file)
    file_label = relative_source_file(path, dataset_root)
    locator = original_id if original_id is not None else f"row:{line_idx}"
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, file_label, locator),
        file_label, original_id, revision, line_idx, spec.license, spec.attribution,
        run_id, original_id or str(line_idx),
    )
    io_data = _decode(record.get("input_output"), {})
    inputs = io_data.get("inputs", []) if isinstance(io_data, dict) else []
    outputs = io_data.get("outputs", []) if isinstance(io_data, dict) else []
    cases = tuple(TestCase(inp, out) for inp, out in zip(inputs[:50], outputs[:50]))
    starter = record.get("starter_code") or ""
    solutions_raw = _decode(record.get("solutions"), [])
    solutions = tuple(Solution("python", item, "python") for item in solutions_raw[:3] if isinstance(item, str) and item.strip()) if isinstance(solutions_raw, list) else ()
    assets = (Asset("starter_code", starter, "python"),) if starter else ()
    title_id = original_id or str(line_idx)
    question = NormalizedQuestion(
        record.get("name") or f"APPS Problem {title_id}", spec.question_type,
        _DIFFICULTY_MAP.get(str(record.get("difficulty") or "").lower(), "Medium"),
        statement, spec.supported_methods, source,
        tuple(record.get("tags") or ()) if isinstance(record.get("tags") or [], list) else (),
        assets=assets, solutions=solutions, test_cases=cases,
    )
    return persist_question(conn, question)
