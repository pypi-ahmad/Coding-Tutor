"""Dataset import orchestrator — coordinates all source importers."""
from __future__ import annotations
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
import duckdb

from coding_tutor.dataset.catalog import DATASET_SPECS, SPECS_BY_KEY, SPECS_BY_NAME
from coding_tutor.dataset.inspection import inspect_dataset

logger = logging.getLogger(__name__)

DATASET_ROOT = Path(__file__).parent.parent.parent.parent / "Dataset"

ALGORITHM_ROOT = DATASET_ROOT / "algorithm_problems"
DATA_ANALYSIS_ROOT = DATASET_ROOT / "data_analysis_problems"


@dataclass
class ImportResult:
    dataset_name: str
    imported: int
    skipped: int
    status: str
    error: str | None = None


def run_import(
    conn: duckdb.DuckDBPyConnection,
    datasets: list[str] | None = None,
    dataset_root: Path | None = None,
) -> list[ImportResult]:
    """
    Import one or more datasets into DuckDB.
    datasets: list of dataset names to import, or None to import all.
    Idempotent — re-running skips already-imported records.
    """
    root = (dataset_root or DATASET_ROOT).resolve()
    if datasets is None:
        specs = list(DATASET_SPECS)
    else:
        specs = []
        for value in datasets:
            spec = SPECS_BY_KEY.get(value) or SPECS_BY_NAME.get(value)
            if spec is None:
                raise ValueError(f"Unknown dataset: {value}. Choose from: {', '.join(SPECS_BY_KEY)}")
            if spec not in specs:
                specs.append(spec)
    results = []

    for spec in specs:
        logger.info("Starting import: %s", spec.dataset_name)
        run_id = _start_run(conn, spec.dataset_name)
        try:
            inspected = inspect_dataset(spec, root)
            for source in inspected:
                logger.info("Inspected %s as %s with fields=%s", source.path, source.source_format, sorted(source.fields))
            mod = importlib.import_module(spec.module)
            result = mod.import_dataset(conn, root, run_id, inspected, spec)
            _finish_run(conn, run_id, result.imported, result.skipped, result.status, result.error)
            results.append(result)
            logger.info("Finished %s: imported=%s, skipped=%s", spec.dataset_name, result.imported, result.skipped)
        except Exception as exc:
            logger.error("Import failed for %s: %s", spec.dataset_name, exc, exc_info=True)
            _finish_run(conn, run_id, 0, 0, "failed", str(exc))
            results.append(ImportResult(spec.dataset_name, 0, 0, "failed", str(exc)))

    return results


def _start_run(conn: duckdb.DuckDBPyConnection, dataset_name: str) -> str:
    """Insert an import_runs record and return its ID."""
    row = conn.execute(
        "INSERT INTO import_runs (dataset_name, status) VALUES (?, 'running') RETURNING id",
        [dataset_name],
    ).fetchone()
    conn.commit()
    return str(row[0])


def _finish_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    imported: int,
    skipped: int,
    status: str,
    error: str | None = None,
) -> None:
    conn.execute(
        """UPDATE import_runs
           SET completed_at = now(), records_imported = ?, records_skipped = ?,
               status = ?, error_message = ?
           WHERE id = ?""",
        [imported, skipped, status, error, run_id],
    )
    conn.commit()
