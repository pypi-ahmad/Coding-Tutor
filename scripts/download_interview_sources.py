"""Download the curated interview source files through authenticated GitHub CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from coding_tutor.dataset.interview_catalog import SOURCES, SOURCES_BY_KEY

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "Dataset" / "interview_sources" / "raw"
MANIFEST = ROOT / "Dataset" / "interview_sources" / "manifest.json"


def gh(*args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(["gh", "api", *args], capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode("utf-8")


def download(keys: list[str] | None = None, dry_run: bool = False) -> dict:
    selected = SOURCES if keys is None else tuple(SOURCES_BY_KEY[key] for key in keys)
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": {}}
    for source in selected:
        revision = json.loads(gh(f"repos/{source.repo}/commits/HEAD"))["sha"]
        entry = {"repository": source.repo, "revision": revision, "license": source.license,
                 "ingestion_allowed": source.ingestion_allowed, "files": []}
        for remote_path in source.paths:
            target = RAW_ROOT / source.key / remote_path
            if dry_run:
                entry["files"].append({"path": remote_path, "status": "planned"})
                continue
            encoded_path = quote(remote_path, safe="/")
            data = gh(f"repos/{source.repo}/contents/{encoded_path}?ref={revision}",
                      "-H", "Accept: application/vnd.github.raw+json", binary=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            entry["files"].append({"path": remote_path, "bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()})
        manifest["sources"][source.key] = entry
    manifest["sources"]["sql-create-context"] = {
        "repository": "b-mc2/sql-create-context", "license": "CC-BY-4.0",
        "ingestion_allowed": True, "status": "reused-existing-local-dataset"}
    manifest["sources"]["RecruitView"] = {
        "repository": "AI4A-lab/RecruitView", "license": "CC-BY-NC-4.0",
        "ingestion_allowed": False, "status": "deferred-access-approval-required"}
    if not dry_run:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="*", choices=tuple(SOURCES_BY_KEY))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        for source in SOURCES:
            print(f"{source.key}\t{'import' if source.ingestion_allowed else 'raw-only'}\t{source.repo}")
        return
    result = download(args.sources, args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
