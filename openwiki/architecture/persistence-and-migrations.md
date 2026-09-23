---
type: architecture
title: Persistence and migrations
description: How database paths, DuckDB connections, migrations, and durable application records fit together.
tags: [duckdb, persistence, schema, migrations]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-e833a9665d2c8d32f4d2229a
    resource: repo://src/coding_tutor/database/connection.py
  - id: openwiki-source-a0ab611fed3fe28beef700bd
    resource: repo://src/coding_tutor/database/migrations.py
  - id: openwiki-source-ba4bcb766b9295038c946319
    resource: repo://src/coding_tutor/database/schema.py
  - id: openwiki-source-0282644ab6d6a7c424248f4e
    resource: repo://tests/test_database.py
  - id: openwiki-source-c105c623359955ec0bd2c62c
    resource: repo://tests/test_progress.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Persistence and migrations

The database layer resolves a selected DuckDB path, reuses a process-cached connection for that path, and applies any missing schema migrations before returning it. File-backed databases retain records across connection close and reopen; tests use separate in-memory connections for isolation.

## Connection lifecycle

When callers omit an explicit path, the connection module chooses the active Streamlit-run path, then `CODING_TUTOR_DB`, then `coding_tutor.duckdb`. Non-memory paths are resolved to absolute paths. `get_db` creates the parent directory as needed, opens and migrates the database once per resolved path, then returns the cached connection. `get_test_db` instead opens a fresh `:memory:` connection and applies migrations. (Sources: `repo://src/coding_tutor/database/connection.py#L17-L48`.)

## Migration behavior

`run_migrations` creates `schema_versions`, skips versions already recorded, and applies each remaining migration in its own transaction. The migration SQL and version record commit together; an exception rolls that transaction back and is re-raised. (Source: `repo://src/coding_tutor/database/migrations.py#L177-L202`.)

The database tests check that the expected tables exist, rerunning migrations leaves the schema version unchanged, and the current version is positive. A failure-path test injects a migration that alters a table and then errors; it verifies both the schema change and version row were rolled back. (Sources: `repo://tests/test_database.py#L7-L32`, `repo://tests/test_progress.py#L201-L218`.)

## Persisted data boundaries

The schema keeps normalized practice questions and their source records distinct from licensed interview items. Supporting tables store question assets, reference solutions, test cases, and generated-question metadata. Learner practice attempts and solution views have their own records; quiz attempts/items and AI-question or interview sessions/turns are modeled separately. (Sources: `repo://src/coding_tutor/database/schema.py#L24-L118`, `repo://src/coding_tutor/database/schema.py#L120-L193`, `repo://src/coding_tutor/database/schema.py#L207-L275`.)

A file-backed progress test inserts a practice attempt, closes the database, reopens the same file, reruns migrations, and reads back the saved submission. This verifies persistence for that tested path; it does not establish backup or multi-user guarantees. (Source: `repo://tests/test_progress.py#L126-L142`.)

## Related pages

- [Runtime and profile routing](runtime-routing.md)
- [Quiz lifecycle](../workflows/quizzes.md)
- [Interview sessions](../workflows/interviews.md)
