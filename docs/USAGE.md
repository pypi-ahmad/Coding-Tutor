# Usage

This guide explains how to run Coding Tutor locally and complete the workflows implemented by the current application.

> [!IMPORTANT]
> The editor stores text. Coding Tutor does not execute Python, SQL, Pandas, PySpark, or Polars submissions. Percentages, marks, solved status, and coding-quiz scores are AI estimates rather than verified test results.

## What the app is for

Use Coding Tutor to practise Python algorithms or write data-analysis solutions in SQL, Pandas, PySpark, or Polars. Questions can come from imported datasets, validated AI generation, or a mixture of both. The app can request static teacher-style feedback, show stored or generated teaching solutions, keep Practice and Quiz history, and summarize progress in local DuckDB storage.

## Prerequisites

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/).
- Git when starting from a clone.
- Your own provider credential for question generation, AI assessment, generated teaching solutions, or Quiz Mode.

Windows 11 is the tested launcher platform. The manual `uv` commands are the documented path on other systems.

## Install the project

From a terminal in the cloned repository:

```powershell
uv sync --locked
```

On Windows, you can instead double-click `launch_app.cmd`. It checks for `uv`, creates the root `.venv` if needed, synchronizes locked dependencies, and starts the app. It does not install `uv` automatically.

## Configure a provider

Set the credential in the environment of the process that launches Streamlit, then restart the app. The implemented variable names are:

| Provider | Variable names |
| --- | --- |
| OpenAI | `OPENAI_API_KEY`; optional `OPENAI_BASE_URL` |
| Agnes AI | `AGNES_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` |

`.env.example` is a blank names-only reference. The application does not load `.env` files and never needs more than one provider key for a single selected provider.

The sidebar reports “configuration available” when the selected provider's expected key is non-blank. This is not a login, connectivity, quota, or model-access test.

## Start the app

```powershell
uv run --locked streamlit run app.py
```

Open <http://127.0.0.1:8551>. The tracked Streamlit configuration supplies the loopback address and port.

## Choose provider and learning settings

The sidebar is shared by Practice and Quiz:

1. Select OpenAI, Agnes AI, or Google Gemini.
2. Select one of the verified model options shown for that provider.
3. Choose **Curated dataset**, **AI generated**, or **Mixed**.
4. Choose **Algorithm** or **Data analysis**.
5. Choose Beginner, Easy, Medium, Hard, or Very Hard.
6. Choose a topic/tag. AI-enabled sources accept a custom topic; curated mode lists matching imported tags.
7. Choose the solution method.

Algorithm questions use Python. Data-analysis questions expose SQL, Pandas, PySpark, and Polars. These method choices control templates and AI review; they do not install or run language runtimes.

## Practise a curated question

Curated questions require a prior dataset import.

1. Select **Practice** and **Curated dataset**.
2. Choose filters and a method.
3. Select a matching question and click **Load Question**.

The picker lists at most 20 complete, non-AI questions matching every active filter. If no question appears, broaden the topic or difficulty, or import a supported source. Incomplete SQL-family records without shared fixture data and expected results are intentionally excluded.

## Generate an AI question

1. Select **Practice** and **AI generated**.
2. Choose a configured provider/model, type, difficulty, topic, and method.
3. Use the generation control displayed by the question picker.

One provider request is made. The response must match the exact question schema before the app stores or displays it. Accepted data-analysis questions contain one shared schema, fixture rows, deterministic expected result, all four starter templates, and all four reference solutions. Invalid or incomplete responses are rejected without saving a usable question.

## Use Mixed mode

Mixed mode can use either a matching curated question or AI generation. When both are available, the app chooses between them with equal probability. When only one source is available, it uses that source. AI selection still requires a configured, verified provider/model.

## Write in the editor

Loaded questions show the title, difficulty, statement, examples, and constraints when available. Complete data-analysis questions also show their shared schema, sample fixture rows, and expected output.

The editor prefers a stored starter template and otherwise supplies a basic method-specific template. Practice drafts are keyed by question and method in the current Streamlit session; they are not durable progress records until submitted.

If you change question type or method after editing, choose one of:

- **Keep draft and switch** to retain the current question/method draft in session state;
- **Discard draft and switch** to remove it explicitly; or
- **Cancel** to keep the current controls and editor.

## Submit with Done

**Done** is enabled after the editor contains non-blank text.

1. Click **Done**.
2. The app saves a new Practice attempt containing the exact submitted text before validating the provider or making a request.
3. With a configured provider and valid model, the question context, selected method, and learner submission are sent for static review.
4. Review the **AI Teacher Assessment**.

Each click creates a separate attempt. Earlier attempts are not overwritten.

The assessment can include:

- AI-estimated correctness from 0–100%;
- AI-estimated marks out of 10, calculated as percentage divided by 10;
- identified issues;
- an explanation;
- a suggested correction; and
- optional corrected code.

No stored test case is executed. `deterministic_test_result` remains `not_run`.

## Apply or restore a correction

When corrected code is available:

1. Inspect the proposed code.
2. Click **Apply correction to editor** to replace the active editor text.
3. Click **Restore pre-correction code** to reverse that replacement.

The app saves the pre-correction editor value in the active Streamlit session. If you edit the applied correction, the restore control warns that restoring will replace those newer edits. The saved attempt always retains the original submitted text.

## View solutions

Click **Show Solution** to open available references.

- Stored references are labelled **Dataset-provided reference** or **Stored AI-generated reference**.
- Algorithm questions can explicitly request up to three generated teaching approaches when meaningful.
- Data-analysis questions show a method selector and can explicitly request one guided solution for the selected method.
- Generated teaching solutions include code, explanation, and theory when validation succeeds.

Showing an existing stored reference makes no provider call. Pressing a generation button does. Generated solutions are not executed, and equivalence across SQL, Pandas, PySpark, and Polars is not deterministically verified. Displayed methods are recorded in local solution-view history.

## Review progress

Open **Progress** to filter by question type, difficulty, or method. The page displays:

- total attempts and distinct attempted questions;
- questions considered AI-estimated solved;
- recent attempts;
- every marked attempt and attempts grouped by question;
- attempts by difficulty;
- quiz attempts, completions, and passes; and
- solution-view history.

A Practice question is AI-estimated solved when at least one completed matching attempt reaches 80%. Repeated attempts remain separate, and their marks are not averaged.

## Use Quiz Mode

Quiz Mode requires a configured provider/model, including for curated questions, because MCQ preparation and non-blank coding assessment can use AI.

1. Select **Quiz**.
2. Choose the shared source, type, difficulty, topic, and method controls.
3. Choose 1–10 total questions and the number of coding questions. The remainder are MCQs.
4. Click **Start quiz**.
5. Answer each item and click **Submit quiz**.

Implemented rules:

- questions are selected randomly without duplicate curated questions;
- AI-source questions use the normal validated generation pipeline;
- each prepared MCQ has four unique options and one validated correct option;
- drafts are saved in DuckDB, and the newest unfinished quiz resumes automatically;
- the quiz is untimed, equally weighted, has no negative marking, and passes at 80%;
- MCQs score 100 or 0 by option ID;
- blank coding answers score 0;
- non-blank coding answers receive static AI-estimated scores; and
- feedback remains hidden until the quiz is scored.

If preparation or coding assessment fails, use **Retry preparation** or **Retry scoring**. Durable answers and already scored items are preserved. A scoring retry requires the same provider/model used for the quiz.

## Prepare local datasets

Downloaded sources are expected under:

```text
Dataset/
├── algorithm_problems/
└── data_analysis_problems/
```

List configured sources, download the default set, and import supported records:

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py
uv run python scripts/import_datasets.py
```

Import selected source keys when needed:

```powershell
uv run python scripts/import_datasets.py --datasets leetcode apps taco
```

The importer inspects files, preserves raw sources, stores provenance, and skips records already identified by the same stable source key. See [Datasets](DATASETS.md) for exact source layouts, licenses, and completeness limits.

## Local storage and privacy

The default database is `coding_tutor.duckdb` in the working directory. `CODING_TUTOR_DB` can select another path before startup. The database can contain imported and generated questions, provenance, learner submissions, AI feedback and corrections, solution views, quiz drafts/results, import runs, and schema versions.

Practice drafts remain only in Streamlit session state until submission; quiz drafts are persisted. The database is not encrypted, backed up, or access-controlled by the app, and there is no supported in-app reset or deletion command.

Typing alone does not contact a provider. Explicit AI actions—question generation, **Done**, generated teaching solutions, and provider-dependent Quiz preparation/scoring—send relevant question and learner context to the selected provider. The app does not send environment-variable values or upload the DuckDB file as a file, but provider-side handling remains governed by that provider. Use only data you are authorized to send.

## Troubleshooting

| Symptom | Implemented meaning and action |
| --- | --- |
| The launcher says `uv` is unavailable | Install `uv` using the official URL shown by the launcher, then run it again. The launcher intentionally does not install software. |
| Provider configuration is unavailable | The required variable is missing or blank. Set it in the launching environment and restart Streamlit. |
| A provider-backed action fails | Configuration presence does not prove authentication, network access, quota, or model entitlement. Correct the provider-side issue and retry; there is no automatic fallback. |
| No curated question matches | No complete imported record matches all active filters. Change a filter or import a supported complete source. |
| Generated content is malformed or incomplete | The provider response failed strict validation. Retry or choose a curated question; rejected content is not accepted as usable. |
| Dataset import reports `No source files match ...` | The selected source is missing from its catalog path or the supplied dataset root is incorrect. Preserve the documented layout. |
| Quiz shows a preparation or scoring error | Restore the original provider/model, resolve its configuration problem, and use the displayed retry control. |
| There is no Run button or runtime output | This is expected. The application has no learner-code execution subsystem. |
| DuckDB cannot be opened or written | Stop Streamlit, confirm the database directory is writable, and test a new path through `CODING_TUTOR_DB` without deleting the existing file. |

See [Troubleshooting](TROUBLESHOOTING.md) for verified symptoms, resolutions, and bug-report guidance.
