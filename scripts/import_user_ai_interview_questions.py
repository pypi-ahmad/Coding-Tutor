"""Import the AI interview questions explicitly supplied by the user."""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from coding_tutor.database.migrations import run_migrations
from coding_tutor.dataset.ai_interview_questions import SECTION_RULES, parse_selected_ai_questions
from coding_tutor.dataset.importer import _finish_run, _start_run
from coding_tutor.dataset.interview import persist_interview_item

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "Dataset/interview_sources/raw/ai-engineering-field-guide/interview/questions"
DEFAULT_DB = ROOT / "Dataset/catalogs/interview.duckdb"
REVISION = "7e269b34c6e967dfcc003b2ed83c148a217c72e0"


def run(db_path: Path = DEFAULT_DB) -> tuple[int, int]:
    conn = duckdb.connect(str(db_path))
    run_migrations(conn)
    run_id = _start_run(conn, "user-provided-ai-engineering-interview-questions")
    imported = skipped = 0
    try:
        for filename in SECTION_RULES:
            for item in parse_selected_ai_questions(RAW / filename, REVISION, run_id):
                _, was_skipped = persist_interview_item(conn, item)
                imported += int(not was_skipped)
                skipped += int(was_skipped)
        _finish_run(conn, run_id, imported, skipped, "completed")
    except Exception as exc:
        _finish_run(conn, run_id, imported, skipped, "failed", str(exc))
        raise
    finally:
        conn.close()
    return imported, skipped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    imported, skipped = run(args.database)
    print(f"Imported {imported}; skipped {skipped}; database={args.database}")


if __name__ == "__main__":
    main()
