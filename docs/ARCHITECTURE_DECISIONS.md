# Architecture Decisions

This document records technical decisions that are implemented and relevant to future contributors. It is intentionally narrower than the broader [Architecture](ARCHITECTURE.md) explanation and [Technical Reference](TECHNICAL_REFERENCE.md).

## ADR-001: Use DuckDB for embedded application persistence

**Status:** Accepted

### Context

Coding Tutor is a local Streamlit application that needs persistent questions, provenance, learner attempts, feedback, quizzes, and progress without a separate database service.

### Decision

Use one embedded DuckDB database. The default file is `coding_tutor.duckdb`; `CODING_TUTOR_DB` can select another path. Apply versioned schema migrations when the application opens the database.

### Consequences

- Questions, normalized assets, progress, attempts, AI feedback, solution views, and quiz state persist across application restarts.
- Tests can use an in-memory DuckDB database.
- The application remains oriented toward one local user rather than concurrent public or multi-user deployment.
- Users are responsible for filesystem access, backup, retention, and deletion. The application does not encrypt the database.
- DuckDB stores exercise context but does not execute learner SQL.

### Date and evidence

- Introduced in commit `9cac9c4` on 2026-08-18.
- Quiz schema added in commit `b92b458` on 2026-08-19.
- Current evidence: `database/connection.py`, `database/schema.py`, `database/migrations.py`, and `tests/test_database.py`.

## ADR-002: Normalize questions as `algorithm` or `data_analysis`

**Status:** Accepted

### Context

The application imports heterogeneous dataset records and also saves AI-generated questions. UI behavior and validation need stable product categories independent of a raw source's directory or field names.

### Decision

Store each normalized question with exactly one of two types:

- `algorithm`, supporting Python; or
- `data_analysis`, declaring SQL, Pandas, PySpark, and Polars.

Dataset catalog metadata and normalization rules set the type. The source directory name alone does not classify a record.

### Consequences

- The sidebar, editor templates, generation validators, importers, and persistence share one method matrix.
- Algorithm normalization rejects method sets other than Python.
- Data-analysis normalization requires the four declared methods.
- PySpark and Polars are authoring and static-review methods; they are not installed execution runtimes.

### Date and evidence

- Dataset normalization and question-source modes were added in commit `e66bf88` on 2026-08-19.
- Current evidence: the `questions.question_type` constraint in `database/schema.py`, `DATA_ANALYSIS_METHODS` and `persist_question()` in `dataset/normalization.py`, `QUESTION_METHODS` in `generation/generator.py`, and importer/UI tests.

## ADR-003: Require shared deterministic assets for complete data-analysis tasks

**Status:** Accepted

### Context

A schema or SQL answer alone does not provide the rows and expected output needed to express the same analytical task through SQL, Pandas, PySpark, and Polars.

### Decision

Treat a data-analysis question as complete only when it has all three shared assets:

- schema;
- fixture data; and
- expected result.

AI-generated data-analysis questions must also provide starter templates and reference solutions for all four methods. Imported records missing the shared assets remain incomplete rather than receiving invented rows or expected output.

### Consequences

- The curated picker excludes incomplete imported SQL records.
- One complete analytical task can be presented through four method-specific editors against the same context.
- Stored test/expected data remains static context because learner code is not executed.
- Current Spider, sql-create-context, and QueryPls imports remain incomplete under this rule.

### Date and evidence

- Implemented with the dataset normalization pipeline in commit `e66bf88` on 2026-08-19.
- Current evidence: `dataset/normalization.py`, the three SQL-family adapters, `generation/validator.py`, and `test_sql_create_context_import_fixture` in `tests/test_import.py`.

## ADR-004: Support curated, AI-generated, and mixed question sources

**Status:** Accepted

### Context

The application supports repeatable imported exercises and provider-generated exercises selected by difficulty, type, topic, and method.

### Decision

Expose three learning sources:

- curated dataset questions from complete normalized records;
- newly generated, strictly validated AI questions; and
- mixed selection, choosing between available curated and generated sources.

Persist accepted generated questions in the same question model, with separate provider, model, prompt-version, and generation metadata.

### Consequences

- Practice and Quiz modes can reuse the same question IDs and provenance-aware storage.
- Curated questions remain usable without a provider after import; AI generation requires a configured provider.
- Malformed or incomplete generated questions are rejected before persistence.
- A mixed request falls back to the source that is available when only one can provide a question.

### Date and evidence

- Added in commit `e66bf88` on 2026-08-19.
- Current evidence: `ui/sidebar.py`, `ui/main_page.py`, `generation/generator.py`, `quiz/service.py`, and generation/UI tests.

## ADR-005: Use static AI assessment instead of executing learner code

**Status:** Accepted

### Context

The initial repository contained a subprocess-based evaluation runner. The current application does not provide an isolation boundary that removes access to secrets, the application database, source files, the network, and unrestricted local resources.

### Decision

Treat editor content as text and send it, with bounded question context, to the selected AI provider for static teacher-style review. Store deterministic execution status as `not_run`, label correctness and marks as AI estimates, and never claim that submissions were run or tested.

### Consequences

- Python, SQL, Pandas, PySpark, and Polars submissions are not executed by Coding Tutor.
- There is no runner, sandbox, execution timeout, resource limit, network block, or runtime dependency detection.
- Static feedback can miss runtime, type, ordering, performance, and edge-case failures.
- Corrected code can be applied reversibly in the editor while the original attempt remains unchanged.

### Alternatives considered

- **Subprocess-based learner-code execution — Superseded.** It existed in the initial commit and was removed rather than represented as secure isolation.

### Date and evidence

- Superseding change: commit `d759332` on 2026-08-19, titled “replace subprocess code execution with AI-only assessment,” which deleted `evaluation/runner.py`.
- Current evidence: `evaluation/feedback.py`, `evaluation/persistence.py`, `ui/submit_handler.py`, and `tests/test_evaluation.py`.

## ADR-006: Read credentials from process environment variables

**Status:** Accepted

### Context

Provider adapters and the optional dataset downloader need user-supplied credentials without storing them in source-controlled configuration or DuckDB.

### Decision

Read provider credentials from `OPENAI_API_KEY`, `AGNES_API_KEY`, and `GOOGLE_API_KEY`. Read optional OpenAI endpoint configuration from `OPENAI_BASE_URL`. The dataset downloader can read `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN`.

Use `.env.example` only as a blank names reference; the application does not load it. Report provider configuration as a Boolean presence check without rendering credential values.

### Consequences

- Each user supplies credentials through the environment of the process that launches Streamlit.
- Restarting the process is required for newly set variables to reach the application.
- Presence does not prove authentication, quota, model access, or provider availability.
- `.gitignore` reduces accidental commits of `.env` and Streamlit secret files but is not a secret scanner.

### Date and evidence

- Environment-backed provider configuration exists from commit `9cac9c4` on 2026-08-18.
- Current evidence: provider adapters, `.env.example`, `.gitignore`, `ui/sidebar.py`, `tests/test_config.py`, and `tests/test_providers.py`.

## ADR-007: Use file-backed prompts and strict structured-response validation

**Status:** Accepted

### Context

Question generation, assessment, teaching solutions, and quiz preparation require different provider instructions and machine-readable responses.

### Decision

Store prompt templates as registered Markdown package resources under `src/coding_tutor/prompts/`. Render only the exact declared placeholder set. Send shared rules as the system instruction and validate operation-specific JSON before display or persistence.

Store prompt-version metadata for generated questions. Use a prompt version in the teaching-solution session cache key; assessment and quiz records do not currently persist a uniform prompt version.

### Consequences

- Prompt changes are reviewable in Git and are not embedded across provider adapters.
- Unknown prompt filenames and placeholder mismatches fail before a provider request.
- Exact-schema validation blocks malformed application data but does not prove semantic correctness.
- Historical traceability differs by interaction because prompt versions are not persisted uniformly.

### Date and evidence

- File-backed prompt wiring was added in commit `20e65bb` on 2026-08-19.
- Current evidence: `prompts/__init__.py`, `generation/prompts.py`, evaluation and quiz services, and `tests/test_prompts.py`.

## ADR-008: Preserve dataset provenance and make imports idempotent

**Status:** Accepted

### Context

Imported datasets use different formats, identifiers, licenses, and field layouts. Re-running an import must not duplicate questions or erase the connection to the original source.

### Decision

Inspect configured source formats and required fields before parsing. Normalize each record with dataset name, stable source key, relative source file, available original ID/revision/index, license, attribution, and import-run identity. Enforce uniqueness on `(dataset_name, source_key)` and insert each question with its source, assets, references, and cases in one transaction.

### Consequences

- Re-running an import skips records with the same stable source identity.
- Raw source files remain separate from normalized DuckDB records and are not renamed or overwritten by importers.
- Provenance supports traceability but does not establish redistribution permission or guarantee that license metadata is complete.
- Import failures and per-run counts are retained in `import_runs`.

### Date and evidence

- Added with the dataset import pipeline in commit `e66bf88` on 2026-08-19.
- Current evidence: `dataset/catalog.py`, `dataset/inspection.py`, `dataset/normalization.py`, `dataset/importer.py`, the source adapters, schema uniqueness constraint, and `tests/test_import.py`.

## ADR-009: Preserve immutable practice attempts and separate quiz persistence

**Status:** Accepted

### Context

Learners can submit the same question repeatedly, apply a suggested correction in the editor, and resume unfinished quizzes. Practice history and quiz lifecycle state have different shapes.

### Decision

Create a new `attempts` row for every Practice submission and never replace its submitted text. Store Quiz attempts and items in `quiz_attempts` and `quiz_items`, referencing the shared question records rather than representing quiz answers as Practice attempts.

### Consequences

- Repeated Practice attempts remain independently visible in progress history.
- Editor correction and restoration do not mutate the saved original submission.
- Quiz drafts, item scores, retry errors, and aggregate results persist separately while retaining question provenance.
- Progress queries must combine practice and quiz summaries deliberately rather than treating them as the same event type.

### Date and evidence

- Immutable Practice attempts exist in the current evaluation persistence flow; separate Quiz schema was added in commit `b92b458` on 2026-08-19 and its lifecycle in `e66bf88` on the same date.
- Current evidence: `evaluation/persistence.py`, `quiz/persistence.py`, `database/schema.py`, `database/progress.py`, and evaluation/progress/quiz tests.
