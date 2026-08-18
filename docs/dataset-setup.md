# Dataset Setup Guide

Coding Tutor imports practice questions from seven public Hugging Face datasets. The raw files are **not included in the repository** because they total roughly 8 GB. This guide explains how to download them and load them into the local DuckDB database.

---

## Quick start

```bash
# 1. Download all datasets (CodeContests is skipped by default — see below)
uv run python scripts/download_datasets.py

# 2. Import questions into DuckDB
uv run python -c "
from coding_tutor.database.connection import get_db
from coding_tutor.dataset.importer import run_import
run_import(get_db())
"
```

The import command is idempotent — re-running it skips already-imported records.

---

## Datasets

| Key | Hugging Face repo | Type | License | Approx. size | Importer status |
|---|---|---|---|---|---|
| `leetcode` | [newfacade/LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset) | Algorithm (Python) | Apache-2.0 | ~60 MB | ✅ Complete |
| `apps` | [codeparrot/apps](https://huggingface.co/datasets/codeparrot/apps) | Algorithm (Python) | MIT | ~130 MB | ✅ Complete |
| `taco` | [BAAI/TACO](https://huggingface.co/datasets/BAAI/TACO) | Algorithm (Python) | Apache-2.0 | ~400 MB | ✅ Complete |
| `codecontests` | [open-thoughts/CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests) | Algorithm | MIT | ~7 GB | ⏭ Skipped (binary archive) |
| `spider` | [xlangai/spider](https://huggingface.co/datasets/xlangai/spider) | Data Analysis | CC BY-SA 4.0 | ~4 MB | ⚠ Schema only |
| `sqlctx` | [b-mc2/sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context) | Data Analysis | CC BY 4.0 | ~30 MB | ⚠ Schema only |
| `querypls` | [samadpls/querypls-prompt2sql-dataset](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset) | Data Analysis | Apache-2.0 | ~15 MB | ⚠ Schema only |

**Complete** — includes reference solutions and executable test cases.  
**Schema only** — provides CREATE TABLE schema and a reference SQL answer but no fixture data rows. Questions are imported as `is_complete = false` and support reference study but not automated test execution.  
**Skipped** — the CodeContests repo contains binary archives; the importer logs a clear skip message and does not block the rest of the pipeline.

---

## Downloader script

`scripts/download_datasets.py` uses `huggingface_hub.snapshot_download` to fetch each dataset to the correct local directory.

### List available datasets

```bash
uv run python scripts/download_datasets.py --list
```

### Download everything (excluding CodeContests)

```bash
uv run python scripts/download_datasets.py
```

### Download specific datasets

```bash
# Download only LeetCode and TACO
uv run python scripts/download_datasets.py --datasets leetcode taco

# Available keys: leetcode, apps, taco, codecontests, spider, sqlctx, querypls
```

### Include CodeContests (7 GB, binary — skipped by importer)

```bash
uv run python scripts/download_datasets.py --include-codecontests
```

### Preview without downloading

```bash
uv run python scripts/download_datasets.py --dry-run
```

### Faster downloads with a Hugging Face token

Authenticated requests use higher rate limits. Set `HF_TOKEN` before running:

```bash
# Windows
set HF_TOKEN=hf_...
uv run python scripts/download_datasets.py

# PowerShell
$env:HF_TOKEN = "hf_..."
uv run python scripts/download_datasets.py
```

Get a free token at <https://huggingface.co/settings/tokens>.

---

## Expected directory structure

After downloading, the `Dataset/` directory should look like this:

```
Dataset/
├── algorithm_problems/
│   ├── LeetCodeDataset/       ← leetcode: *.jsonl files
│   ├── apps/                  ← apps: *.jsonl files
│   ├── TACO/
│   │   └── ALL/               ← taco: *.parquet files here
│   └── CodeContests/          ← codecontests: (skipped by importer)
└── data_analysis_problems/
    ├── spider/
    │   └── spider/            ← spider: *.parquet files here
    ├── sql-create-context/
    │   └── sql_create_context_v4.json   ← sqlctx: single JSON file
    └── querypls-prompt2sql-dataset/
        └── data/              ← querypls: *.parquet files here
```

> **Note:** The sub-paths (e.g. `TACO/ALL/`, `spider/spider/`, `querypls-prompt2sql-dataset/data/`) reflect the internal directory structure of the Hugging Face repositories. `snapshot_download` preserves this structure automatically.

---

## Running the import

Once datasets are downloaded, import them into DuckDB:

```bash
uv run python -c "
from coding_tutor.database.connection import get_db
from coding_tutor.dataset.importer import run_import
run_import(get_db())
"
```

### Import specific datasets only

```python
from coding_tutor.database.connection import get_db
from coding_tutor.dataset.importer import run_import

# Import only leetcode and spider
results = run_import(get_db(), datasets=["leetcode", "spider"])
for r in results:
    print(r.dataset_name, r.status, r.imported, "imported,", r.skipped, "skipped")
```

### Check import status

```python
import duckdb

conn = duckdb.connect("coding_tutor.duckdb")
conn.execute("""
    SELECT dataset_name, status, records_imported, records_skipped, started_at
    FROM import_runs
    ORDER BY started_at DESC
""").df()
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `No .jsonl files found` | LeetCode or APPS download didn't land in the right folder | Check that `Dataset/algorithm_problems/LeetCodeDataset/*.jsonl` exists |
| `No parquet files found` | TACO files are in a different subdirectory | Ensure `Dataset/algorithm_problems/TACO/ALL/*.parquet` exists |
| `File not found: sql_create_context_v4.json` | sql-create-context downloaded to a different name | Look for the JSON file in `Dataset/data_analysis_problems/sql-create-context/` and rename if needed |
| `huggingface_hub not found` | Dependency not installed | Run `uv sync` to install dependencies |
| Download rate-limited or slow | No HF token | Set `HF_TOKEN` environment variable |
| `401 Unauthorized` | Dataset requires login | Log in at huggingface.co and set `HF_TOKEN` |

---

## Dataset licenses and attribution

By downloading and using these datasets you agree to their respective licenses:

| Dataset | License | Citation |
|---|---|---|
| LeetCodeDataset | Apache-2.0 | newfacade |
| APPS | MIT | Hendrycks et al., 2021 |
| TACO | Apache-2.0 | BAAI |
| CodeContests | MIT | open-thoughts |
| Spider | CC BY-SA 4.0 | Yu et al., 2018 |
| sql-create-context | CC BY 4.0 | b-mc2 |
| querypls | Apache-2.0 | samadpls |

See each dataset's Hugging Face page for full license terms.
