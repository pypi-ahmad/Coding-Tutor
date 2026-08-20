"""Launch one consolidated Coding Tutor catalog."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from coding_tutor.catalog import get_catalog_profile


REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", choices=("algorithm", "data-analysis"))
    args = parser.parse_args(argv)

    key = args.catalog.replace("-", "_")
    profile = get_catalog_profile(key)
    env = os.environ.copy()
    env["CODING_TUTOR_CATALOG"] = key
    env["CODING_TUTOR_DB"] = str((REPO_ROOT / profile.database).resolve())
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(REPO_ROOT / "app.py"),
        "--server.address=127.0.0.1",
        f"--server.port={profile.port}",
    ]
    return subprocess.call(command, cwd=REPO_ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
