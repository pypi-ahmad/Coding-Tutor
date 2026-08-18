"""CodeContests Parquet/archive importer without extracting source files."""
from __future__ import annotations

import io
import json
import logging
import tarfile
import tomllib
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from coding_tutor.dataset.catalog import SPECS_BY_KEY, DatasetSpec
from coding_tutor.dataset.importer import DATASET_ROOT, ImportResult
from coding_tutor.dataset.inspection import InspectedFile
from coding_tutor.dataset.normalization import (
    NormalizedQuestion, SourceMetadata, TestCase, persist_question,
    relative_source_file, stable_source_key,
)

logger = logging.getLogger(__name__)
SPEC = SPECS_BY_KEY["codecontests"]
DATASET_NAME = SPEC.dataset_name
_DIFFICULTIES = {"beginner": "Beginner", "easy": "Easy", "medium": "Medium", "hard": "Hard", "very_hard": "Very Hard", "very hard": "Very Hard"}


def _read_member(archive: tarfile.TarFile, name: str, limit: int = 2_000_000) -> bytes:
    member = archive.getmember(name)
    if not member.isfile() or member.size > limit:
        raise ValueError(f"Invalid archive member: {name}")
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError(f"Missing archive member: {name}")
    value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError(f"Archive member exceeds limit: {name}")
    return value


def import_dataset(conn: duckdb.DuckDBPyConnection, dataset_root: Path, run_id: str,
                   sources: list[InspectedFile], spec: DatasetSpec = SPEC) -> ImportResult:
    imported = skipped = 0
    for source in sources:
        index = 0
        for batch in pq.ParquetFile(source.path).iter_batches(columns=["path", "task_binary"], batch_size=100):
            for record in batch.to_pylist():
                try:
                    ok, was_skipped = _upsert(conn, record, run_id, str(source.path), index, dataset_root, source.revision, spec)
                    imported += int(ok and not was_skipped)
                    skipped += int(was_skipped)
                except Exception as exc:
                    logger.warning("Skipping CodeContests task %s: %s", record.get("path"), exc)
                    skipped += 1
                index += 1
    return ImportResult(spec.dataset_name, imported, skipped, "completed")


def _upsert(conn: duckdb.DuckDBPyConnection, record: dict, run_id: str, source_file: str,
            record_index: int = 0, dataset_root: Path = DATASET_ROOT,
            revision: str | None = None, spec: DatasetSpec = SPEC) -> tuple[bool, bool]:
    original_id = str(record.get("path") or "")
    if not original_id or not record.get("task_binary"):
        return False, True
    with tarfile.open(fileobj=io.BytesIO(record["task_binary"]), mode="r:*") as archive:
        instruction = _read_member(archive, "instruction.md").decode("utf-8")
        metadata = tomllib.loads(_read_member(archive, "task.toml").decode("utf-8"))["metadata"]
        tests = json.loads(_read_member(archive, "tests/test_data.json"))
    path = Path(source_file)
    source = SourceMetadata(
        spec.dataset_name, stable_source_key(spec.dataset_name, original_id),
        relative_source_file(path, dataset_root), original_id, revision, record_index,
        spec.license, spec.attribution, run_id, original_id,
    )
    difficulty = _DIFFICULTIES.get(str(metadata.get("difficulty", "medium")).lower(), "Medium")
    inputs, outputs = tests.get("inputs", []), tests.get("outputs", [])
    cases = tuple(TestCase(inp, out) for inp, out in zip(inputs[:10], outputs[:10]))
    title = instruction.splitlines()[0].lstrip("# ").strip() or original_id
    question = NormalizedQuestion(
        title, spec.question_type, difficulty, instruction, spec.supported_methods,
        source, tuple(metadata.get("tags") or ()), test_cases=cases,
    )
    return persist_question(conn, question)
