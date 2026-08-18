# Technical Reference

## Runtime structure

| Path | Responsibility |
| --- | --- |
| `app.py` | Streamlit entry point and Practice/Quiz/Progress navigation. |
| `src/coding_tutor/ui/` | Sidebar state, question rendering, submission, solutions, quizzes, progress. |
| `providers/` | Common chat interface and OpenAI, Agnes, Gemini adapters. |
| `generation/` | Prompt construction, strict question validation, atomic persistence. |
| `evaluation/` | Static assessment, teaching-solution validation, immutable attempt persistence. |
| `database/` | DuckDB connection, schema migrations, progress queries. |
| `dataset/` | Source catalog, file inspection, seven normalization adapters. |
| `quiz/` | Quiz rules, durable drafts, selection, MCQ preparation, scoring. |
| `prompts/*.md` | Runtime prompt contracts loaded by name. |
| `scripts/` | Dataset download and import CLIs. |
| `tests/` | Unit, temporary-DuckDB, mocked-provider, and Streamlit AppTest coverage. |

The sidebar writes provider/model and learning selections into `st.session_state`. Question loading joins normalized questions with dataset or generation provenance. Editor keys include question ID and method. Type/method changes compare editor content with a baseline and require a keep/discard/cancel decision when dirty.

## Environment variables

| Name | Behavior |
| --- | --- |
| `OPENAI_API_KEY` | Non-blank value configures the OpenAI adapter. |
| `OPENAI_BASE_URL` | Optional OpenAI SDK base URL; blank becomes `None`. |
| `AGNES_API_KEY` | Non-blank value configures Agnes. |
| `GOOGLE_API_KEY` | Non-blank value configures Gemini; `GEMINI_API_KEY` is not used. |
| `CODING_TUTOR_DB` | Database path; default `coding_tutor.duckdb`. |
| `HF_TOKEN` | Optional downloader token. |
| `HUGGING_FACE_HUB_TOKEN` | Downloader fallback token name. |

`.env.example` is not loaded. Provider status checks presence only and never contacts the provider.

## Providers and models

`BaseProvider` defines `is_configured()`, `get_model_options()`, and `chat()`. The registry implements:

| Provider | Model ID | Adapter call | Verification boundary |
| --- | --- | --- | --- |
| OpenAI | [`gpt-5.6-luna`](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | OpenAI Chat Completions; `reasoning_effort=medium` | Official model page supports Chat Completions and medium effort; request is mock-tested, not live-tested. |
| Agnes | [`agnes-2.5-flash`](https://www.agnes-ai.com/en/docs/agnes-25-flash) | OpenAI SDK at `https://apihub.agnes-ai.com/v1` | [Official overview](https://www.agnes-ai.com/en/docs/overview) documents OpenAI compatibility/base URL; request is mock-tested, not live-tested. |
| Gemini | [`gemini-3.5-flash-lite`](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [`gemini-3.7-flash`](https://ai.google.dev/gemini-api/docs/thinking) | Google Gen AI Interactions; `thinking_level=medium`, `store=False` | Official thinking table supports medium; requests are mock-tested, not live-tested. |

All are marked `verified=True` in code. That means accepted by the app registry, not guaranteed account access, availability, quota, or successful authentication.

## DuckDB schema

Schema version 5 uses twelve tables:

| Table | Purpose |
| --- | --- |
| `schema_versions` | Applied transactional migrations. |
| `import_runs` | Per-dataset status and imported/skipped counts. |
| `question_sources` | Dataset identity, file/revision/index, license, attribution. |
| `questions` | Normalized type, difficulty, statement, methods, tags, completeness. |
| `question_assets` | Schema, fixture data, expected result, starter code. |
| `reference_solutions` | Dataset or generated method-specific code/explanation. |
| `question_test_cases` | Stored input/expected-output context. |
| `ai_generated_questions` | Provider/model, prompt version, non-secret generation metadata. |
| `attempts` | Immutable practice submissions and assessment lifecycle. |
| `solution_views` | Viewed methods and optional attempt link. |
| `quiz_attempts` | Quiz settings, lifecycle, aggregate result. |
| `quiz_items` | Question provenance, drafts, MCQ data, scores, feedback. |

## Question and import contracts

`question_type` is `algorithm` or `data_analysis`. Algorithms must support only `python`. Data-analysis records declare `sql`, `pandas`, `pyspark`, and `polars`; they are complete only when schema, fixture data, and expected result assets all exist.

The importer discovers files from the catalog, verifies magic/format and required fields, records a run, and calls a source adapter. `stable_source_key()` plus a unique `(dataset_name, source_key)` index makes reruns idempotent. Each question, source, asset, solution, and test-case insertion is one transaction. Folder name does not determine stored type; catalog metadata does.

Generated algorithm questions require examples, constraints, starter code, and test cases. Generated data-analysis questions require one table/schema, consistent non-empty fixture/expected rows, all four methods, starters, and references. Unexpected or missing fields reject the response before persistence.

## Assessment and safety boundary

There is no execution subsystem. **Done** stores the exact text, validates provider/model/method, then sends bounded context to the provider. A strict JSON parser accepts an estimated percentage; marks are derived as `percentage / 10`. Provider errors are sanitized. Deterministic status remains `not_run`.

Consequently there is no process isolation, network blocking, timeout, memory limit, or filesystem sandbox to claim. This is safe from untrusted local code execution only because that code is never executed. Provider-side processing remains governed by the chosen provider.

## Progress and quizzes

Every submission receives a new UUID. Solved status requires a completed assessment at or above 80%. Filters apply to type, difficulty, and method. Quiz tables remain separate from practice attempts while sharing question IDs. Quiz rules are documented in [Usage](USAGE.md#use-quiz-mode).

## Tests

```powershell
uv run pytest -q
```

Tests cover migrations, import adapters/idempotency, model request construction without network, response validation, immutable attempts, reversible corrections, solutions, progress persistence, quiz scoring, and UI controls. They do not run learner code, contact providers, or import the complete downloaded corpora.
