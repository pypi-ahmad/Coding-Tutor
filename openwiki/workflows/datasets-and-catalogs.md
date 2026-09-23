---
type: workflow
title: Datasets and question catalogs
description: How downloaded source material is inspected, normalized, provenance-tracked, and routed into local DuckDB catalogs.
tags: [datasets, catalogs, provenance, licensing]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-17dded95897e01ee430228e3
    resource: repo://app.py
  - id: openwiki-source-8b9e30a670716b39995d2de0
    resource: repo://docs/DATASETS.md
  - id: openwiki-source-b9b65108b1f09cf6c4f0ff68
    resource: repo://scripts/download_datasets.py
  - id: openwiki-source-3b545556a8879bcd88b8b32e
    resource: repo://scripts/download_interview_sources.py
  - id: openwiki-source-ed27af1727d778c095447056
    resource: repo://scripts/import_interview_sources.py
  - id: openwiki-source-6e3ad3af4ba1e470a3d4335c
    resource: repo://src/coding_tutor/catalog.py
  - id: openwiki-source-1e9732862b087442caed105d
    resource: repo://tests/test_interview_dataset.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Datasets and question catalogs

The repository separates raw downloads from runtime catalogs. Coding/data-analysis source files live under the gitignored `Dataset/` tree; importers read those inputs without renaming or overwriting them and store normalized records separately in DuckDB. The application queries the catalogs during normal use rather than reading raw source directories. (Sources: `repo://docs/DATASETS.md#L17-L37`, `repo://docs/DATASETS.md#L204-L212`.)

## Coding and data-analysis sources

`scripts/download_datasets.py` downloads configured Hugging Face datasets and supports list, dataset selection, and dry-run modes. Downloading does not itself create selectable questions: the separate importer inspects source files and normalizes records into question/source/asset/reference/test-case tables. Stable `(dataset_name, source_key)` identity makes repeated imports idempotent. (Sources: `repo://scripts/download_datasets.py#L1-L21`, `repo://docs/DATASETS.md#L27-L42`.)

Records lacking the schema, fixture rows, or deterministic expected result required for a complete exercise stay marked incomplete and are excluded from the curated question picker. Source test cases are stored as static context; the app does not execute imported solutions or tests. (Source: `repo://docs/DATASETS.md#L39-L42`.)

The runtime profiles map algorithm, data-analysis, and interview use to separate catalog database paths. The `all` profile routes Coding and Quiz by question type and other pages to the interview catalog; see [Runtime and profile routing](../architecture/runtime-routing.md). (Sources: `repo://src/coding_tutor/catalog.py#L22-L60`, `repo://app.py#L38-L48`.)

## Interview source gate

Interview-source downloads use authenticated GitHub CLI requests, pin a repository revision, and record file hashes plus licensing and ingestion decisions in a manifest. Importing is a separate step, and the importer skips sources whose `ingestion_allowed` flag is false. Tests cover idempotent persistence and the relationship between a source's license and whether it may be ingested. (Sources: `repo://scripts/download_interview_sources.py#L19-L53`, `repo://scripts/import_interview_sources.py#L21-L55`, `repo://tests/test_interview_dataset.py#L12-L32`.)

License and attribution metadata are traceability information, not permission to redistribute. Review upstream terms and retain applicable notices and provenance when using dataset-derived content. (Source: `repo://docs/DATASETS.md#L214-L222`.)

## Related pages

- [Data import operations](../operations/data-import.md)
- [Runtime and profile routing](../architecture/runtime-routing.md)
- [Testing and verification strategy](../testing/verification-strategy.md)
