---
type: testing
title: Testing and verification strategy
description: What the repository's pytest suites cover and what their fixtures do not establish.
tags: [pytest, testing, verification, mocks]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-8b9e30a670716b39995d2de0
    resource: repo://docs/DATASETS.md
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-e833a9665d2c8d32f4d2229a
    resource: repo://src/coding_tutor/database/connection.py
  - id: openwiki-source-f0a6e7dc03522b2682f88655
    resource: repo://tests/conftest.py
  - id: openwiki-source-0282644ab6d6a7c424248f4e
    resource: repo://tests/test_database.py
  - id: openwiki-source-9dd1c269b639dfa34bd360e7
    resource: repo://tests/test_generation.py
  - id: openwiki-source-5230999b290c20cd5367dde7
    resource: repo://tests/test_import.py
  - id: openwiki-source-5bf5d615e5204731b92ac41c
    resource: repo://tests/test_interview_modes.py
  - id: openwiki-source-c105c623359955ec0bd2c62c
    resource: repo://tests/test_progress.py
  - id: openwiki-source-dd61b439e43007c24fc72d70
    resource: repo://tests/test_quiz.py
  - id: openwiki-source-0720c5a3812dee82f153074a
    resource: repo://tests/test_ui.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Testing and verification strategy

The documented full-suite command is:

```powershell
uv run pytest -q
```

Pytest is configured to collect from `tests/` and add `src/` to the import path. (Sources: `repo://README.md#L215-L222`, `repo://pyproject.toml#L33-L35`.)

## Test boundaries

An autouse fixture removes provider credential variables before every test. Generation tests use mocked provider objects and synthetic responses; they verify validation, provenance, bounded context, safe provider errors, and persistence rollback without establishing that a live provider request succeeds. (Sources: `repo://tests/conftest.py#L1-L15`, `repo://tests/test_generation.py#L66-L111`, `repo://tests/test_generation.py#L365-L430`.)

Most database-backed tests use `get_test_db`, which creates an in-memory DuckDB database with migrations applied. Specific tests use temporary file-backed databases to check persistence across reopen. (Sources: `repo://src/coding_tutor/database/connection.py#L43-L48`, `repo://tests/test_progress.py#L126-L142`.)

Streamlit UI coverage uses `AppTest` for navigation and selected controls. The import tests exercise fixture records and importer helpers; they do not constitute a complete import of downloaded corpora. (Sources: `repo://tests/test_interview_modes.py#L142-L160`, `repo://tests/test_ui.py#L263-L329`, `repo://tests/test_import.py#L15-L44`, `repo://docs/DATASETS.md#L5-L15`.)

## Coverage map

| Area | Representative evidence |
| --- | --- |
| Database schema and migrations | `test_database.py` checks expected tables and migration idempotency; `test_progress.py` covers persistence and rollback. |
| Question generation | `test_generation.py` covers contracts, prompt/context, provenance, provider failures, and atomic save behavior. |
| Quizzes | `test_quiz.py` covers question selection, MCQ contract validation, staged scoring, retry, and progress. |
| Interviews and AI Questions | `test_interview_modes.py` covers local/AI mode behavior, persisted timing/report, adaptive context, and navigation. |
| Dataset import | `test_import.py` covers fixture normalization, idempotency, source identity, and input validation. |
| UI state | `test_ui.py` and Streamlit `AppTest` cases cover selected routing, editing, and error presentation. |

(Sources: `repo://tests/test_database.py#L7-L32`, `repo://tests/test_progress.py#L20-L218`, `repo://tests/test_generation.py#L133-L430`, `repo://tests/test_quiz.py#L32-L245`, `repo://tests/test_interview_modes.py#L19-L176`, `repo://tests/test_import.py#L15-L201`, `repo://tests/test_ui.py#L160-L496`.)

## Related pages

- [Repository guide](../quickstart.md)
- [Coding practice and question generation](../workflows/coding-practice.md)
- [Quiz lifecycle](../workflows/quizzes.md)
- [Interview sessions](../workflows/interviews.md)
