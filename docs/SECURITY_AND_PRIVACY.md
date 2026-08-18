# Security and Privacy

Coding Tutor is designed for a single user running the Streamlit application on their own machine. This document describes the protections and limitations implemented by the current codebase. It is not a security certification, privacy guarantee, or legal opinion.

## Security boundary at a glance

- Streamlit is configured to listen on `127.0.0.1:8551`.
- The application has no user-account or authentication system.
- Questions, attempts, feedback, quizzes, and progress are stored in a local DuckDB file.
- AI-backed actions send selected question and learner context to the configured external provider.
- Learner Python, SQL, Pandas, PySpark, and Polars text is never executed by the application.
- The project does not implement database encryption, a code sandbox, process isolation, network isolation, or filesystem isolation.

Binding to the loopback address limits the default listener to the local machine, but it is not an authentication control. Do not reconfigure the app for public or multi-user access without adding and reviewing appropriate protections.

## API-key handling

### Provider variables

The provider adapters read credentials directly from the process environment:

| Provider | Environment variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Agnes AI | `AGNES_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` |

OpenAI also reads `OPENAI_BASE_URL` as an optional endpoint override. When it is set, OpenAI requests and their included content are sent to that configured endpoint rather than necessarily to the default OpenAI endpoint.

The dataset downloader can read `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN`. Those variables are used only when the downloader is explicitly run.

Provider configuration checks return only whether the required variable contains non-whitespace text. They do not display the value or validate it with the provider. The application does not load a `.env` file.

### `.env.example` and ignore rules

The repository includes `.env.example` with blank entries for:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `AGNES_API_KEY`
- `GOOGLE_API_KEY`

It is a names-only reference and is not loaded by the application. Do not put real values in it.

The checked-in `.gitignore` excludes:

- `.env` and `.env.*`, while explicitly retaining `.env.example`;
- `.streamlit/secrets.toml`;
- DuckDB and common database files;
- the raw `Dataset/` directory;
- virtual environments, caches, temporary runner files, and `*.log` files.

Automated configuration tests verify these ignore patterns and verify that `.env.example` remains blank. Ignore rules reduce accidental commits; they do not detect secrets placed in other tracked files, commit history, screenshots, terminal output, or external logs.

## Local storage

DuckDB is the only application database. By default, the app opens `coding_tutor.duckdb` in its working directory. `CODING_TUTOR_DB` can select a different path. Startup creates a missing parent directory and applies schema migrations.

The database can contain:

- normalized dataset and AI-generated questions;
- source file, revision, record identifier, license, and attribution metadata;
- question schemas, fixture data, expected results, starter templates, references, and test-case context;
- original learner submissions and selected methods;
- AI-estimated percentages, marks, mistakes, explanations, suggested corrections, and optional corrected code;
- provider and model identifiers used for an interaction;
- solution-view history;
- quiz settings, question snapshots, drafts, selected options, MCQ answers and explanations, coding answers, scores, and errors; and
- dataset import history and migration versions.

Every Practice submission is stored as a new attempt. Applying AI-corrected code changes the active editor but does not replace the original saved submission. Quiz drafts are written to DuckDB; ordinary Practice drafts remain in Streamlit session state until submitted.

The project does not encrypt the DuckDB file or manage operating-system permissions, backups, retention, secure deletion, or cloud synchronization. Anyone or any process that can read the database file may be able to read its contents. The app provides no in-app data-reset or deletion workflow.

## Data sent to AI providers

No provider request is made merely because text is typed into the editor. External requests occur after an AI-backed user action, including generating a question, selecting **Done**, requesting an AI teaching solution, or preparing/scoring provider-dependent quiz content.

### Question generation

The selected provider receives the requested difficulty, topic, question type-specific contract, and solution method. It does not receive the current learner editor text through this path.

### Submission assessment

Selecting **Done** can send:

- the learner's submitted editor text;
- the selected method;
- question title, type, difficulty, statement, constraints, examples, and tags;
- a stored method-specific reference solution, when available;
- matching schema, fixture-data, and expected-result assets; and
- stored test-case inputs and expected outputs.

The request builder applies documented length and item limits, but the submitted text itself can be up to 12,000 characters. The original attempt is saved locally before provider validation and before the provider request.

### Teaching solutions

An explicit AI teaching-solution request can include bounded question fields, the selected method, stored assets, test cases, and reference solutions. Displaying an already stored reference solution does not itself require a provider call.

### Quizzes

AI-generated quiz questions use the normal question-generation request. MCQ preparation sends a batch containing question IDs, titles, selected methods, bounded statements and constraints, and examples. Non-blank coding answers use the same static-assessment context as Practice mode. MCQ answer scoring compares option IDs locally and does not call a provider.

### Content not included by request builders

The implemented request builders do not add environment-variable values or transmit the DuckDB file as a file. They query and serialize the fields needed for the current question or quiz operation rather than uploading the entire database.

These statements describe Coding Tutor's request construction. They do not make guarantees about provider-side retention, logging, training, subprocesses, SDK behavior, or policies. Review the selected provider's terms and settings before sending content. See [AI Behavior](AI_BEHAVIOR.md) for the exact request and persistence contracts.

## Dataset handling and provenance

Datasets are optional. The application has no Streamlit file-upload control. Raw source data enters the workflow only through files placed under the expected dataset directories, commonly by explicitly running the separate download script.

The downloader contacts Hugging Face and writes snapshots under the gitignored `Dataset/` directory. It reports whether an optional Hugging Face token was detected but does not print the token value in project code.

The importer:

- discovers only configured file patterns;
- checks file format and required fields before parsing;
- reads JSON, JSONL, or Parquet source files without renaming or overwriting them;
- reads CodeContests archive members in memory rather than extracting them into the source directory;
- stores normalized questions separately in DuckDB;
- records source dataset, stable identity, relative source file, available revision/index, license, attribution, and import time; and
- uses stable source keys to avoid duplicate normalized records on rerun.

License and attribution metadata are traceability records, not legal clearance. Some configured sources have incomplete or mixed licensing information. Users must review source terms before downloading, using, or redistributing dataset material. See [Datasets](DATASETS.md).

## Editor and code execution

The Practice and Quiz editors are plain Streamlit text areas. Their contents are treated as text for local storage, display, and optional provider review.

The application does not execute, import, compile, evaluate, or query learner Python, SQL, Pandas, PySpark, or Polars submissions. Stored test cases are sent as static context and are not run. Correctness percentages, marks, coding-quiz scores, errors, and corrections from a provider are AI estimates.

Because there is no code runner, the project implements no learner-code sandbox, timeout, resource limit, network block, temporary execution directory, or PySpark runtime. This avoids executing learner text inside the app, but it does not prove that the text is correct or safe to run elsewhere.

AI-corrected code and teaching solutions are also unexecuted. Review them before copying them into another environment.

## Logging and error messages

Project provider paths use user-facing generic errors for unexpected provider failures. Question generation logs the exception type rather than the provider exception text. The code does not intentionally add API-key values to its log messages.

Dataset command-line paths are less private: downloader/importer output can contain dataset names, destination or source paths, discovered field names, record indices or task identifiers, and exception messages. Import failures are also recorded in DuckDB. Avoid sharing terminal output or database files without reviewing them.

The downloader configures console logging. The application does not configure a dedicated encrypted or access-controlled audit log. Third-party SDK and hosting-process logging is outside the guarantees of this repository.

## User responsibility

Users must supply and manage their own API credentials. Users are responsible for:

- ensuring they are authorized to submit code, questions, datasets, and other content;
- deciding whether content may be sent to the selected provider or custom OpenAI base URL;
- following provider terms and dataset licenses;
- protecting environment variables, the DuckDB file, raw datasets, backups, terminal output, and screenshots;
- reviewing AI feedback and generated code before relying on or executing it; and
- removing or rotating credentials after suspected exposure.

Do not enter secrets, personal data, confidential source code, proprietary datasets, or regulated information unless you have reviewed the entire local and provider-side data path and are authorized to use it.

## Known limitations and recommended safe use

- The app has no authentication or multi-user authorization.
- Local storage is not encrypted by the application.
- Provider configuration checks do not prove that a credential is valid or that a model is available.
- AI responses are structurally validated but can still be incorrect, unsafe, or misleading.
- Prompt instructions reduce accidental instruction-following from embedded content but do not establish complete prompt-injection resistance.
- No automated secret scanner, data-loss-prevention control, malware scanner, dataset-content scanner, or retention manager is implemented.
- The application cannot verify dataset redistribution rights or the sensitivity of imported records.
- Loopback binding is appropriate for local use but should not be treated as a replacement for authentication.

Recommended practice:

1. Keep the default loopback binding and do not expose the Streamlit server publicly.
2. Use credentials intended for your own local use and follow the provider's access-management guidance.
3. Review editor text, question context, and dataset content before triggering an AI action.
4. Keep the project, DuckDB file, raw datasets, and backups in a location protected by operating-system permissions.
5. Review terminal output before sharing it because dataset operations can reveal paths and identifiers.
6. Treat all AI-generated assessments, corrections, quiz content, and solutions as unverified suggestions.
7. Review dataset provenance and current licensing terms before use or redistribution.

For vulnerability reporting, see the repository [Security Policy](../SECURITY.md). For general limitations, see the [Disclaimer](../DISCLAIMER.md).
