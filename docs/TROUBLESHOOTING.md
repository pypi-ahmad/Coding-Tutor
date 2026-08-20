# Troubleshooting

This guide covers repeatable setup and runtime failures represented by the current launcher, application messages, import pipeline, and automated tests. It does not provide fixes for speculative failures.

Before sharing diagnostics, remove credentials, learner submissions, dataset records, personal paths, and DuckDB contents. Report the exact safe error message, the command used, the operating system, Python and `uv` versions, and the relevant non-secret selections.

## The Windows launcher says `uv` is unavailable

**Symptom**

`launch_app.cmd` displays:

```text
ERROR: uv is not installed or is not available on PATH.
```

**Likely cause**

The launcher could not resolve the `uv` command from `PATH`.

**Verified resolution steps**

1. Install `uv` using the official installation URL printed by the launcher: <https://docs.astral.sh/uv/getting-started/installation/>.
2. Close and reopen the terminal or launcher so it receives the updated `PATH`.
3. From the repository root, run:

   ```powershell
   uv --version
   ```

4. Run `launch_app.cmd` again.

The launcher intentionally does not download or install `uv`.

**Confirm the issue is resolved**

`uv --version` prints a version, and the launcher advances to creating or synchronizing `.venv`.

**Report a bug instead when**

`uv --version` succeeds in the same terminal, but the launcher still reports that `uv` is unavailable. Include the launcher output without environment-variable values.

## The virtual environment cannot be created

**Symptom**

The Windows launcher displays:

```text
ERROR: The project virtual environment could not be created.
```

**Likely cause**

`uv venv .venv` returned a nonzero status. The launcher specifically directs the user to check the preceding `uv` output and whether the project directory is writable.

**Verified resolution steps**

1. Read the `uv` error immediately above the launcher message.
2. Confirm the repository directory is writable by your user.
3. From the repository root, run the same operation directly:

   ```powershell
   uv venv .venv
   ```

4. After it succeeds, run `launch_app.cmd` again.

Do not remove an existing `.venv` merely because creation failed; the project has no automated environment-repair command.

**Confirm the issue is resolved**

`.venv` contains the platform's Python executable, and the launcher advances to dependency synchronization.

**Report a bug instead when**

The direct command reproducibly fails in a writable repository with a supported Python installation, and the failure is caused by project configuration rather than `uv` installation or operating-system policy. Include the safe `uv` error text.

## Dependency synchronization fails

**Symptom**

The Windows launcher displays:

```text
ERROR: Dependency setup failed.
```

**Likely cause**

The checked-in command `uv sync --locked` returned a nonzero status. The exact cause is reported in the `uv` output; the launcher does not infer it.

**Verified resolution steps**

1. Confirm `pyproject.toml` and `uv.lock` exist in the repository root.
2. Run the same locked synchronization command directly to retain the complete error output:

   ```powershell
   uv sync --locked
   ```

3. Correct only the environment-specific condition identified by `uv`, then rerun the command. Do not regenerate or edit the lock file as a troubleshooting shortcut.
4. Confirm Streamlit is available in the synchronized environment:

   ```powershell
   uv run streamlit version
   ```

**Confirm the issue is resolved**

`uv sync --locked` exits successfully and `uv run streamlit version` prints the installed Streamlit version.

**Report a bug instead when**

A fresh clone with unchanged `pyproject.toml` and `uv.lock` fails reproducibly on a supported Python version. Include the command output after removing paths, credentials, and private package information.

## Streamlit does not start

**Symptom**

The launcher displays:

```text
ERROR: Streamlit failed to start.
```

or the application is not available at <http://127.0.0.1:8551>.

**Likely cause**

The checked-in Streamlit launch command returned a nonzero status. The actionable cause is in the output immediately above the launcher message.

**Verified resolution steps**

1. Confirm dependency synchronization succeeds:

   ```powershell
   uv sync --locked
   ```

2. Run the same application command directly:

   ```powershell
   uv run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8551
   ```

3. Read the first application or Streamlit error in the terminal rather than relying only on the final launcher message.
4. Keep that terminal open while using the application.

**Confirm the issue is resolved**

The terminal reports the Streamlit server URL, and <http://127.0.0.1:8551> opens locally.

**Report a bug instead when**

The exact checked-in command fails reproducibly after a successful locked synchronization. Include the traceback with credentials, learner content, database contents, and personal paths removed.

## The sidebar says provider configuration is unavailable

**Symptom**

The sidebar reports that the selected provider's configuration is unavailable, or an action displays:

```text
The selected provider is not configured. Set its API key in the system environment.
```

**Likely cause**

The required process environment variable is absent, empty, or whitespace-only:

| Provider | Required variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Agnes AI | `AGNES_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` |

`OPENAI_BASE_URL` alone does not configure OpenAI. `GEMINI_API_KEY` is not read.

**Verified resolution steps**

1. Set the correct variable in the operating-system or launching shell environment without printing it.
2. Stop and restart Streamlit so the new process receives the variable.
3. Select the provider again in the sidebar.

Do not put a real credential in `.env.example`; the application does not load it.

**Confirm the issue is resolved**

The sidebar reports that the selected provider's configuration is available. This confirms presence only, not credential validity or model access.

**Report a bug instead when**

The correct variable is non-blank in the environment inherited by Streamlit, but the sidebar still reports it as unavailable. Do not include the value in the report.

## A provider-backed action fails

**Symptom**

Question generation reports:

```text
The provider request failed. Check network access, credentials, quota, and model access.
```

Coding assessment reports that the provider could not complete the assessment, or solution/quiz/AI-question/interview generation displays its provider-error or retry message.

**Likely cause**

The provider adapter raised an exception. The application deliberately replaces raw provider details with a generic message, so it cannot distinguish authentication, connectivity, quota, and account/model-access failures in the UI.

**Verified resolution steps**

1. Confirm the sidebar reports the selected provider as configured.
2. Confirm the selected model still belongs to that provider in the sidebar.
3. Check network access and the provider account's credential status, quota, and model access without sharing the credential.
4. Retry the same explicit action. Quiz preparation and scoring preserve a retry path.

The application has no automatic fallback to another provider or model.

**Confirm the issue is resolved**

The requested question, assessment, teaching solution, or quiz content appears and no provider-error state remains.

**Report a bug instead when**

The provider and model work for other requests, but this application fails reproducibly with the same safe input and settings. Include the operation, provider/model identifiers, and sanitized UI message—not the key or submitted private content.

## The provider returns malformed or incomplete content

**Symptom**

The UI reports malformed JSON, an incomplete or invalid generated question, an invalid structured solution, or malformed/incomplete quiz content.

**Likely cause**

The provider response did not match the exact JSON schema or completeness rules enforced for that operation. Generated data-analysis questions also require schema, fixture rows, expected results, starters, and references for every supported method.

**Verified resolution steps**

1. Retry the same action once; provider output can vary between calls.
2. If question generation continues to fail, choose a curated question that matches the current filters.
3. If a teaching solution reports incomplete context, use an available stored reference or choose a complete question. The application does not invent missing schema, fixture data, or expected results.
4. For quiz preparation, use **Retry quiz creation**; existing durable quiz state is retained.

**Confirm the issue is resolved**

Validated content is displayed. Rejected generated questions and solutions are not saved as usable content.

**Report a bug instead when**

A response matching the current documented contract is reproducibly rejected. Provide a minimal redacted response shape that contains no learner, dataset, or provider-sensitive content.

## Dataset import reports no matching source files

**Symptom**

The import summary has status `failed` and includes:

```text
No source files match ...
```

**Likely cause**

The selected dataset is absent from its configured relative path, or `--dataset-root` points at the wrong directory.

**Verified resolution steps**

1. List the supported dataset keys:

   ```powershell
   uv run python scripts/download_datasets.py --list
   ```

2. Check the expected relative layout in [Dataset Setup](dataset-setup.md).
3. If the files have not been downloaded, run the supported downloader or place an authorized source snapshot in the documented layout.
4. Import one dataset key to isolate the result:

   ```powershell
   uv run python scripts/import_datasets.py --datasets leetcode
   ```

5. When using another source root, pass the directory that directly contains `algorithm_problems/` and `data_analysis_problems/` through `--dataset-root`.

**Confirm the issue is resolved**

The import summary reports `completed` for the selected dataset and shows imported/skipped counts instead of `failed`.

**Report a bug instead when**

The files exist at the exact configured pattern but discovery still reports no match. Include relative paths only; do not attach the raw dataset.

## Dataset import rejects a file or fields

**Symptom**

The import reports one of these real inspection errors:

```text
Expected Parquet file: ...
Expected JSON objects in ...
Expected a non-empty JSON object array in ...
... is missing required fields: ...
```

**Likely cause**

The source file's actual format or first-record/schema fields do not match the configured dataset contract. A truncated or different dataset revision can produce the same result.

**Verified resolution steps**

1. Confirm the selected dataset key and expected file format in [Datasets](DATASETS.md).
2. Confirm the source snapshot came from the configured dataset repository and retained its documented internal layout.
3. Do not rename a different format or add invented fields to bypass inspection.
4. Obtain a valid source snapshot, then rerun the one-dataset import command.

**Confirm the issue is resolved**

Inspection completes and the dataset import summary reports `completed`. Individual invalid records can still be counted as skipped by a source adapter.

**Report a bug instead when**

A verified source file has the configured format and required fields but the importer rejects it. Report field names and format metadata only, not raw records.

## No curated question appears after import

**Symptom**

Coding displays a message such as:

```text
No curated algorithm questions for PYTHON at Easy difficulty. Try a different difficulty or import datasets.
```

**Likely cause**

No complete, non-AI question matches the selected type, difficulty, method, and topic. The current SQL-family importers deliberately mark records incomplete because their sources do not provide shared fixture rows and deterministic expected results.

**Verified resolution steps**

1. Check the import summary for the intended dataset.
2. Reset the topic to **All topics** and try another implemented difficulty.
3. Confirm algorithm questions use Python, JavaScript/TypeScript, Java, or C++, and data-analysis filters use SQL, Pandas, PySpark, or Polars.
4. Review [Datasets](DATASETS.md) to confirm whether that source can produce complete selectable questions.

**Confirm the issue is resolved**

The curated picker lists at least one matching question and **Open question** opens it.

**Report a bug instead when**

DuckDB contains a complete, non-AI question matching every active filter, but the picker does not list it. Report non-sensitive metadata and filter values only.

## The app cannot open or write DuckDB data

**Symptom**

The app fails during startup/database migration, or displays a storage message such as:

```text
The original attempt could not be saved locally. Assessment was not requested.
```

or:

```text
The valid question could not be saved locally. No partial question was kept.
```

**Likely cause**

DuckDB could not open, migrate, or write the configured database path. The UI intentionally does not expose the underlying database exception for these operations.

**Verified resolution steps**

1. Stop Streamlit before changing database configuration.
2. Confirm the current database directory is writable and protect any existing database as user data.
3. To distinguish an existing-file problem from application startup, set `CODING_TUTOR_DB` to a new file path in a writable directory before launching the process.
4. Restart the app with the normal command:

   ```powershell
   uv run streamlit run app.py
   ```

Do not delete or overwrite the existing DuckDB file as a troubleshooting step; the project has no automated recovery or restore command.

**Confirm the issue is resolved**

The app starts, migrations complete without an error, and a new submission can be saved and appears in Progress.

**Report a bug instead when**

A new database in a writable location fails reproducibly. Include the traceback or safe UI message, schema version if available, and operating system—never the database file itself if it contains learner data.

## Quiz preparation or scoring remains in an error state

**Symptom**

Quiz Mode shows **Retry quiz creation**, **Retry assessment**, or a warning that some AI assessments failed.

**Likely cause**

Question generation, MCQ preparation, or static coding assessment failed. Quiz state and completed item scores are stored before the retry.

**Verified resolution steps**

1. Restore the provider/model used when the quiz was started. Scoring retry rejects a different provider or model.
2. Resolve the provider configuration or response problem described in the displayed warning.
3. Use **Retry quiz creation** or **Retry assessment**. Do not start by clearing the database; drafts and completed assessments are intended to survive retry.
4. If status remains `preparing`, reload the page as the UI instructs, then retry if the error state appears.

**Confirm the issue is resolved**

The quiz enters the answering view or reaches the completed result while preserving prior answers and scored items.

**Report a bug instead when**

The same provider/model is selected and available, but retry loses durable answers, changes completed scores, or cannot progress from a valid stored quiz state.

## A curated quiz has too few matching questions

**Symptom**

Quiz preparation stops with a message in this form:

```text
Only 0 matching curated questions are available; 2 are required.
```

The numbers reflect the available and requested counts.

**Likely cause**

The database contains fewer complete, non-AI questions than the quiz requires for its stored question type, difficulty, topic, and method. Curated quiz selection does not duplicate a question to fill the requested count.

**Verified resolution steps**

1. Note the filters and question count used to start the quiz.
2. Import additional authorized dataset records that can produce complete questions matching those filters. Follow [Dataset Setup](dataset-setup.md); rerunning an import is idempotent.
3. Return to Quiz Mode and select **Retry quiz creation**. The retry uses the settings stored with the existing quiz attempt.

Changing the current sidebar filters or question count does not reconfigure that stored attempt. The current UI has no abandon-or-reconfigure control for an unfinished quiz.

**Confirm the issue is resolved**

Quiz Mode enters the answering view with the requested number of distinct questions.

**Report a bug instead when**

Enough complete curated questions match every stored filter, but retry still reports a smaller available count. Include the safe count message and filter values; do not attach the database or raw dataset records.

## Firecrawl is keyless or unavailable

If the app reports keyless access even after setting `FIRECRAWL_API_KEY`, close and restart the terminal and Streamlit. Windows user-environment changes are not inherited by processes that were already running. Confirm only that the variable exists; never print or paste its value into logs. When Firecrawl is unavailable, the app preserves the session and falls back to local/model-only question generation with a warning.

## A JD or resume cannot be read

Uploads must be PDF, DOCX, or TXT and no larger than 5 MB. Encrypted, damaged, or image-only scanned PDFs are rejected because the app does not perform OCR. Convert the document to selectable text and retry. Raw documents are not stored in DuckDB.

## PySpark or another learner solution does not run

**Symptom**

There is no Run button, runtime output, or executed test result for Python, JavaScript/TypeScript, Java, C++, SQL, Pandas, PySpark, or Polars code.

**Likely cause**

This is the implemented behavior, not a missing runtime dependency. The editor stores text and sends it for optional AI static review; the app has no learner-code execution subsystem or PySpark runtime detection.

**Verified resolution steps**

1. Use the editor to write the selected method.
2. Select **Submit solution** for AI-estimated feedback, understanding that no code is executed.
3. Run code in a separate environment only after reviewing it and accepting responsibility for that environment's safety and data access.

Installing PySpark into this project does not enable execution in the application.

**Confirm the issue is resolved**

The UI accepts PySpark text and can return a clearly labelled static AI assessment when a provider is configured. No executed result should appear.

**Report a bug instead when**

The PySpark method is unavailable for a complete data-analysis question, the editor cannot retain its text, or the UI falsely labels an AI estimate as an executed result.

## Reporting a reproducible problem

Use the repository's bug-report template. Include:

- exact reproduction steps;
- the safe symptom/error text;
- operating system, Python, `uv`, and Streamlit versions;
- question source/type, difficulty, method, provider, and model identifiers when relevant;
- whether a new writable DuckDB path reproduces a storage problem; and
- the narrowest relevant test result.

Do not attach API keys, environment dumps, raw datasets, DuckDB files, private learner code, or unredacted logs. For security-sensitive issues, follow the [Security Policy](../SECURITY.md) instead of filing a public bug.
