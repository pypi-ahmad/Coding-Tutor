"""Spider text-to-SQL Parquet importer."""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from coding_tutor.dataset.catalog import SPECS_BY_KEY, DatasetSpec
from coding_tutor.dataset.importer import DATASET_ROOT, ImportResult
from coding_tutor.dataset.inspection import InspectedFile
from coding_tutor.dataset.normalization import (
    DATA_ANALYSIS_METHODS, NormalizedQuestion, Solution, SourceMetadata,
    persist_question, relative_source_file, stable_source_key,
)

logger = logging.getLogger(__name__)
SPEC = SPECS_BY_KEY["spider"]
DATASET_NAME = SPEC.dataset_name
SUPPORTED_METHODS = list(DATA_ANALYSIS_METHODS)


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        index = 0
        for batch in pq.ParquetFile(source.path).iter_batches(batch_size=500):
            for record in batch.to_pylist():
                try:
                    ok, was_skipped = _upsert_question(conn, record, run_id, str(source.path), index, dataset_root, source.revision, spec)
                    imported += int(ok and not was_skipped)
                    skipped += int(was_skipped)
                except Exception as exc:
                    logger.warning("Skipping Spider record %s in %s: %s", index, source.path, exc)
                    skipped += 1
                index += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _upsert_question(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str,
                     source_file: str, record_index: int = 0,
                     dataset_root: Path = DATASET_ROOT, revision: str | None = None,
                     spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    question_text = record.get("question") or ""
    sql_answer = record.get("query") or ""
    db_id = str(record.get("db_id") or "unknown")
    if not question_text or not sql_answer:
        return False, True
    path = Path(source_file)
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, db_id, question_text, sql_answer),
        relative_source_file(path, dataset_root), None, revision, record_index,
        spec.license, spec.attribution, run_id, f"{db_id}__{question_text[:50]}",
    )
    solution = Solution("sql", sql_answer, "sql")
    normalized = NormalizedQuestion(
        f"SQL: {question_text[:60]}", spec.question_type, "Medium",
        f"Database: **{db_id}**\n\n**Question:** {question_text}",
        spec.supported_methods, source, solutions=(solution,), is_complete=False,
    )
    return persist_question(conn, normalized)
