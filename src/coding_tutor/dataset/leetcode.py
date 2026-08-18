"""LeetCodeDataset JSONL importer."""
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
SPEC = SPECS_BY_KEY["leetcode"]
DATASET_NAME = SPEC.dataset_name
_DIFFICULTY_MAP = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        with source.path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream):
                if not line.strip():
                    continue
                try:
                    ok, was_skipped = _upsert_question(
                        conn, json.loads(line), run_id, str(source.path), index,
                        dataset_root, source.revision, spec,
                    )
                    imported += int(ok and not was_skipped)
                    skipped += int(was_skipped)
                except Exception as exc:
                    logger.warning("Skipping LeetCode record %s in %s: %s", index, source.path, exc)
                    skipped += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _upsert_question(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str,
                     source_file: str, record_index: int | None = None,
                     dataset_root: Path = DATASET_ROOT, revision: str | None = None,
                     spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    original_id = str(record.get("task_id") or record.get("question_id") or "")
    statement = record.get("problem_description") or ""
    if not original_id or not statement:
        return False, True
    path = Path(source_file)
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, original_id),
        relative_source_file(path, dataset_root), original_id, revision, record_index,
        spec.license, spec.attribution, run_id, original_id,
    )
    raw_cases = record.get("input_output") or []
    cases = tuple(
        TestCase(item.get("input"), item.get("output"))
        for item in raw_cases[:50] if isinstance(item, dict)
    ) if isinstance(raw_cases, list) else ()
    starter = record.get("starter_code") or ""
    solution = record.get("completion") or ""
    assets = (Asset("starter_code", starter, "python"),) if starter else ()
    solutions = (Solution("python", solution, "python"),) if solution else ()
    task_id = str(record.get("task_id") or original_id)
    question = NormalizedQuestion(
        " ".join(word.capitalize() for word in task_id.replace("-", " ").split()),
        spec.question_type,
        _DIFFICULTY_MAP.get(str(record.get("difficulty", "medium")).lower(), "Medium"),
        statement, spec.supported_methods, source,
        tuple(record.get("tags") or ()) if isinstance(record.get("tags") or [], list) else (),
        assets=assets, solutions=solutions, test_cases=cases,
    )
    return persist_question(conn, question)
