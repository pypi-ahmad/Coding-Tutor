# Architecture Decisions

This document records technical decisions that are implemented and relevant to future contributors. It is intentionally narrower than the broader [Architecture](ARCHITECTURE.md) explanation and [Technical Reference](TECHNICAL_REFERENCE.md).

Commit hashes and dates below come from the repository's local Git history. File links point to the current implementation; a later change may supersede a decision even when its original commit remains in history.

## ADR-001: Use DuckDB for embedded application persistence

**Status:** Superseded by ADR-013

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
- Current evidence: [connection management](../src/coding_tutor/database/connection.py), [schema](../src/coding_tutor/database/schema.py), [migrations](../src/coding_tutor/database/migrations.py), and [database tests](../tests/test_database.py).

## ADR-002: Normalize questions as `algorithm` or `data_analysis`

**Status:** Accepted

### Context

The application imports heterogeneous dataset records and also saves AI-generated questions. UI behavior and validation need stable product categories independent of a raw source's directory or field names.

### Decision

Store each normalized question with exactly one of two types:

- `algorithm`, supporting Python, JavaScript/TypeScript, Java, and C++; or
- `data_analysis`, declaring SQL, Pandas, PySpark, and Polars.

Dataset catalog metadata and normalization rules set the type. The source directory name alone does not classify a record.

### Consequences

- The sidebar, editor templates, generation validators, importers, and persistence share one method matrix.
- Curated algorithm normalization requires all four declared languages; AI-generated algorithm questions store only their requested language.
- Data-analysis normalization requires the four declared methods.
- PySpark and Polars are authoring and static-review methods; they are not installed execution runtimes.

### Date and evidence

- Dataset normalization and question-source modes were added in commit `e66bf88` on 2026-08-19.
- Current evidence: the `questions.question_type` constraint in the [schema](../src/coding_tutor/database/schema.py), `DATA_ANALYSIS_METHODS` and `persist_question()` in [dataset normalization](../src/coding_tutor/dataset/normalization.py), `QUESTION_METHODS` in [question generation](../src/coding_tutor/generation/generator.py), and the [import](../tests/test_import.py) and [UI tests](../tests/test_ui.py).

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
- Current evidence: [dataset normalization](../src/coding_tutor/dataset/normalization.py), the [Spider](../src/coding_tutor/dataset/spider.py), [sql-create-context](../src/coding_tutor/dataset/sql_create_context.py), and [QueryPls](../src/coding_tutor/dataset/querypls.py) adapters, [generated-question validation](../src/coding_tutor/generation/validator.py), and [import tests](../tests/test_import.py).

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
- Current evidence: the [sidebar](../src/coding_tutor/ui/sidebar.py), [Practice page](../src/coding_tutor/ui/main_page.py), [question generator](../src/coding_tutor/generation/generator.py), [Quiz service](../src/coding_tutor/quiz/service.py), and [generation](../tests/test_generation.py), [Quiz](../tests/test_quiz.py), and [UI tests](../tests/test_ui.py).

## ADR-005: Use static AI assessment instead of executing learner code

**Status:** Accepted

### Context

The initial repository contained a subprocess-based evaluation runner. The current application does not provide an isolation boundary that removes access to secrets, the application database, source files, the network, and unrestricted local resources.

### Decision

Treat editor content as text and send it, with bounded question context, to the selected AI provider for static teacher-style review. Store deterministic execution status as `not_run`, label correctness and marks as AI estimates, and never claim that submissions were run or tested.

### Consequences

- Python, JavaScript/TypeScript, Java, C++, SQL, Pandas, PySpark, and Polars submissions are not executed by Coding Tutor.
- There is no runner, sandbox, execution timeout, resource limit, network block, or runtime dependency detection.
- Static feedback can miss runtime, type, ordering, performance, and edge-case failures.
- Corrected code can be applied reversibly in the editor while the original attempt remains unchanged.

### Alternatives considered

- **Subprocess-based learner-code execution — Superseded.** It existed in the initial commit and was removed rather than represented as secure isolation.

### Date and evidence

- Superseding change: commit `d759332` on 2026-08-19, titled “replace subprocess code execution with AI-only assessment,” which deleted `evaluation/runner.py`.
- Current evidence: [static feedback](../src/coding_tutor/evaluation/feedback.py), [attempt persistence](../src/coding_tutor/evaluation/persistence.py), the [submission handler](../src/coding_tutor/ui/submit_handler.py), and [evaluation tests](../tests/test_evaluation.py).

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
- Current evidence: the [provider modules](../src/coding_tutor/providers), [.env.example](../.env.example), [.gitignore](../.gitignore), [sidebar status](../src/coding_tutor/ui/sidebar.py), [configuration tests](../tests/test_config.py), and [provider tests](../tests/test_providers.py).

## ADR-007: Use file-backed prompts and strict structured-response validation

**Status:** Accepted

### Context

Question generation, assessment, teaching solutions, quiz preparation, AI Questions, and Interview planning, follow-ups, assessment, and reporting require different provider instructions and machine-readable responses.

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
- Current evidence: the [prompt loader](../src/coding_tutor/prompts/__init__.py), [generation prompt builders](../src/coding_tutor/generation/prompts.py), [Interview prompt builders](../src/coding_tutor/interview/prompts.py), [Interview AI contracts](../src/coding_tutor/interview/ai.py), [assessment](../src/coding_tutor/evaluation/feedback.py), [teaching solutions](../src/coding_tutor/evaluation/solutions.py), [Quiz service](../src/coding_tutor/quiz/service.py), and [prompt tests](../tests/test_prompts.py).

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
- Current evidence: the dataset [catalog](../src/coding_tutor/dataset/catalog.py), [inspection](../src/coding_tutor/dataset/inspection.py), [normalization](../src/coding_tutor/dataset/normalization.py), and [import orchestration](../src/coding_tutor/dataset/importer.py), the [schema uniqueness constraint](../src/coding_tutor/database/schema.py), and [import tests](../tests/test_import.py).

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
- Current evidence: [Practice persistence](../src/coding_tutor/evaluation/persistence.py), [Quiz persistence](../src/coding_tutor/quiz/persistence.py), the [schema](../src/coding_tutor/database/schema.py), [progress queries](../src/coding_tutor/database/progress.py), and the [evaluation](../tests/test_evaluation.py), [progress](../tests/test_progress.py), and [Quiz tests](../tests/test_quiz.py).

## ADR-010: Use Streamlit session state for local interaction state

**Status:** Accepted

### Context

The local browser interface needs to retain selections, the loaded question, editor drafts, and reversible corrections across Streamlit reruns. Durable learner history has a different lifecycle and belongs in DuckDB.

### Decision

Use Streamlit as the application entry point and `st.session_state` for transient UI state. Keep Practice editor drafts keyed by question and method, and require an explicit keep, discard, or cancel choice before a selection change can replace a dirty draft. Persist completed attempts and Quiz state in DuckDB instead of relying on session state.

### Consequences

- The application uses one Python UI process and does not require a separate frontend build.
- Widget interactions rerun the script, so state keys and deferred selection changes are part of the UI contract.
- Unsubmitted Practice drafts and correction backups are process-session state and can be lost when the session ends; saved attempts and Quiz state remain in DuckDB.
- The current interface is local and single-user oriented; it does not implement authentication or multi-user isolation.

### Date and evidence

- The Streamlit entry point and session-state foundation were introduced in commit `9cac9c4` on 2026-08-18.
- Current evidence: the [application entry point](../app.py), [session-state helpers](../src/coding_tutor/quiz/session.py), [sidebar state flow](../src/coding_tutor/ui/sidebar.py), [UI tests](../tests/test_ui.py), and [configuration tests](../tests/test_config.py).

## ADR-011: Route AI operations through a common provider contract and verified-model registry

**Status:** Accepted

### Context

Question generation, assessment, teaching solutions, and Quiz generation can use multiple providers. Callers need one request boundary, while the UI must avoid presenting an unverified model as usable.

### Decision

Define provider adapters through `BaseProvider`, describe model choices with `ModelOption`, and resolve adapters through the provider registry. Only models marked `verified` are selectable. AI operations validate the provider/model association and configuration status and do not silently substitute another model.

### Consequences

- Application services can call providers through one interface rather than provider-specific UI branches.
- Unverified choices remain nonselectable and can expose a setup/status explanation without exposing credentials.
- Configuration status proves only that the required environment variable is present; it does not verify credentials, quota, model entitlement, or live service availability.
- Adding a provider or model requires adapter, registry, configuration, and test updates.

### Date and evidence

- The provider contract and registry were introduced in commit `9cac9c4` on 2026-08-18; verified provider settings were updated in commit `25a19b7` on 2026-08-19.
- Current evidence: the [provider contract](../src/coding_tutor/providers/base.py), [registry](../src/coding_tutor/providers/registry.py), [model configuration](../src/coding_tutor/providers/config.py), [sidebar filtering](../src/coding_tutor/ui/sidebar.py), [configuration tests](../tests/test_config.py), and [provider tests](../tests/test_providers.py).

## ADR-012: Represent expected AI generation failures as typed results

**Status:** Accepted

### Context

Question generation and teaching-solution requests have expected failure modes such as missing configuration, unsupported selections, malformed provider output, and persistence failure. The UI needs stable, safe failure handling without displaying raw provider exceptions.

### Decision

Return `GenerationResult`/`GenerationFailure` and `SolutionGenerationResult`/`SolutionFailure` from the corresponding services. Map their failure categories to user-facing messages in the UI, and contain provider or validation exception details within the service boundary.

### Consequences

- Expected failures are explicit and can be asserted without matching SDK-specific exception text.
- These UI paths do not need to render raw provider error details.
- Question persistence failure is distinguishable from response validation failure, and generated-question writes remain transactional.
- Assessment and Quiz flows retain their own error and persistence contracts; this decision does not impose one result type on every AI operation.

### Date and evidence

- Typed generation and solution failure handling was introduced or refined in commit `d759332` on 2026-08-19.
- Current evidence: [question-generation results](../src/coding_tutor/generation/generator.py), [teaching-solution results](../src/coding_tutor/evaluation/solutions.py), [generation UI handling](../src/coding_tutor/ui/main_page.py), [solution UI handling](../src/coding_tutor/ui/solution_view.py), [generation tests](../tests/test_generation.py), [solution tests](../tests/test_solutions.py), and [UI tests](../tests/test_ui.py).

## ADR-013: Route activities across three DuckDB catalogs

**Status:** Accepted

### Context

The original application used one default DuckDB file. Algorithm practice, data-analysis practice, and interview workflows now have independent source catalogs, schemas, import lifecycles, and progress views. Normal unified operation needs deterministic ownership for each activity without requiring separate database services.

### Decision

Use `Dataset/catalogs/algorithm.duckdb` for algorithm Coding and Quiz activity, `Dataset/catalogs/data_analysis.duckdb` for data-analysis Coding and Quiz activity, and `Dataset/catalogs/interview.duckdb` for AI Questions and Interview activity. Progress reads the applicable catalogs together.

Retain `CODING_TUTOR_DB` as an advanced compatibility and test override for Coding, Quiz, Progress, and import commands that omit `--database`. AI Questions and Interview continue to open the interview catalog explicitly.

### Consequences

- Normal runtime storage is separated by activity while remaining local and embedded.
- The unified Progress page combines results across the three catalogs.
- Raw dataset directories remain import inputs and are not queried during normal practice.
- The override is intentionally not a universal replacement for all three runtime catalogs.
- Users must back up each catalog that contains activity they want to retain.

### Date and evidence

- Independent catalog profiles were introduced in commit `14fa303` on 2026-08-20.
- AI Questions and Interview catalog routing was introduced in commit `e38e305` on 2026-08-20.
- Current evidence: [catalog routing](../src/coding_tutor/catalog.py), [application entry point](../app.py), [interview service](../src/coding_tutor/interview/service.py), and [progress UI](../src/coding_tutor/ui/progress_page.py).
