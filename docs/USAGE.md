# Usage

This guide describes the behavior implemented by the current Streamlit application.

## Choose a question source

- **Curated dataset** lists up to 20 complete, non-AI questions matching the selected type, difficulty, method, and topic.
- **AI generated** makes one provider request, validates the exact JSON contract, and saves an accepted question atomically in DuckDB.
- **Mixed** uses a 50/50 random choice when both sources are available; otherwise it uses the available source.

## Choose difficulty and method

The implemented difficulty values are **Beginner**, **Easy**, **Medium**, **Hard**, and **Very Hard**. Algorithms use Python. Data-analysis questions expose SQL, Pandas, PySpark, and Polars. Changing type or method with an unsaved editor change opens a Keep draft, Discard draft, or Cancel dialog.

## Solve in the editor

Stored starter code is preferred. Otherwise the app supplies a basic method-specific template. Drafts are keyed by question and method in the current Streamlit session; they are not durable progress records until submission or quiz draft saving.

For data analysis, complete questions display shared schema, sample fixture data, and expected output. Imported SQL-only records without all three assets are excluded from the curated picker.

## Submit with Done

**Done** is enabled for non-blank editor text. Each click creates a new attempt containing the original submission, method, provider/model metadata, deterministic status `not_run`, and pending assessment status. Earlier attempts are never overwritten.

The selected model receives bounded question/reference context and the learner submission. A valid response provides:

- AI-estimated correctness from 0–100%;
- a derived mark equal to percentage divided by 10;
- identified issues;
- an explanation;
- a suggested correction; and
- optional corrected code.

These are not test results. No Python, SQL, Pandas, PySpark, or Polars code runs.

If corrected code is present, inspect it before selecting **Apply correction to editor**. The current editor value is backed up in session state, the immutable attempt remains unchanged, and **Restore pre-correction code** reverses the application. Editing after application triggers a warning before restore replaces those later edits.

## Show solutions

**Show Solution** displays stored references with either **Dataset-provided reference** or **Stored AI-generated reference** labels. Stored source artifacts may have no explanation.

An explicit generation button can request a structured, commented teaching solution. Algorithms allow up to three approaches when meaningful. A data-analysis request generates one solution for the selected method; use the method control to request others separately. Generated solutions include explanation and theory, but are not executed and cross-method equivalence is not verified.

Viewing a displayed method creates or updates a local solution-view record and links it to the matching most recent attempt when possible.

## Review progress

Open **Progress** and filter by question type, difficulty, or method. The page shows total attempts, attempted questions, AI-estimated solved questions, five recent attempts, each marked attempt, attempts grouped by question, attempts by difficulty, quiz history, and solution views.

A question is considered AI-estimated solved when any completed matching attempt reaches 80%. Repeated attempts remain separate and marks are not averaged.

## Use Quiz Mode

Quiz Mode requires a configured provider/model even for curated questions. Choose 1–10 total items and how many are coding items; the remainder are MCQs. It uses the selected source, type, difficulty, topic, and method.

- Curated questions are selected randomly without duplicates.
- AI-source questions use the normal validated generation pipeline.
- Mixed selection independently chooses AI or an available curated candidate.
- Each MCQ receives exactly four unique model-generated choices and one validated correct option ID.
- Draft answers are saved to DuckDB and the newest unfinished quiz resumes automatically.
- The quiz is untimed, equally weighted, has no negative marking, and passes at 80%.
- MCQs score 100 or 0 by option ID. Blank coding answers score 0. Non-blank coding answers receive AI-estimated scores.
- Feedback stays hidden until scoring completes. Failed AI scoring remains retryable, preserving drafts and already scored items.

## Manage local datasets

Use `scripts/download_datasets.py` and `scripts/import_datasets.py` as documented in [Datasets](DATASETS.md). Import is idempotent by source identity; source files are read only.

There is no implemented in-app reset or supported destructive reset command. To start with a separate database without deleting history, set a new path before launch:

```powershell
$env:CODING_TUTOR_DB = "coding_tutor_fresh.duckdb"
uv run streamlit run app.py
```

Back up and protect database files yourself. Do not post them publicly because they can contain learner submissions and AI feedback.
