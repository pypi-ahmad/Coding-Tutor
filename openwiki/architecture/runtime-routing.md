---
type: architecture
title: Runtime and profile routing
description: How the Streamlit entry point selects a catalog profile, page, and DuckDB database.
tags: [streamlit, routing, catalog, profiles]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-17dded95897e01ee430228e3
    resource: repo://app.py
  - id: openwiki-source-6e3ad3af4ba1e470a3d4335c
    resource: repo://src/coding_tutor/catalog.py
  - id: openwiki-source-5bf5d615e5204731b92ac41c
    resource: repo://tests/test_interview_modes.py
  - id: openwiki-source-0720c5a3812dee82f153074a
    resource: repo://tests/test_ui.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Runtime and profile routing

`app.py` is the Streamlit entry point. It resolves a catalog profile, configures the page, initializes session state, applies profile constraints, and presents five navigation modes: Coding, Quiz, AI Questions, Interview, and Progress. Each mode is dispatched to its page renderer. (Sources: `repo://app.py#L18-L36`, `repo://app.py#L50-L68`.)

## Catalog profiles

`CODING_TUTOR_CATALOG` selects a profile and defaults to `all`. The profiles include `all`, `algorithm`, `data_analysis`, and `interview`; fixed profiles can constrain the question type, learning sources, database, and port. Applying a fixed profile pins its question type and replaces unsupported source or method selections with an allowed choice. (Sources: `repo://src/coding_tutor/catalog.py#L12-L50`, `repo://src/coding_tutor/catalog.py#L63-L83`.)

## Database routing

`CODING_TUTOR_DB`, when set, overrides the profile-based route. Without it, a fixed profile uses its configured database. The `all` profile routes Coding and Quiz to the catalog for the selected question type, while AI Questions, Interview, and Progress use the interview database. (Sources: `repo://app.py#L38-L48`, `repo://src/coding_tutor/catalog.py#L53-L60`.)

The connection layer resolves the chosen path and reuses a migrated connection for that resolved path; see [Persistence and migrations](persistence-and-migrations.md). This describes application routing, not a guarantee about concurrent access. (Source: `repo://src/coding_tutor/database/connection.py#L29-L40`.)

## Session-state behavior

Tests exercise Streamlit navigation into AI Questions and Interview. Other UI tests verify that changing a learning method while the code editor contains an unsaved draft requires a keep, discard, or cancel decision; keeping preserves the draft, while cancel restores the prior method. (Sources: `repo://tests/test_interview_modes.py#L142-L160`, `repo://tests/test_ui.py#L160-L184`.)

## Related pages

- [Persistence and migrations](persistence-and-migrations.md)
- [Interview sessions](../workflows/interviews.md)
- [Repository guide](../quickstart.md)
