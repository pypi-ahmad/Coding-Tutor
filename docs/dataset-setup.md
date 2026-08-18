# Dataset Setup Guide

Coding Tutor imports practice questions from seven public Hugging Face datasets. The raw files are **not included in the repository** because they total roughly 8 GB. This guide explains how to download them and load them into the local DuckDB database.

---

## Quick start

```bash
# 1. Download all datasets (CodeContests is skipped by default — see below)
uv run python scripts/download_datasets.py

# 2. Inspect, normalize, and import questions into DuckDB
uv run python scripts/import_datasets.py
```

The import command is idempotent — re-running it skips already-imported records.

---

## Datasets

| Key | Hugging Face repo | Type | License | Approx. size | Importer status |
|---|---|---|---|---|---|
| `leetcode` | [newfacade/LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset) | Algorithm (Python) | Apache-2.0 | ~60 MB | ✅ Complete |
| `apps` | [codeparrot/apps](https://huggingface.co/datasets/codeparrot/apps) | Algorithm (Python) | MIT | ~130 MB | ✅ Complete |
| `taco` | [BAAI/TACO](https://huggingface.co/datasets/BAAI/TACO) | Algorithm (Python) | Apache-2.0 | ~400 MB | ✅ Complete |
| `codecontests` | [open-thoughts/CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests) | Algorithm | Not stated in the downloaded card | ~45 MB | ✅ Complete |
| `spider` | [xlangai/spider](https://huggingface.co/datasets/xlangai/spider) | Data Analysis | CC BY-SA 4.0 | ~4 MB | ⚠ Schema only |
| `sqlctx` | [b-mc2/sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context) | Data Analysis | CC BY 4.0 | ~30 MB | ⚠ Schema only |
| `querypls` | [samadpls/querypls-prompt2sql-dataset](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset) | Data Analysis | Apache-2.0 | ~15 MB | ⚠ Schema only |

**Complete** — includes reference solutions and executable test cases.  
**Schema only** — provides a schema and/or reference SQL but no shared fixture rows and expected result. These records are retained with `is_complete=false` and are not offered as learner tasks.

Before reading records, the importer validates each file's real format and required fields. JSONL, JSON arrays, ordinary Parquet files, and CodeContests' Parquet-wrapped task archives are handled by separate adapters.

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

### Include CodeContests (archive records supported by the importer)

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
│   └── CodeContests/          ← codecontests: tasks.parquet
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

Once datasets are downloaded, inspect and import them into DuckDB:

```bash
uv run python scripts/import_datasets.py
```

### Import specific datasets only

```bash
uv run python scripts/import_datasets.py --datasets leetcode spider
```

Available keys are `leetcode`, `apps`, `codecontests`, `taco`, `spider`, `sqlctx`, and `querypls`. Use `--dataset-root PATH` for a different read-only source location or `--database PATH` for a different DuckDB file. Omitting `--database` respects `CODING_TUTOR_DB` and otherwise uses `coding_tutor.duckdb`.

The importer never renames, moves, overwrites, or extracts into the downloaded source directories. Provenance stores the relative source path, original ID where available, Hugging Face revision metadata where present, license, attribution, and import timestamp.

> [!NOTE]
> A full import can take well over an hour and require several gigabytes of local disk space, especially on Windows. Importing one dataset at a time with `--datasets` makes progress and failures easier to monitor. If the process is interrupted, already committed source records remain protected by the idempotency key, but the interrupted `import_runs` row may remain marked `running`; rerun the same dataset to continue without duplicating those records.

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
| `No source files match ...` | A download is missing or has a different layout | Re-run the downloader for that dataset or pass the correct `--dataset-root`; do not rename downloaded source files |
| `missing required fields` | The downloaded revision has a schema the adapter does not support | Keep the source untouched and report the dataset, revision, and error message |
| Import remains active for a long time | Large sources are normalized and persisted record by record | Allow substantial time and disk space, or import one dataset key at a time |
| An interrupted run still shows `running` | The process ended before it could finalize its import-run record | Rerun that dataset; existing source records are skipped idempotently |
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
| CodeContests | Not stated in the downloaded dataset card | open-thoughts repackaging of DeepMind CodeContests |
| Spider | CC BY-SA 4.0 | Yu et al., 2018 |
| sql-create-context | CC BY 4.0 | b-mc2 |
| querypls | Apache-2.0 | samadpls |

The Coding Tutor MIT license applies only to this project's source code. It does not relicense, replace, or expand the permissions granted by any imported dataset.

Before importing, sharing, publishing, or redistributing dataset-derived questions:

1. Review the current dataset card, upstream source, license text, and usage restrictions.
2. Preserve all required copyright notices, attribution, share-alike terms, and citations.
3. Keep the dataset name, original record identifier, source file/revision, license, and attribution metadata recorded by the importer.
4. Treat absent or unclear license information as unresolved; it is not permission to use or redistribute the material.

CodeContests is intentionally documented as having no license stated in the downloaded dataset card. Users must resolve its applicable terms for their own use. See each dataset's Hugging Face page and upstream project for authoritative, current license terms.
