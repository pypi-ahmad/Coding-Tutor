"""Read-only source discovery and format/schema inspection."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq

from coding_tutor.dataset.catalog import DatasetSpec


@dataclass(frozen=True)
class InspectedFile:
    path: Path
    source_format: str
    fields: frozenset[str]
    revision: str | None


def _revision_for(path: Path, dataset_root: Path) -> str | None:
    relative = path.resolve().relative_to(dataset_root.resolve())
    parts = relative.parts
    if len(parts) < 3:
        return None
    dataset_dir = dataset_root / parts[0] / parts[1]
    within_dataset = Path(*parts[2:])
    metadata = dataset_dir / ".cache" / "huggingface" / "download" / Path(str(within_dataset) + ".metadata")
    if not metadata.is_file():
        return None
    first_line = metadata.read_text(encoding="utf-8").splitlines()
    return first_line[0].strip() if first_line else None


def _inspect_jsonl(path: Path) -> frozenset[str]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"Expected JSON objects in {path}")
                return frozenset(value)
    raise ValueError(f"No JSON records found in {path}")


def _inspect_json_array(path: Path) -> frozenset[str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        raise ValueError(f"Expected a non-empty JSON object array in {path}")
    return frozenset(value[0])


def inspect_dataset(spec: DatasetSpec, dataset_root: Path) -> list[InspectedFile]:
    """Discover and validate all files for one dataset before importing any rows."""
    files = sorted(dataset_root.glob(spec.file_pattern))
    if not files:
        raise FileNotFoundError(f"No source files match {spec.file_pattern}")

    inspected: list[InspectedFile] = []
    for path in files:
        if spec.source_format == "parquet":
            with path.open("rb") as stream:
                if stream.read(4) != b"PAR1":
                    raise ValueError(f"Expected Parquet file: {path}")
            fields = frozenset(pq.ParquetFile(path).schema_arrow.names)
        elif spec.source_format == "jsonl":
            fields = _inspect_jsonl(path)
        elif spec.source_format == "json_array":
            fields = _inspect_json_array(path)
        else:
            raise ValueError(f"Unsupported source format: {spec.source_format}")

        missing = spec.required_fields - fields
        if missing:
            raise ValueError(f"{path} is missing required fields: {', '.join(sorted(missing))}")
        inspected.append(InspectedFile(path, spec.source_format, fields, _revision_for(path, dataset_root)))
    return inspected
