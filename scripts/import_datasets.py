"""Import downloaded Coding Tutor datasets into the local DuckDB database."""
from __future__ import annotations

import argparse
from pathlib import Path

from coding_tutor.database.connection import get_db, reset_connection
from coding_tutor.dataset.catalog import SPECS_BY_KEY
from coding_tutor.dataset.importer import DATASET_ROOT, run_import


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets", nargs="+", choices=tuple(SPECS_BY_KEY),
        help="Dataset keys to import; omit to import every supported dataset.",
    )
    parser.add_argument(
        "--dataset-root", type=Path, default=DATASET_ROOT,
        help=f"Downloaded dataset root (default: {DATASET_ROOT}).",
    )
    parser.add_argument(
        "--database", type=Path,
        help="DuckDB path; omit to use CODING_TUTOR_DB or coding_tutor.duckdb.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    conn = get_db(str(args.database) if args.database else None)
    try:
        results = run_import(conn, args.datasets, args.dataset_root)
        for result in results:
            summary = f"{result.dataset_name}: {result.status}; {result.imported} imported, {result.skipped} skipped"
            if result.error:
                summary += f"; {result.error}"
            print(summary)
        return 1 if any(result.status == "failed" for result in results) else 0
    finally:
        reset_connection()


if __name__ == "__main__":
    raise SystemExit(main())
