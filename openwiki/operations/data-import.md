---
type: operations
title: Data import operations
description: Safe, documented commands for importing downloaded coding and interview datasets into local catalogs.
tags: [datasets, imports, operations, duckdb]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-8b9e30a670716b39995d2de0
    resource: repo://docs/DATASETS.md
  - id: openwiki-source-fd9d2f4f694e43f840998a75
    resource: repo://scripts/import_datasets.py
  - id: openwiki-source-ed27af1727d778c095447056
    resource: repo://scripts/import_interview_sources.py
  - id: openwiki-source-287be9d422be4e897346f8fb
    resource: repo://src/coding_tutor/dataset/importer.py
  - id: openwiki-source-c11836d2de4c2cce2a51812e
    resource: repo://src/coding_tutor/dataset/inspection.py
  - id: openwiki-source-5230999b290c20cd5367dde7
    resource: repo://tests/test_import.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Data import operations

Downloading source files and importing records into DuckDB are separate steps. The dataset guide distinguishes adapter support from a complete imported/selectable corpus and notes that a complete import of the local snapshots was not run for that verification. (Source: `repo://docs/DATASETS.md#L1-L15`.)

## Coding and data-analysis datasets

The importer defaults to all configured datasets under the default dataset root. Use `--datasets` to select keys, `--dataset-root` to change the raw-data root, and `--database` to choose the DuckDB file. If `--database` is omitted, `CODING_TUTOR_DB` or `coding_tutor.duckdb` is used. Examples from the project documentation:

```powershell
uv run python scripts/import_datasets.py
uv run python scripts/import_datasets.py --datasets leetcode apps taco
uv run python scripts/import_datasets.py --datasets leetcode apps taco --database Dataset/catalogs/algorithm.duckdb
```

(Sources: `repo://scripts/import_datasets.py#L12-L25`, `repo://scripts/import_datasets.py#L29-L41`, `repo://docs/DATASETS.md#L176-L188`, `repo://docs/RUNBOOK.md#L89-L101`.)

Before importing a dataset, the importer inspects matching files and checks that their format and required fields are valid. Each import run records a status and imported/skipped counts. A failed source is recorded as failed and processing can continue to other configured sources. (Sources: `repo://src/coding_tutor/dataset/inspection.py#L53-L77`, `repo://src/coding_tutor/dataset/importer.py#L29-L69`, `repo://src/coding_tutor/dataset/importer.py#L72-L97`.)

Imports use stable source identities so a rerun skips records already imported instead of duplicating them. Tests exercise an idempotent repeated insert and verify that import-run counts and status are stored. (Sources: `repo://src/coding_tutor/dataset/importer.py#L29-L38`, `repo://tests/test_import.py#L16-L44`, `repo://tests/test_import.py#L85-L95`.)

## Interview sources

The interview-source workflow downloads pinned source revisions into `Dataset/interview_sources/raw`, records hashes and ingestion decisions in a manifest, then normalizes allowed material into the interview catalog. The importer skips sources whose manifest entry has `ingestion_allowed` set to false. The documented import command is:

```powershell
uv run python scripts/import_interview_sources.py
```

It accepts `--database` to select a different target; otherwise the script defaults to `Dataset/catalogs/interview.duckdb`. (Sources: `repo://docs/DATASETS.md#L190-L202`, `repo://scripts/import_interview_sources.py#L15-L25`, `repo://scripts/import_interview_sources.py#L28-L64`.)

Do not treat an import command succeeding as legal clearance to redistribute third-party content. Review source and license terms before use; the project documentation makes that distinction explicit. (Source: `repo://docs/DATASETS.md#L1-L15`.)

## Related pages

- [Datasets and question catalogs](../workflows/datasets-and-catalogs.md)
- [Local development](local-development.md)
- [Testing and verification strategy](../testing/verification-strategy.md)
