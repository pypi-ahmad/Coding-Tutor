"""sql-create-context JSON-array importer."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb

from coding_tutor.dataset.catalog import SPECS_BY_KEY, DatasetSpec
from coding_tutor.dataset.importer import DATASET_ROOT, ImportResult
from coding_tutor.dataset.inspection import InspectedFile
from coding_tutor.dataset.normalization import (
    DATA_ANALYSIS_METHODS, Asset, NormalizedQuestion, Solution, SourceMetadata,
    persist_question, relative_source_file, stable_source_key,
)

logger = logging.getLogger(__name__)
SPEC = SPECS_BY_KEY["sqlctx"]
DATASET_NAME = SPEC.dataset_name
SUPPORTED_METHODS = list(DATA_ANALYSIS_METHODS)


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        records = json.loads(source.path.read_text(encoding="utf-8"))
        for index, record in enumerate(records):
            try:
                ok, was_skipped = _upsert_question(conn, record, run_id, str(source.path), index, dataset_root, source.revision, spec)
                imported += int(ok and not was_skipped)
                skipped += int(was_skipped)
            except Exception as exc:
                logger.warning("Skipping sql-create-context record %s: %s", index, exc)
                skipped += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _upsert_question(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str,
                     source_file: str, idx: int,
                     dataset_root: Path = DATASET_ROOT, revision: str | None = None,
                     spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    question_text = record.get("question") or record.get("input") or ""
    schema = record.get("context") or record.get("schema") or ""
    sql_answer = record.get("answer") or record.get("output") or ""
    if not question_text or not sql_answer:
        return False, True
    path = Path(source_file)
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, question_text, schema, sql_answer),
        relative_source_file(path, dataset_root), None, revision, idx,
        spec.license, spec.attribution, run_id, str(idx),
    )
    assets = (Asset("schema", schema, content_type="sql"),) if schema else ()
    normalized = NormalizedQuestion(
        f"SQL: {question_text[:60]}", spec.question_type, "Easy", question_text,
        spec.supported_methods, source, assets=assets,
        solutions=(Solution("sql", sql_answer, "sql"),), is_complete=False,
    )
    return persist_question(conn, normalized)
