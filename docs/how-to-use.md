# How to Use Coding Tutor

> **Document type:** How-to guides (Diátaxis) — each section is a self-contained recipe for one specific task. For a shorter introduction, see [Getting Started](GETTING_STARTED.md). For internals, see the [maintainer reference](technical-reference.md).

Coding Tutor runs on your machine at `http://127.0.0.1:8551`. AI-backed actions require at least one provider key in the environment inherited by the app; curated Practice browsing, Progress, and dataset commands do not.

---

## Contents

**Using the app**
- [Set up and launch on Windows](#set-up-and-launch-on-windows)
- [Configure an AI provider and model](#configure-an-ai-provider-and-model)
- [Practice a curated dataset question](#practice-a-curated-dataset-question)
- [Generate a fresh AI question](#generate-a-fresh-ai-question)
- [Use Mixed mode](#use-mixed-mode)
- [Filter questions by topic](#filter-questions-by-topic)
- [Solve an algorithm question](#solve-an-algorithm-question)
- [Solve a data-analysis question](#solve-a-data-analysis-question)
- [Submit a solution for AI assessment](#submit-a-solution-for-ai-assessment)
- [Apply and undo an AI-suggested correction](#apply-and-undo-an-ai-suggested-correction)
- [View or generate a solution](#view-or-generate-a-solution)
- [Switch question type or method without losing your draft](#switch-question-type-or-method-without-losing-your-draft)
- [Take a quiz](#take-a-quiz)
- [Resume an interrupted quiz](#resume-an-interrupted-quiz)
- [Retry a failed quiz assessment](#retry-a-failed-quiz-assessment)
- [Review your progress](#review-your-progress)
- [Use a custom database location](#use-a-custom-database-location)

**Datasets and development**
- [Download practice datasets](#download-practice-datasets)
- [Import downloaded datasets into DuckDB](#import-downloaded-datasets-into-duckdb)
- [Import only specific datasets](#import-only-specific-datasets)
- [Preview a dataset download without transferring files](#preview-a-dataset-download-without-transferring-files)
- [Run the test suite](#run-the-test-suite)
- [Understand local storage and privacy](#understand-local-storage-and-privacy)
- [Troubleshoot common failures](#troubleshoot-common-failures)

---

## Using the app

### Set up and launch on Windows

1. Install Python 3.11 or newer and [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and open its root directory:

   ```powershell
   git clone https://github.com/pypi-ahmad/Coding-Tutor.git
   Set-Location Coding-Tutor
   ```
3. Double-click `launch_app.cmd`.
4. The launcher creates `.venv` when needed, runs `uv sync --locked`, and starts Streamlit at `http://127.0.0.1:8551`.

The launcher does not download or install `uv`. If `uv` is missing, it displays the official installation URL and exits without changing the machine.

From PowerShell, the equivalent launch command is:

```powershell
uv sync --locked
uv run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8551
```

### Configure an AI provider and model

You need this before generating questions, starting a quiz, requesting an assessment, or viewing AI-authored solutions.

1. Set a provider key in the environment before starting the app. The project does not load `.env` files. Pick one provider:

   ```powershell
   $env:OPENAI_API_KEY = "<your-key>"
   # Optional for an OpenAI-compatible endpoint:
   $env:OPENAI_BASE_URL = "https://your-endpoint.example/v1"

   # Or configure one of these providers instead:
   $env:AGNES_API_KEY = "<your-key>"
   $env:GOOGLE_API_KEY = "<your-key>"
   ```

   These assignments apply only to the current PowerShell process. To use the double-click launcher, create the variable in Windows user environment settings, then start a new launcher process. Never put real keys in `.env.example`.
2. Restart the app after changing an environment variable.
3. In the sidebar, open **AI provider** and select the provider you configured.
4. Confirm the sidebar shows a green "configuration available" message. If it shows a warning, the key was not found — double-check the variable name and restart the app.
5. Select a model from the **Model** dropdown. Only verified models can be used; an unverified model shows a warning with a link to its official documentation instead of a working option.

### Practice a curated dataset question

Curated questions come from imported datasets and work without an API key.

1. In the sidebar, set **Learning mode** to **Curated dataset**.
2. Choose **Question type** (Algorithm or Data analysis), **Difficulty**, and **Solution method**.
3. Optionally choose a **Topic/tag** to narrow the list to a specific area.
4. On the Practice page, pick a question from the dropdown and select **Load Question**. The picker shows up to 20 matching questions at a time.

> If the dropdown is empty, no imported questions match your current type/difficulty/method/topic combination — see [Import downloaded datasets into DuckDB](#import-downloaded-datasets-into-duckdb) or relax your filters.

### Generate a fresh AI question

Requires a configured, verified provider and model (see [Configure an AI provider and model](#configure-an-ai-provider-and-model)).

1. Set **Learning mode** to **AI generated**.
2. Set **Question type**, **Difficulty**, **Solution method**, and optionally a free-text **Topic** of at most 100 characters.
3. Select **Generate Question**.
4. Wait for the spinner — the question is validated against a strict schema and saved before it's shown; if generation fails, nothing partial is saved and an error explains why (e.g., malformed provider response, unconfigured provider).

### Use Mixed mode

1. Set **Learning mode** to **Mixed**.
2. Select **Get Question**. The app picks a curated question or generates one with equal probability when both are available.
3. If only one source is available (e.g., no matching curated questions, or no provider configured), the app uses that source automatically and tells you which one.

### Filter questions by topic

1. After choosing question type and difficulty, open the **Topic/tag** dropdown.
2. In Curated dataset mode, this lists only tags that actually exist among matching imported questions.
3. In AI Generated or Mixed mode, you can also type a custom topic — it steers what the AI generates rather than filtering existing rows.

### Solve an algorithm question

1. Select **Algorithm** as the question type. The available solution method is Python.
2. Load a curated question or generate one with AI.
3. Read the statement, examples, and constraints, then write Python in the editor.
4. Select **Done** when you want a static AI assessment, or **Show Solution** to view stored references and optionally request teaching approaches.

The app stores imported test cases as question context where available, but it does not execute the learner submission against them.

### Solve a data-analysis question

1. Select **Data analysis**, then choose SQL, Pandas, PySpark, or Polars.
2. Load a complete matching question or generate one with AI. Complete tasks display shared schema, fixture data, and expected results.
3. Write the selected method in the editor. Python-family methods receive Python templates; SQL receives a SQL template.
4. Select **Done** for static AI review. The selected text is not executed against DuckDB, a Python runtime, or Spark.

Changing the method uses the draft-protection dialog described below. PySpark is treated as text for AI review and does not require a local Spark runtime because the app does not execute it.

### Submit a solution for AI assessment

1. Load a question and write your solution in the code editor.
2. Select **✅ Done**.
3. The app first saves your original submission as a permanent attempt record, then requests a static AI review.
4. Read the AI-estimated correctness percentage, marks, identified mistakes, explanation, and suggested correction.

> Your code is never executed. The percentage and marks are an AI estimate from static review, not a test result — this is stated in the assessment panel itself.

### Apply and undo an AI-suggested correction

1. After an assessment with a suggested correction, select **Apply correction to editor**.
2. The correction replaces the editor's contents; your original submitted attempt in the database is untouched.
3. To go back, select **Restore pre-correction code**. If you edited the correction further, the button warns you before discarding those edits.

### View or generate a solution

1. With a question loaded, select **💡 Show Solution**.
2. Stored references (from the dataset or a previous AI generation) appear immediately, labeled by source.
3. For data-analysis questions, pick a method with the segmented control first.
4. Select **Generate teaching approaches** (algorithm) or **Generate guided {METHOD} solution** (data analysis) to request a new AI-authored, validated solution. Algorithm questions may return up to three distinct approaches when meaningfully different; data-analysis questions return exactly one per method.
5. Select **Hide Solutions** to close the panel.

### Switch question type or method without losing your draft

1. If you change **Question type** or **Solution method** while you have unsaved edits in the editor, a dialog appears.
2. Choose **Keep draft and switch** to preserve your edits under the new setting (they reappear if you switch back), **Discard draft and switch** to clear them, or **Cancel** to stay on the current setting.

### Take a quiz

1. Configure a verified provider and model, then go to the **🧠 Quiz** page. A provider is required even for a curated, coding-only quiz.
2. In the sidebar's **Quiz setup**, set the total number of questions (1–10) and how many should be coding questions (the rest become multiple choice).
3. Select **Start quiz**. This may make billable AI calls if you're using AI-generated questions or if any items are multiple choice. MCQ preparation sends bounded question contexts to the selected provider so it can author the options.
4. Answer each item — coding answers in the text area, multiple choice with the radio buttons. Every change is saved as a draft automatically.
5. Select **Submit quiz**. Feedback stays hidden until every item is scored.
6. Review your per-item results: multiple-choice items show the correct answer and explanation; coding items show the AI-estimated percentage and feedback. The pass threshold is 80%.

### Resume an interrupted quiz

If you close the app or navigate away mid-quiz, your single active quiz resumes automatically the next time you open the **Quiz** page — no action needed.

### Retry a failed quiz assessment

1. If quiz preparation or scoring fails for any item (e.g., a provider error), the page shows a warning with **Retry preparation** or **Retry scoring**.
2. Select it. Only the failed step is retried — previously scored items and saved answers are not touched.

> Retrying scoring requires the same provider and model that started the quiz. If you've changed your sidebar selection, switch back before retrying.

### Review your progress

1. Go to the **📈 Progress** page.
2. Use the **Question type**, **Difficulty**, and **Method** filters at the top to narrow every section below them.
3. Check the summary metrics (total attempts, attempted questions, AI-estimated solved questions), the recent-attempts table, per-question grouped attempt history, and the attempts-by-difficulty chart.
4. Scroll down for **Quiz progress** (attempts, completions, pass count) and **Solution views** (which questions and methods you've viewed solutions for) — both filtered by the same controls, and never mixed with practice-attempt statistics.

### Use a custom database location

1. Set `CODING_TUTOR_DB` to your preferred file path before starting the app:

   ```powershell
   $env:CODING_TUTOR_DB = "$PWD\local-data\coding_tutor.duckdb"
   uv run streamlit run app.py
   ```

2. The app creates the file (and any missing parent directories) on first use and applies migrations automatically. All questions, attempts, and quiz history live in that file from then on.

---

## Datasets and development

### Download practice datasets

Datasets are optional and are not included in the Git repository. Run the list command below to see the downloader's current approximate size hints before transferring data.

```bash
# See what's available first
uv run python scripts/download_datasets.py --list

# Download the default set (skips CodeContests)
uv run python scripts/download_datasets.py
```

Files land under the gitignored `Dataset/` directory, preserving each source repository's internal structure. For per-dataset file layouts and troubleshooting, see [docs/dataset-setup.md](dataset-setup.md).

### Import downloaded datasets into DuckDB

```bash
uv run python scripts/import_datasets.py
```

This inspects every file's real format before parsing, normalizes records into the shared `questions` schema, and skips any record it has already imported — safe to re-run at any time, including after downloading more data later.

### Import only specific datasets

```bash
uv run python scripts/import_datasets.py --datasets leetcode apps spider
```

Valid keys: `leetcode`, `apps`, `taco`, `codecontests`, `spider`, `sqlctx`, `querypls`.

### Preview a dataset download without transferring files

```bash
uv run python scripts/download_datasets.py --dry-run
```

Useful for confirming which files would be fetched — for example, before deciding whether to include CodeContests (`--include-codecontests`), which the default download set skips.

### Run the test suite

```bash
uv run pytest -q
```

No API keys or downloaded datasets are required. Database-backed tests use in-memory DuckDB, and provider calls are mocked or faked. Use this before opening a pull request; see [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution workflow.

### Understand local storage and privacy

- Questions, attempts, quiz records, and progress are stored in `coding_tutor.duckdb` by default, or at the path in `CODING_TUTOR_DB`.
- Editor state is also held in the active Streamlit session. It is not a substitute for the saved attempt history.
- The app does not execute learner Python, SQL, Pandas, PySpark, or Polars code.
- AI question generation, assessment, teaching solutions, and AI-authored quiz content send the bounded question context and relevant learner input to the provider selected in the sidebar.
- Provider handling is governed by that provider's terms and privacy policy. Do not submit data you are not authorized to process.
- Dataset downloads contact Hugging Face only when you explicitly run the downloader.

### Troubleshoot common failures

| Message or symptom | Action |
|---|---|
| `uv is not installed or is not available on PATH` | Install `uv` from the URL printed by `launch_app.cmd`, open a new process, and run the launcher again. |
| `Dependency setup failed` | Confirm `pyproject.toml` and `uv.lock` are present and that the project directory is writable, then run `uv sync --locked` to see the underlying error. |
| Provider configuration is unavailable | Check the exact environment-variable name, restart the app, and confirm the sidebar status. Do not paste the key into the UI. |
| No curated questions match | Import datasets, choose another difficulty/topic/method, or use AI Generated mode with a configured provider. |
| Generated content is malformed or incomplete | Nothing partial is saved as a usable question. Retry, or select a curated question. |
| AI assessment or quiz preparation fails | Check provider connectivity, quota, and model access. Quiz preparation and scoring expose retry actions for retryable states. |
| Port `8551` is already in use | Stop the existing process using that port before launching another instance. The project is configured specifically for `127.0.0.1:8551`. |

---

*Something missing or unclear? Open an issue — see [SUPPORT.md](../SUPPORT.md).*
