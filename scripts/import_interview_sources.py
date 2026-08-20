"""Normalize licensed local interview sources into interview.duckdb."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from coding_tutor.database.migrations import run_migrations
from coding_tutor.dataset.importer import _finish_run, _start_run
from coding_tutor.dataset.interview import parse_30_seconds, parse_markdown, persist_interview_item

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
RAW = DATASET / "interview_sources" / "raw"
DB = DATASET / "catalogs" / "interview.duckdb"


def import_sources(db_path: Path = DB) -> tuple[int, int]:
    manifest = json.loads((DATASET / "interview_sources" / "manifest.json").read_text(encoding="utf-8"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    run_migrations(conn)
    imported = skipped = 0
    try:
        for key in ("30-seconds-of-interviews", "data-science-interviews", "interview-questions", "tech-interview-handbook"):
            meta = manifest["sources"][key]
            if not meta["ingestion_allowed"]:
                continue
            run_id = _start_run(conn, key)
            source_imported = source_skipped = 0
            paths = [RAW / key / file["path"] for file in meta["files"]]
            if key == "30-seconds-of-interviews":
                items = parse_30_seconds(RAW / key / "data/questions.json", meta["revision"], run_id)
            else:
                domain = {"data-science-interviews": "data-science", "interview-questions": "software-engineering",
                          "tech-interview-handbook": "interview"}[key]
                items = []
                for path in paths:
                    if path.suffix.lower() == ".md" and path.name.lower() != "readme.md":
                        items.extend(parse_markdown(path, key, meta["revision"], run_id, meta["license"], domain))
            for item in items:
                _, was_skipped = persist_interview_item(conn, item)
                source_skipped += int(was_skipped)
                source_imported += int(not was_skipped)
            _finish_run(conn, run_id, source_imported, source_skipped, "completed")
            imported += source_imported
            skipped += source_skipped
    finally:
        conn.close()
    return imported, skipped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DB)
    args = parser.parse_args()
    imported, skipped = import_sources(args.database)
    print(f"Imported {imported}; skipped {skipped}; database={args.database}")


if __name__ == "__main__":
    main()
