# Coding Tutor — Technical Reference

> **Document type:** Reference (Diátaxis) — information-oriented, dictionary-style. For architectural narrative, rationale, and decision records, see [Project_Architecture_Blueprint.md](../Project_Architecture_Blueprint.md). For task-based instructions, see [how-to-use.md](how-to-use.md).

This document is a standalone technical reference for Coding Tutor's internals: entry points, environment variables, package layout, domain types, database schema, provider/model registry, CLI scripts, and test suite. Every entry is sourced directly from the current codebase.

---

## Contents

- [1. Entry Points](#1-entry-points)
- [2. Environment Variables](#2-environment-variables)
- [3. Package Reference](#3-package-reference)
- [4. Domain Types Reference](#4-domain-types-reference)
- [5. Database Schema Reference](#5-database-schema-reference)
- [6. Migrations Reference](#6-migrations-reference)
- [7. Provider and Model Registry](#7-provider-and-model-registry)
- [8. CLI Scripts Reference](#8-cli-scripts-reference)
- [9. Configuration Reference](#9-configuration-reference)
- [10. Runtime Boundaries, Calculations, and Extension Points](#10-runtime-boundaries-calculations-and-extension-points)
- [11. Testing Reference](#11-testing-reference)

---

## 1. Entry Points

| Entry point | Command | Purpose |
|---|---|---|
| `app.py` | `uv run streamlit run app.py` | Streamlit application entry point; sets page config, initializes session state, renders sidebar, routes between Practice/Quiz/Progress pages |
| `launch_app.cmd` | Double-click (Windows) | Checks for `uv` and exits with the official installation URL if it is missing; otherwise creates `.venv` when needed, runs `uv sync --locked`, and launches `app.py` on `127.0.0.1:8551` |
| `scripts/download_datasets.py` | `uv run python scripts/download_datasets.py` | Downloads raw dataset files from Hugging Face Hub into the gitignored `Dataset/` directory |
| `scripts/import_datasets.py` | `uv run python scripts/import_datasets.py` | Normalizes downloaded dataset files into the local DuckDB database |
| Test suite | `uv run pytest -q` | Runs all tests against in-memory DuckDB with mocked providers |

**Default network binding:** `127.0.0.1:8551` (configured in `.streamlit/config.toml`).

**`app.py` routing:**
```python
page = st.sidebar.radio("Navigation", ["🎓 Practice", "🧠 Quiz", "📈 Progress"], key="nav_page")
```
Practice → `ui.main_page.render_main_page()`; Quiz → `ui.quiz_page.render_quiz_page()`; Progress → `ui.progress_page.render_progress_page()`.

---

## 2. Environment Variables

| Variable | Read by | Required | Effect when unset |
|---|---|---|---|
| `OPENAI_API_KEY` | `providers/openai_provider.py` | For OpenAI | `is_configured()` returns `False`; OpenAI marked unavailable in sidebar |
| `OPENAI_BASE_URL` | `providers/openai_provider.py` | No | Falls back to the OpenAI SDK's default endpoint |
| `AGNES_API_KEY` | `providers/agnes_provider.py` | For Agnes AI | `is_configured()` returns `False` |
| `GOOGLE_API_KEY` | `providers/gemini_provider.py` | For Gemini | `is_configured()` returns `False` |
| `CODING_TUTOR_DB` | `database/connection.py` | No | Defaults to `coding_tutor.duckdb` in the working directory |
| `HF_TOKEN` | `scripts/download_datasets.py` | No | Falls back to `HUGGING_FACE_HUB_TOKEN`, then anonymous (rate-limited) download |
| `HUGGING_FACE_HUB_TOKEN` | `scripts/download_datasets.py` | No | Fallback name checked after `HF_TOKEN` |

No other environment variable is read anywhere in the source tree. `.env` files are never loaded — `.env.example` exists only as a documentation template with empty values.

---

## 3. Package Reference

### `coding_tutor.database`

| Symbol | Signature | Purpose |
|---|---|---|
| `connection.get_db` | `get_db(path: str \| None = None) -> DuckDBPyConnection` | Returns the process-wide singleton connection; creates the file and runs migrations on first call |
| `connection.get_test_db` | `get_test_db() -> DuckDBPyConnection` | Returns a fresh `:memory:` connection with migrations applied for database-backed tests |
| `connection.reset_connection` | `reset_connection() -> None` | Closes and clears the singleton (test teardown) |
| `schema.SCHEMA_SQL` | `str` constant | Full DDL for all 12 tables, applied as migration version 1 |
| `migrations.MIGRATIONS` | `list[tuple[int, str, str]]` | `(version, description, sql)` triples applied in order |
| `migrations.run_migrations` | `run_migrations(conn) -> None` | Applies unapplied migrations transactionally |
| `migrations.get_schema_version` | `get_schema_version(conn) -> int` | Highest applied migration version |
| `progress.get_all_attempts` | `get_all_attempts(conn, question_type=None, difficulty=None, method=None) -> list[dict]` | Every matching attempt, newest first per question |
| `progress.get_progress_summary` | `get_progress_summary(conn, ...) -> dict` | Combined-query aggregate: total attempts, attempted/solved/assessed question counts, recent attempts, by-difficulty breakdown |
| `progress.get_question_attempts` | `get_question_attempts(conn, question_id) -> list[dict]` | All attempts for one question |
| `progress.get_quiz_progress` | `get_quiz_progress(conn, ...) -> dict` | Quiz-only aggregate and attempt list, fully independent of practice `attempts` |
| `progress.get_solution_view_history` | `get_solution_view_history(conn, limit=100, ...) -> list[dict]` | Recent solution-view events |
| `progress.SOLVED_THRESHOLD` | `float = 80.0` | Minimum AI-estimated percentage counted as "solved" |

### `coding_tutor.providers`

| Symbol | Signature | Purpose |
|---|---|---|
| `base.BaseProvider` | ABC with `is_configured()`, `get_model_options()`, `chat()` | Contract every provider implements |
| `base.ModelOption` | dataclass: `provider, model_id, display_name, verified, unverified_reason, documentation_url, extra_params` | Selectable model with verification metadata |
| `base.ChatMessage` | dataclass: `role, content` | One message in a chat request |
| `base.ChatResponse` | dataclass: `content, model, provider` | Normalized provider response |
| `registry.PROVIDERS` | `dict[str, BaseProvider]` | `{"openai": ..., "agnes": ..., "gemini": ...}` |
| `registry.PROVIDER_DISPLAY_NAMES` | `dict[str, str]` | UI display names |
| `registry.get_provider` | `get_provider(name) -> BaseProvider` | Raises `KeyError` for unknown names |
| `config.get_verified_models` | `get_verified_models() -> list[ModelOption]` | All `verified=True` models across providers |
| `config.get_models_for_provider` | `get_models_for_provider(provider) -> list[ModelOption]` | All models (verified and not) for one provider |

### `coding_tutor.generation`

| Symbol | Signature | Purpose |
|---|---|---|
| `generator.generate_question` | `generate_question(provider_name, model, question_type, difficulty, method, topic="general") -> GenerationResult` | Full pipeline: validate inputs → call provider → parse → validate schema → persist atomically |
| `generator.GenerationResult` | frozen dataclass: `question_id, failure, detail`, `.ok` property | Never-raise return type |
| `generator.GenerationFailure` | `str, Enum` | `INVALID_SELECTION`, `MODEL_UNAVAILABLE`, `PROVIDER_UNAVAILABLE`, `PROVIDER_ERROR`, `MALFORMED_RESPONSE`, `INCOMPLETE_RESPONSE`, `STORAGE_ERROR` |
| `generator.QUESTION_METHODS` | `dict` | `{"algorithm": ("python",), "data_analysis": ("sql","pandas","pyspark","polars")}` |
| `generator.MAX_TOPIC_LENGTH` | `int = 100` | Topic string length cap |
| `validator.validate_algorithm_question` | `validate_algorithm_question(data, *, expected_difficulty) -> None` | Raises `ValidationError` on schema mismatch |
| `validator.validate_data_analysis_question` | `validate_data_analysis_question(data, *, expected_difficulty) -> None` | Raises `ValidationError`; requires exactly SQL/Pandas/PySpark/Polars coverage |
| `prompts.build_algorithm_user_prompt` | `(difficulty, method, topic) -> str` | Embeds the exact expected JSON schema in the prompt text |
| `prompts.build_data_analysis_user_prompt` | `(difficulty, method, topic) -> str` | Same, for the multi-method data-analysis schema |
| `prompts.PROMPT_VERSION` | `str = "v3"` | Recorded per generated question in `ai_generated_questions.prompt_version` |

#### Markdown prompt contracts

`coding_tutor.prompts` loads only allowlisted Markdown files and replaces an exact set of `{{placeholder}}` values. Missing, extra, non-text, or unknown prompt inputs raise `ValueError` before a provider request.

| Prompt file | Runtime use | Response enforcement |
|---|---|---|
| `shared_rules.md` | System instruction for question generation, assessment, teaching solutions, and MCQ generation | Instructs the model to treat marked content as untrusted, perform static reasoning only, and return JSON |
| `algorithm_question_generator.md` | Algorithm question generation | `validate_algorithm_question()` requires the current algorithm schema, requested difficulty, examples, starter code, and deterministic test-case records |
| `data_analysis_question_generator.md` | Data-analysis question generation | `validate_data_analysis_question()` requires schema SQL, fixture rows, expected rows, and exact SQL/Pandas/PySpark/Polars starter and solution maps |
| `static_code_reviewer.md` | `Done` assessment | `_parse_assessment()` requires exactly five bounded fields and a numeric percentage from 0 through 100 |
| `solution_teacher.md` | On-demand teaching solutions | `_validate_payload()` limits algorithms to three approaches and data analysis to one requested-method solution; code must contain comments |
| `quiz_generator.md` | Four-option MCQ preparation | `_validate_mcq_response()` requires one unique four-option item per selected question and exactly one valid answer ID |
| `dataset_record_converter.md` | Registered and render-tested only | No runtime dataset-import path currently calls this prompt |

Question generation persists `PROMPT_VERSION` and generation metadata. The solution version is used in the Streamlit cache key. Assessment, solution-view, and quiz persistence do not currently store a prompt filename/version, so they must not be described as fully prompt-versioned audit records.

### `coding_tutor.evaluation`

| Symbol | Signature | Purpose |
|---|---|---|
| `feedback.validate_assessment_request` | `(question, submitted_code, method, provider_name, model) -> BaseProvider` | Pre-flight checks; raises `AssessmentError` |
| `feedback.assess_solution` | `(question, submitted_code, method, provider_name, model) -> AIAssessment` | Builds bounded context, calls provider, strictly parses response |
| `feedback.AIAssessment` | frozen dataclass: `estimated_percentage_correct, marks, identified_mistakes, explanation, suggested_correction, corrected_code, model_id, provider` | |
| `feedback.AssessmentError` | `ValueError` subclass | Raised for any invalid submission or malformed AI response |
| `feedback.MAX_SUBMISSION_CHARS` | `int = 12_000` | Learner submission length cap |
| `persistence.create_attempt` | `(question_id, method, submitted_code, provider=None, model_id=None) -> str` | Inserts an immutable attempt row, `deterministic_test_result='not_run'` |
| `persistence.complete_attempt` | `(attempt_id, assessment: AIAssessment) -> None` | Records AI-estimated result |
| `persistence.fail_attempt` | `(attempt_id, error: str) -> None` | Records a sanitized failure message (truncated to 2000 chars) |
| `persistence.mark_solution_viewed` | `(attempt_id) -> None` | Sets `attempts.solution_viewed = true` |
| `persistence.record_solution_method` | `(question_id, attempt_id, method, view_id=None) -> str` | Appends a viewed method to a `solution_views` row, creating one if `view_id` is `None` |
| `solutions.generate_teaching_solutions` | `(question, method, provider_name, model) -> SolutionGenerationResult` | Validated, multi-approach (algorithm) or single-approach (data analysis) teaching solution generation |
| `solutions.TeachingSolution` | frozen dataclass: `title, code, explanation, theory, complexity` | |
| `solutions.SolutionBundle` | frozen dataclass: `method, solutions, multiple_approaches_meaningful, availability_note, provider, model_id` | |
| `solutions.SolutionGenerationResult` | frozen dataclass: `bundle, failure` | |
| `solutions.SolutionFailure` | `str, Enum` | `UNAVAILABLE`, `INCOMPLETE_CONTEXT`, `PROVIDER_ERROR`, `INVALID_RESPONSE` |
| `solutions.PROMPT_VERSION` | `str = "solution-v2"` | Used as part of the Streamlit session-state cache key |

### `coding_tutor.dataset`

| Symbol | Signature | Purpose |
|---|---|---|
| `catalog.DatasetSpec` | frozen dataclass: `key, dataset_name, module, question_type, source_format, file_pattern, required_fields, license, attribution, supported_methods` | One entry per supported dataset |
| `catalog.DATASET_SPECS` | `tuple[DatasetSpec, ...]` | All 7 supported datasets |
| `catalog.SPECS_BY_KEY` / `SPECS_BY_NAME` | `dict[str, DatasetSpec]` | Lookup by CLI key or Hugging Face dataset name |
| `importer.run_import` | `(conn, datasets=None, dataset_root=None) -> list[ImportResult]` | Orchestrates one or more imports; logs to `import_runs` |
| `importer.ImportResult` | dataclass: `dataset_name, imported, skipped, status, error` | |
| `importer.DATASET_ROOT` | `Path` | `<repo_root>/Dataset` |
| `inspection.inspect_dataset` | `(spec, root) -> list[InspectedFile]` | Sniffs real file format before parsing |
| `normalization.persist_question` | Shared write path called by every per-dataset importer | Idempotency check + `questions`/`question_assets`/`reference_solutions`/`question_test_cases` inserts |
| `normalization.stable_source_key` | `(dataset_name, original_id) -> str` | Deterministic dedup key |
| `leetcode.py`, `apps_dataset.py`, `taco.py`, `codecontests.py` | each exports `import_dataset(conn, dataset_root, run_id, sources, spec) -> ImportResult` | Algorithm dataset importers |
| `spider.py`, `sql_create_context.py`, `querypls.py` | same signature | Data-analysis dataset importers (schema-only; `is_complete=false`) |

### `coding_tutor.quiz`

| Symbol | Signature | Purpose |
|---|---|---|
| `session.initialize_session_state` | `(state=None) -> None` | Sets session defaults; applies queued control updates from the prior run |
| `session.load_question` | `(question_id) -> None` | Loads a question + source/generation metadata into `st.session_state["current_question"]` |
| `session.request_learning_change` / `resolve_pending_learning_change` | | Unsaved-editor-draft confirmation flow |
| `session.METHODS_BY_QUESTION_TYPE` | `dict` | `{"algorithm": ("python",), "data_analysis": ("sql","pandas","pyspark","polars")}` |
| `service.start_quiz` | `(settings: dict, model) -> str` | Creates the durable `quiz_attempts` row, then prepares questions and MCQs |
| `service.retry_preparation` | `(attempt_id, model) -> None` | Retries a failed preparation step |
| `service.evaluate_quiz` | `(attempt_id, provider_name, model) -> bool` | Scores all unscored items; returns `False` if any AI call failed (state is retryable) |
| `service.QuizError` | `ValueError` subclass | The only exception type surfaced to the Quiz UI |
| `persistence.create_quiz_attempt` / `insert_quiz_items` / `save_mcq_content` / `score_item` / `complete_quiz` | | DuckDB writes for `quiz_attempts` / `quiz_items` |
| `persistence.latest_unfinished_quiz` | `() -> str \| None` | Drives automatic single-quiz resume |
| `persistence.UNFINISHED_STATUSES` | `tuple` | `("preparing", "preparation_error", "in_progress", "evaluating", "evaluation_error")` |
| `templates.EDITOR_TEMPLATES` / `get_editor_template` | `dict[str, str]` / `(method) -> str` | Starter code per method when no dataset asset exists |

### `coding_tutor.ui`

| Module | Public entry point | Notes |
|---|---|---|
| `sidebar.py` | `render_sidebar()`, `render_pending_learning_change_dialog()` | Provider/model, question source, type, difficulty, method, topic, Quiz setup |
| `main_page.py` | `render_main_page()` | Question picker + problem display + editor + action panel |
| `submit_handler.py` | `handle_submit(question, method)` | Persists attempt first, then requests AI assessment; every failure path calls `fail_attempt()` |
| `evaluation_view.py` | `render_evaluation(question, assessment, attempt_id, method)` | Assessment display + correction apply/restore |
| `solution_view.py` | `render_solution_view(question, panel)` | Stored + on-demand AI teaching solutions |
| `quiz_page.py` | `render_quiz_page()` | Start / preparation / answering / completed screens |
| `progress_page.py` | `render_progress_page()` | Filtered practice, quiz, and solution-view dashboards |

---

## 4. Domain Types Reference

| Type | Module | Shape |
|---|---|---|
| `ModelOption` | `providers.base` | `provider: str, model_id: str, display_name: str, verified: bool, unverified_reason: str = "", documentation_url: str = "", extra_params: dict = {}` |
| `ChatMessage` | `providers.base` | `role: str, content: str` |
| `ChatResponse` | `providers.base` | `content: str, model: str, provider: str` |
| `GenerationResult` | `generation.generator` | `question_id: str \| None, failure: GenerationFailure \| None, detail: str` — `.ok` is `question_id is not None and failure is None` |
| `GenerationFailure` | `generation.generator` | `str, Enum` — 7 values (see §3) |
| `AIAssessment` | `evaluation.feedback` | `estimated_percentage_correct: float, marks: float, identified_mistakes: list[str], explanation: str, suggested_correction: str, corrected_code: str \| None, model_id: str, provider: str` |
| `AssessmentError` | `evaluation.feedback` | `ValueError` subclass |
| `TeachingSolution` | `evaluation.solutions` | `title: str, code: str, explanation: str, theory: str, complexity: str \| None` |
| `SolutionBundle` | `evaluation.solutions` | `method: str, solutions: tuple[TeachingSolution, ...], multiple_approaches_meaningful: bool, availability_note: str \| None, provider: str, model_id: str` |
| `SolutionGenerationResult` | `evaluation.solutions` | `bundle: SolutionBundle \| None, failure: SolutionFailure \| None` |
| `SolutionFailure` | `evaluation.solutions` | `str, Enum` — 4 values (see §3) |
| `QuizError` | `quiz.service` | `ValueError` subclass — the only exception the Quiz UI catches |
| `DatasetSpec` | `dataset.catalog` | `key, dataset_name, module, question_type, source_format, file_pattern, required_fields: frozenset, license, attribution, supported_methods: tuple` |
| `ImportResult` | `dataset.importer` | `dataset_name: str, imported: int, skipped: int, status: str, error: str \| None` |

**Standard failure pattern:** `GenerationResult`/`GenerationFailure` and `SolutionGenerationResult`/`SolutionFailure` never raise for expected failure modes — every failure is an enumerable value. `AssessmentError` and `QuizError` are the two exception types the UI actually catches; every other exception path is converted to a sanitized message before reaching a `st.error()`/`st.warning()` call.

---

## 5. Database Schema Reference

Database: DuckDB, single file (`coding_tutor.duckdb` by default, or `$CODING_TUTOR_DB`). The 12-table current schema is defined in `database/schema.py` (`SCHEMA_SQL`); compatibility migrations upgrade existing database files.

### `schema_versions`
| Column | Type | Notes |
|---|---|---|
| `version` | `INTEGER PK` | |
| `applied_at` | `TIMESTAMPTZ` | default `now()` |
| `description` | `TEXT` | |

### `import_runs`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | default `gen_random_uuid()` |
| `dataset_name` | `TEXT NOT NULL` | |
| `started_at` / `completed_at` | `TIMESTAMPTZ` | |
| `records_imported` / `records_skipped` | `INTEGER` | default `0` |
| `status` | `TEXT NOT NULL` | default `'running'`; set to `'completed'` or `'failed'` |
| `error_message` | `TEXT` | |

### `question_sources`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `dataset_name` | `TEXT NOT NULL` | |
| `original_id` | `TEXT` | dataset's own record ID |
| `source_key` | `TEXT` | deterministic dedup key (migration 3) |
| `source_file` | `TEXT` | path relative to `Dataset/` |
| `source_revision` | `TEXT` | Hugging Face snapshot revision, if known |
| `source_record_index` | `BIGINT` | line/row index within the source file |
| `license` / `attribution` | `TEXT` | from `DatasetSpec` |
| `import_run_id` | `UUID FK → import_runs` | |
| `imported_at` | `TIMESTAMPTZ` | |

**Unique index:** `question_sources_identity_idx` on `(dataset_name, source_key)` — the idempotency mechanism for re-runnable imports.

### `questions`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `title` | `TEXT NOT NULL` | |
| `question_type` | `TEXT NOT NULL` | `CHECK IN ('algorithm','data_analysis')` |
| `difficulty` | `TEXT NOT NULL` | `CHECK IN ('Beginner','Easy','Medium','Hard','Very Hard')` |
| `problem_statement` | `TEXT NOT NULL` | |
| `constraints` | `TEXT` | |
| `examples` | `JSON` | array of `{input, output/expected_output}` |
| `supported_methods` | `JSON NOT NULL` | default `'[]'`; array of method strings |
| `tags` | `JSON` | default `'[]'`; used as topic filter values |
| `source_id` | `UUID FK → question_sources` | `NULL` for AI-generated questions |
| `is_ai_generated` | `BOOLEAN` | default `false` |
| `is_complete` | `BOOLEAN` | default `true`; `false` for schema-only data-analysis imports |
| `created_at` | `TIMESTAMPTZ` | |

### `question_assets`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `asset_type` | `TEXT NOT NULL` | `CHECK IN ('schema','fixture_data','expected_result','starter_code')` |
| `method` | `TEXT` | `NULL`/`'shared'` for method-independent assets, else a specific method |
| `content` | `TEXT NOT NULL` | |
| `content_type` | `TEXT NOT NULL` | default `'text'` (also `'sql'`, `'json'`) |

### `reference_solutions`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `method` | `TEXT NOT NULL` | |
| `code` | `TEXT NOT NULL` | |
| `language` | `TEXT NOT NULL` | default `'python'` (also `'sql'`) |
| `is_from_dataset` | `BOOLEAN` | default `true`; `false` for AI-generated |
| `explanation` | `TEXT` | |

### `question_test_cases`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `input_data` / `expected_output` | `JSON` | |
| `is_example` | `BOOLEAN` | default `false` |

### `ai_generated_questions`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `provider` / `model_id` | `TEXT NOT NULL` | |
| `generated_at` | `TIMESTAMPTZ` | |
| `prompt_version` | `TEXT` | e.g. `"v3"` |
| `generation_metadata` | `JSON` | `{prompt_template, question_type, difficulty, method, topic}` |

### `attempts`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `attempted_at` | `TIMESTAMPTZ` | |
| `method` | `TEXT NOT NULL` | |
| `submitted_code` | `TEXT NOT NULL` | verbatim, never mutated after insert |
| `deterministic_test_result` | `TEXT NOT NULL` | default `'not_run'` (migration 4) — explicitly documents that no code execution occurred |
| `test_result` | `TEXT` | legacy column; `CHECK IN ('passed','failed','error','timeout','pending')`; superseded by `assessment_status` |
| `tests_passed` / `tests_total` | `INTEGER` | legacy, unused by current code paths |
| `percentage_correct` | `DOUBLE` | AI estimate |
| `marks` | `DOUBLE` | AI estimate, `percentage_correct / 10` |
| `ai_feedback` | `TEXT` | JSON string: `{identified_mistakes, explanation, suggested_correction, corrected_code}` |
| `error_details` | `TEXT` | sanitized failure message, truncated to 2000 chars |
| `solution_viewed` | `BOOLEAN` | default `false` |
| `provider` / `model_id` | `TEXT` | which AI handled this attempt |
| `assessment_status` | `TEXT` | added by migration 2: `'pending'`, `'completed'`, `'error'` |

### `solution_views`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `question_id` | `UUID FK → questions` | |
| `attempt_id` | `UUID FK → attempts` | nullable |
| `viewed_at` | `TIMESTAMPTZ` | |
| `methods_viewed` | `JSON` | default `'[]'`; array of method strings, appended to (not overwritten) |

### `quiz_attempts` (migration 5)
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `started_at` / `completed_at` | `TIMESTAMPTZ` | |
| `status` | `TEXT NOT NULL` | state machine: see below |
| `question_source` | `TEXT NOT NULL` | `dataset` / `ai_generated` / `mixed` |
| `question_type`, `difficulty`, `topic`, `method` | `TEXT NOT NULL` | |
| `total_items`, `coding_items`, `mcq_items` | `INTEGER NOT NULL` | |
| `percentage_correct` / `marks` | `DOUBLE` | average across items |
| `passed` | `BOOLEAN` | `percentage_correct >= 80.0` |
| `provider` / `model_id` | `TEXT` | |
| `error_details` | `TEXT` | |

**Status state machine:** `preparing → (preparation_error ↔ preparing) → in_progress → evaluating → (evaluation_error ↔ evaluating) → completed`

### `quiz_items` (migration 5)
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `quiz_attempt_id` | `UUID FK → quiz_attempts` | |
| `position` | `INTEGER NOT NULL` | 1-indexed order within the quiz |
| `question_id` | `UUID FK → questions` | |
| `answer_format` | `TEXT NOT NULL` | `'coding'` or `'mcq'` |
| `method` | `TEXT NOT NULL` | |
| `prompt_snapshot` | `TEXT` | the exact problem statement / MCQ prompt shown |
| `options` | `JSON` | MCQ only: array of `{id, text}` |
| `correct_option_id` | `TEXT` | MCQ only |
| `explanation` | `TEXT` | MCQ only, shown after scoring |
| `answer_text` | `TEXT` | coding-item draft/final answer |
| `selected_option_id` | `TEXT` | MCQ draft/final answer |
| `item_status` | `TEXT NOT NULL` | default `'pending'`, then `'scored'` or `'error'` |
| `percentage_correct` / `marks` | `DOUBLE` | |
| `ai_feedback` | `TEXT` | JSON, coding items only |
| `provider` / `model_id` | `TEXT` | |
| `error_details` | `TEXT` | |

**Unique constraints:** `(quiz_attempt_id, position)` and `(quiz_attempt_id, question_id)` — one item per position, one appearance per question within a quiz.

---

## 6. Migrations Reference

`database/migrations.py` — `MIGRATIONS: list[tuple[int, str, str]]`, applied transactionally in order, recorded in `schema_versions`:

| Version | Description | Effect |
|---|---|---|
| 1 | initial schema | Applies the current idempotent `SCHEMA_SQL` definition |
| 2 | AI assessment lifecycle | Adds `attempts.assessment_status`; backfills legacy rows as `'legacy_' \|\| test_result` |
| 3 | dataset source identity and revision provenance | Adds `question_sources.source_key/source_revision/source_record_index`; backfills legacy keys; creates `question_sources_identity_idx` |
| 4 | explicit deterministic verification status | Adds `attempts.deterministic_test_result` defaulting to `'not_run'`; backfills existing rows |
| 5 | separate resumable quiz attempts and items | Creates `quiz_attempts` and `quiz_items` |

All migrations use `ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS` for safe re-application. A failed migration rolls back only that migration's transaction; already-applied migrations are untouched.

---

## 7. Provider and Model Registry

Source of truth: `providers/config.py`. Every `verified=True` entry cites an official documentation URL. In this codebase, `verified` means the option is allowlisted for request construction; it does not prove that a user's account has access or that a live request will succeed.

| Provider key | Display name | Model ID | `extra_params` | Documentation |
|---|---|---|---|---|
| `openai` | OpenAI | `gpt-5.6-luna` | `{"reasoning_effort": "medium"}` | [developers.openai.com/api/docs/models/gpt-5.6-luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) |
| `agnes` | Agnes AI | `agnes-2.5-flash` | `{}` | [agnes-ai.com/en/docs/agnes-25-flash](https://www.agnes-ai.com/en/docs/agnes-25-flash) |
| `gemini` | Google Gemini | `gemini-3.5-flash-lite` | `{"thinking_level": "medium"}` | [ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) |
| `gemini` | Google Gemini | `gemini-3.7-flash` | `{"thinking_level": "medium"}` | [ai.google.dev/gemini-api/docs/thinking](https://ai.google.dev/gemini-api/docs/thinking) |

**Request dispatch per provider:**

| Provider | SDK | Auth | Call shape |
|---|---|---|---|
| `OpenAIProvider` | `openai` Python SDK | `OPENAI_API_KEY`, optional `OPENAI_BASE_URL` | `client.chat.completions.create(model=..., messages=[...], **model.extra_params)` |
| `AgnesProvider` | `openai` Python SDK, `base_url="https://apihub.agnes-ai.com/v1"` | `AGNES_API_KEY` | Same shape as OpenAI, OpenAI-compatible endpoint |
| `GeminiProvider` | `google-genai` SDK | `GOOGLE_API_KEY` | `client.interactions.create(model=..., input=..., system_instruction=..., generation_config={"thinking_level": ...}, store=False)` |

**Common request gates:**
1. The selected model exists and has `verified=True`.
2. Its `provider` matches the selected provider.
3. The provider is registered and its required credential is present.

Assessment, solution, and quiz paths additionally confirm the selected model against the provider's configured options. Question generation validates the model/provider fields before dispatch but does not repeat that option-list lookup.

If unverified options are configured, the sidebar shows them as warnings with their reason and documentation link; they are not selectable for requests. The automated suite uses mocked providers and does not establish live credentials, quota, account access, or provider availability.

---

## 8. CLI Scripts Reference

### `scripts/download_datasets.py`

| Flag | Effect |
|---|---|
| `--list` | Print available dataset keys and exit |
| (no flags) | Download the default set (all datasets except `codecontests`) |
| `--datasets KEY [KEY ...]` | Download only the named datasets |
| `--skip-codecontests` | Explicitly retain the default CodeContests exclusion |
| `--include-codecontests` | Include CodeContests in the default download |
| `--dry-run` | Preview what would be downloaded without transferring files |

Uses `huggingface_hub.snapshot_download`, preserving each source repository's internal directory structure under `Dataset/`. The `--list` output includes approximate snapshot sizes that can change upstream; see the [Dataset Setup Guide](dataset-setup.md) for the currently tested estimates.

### `scripts/import_datasets.py`

| Flag | Effect |
|---|---|
| (no flags) | Import every supported dataset found under `Dataset/` |
| `--datasets KEY [KEY ...]` | Import only the named datasets (choices: `leetcode`, `apps`, `taco`, `codecontests`, `spider`, `sqlctx`, `querypls`) |
| `--dataset-root PATH` | Override the default `<repo_root>/Dataset` |
| `--database PATH` | Override `$CODING_TUTOR_DB` / `coding_tutor.duckdb` for this run |

Exit code `1` if any dataset import status is `"failed"`, else `0`. Prints one summary line per dataset: `"{name}: {status}; {imported} imported, {skipped} skipped[; {error}]"`.

---

## 9. Configuration Reference

| File | Key(s) | Value |
|---|---|---|
| `.streamlit/config.toml` | server address/port | `127.0.0.1:8551` |
| `pyproject.toml` | `requires-python` | `>=3.11` |
| `pyproject.toml` | `[project.dependencies]` | `streamlit>=1.59.1`, `duckdb>=1.0.0`, `openai>=1.40.0`, `pandas>=2.1.0`, `pyarrow>=15.0.0`, `huggingface-hub>=0.23.0`, `google-genai>=2.18.1` |
| `pyproject.toml` | `[tool.pytest.ini_options]` | `testpaths = ["tests"]`, `pythonpath = ["src"]` |
| `pyproject.toml` | `[build-system]` | `hatchling` |

No feature flags exist. All runtime behavior is controlled by `st.session_state` (per-session) or the environment variables in §2 (per-process).

---

## 10. Runtime Boundaries, Calculations, and Extension Points

### Security and failure boundaries

- Learner Python, SQL, Pandas, PySpark, and Polars text is never executed by the application. Assessment and coding-quiz scores are AI estimates from static review.
- AI-backed actions send bounded question context and relevant learner input to the explicitly selected provider. DuckDB persistence is local, but provider-bound content leaves the machine.
- The Streamlit server binds to loopback (`127.0.0.1`) and implements no user authentication. Loopback binding reduces network exposure; it is not a sandbox or authorization system.
- Marked model inputs are JSON-encoded and paired with `shared_rules.md`. This reduces accidental instruction confusion but cannot make model output trusted.
- Generated questions, assessments, teaching solutions, and MCQs pass strict shape/type/size validation before use. Valid generated questions are saved inside a DuckDB transaction.
- Expected provider failures are converted to enumerated results or sanitized UI messages. Provider exception text is not intentionally rendered by AI request paths.
- API keys are read from process environment variables. Prompt files and DuckDB records do not intentionally store credential values.

### Progress and scoring calculations

- Every practice submission creates a separate `attempts` row before assessment. Failed and repeated assessments remain in history.
- Practice marks equal `estimated_percentage_correct / 10`. A question counts as solved when at least one completed assessment reaches `SOLVED_THRESHOLD` (`80.0`).
- Practice summaries count distinct attempted, assessed, and solved question IDs; recent attempts are the five newest matching rows.
- MCQ items score either `100.0` or `0.0`. Coding quiz items use the AI-estimated percentage.
- Quiz percentage is the arithmetic mean of all item percentages. Quiz `marks` stores that same percentage, and `passed` is true at 80% or higher.
- Quiz attempts and practice attempts are queried separately. Question type, difficulty, and method filters apply to both progress sections.

### Extension points

- Add providers by implementing `BaseProvider`, registering the provider, defining model options, and adding mocked request/secret-handling tests.
- Change a prompt response contract only together with its parser/validator and malformed-response tests. Register new Markdown prompts in `PROMPT_NAMES`.
- Add datasets through `DatasetSpec`, format inspection, a source-specific importer, normalized provenance, fixture tests, and license/attribution documentation.
- Evolve persisted data only by appending a transactional migration; do not rewrite or delete prior learner attempts.
- Add UI behavior through the existing Practice, Quiz, or Progress entry point while preserving session-state draft protection.

---

## 11. Testing Reference

```bash
uv run pytest -q
```

| Test file | Covers |
|---|---|
| `conftest.py` | Autouse `clear_provider_env` fixture — removes all 5 provider-related env vars before every test |
| `test_config.py` | `ModelOption`, verified flag, provider registry |
| `test_providers.py` | `BaseProvider` interface, mocked chat responses |
| `test_database.py` | Schema creation, migration idempotency |
| `test_import.py` | Dataset importer logic against fixture files in `tests/fixtures/` |
| `test_generation.py` | `generate_question()` flow, `GenerationResult`/`GenerationFailure`, validator edge cases |
| `test_evaluation.py` | Assessment parsing, bounds validation, attempt persistence, sanitized-failure guarantees |
| `test_progress.py` | Combined-query progress summary, filtered attempt queries |
| `test_prompts.py` | Prompt loading, rendering, and structured-response contracts |
| `test_quiz.py` | Quiz creation, resume, item draw, MCQ generation/validation, scoring; includes `streamlit.testing.v1.AppTest` end-to-end checks |
| `test_solutions.py` | Reference retrieval, AI teaching-solution generation and validation |
| `test_ui.py` | Session-state helpers, sidebar state, unsaved-draft flow; also uses `AppTest` |

The currently verified 153-test suite uses `get_test_db()` (`:memory:` DuckDB with migrations applied) where storage is needed and hand-written fake providers for AI paths. It requires no real network calls, API keys, or downloaded datasets.

---

*This reference reflects the codebase as of 2026-08-19. When source and reference disagree, the source is authoritative — please open an issue or PR to correct this document.*
