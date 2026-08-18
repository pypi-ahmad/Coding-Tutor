"""Download all Coding Tutor datasets from Hugging Face.

Usage
-----
    # Download everything (skips datasets already present)
    uv run python scripts/download_datasets.py

    # Download specific datasets only
    uv run python scripts/download_datasets.py --datasets leetcode taco

    # List available dataset names and exit
    uv run python scripts/download_datasets.py --list

    # See what would be downloaded without fetching
    uv run python scripts/download_datasets.py --dry-run

Optional environment variable
------------------------------
    HF_TOKEN=<your_token>   Speeds up downloads and gives access to gated repos.
                            Get a token at https://huggingface.co/settings/tokens
                            Not required for the public datasets listed here.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Repository root (two directories above this script) ──────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = REPO_ROOT / "Dataset"
ALGO_ROOT = DATASET_ROOT / "algorithm_problems"
DA_ROOT = DATASET_ROOT / "data_analysis_problems"

# ── Dataset registry ─────────────────────────────────────────────────────────
# Each entry:
#   hf_repo       — Hugging Face repo id (owner/name)
#   local_dir     — directory where snapshot_download writes files
#   importer_key  — short name for --datasets filtering
#   note          — displayed next to the dataset in --list output
#
# The importer expects the following paths inside local_dir:
#   leetcode   → local_dir / "*.jsonl"
#   apps       → local_dir / "*.jsonl"
#   taco       → local_dir / "ALL" / "*.parquet"
#   codecont   → local_dir / "*.parquet"  (skipped by importer — binary)
#   spider     → local_dir / "spider" / "*.parquet"
#   sqlctx     → local_dir / "sql_create_context_v4.json"
#   querypls   → local_dir / "data" / "*.parquet"

DATASETS: list[dict] = [
    # ── Algorithm (Python) ──────────────────────────────────────────────────
    {
        "key": "leetcode",
        "hf_repo": "newfacade/LeetCodeDataset",
        "local_dir": ALGO_ROOT / "LeetCodeDataset",
        "size_hint": "~60 MB",
        "note": "Algorithm problems with reference solutions and test cases",
    },
    {
        "key": "apps",
        "hf_repo": "codeparrot/apps",
        "local_dir": ALGO_ROOT / "apps",
        "size_hint": "~130 MB",
        "note": "Introductory / interview / competition Python problems",
    },
    {
        "key": "taco",
        "hf_repo": "BAAI/TACO",
        "local_dir": ALGO_ROOT / "TACO",
        "size_hint": "~400 MB",
        "note": "Competitive programming (importer reads ALL/*.parquet)",
    },
    {
        "key": "codecontests",
        "hf_repo": "open-thoughts/CodeContests",
        "local_dir": ALGO_ROOT / "CodeContests",
        "size_hint": "~7 GB",
        "note": "Binary archive format — downloaded but skipped by importer",
    },
    # ── Data analysis (SQL) ─────────────────────────────────────────────────
    {
        "key": "spider",
        "hf_repo": "xlangai/spider",
        "local_dir": DA_ROOT / "spider",
        "size_hint": "~4 MB",
        "note": "Text-to-SQL (importer reads spider/*.parquet)",
    },
    {
        "key": "sqlctx",
        "hf_repo": "b-mc2/sql-create-context",
        "local_dir": DA_ROOT / "sql-create-context",
        "size_hint": "~30 MB",
        "note": "SQL + CREATE TABLE context (importer reads sql_create_context_v4.json)",
    },
    {
        "key": "querypls",
        "hf_repo": "samadpls/querypls-prompt2sql-dataset",
        "local_dir": DA_ROOT / "querypls-prompt2sql-dataset",
        "size_hint": "~15 MB",
        "note": "Prompt-to-SQL pairs (importer reads data/*.parquet)",
    },
]

DATASET_BY_KEY = {d["key"]: d for d in DATASETS}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_already_present(local_dir: Path) -> bool:
    """Return True if the local_dir is non-empty (dataset already downloaded)."""
    if not local_dir.exists():
        return False
    files = [f for f in local_dir.rglob("*") if f.is_file()]
    return len(files) > 0


def _download_one(dataset: dict, token: str | None, dry_run: bool) -> bool:
    key = dataset["key"]
    hf_repo = dataset["hf_repo"]
    local_dir: Path = dataset["local_dir"]
    size_hint = dataset["size_hint"]
    note = dataset["note"]

    if _check_already_present(local_dir):
        log.info("[%s] Already present at %s — skipping.", key, local_dir)
        return True

    if dry_run:
        log.info("[%s] DRY RUN — would download %s (%s) → %s", key, hf_repo, size_hint, local_dir)
        return True

    log.info("[%s] Downloading %s (%s) …", key, hf_repo, size_hint)
    log.info("[%s] Note: %s", key, note)
    log.info("[%s] Destination: %s", key, local_dir)

    try:
        from huggingface_hub import snapshot_download

        local_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=hf_repo,
            repo_type="dataset",
            local_dir=str(local_dir),
            token=token,
            ignore_patterns=["*.git*", ".git*", "*.md"],
        )
        log.info("[%s] Done.", key)
        return True
    except Exception as exc:
        log.error("[%s] Download failed: %s", key, exc)
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def _list_datasets() -> None:
    print(f"\n{'Key':<12} {'HF Repo':<42} {'Size':<12} Note")
    print("-" * 110)
    for d in DATASETS:
        print(f"  {d['key']:<10} {d['hf_repo']:<42} {d['size_hint']:<12} {d['note']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Coding Tutor datasets from Hugging Face.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        metavar="KEY",
        help="Dataset keys to download (default: all). Use --list to see keys.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print available dataset keys and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without fetching anything.",
    )
    parser.add_argument(
        "--skip-codecontests",
        action="store_true",
        default=True,
        help="Skip CodeContests (7 GB, binary archive — skipped by importer anyway). Default: True.",
    )
    parser.add_argument(
        "--include-codecontests",
        action="store_true",
        help="Override --skip-codecontests and download CodeContests.",
    )
    args = parser.parse_args()

    if args.list:
        _list_datasets()
        return

    # Resolve token from environment
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        log.info("HF_TOKEN detected — authenticated downloads enabled.")
    else:
        log.info("No HF_TOKEN set. Proceeding with unauthenticated downloads.")
        log.info("Set HF_TOKEN for faster downloads: https://huggingface.co/settings/tokens")

    # Resolve which datasets to download
    if args.datasets:
        unknown = [k for k in args.datasets if k not in DATASET_BY_KEY]
        if unknown:
            log.error("Unknown dataset keys: %s", unknown)
            log.error("Run with --list to see available keys.")
            sys.exit(1)
        targets = [DATASET_BY_KEY[k] for k in args.datasets]
    else:
        targets = list(DATASETS)

    # Filter CodeContests unless explicitly requested
    if not args.include_codecontests:
        targets = [d for d in targets if d["key"] != "codecontests"]
        if not args.datasets:
            log.info("CodeContests skipped by default (7 GB, binary — use --include-codecontests to download).")

    if not targets:
        log.info("Nothing to download.")
        return

    print()
    log.info("Datasets to download: %s", [d["key"] for d in targets])
    log.info("Dataset root: %s", DATASET_ROOT)
    print()

    results: dict[str, bool] = {}
    for dataset in targets:
        results[dataset["key"]] = _download_one(dataset, token=token, dry_run=args.dry_run)

    # Summary
    print()
    log.info("─" * 50)
    ok = [k for k, v in results.items() if v]
    failed = [k for k, v in results.items() if not v]
    if ok:
        log.info("Completed: %s", ok)
    if failed:
        log.error("Failed:    %s", failed)

    if not args.dry_run and ok:
        print()
        log.info("Next step: run the import pipeline to load questions into DuckDB:")
        log.info("  uv run python -c \"")
        log.info("    from coding_tutor.database.connection import get_db")
        log.info("    from coding_tutor.dataset.importer import run_import")
        log.info("    run_import(get_db())\"")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
