# How to Use Coding Tutor

This how-to guide explains how to complete common tasks in the current Coding Tutor application. For implementation details, see the [Technical Reference](TECHNICAL_REFERENCE.md).

> [!IMPORTANT]
> Coding Tutor does not execute learner code. Coding scores and correctness percentages come from static AI review.

## Install and launch

### Launch on Windows

1. Install Python 3.11 or newer, Git, and [`uv`](https://docs.astral.sh/uv/).
2. Clone the repository:

   ```powershell
   git clone https://github.com/pypi-ahmad/Coding-Tutor.git
   Set-Location Coding-Tutor
   ```

3. Run `launch_app.cmd`.
4. Open <http://127.0.0.1:8551> if the browser does not open automatically.

The launcher verifies `uv`, creates `.venv` when necessary, runs `uv sync --locked`, and starts Streamlit. It does not install `uv` automatically.

### Launch manually

```powershell
uv sync --locked
uv run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8551
```

Stop the server with `Ctrl+C`.

## Configure external services

### Configure an AI provider

Set one provider credential in the environment before launching the app:

```powershell
$env:OPENAI_API_KEY = "<your-key>"

# Or use one of these providers:
$env:AGNES_API_KEY = "<your-key>"
$env:GOOGLE_API_KEY = "<your-key>"
```

For an OpenAI-compatible endpoint, also set:

```powershell
$env:OPENAI_BASE_URL = "https://your-endpoint.example/v1"
```

Restart Streamlit after changing environment variables. Select the configured provider and model in the sidebar.

> [!CAUTION]
> `.env.example` is not loaded by the application. Never place real credentials in that file or commit credentials to Git.

### Enable authenticated Firecrawl research

Firecrawl research is optional and disabled by default in the UI. Set a key before launching Streamlit for authenticated access:

```powershell
$env:FIRECRAWL_API_KEY = "<your-key>"
```

Without a key, the application may use Firecrawl's limited keyless mode. Restart the terminal and Streamlit after changing a Windows user environment variable.

## Use Coding mode

### Practice a curated algorithm question

1. Select **Coding**.
2. Choose **Algorithm** as the question type.
3. Choose **Curated questions** as the source.
4. Choose Python, JavaScript/TypeScript, Java, or C++, then select a difficulty and optional topic.
5. Load a question and write your solution in the editor.
6. Select **Submit solution** for static AI review.

If no question is available, relax the filters or import the algorithm datasets. Dataset-provided starter and reference code may be Python-only; the editor supplies a generic template and can request an AI teaching solution for another selected language.

### Build an algorithm catalog in the app

If algorithm source files are already present but their imports are incomplete:

1. Select **Coding**, **Algorithm**, and either **Curated questions** or **Mixed**.
2. Select **Build question catalog**.
3. Wait for each available algorithm source to finish importing.
4. Review the completion or failure message, then retry any failed source after resolving the reported problem.

This algorithm-only action attempts pending LeetCodeDataset, CodeContests, APPS, and TACO imports against the active algorithm database, including a `CODING_TUTOR_DB` override when configured. It does not download missing datasets or build the data-analysis catalog. An absent source is reported as a failed import. CodeContests remains subject to its unresolved source-license status.

### Practice a data-analysis question

1. Select **Coding** and choose **Data analysis**.
2. Choose SQL, Pandas, PySpark, or Polars.
3. Select or generate a question.
4. Review the displayed schema, fixture data, and expected result.
5. Write the solution in the editor.
6. Select **Submit solution**.

The app does not run the SQL or Python-family text. PySpark and Polars do not need to be installed for authoring and AI review.

### Generate a Coding question

1. Configure an AI provider.
2. Select **AI generated** as the source.
3. Choose the question type, difficulty, method, and optional topic.
4. Optionally enable **Web research** for a specific non-general topic.
5. Select **Generate question**.
6. Wait for validation and storage to complete.

Enabled web research runs only when the selected topic is absent from the local reference context. Malformed or incomplete provider output is rejected. A rejected response does not become a usable question.

### Use Mixed question selection

1. Select **Mixed** as the source.
2. Choose the remaining filters.
3. Request a question.

The app uses a matching local question or generates one according to availability and the mode's selection rules.

### Submit a solution

1. Enter a non-blank answer.
2. Select **Submit solution**.
3. Review the AI-estimated percentage, marks, mistakes, explanation, and suggested correction.

The original answer is saved before provider validation or assessment. Every submission creates a separate attempt.

### Apply and restore a correction

1. After assessment, select **Apply suggested correction**.
2. Continue editing if desired.
3. Select **Restore pre-correction code** to return to the editor state saved before applying the correction.

Restoring can replace edits made after applying the correction. The immutable submitted attempt is never changed.

### View a solution

1. Load a question.
2. Select **Show solution**.
3. Review any stored dataset or generated references.
4. Optionally request teaching approaches from the selected provider.

Displaying an existing stored reference does not require a provider call. Requested teaching solutions are validated but not executed.

### Switch settings without losing a draft

When changing question type or method with a modified editor:

- Choose **Keep draft and switch** to retain it under the current question/method key.
- Choose **Discard draft and switch** to clear it.
- Choose **Cancel** to keep the current selection.

## Use Quiz mode

### Start and submit a quiz

1. Configure an AI provider and select **Quiz**.
2. In the sidebar, choose the question source, Algorithm or Data analysis, difficulty, optional topic, and solution method.
3. Choose 1–10 total questions.
4. Choose how many should be coding questions; the remainder are MCQs.
5. Select **Start quiz**.
6. Answer each item. Changes are saved as durable drafts.
7. Select **Submit quiz**.
8. Review item feedback and the final score after scoring finishes.

MCQs are scored locally. Non-blank coding answers receive static AI review. The pass threshold is 80%, with equal item weights and no negative marking.

### Resume an interrupted quiz

Open **Quiz** again. The active quiz and saved answers load automatically.

### Retry a failed quiz step

1. Resolve the provider, connectivity, quota, or model-access problem.
2. Restore the provider and model used when the quiz began.
3. Select **Retry quiz creation** after a preparation failure, or **Retry assessment** after a scoring failure.

Previously saved answers and successfully processed items remain unchanged.

## Use AI Questions mode

### Start an AI Questions session

1. Select **AI Questions**.
2. Choose **Local catalog**, **AI generated**, or **Mixed**.
3. Choose domain, topic, difficulty, answer format, and prompt style.
4. For coding questions, choose Python, JavaScript/TypeScript, Java, C++, or SQL.
5. Optionally enable **Web research** for generated questions.
6. Select **Start practice**.

The app presents one question at a time. **Local catalog** means `Dataset/catalogs/interview.duckdb`. Generated questions are validated and stored there for later reuse.

AI Questions sessions are not adaptive. Starting another question does not send earlier answers, scores, or feedback to the question generator.

### Answer an AI question

1. Enter a theory or coding response, or choose an MCQ option.
2. Select **Submit answer**.
3. Review the immediate AI-estimated score, feedback, and identified gaps.
4. Continue to the next question when ready.

MCQs are scored locally. Theory and coding answers require the selected provider. Code is never executed.

### Use web research for question generation

1. Select AI-generated or Mixed source mode.
2. Enable **Web research**.
3. Generate the next question.

The app searches only when local reference material is insufficient. Source links are retained with generated material. Firecrawl failure produces a warning and the app continues with local/model-only generation. Live web content is never used for grading.

The Interview **Web research** toggle follows the same boundary: it applies only when an AI-generated turn is needed and fewer than three local references are available. Local-only interview questions never invoke Firecrawl.

## Use Interview mode

### Start a tech interview

1. Configure an AI provider and select **Interview**.
2. Choose **Tech interview**.
3. Enter the requested role and level information.
4. Choose the source mode, topics, answer formats, and coding languages.
5. Choose 30, 45, 60, or 90 minutes.
6. Create and review the interview plan.
7. Edit the plan if necessary, then start the interview.

### Start a JD-based interview

1. Choose **JD-based interview**.
2. Paste a job description or upload a PDF, DOCX, or TXT file.
3. Optionally paste or upload a resume.
4. Create the interview plan with the selected provider.
5. Review and edit its topics, formats, and languages.
6. Select a duration and start.

Uploads must be 5 MB or smaller. Image-only scans are unsupported because the app does not perform OCR.

> [!CAUTION]
> JD and resume text is held in memory and is not stored in DuckDB, but creating the plan sends the extracted text to the selected provider. Submit only information you are authorized to share.

### Answer interview questions

1. Read the current question and enter an answer or choose an MCQ option.
2. Select **Submit answer**.
3. Continue until the timer expires or select **Finish interview early**.

The app stores per-turn scoring but withholds feedback until completion. For generated questions, the next question can use the editable plan and up to three recent scored turns: their questions, submitted answers or options, scores, gaps, and next-focus values. The generated question remains standalone and does not reveal that scoring metadata.

Local catalog questions are selected from the interview plan but do not adapt from answer history. In Mixed mode, only the generated turns use adaptive context.

### Finish at timeout

When the timer reaches zero, the current input remains visible:

- Select **Submit answer** to assess the current non-blank answer and immediately complete the report; or
- Select **Finish without answering** to skip it.

The app does not create another question after the deadline. The persisted deadline is not reset by refreshing or rerunning Streamlit.

### Read the final report

After completion, review the overall AI-estimated score, summary, strengths, gaps, and recommendations. The report is coaching feedback, not a hire/no-hire decision.

## Review Progress

1. Select **Progress**.
2. Choose Overview, Algorithms, Data analysis, AI Questions, or Interviews.
3. For coding activities, use difficulty and method filters.
4. Review attempts, grouped history, quiz summaries, solution views, AI-question scores, or interview completion data.

The Overview counts Coding attempts and Quiz attempts across both coding catalogs, scored AI-question items in the interview catalog, and completed interview sessions. Coding **Attempted questions** counts distinct question IDs. Coding attempts remain separate and marks are not averaged; a question is AI-estimated solved when at least one completed attempt reaches 80%. AI Questions averages scored items. Interview completion and average score include completed sessions only.

## Understand activity storage

| Mode | Catalog used |
| --- | --- |
| Coding: Algorithm | `Dataset/catalogs/algorithm.duckdb` |
| Coding: Data analysis | `Dataset/catalogs/data_analysis.duckdb` |
| Quiz | The catalog matching its algorithm or data-analysis question type |
| AI Questions | `Dataset/catalogs/interview.duckdb` |
| Interview | `Dataset/catalogs/interview.duckdb` |
| Progress | Reads the relevant catalog or all three for Overview |

## Manage datasets

### Download coding datasets

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py
```

Raw files are stored below `Dataset/algorithm_problems` and `Dataset/data_analysis_problems`.

CodeContests is skipped by default because its downloaded source card does not state a license. After reviewing and accepting that constraint, download it explicitly:

```powershell
uv run python scripts/download_datasets.py --datasets codecontests --include-codecontests
```

### Build the coding catalogs

```powershell
uv run python scripts/import_datasets.py --datasets leetcode apps taco --database Dataset/catalogs/algorithm.duckdb
uv run python scripts/import_datasets.py --datasets spider sqlctx querypls --database Dataset/catalogs/data_analysis.duckdb
```

Imports are idempotent. Existing stable source identities are skipped.

If you opted into CodeContests, import it separately:

```powershell
uv run python scripts/import_datasets.py --datasets codecontests --database Dataset/catalogs/algorithm.duckdb
```

### Download and import interview sources

Authenticate GitHub CLI, inspect the source list, then download and import:

```powershell
gh auth status
uv run python scripts/download_interview_sources.py --list
uv run python scripts/download_interview_sources.py
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

The downloader records source revisions, hashes, licenses, and ingestion decisions. Sources marked raw-only are retained for later review but are not normalized into usable questions.

### Populate all three catalogs end to end

```powershell
# Download coding sources, then build both coding catalogs
uv run python scripts/download_datasets.py
uv run python scripts/import_datasets.py --datasets leetcode apps taco --database Dataset/catalogs/algorithm.duckdb
uv run python scripts/import_datasets.py --datasets spider sqlctx querypls --database Dataset/catalogs/data_analysis.duckdb

# Download allowed interview sources, then import both interview collections
gh auth status
uv run python scripts/download_interview_sources.py
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

### Use a custom database path

Set `CODING_TUTOR_DB` before launch only when you intentionally want Coding, Quiz, and Progress to use an advanced override path:

```powershell
$env:CODING_TUTOR_DB = "$PWD\local-data\coding-tutor.duckdb"
uv run --locked streamlit run app.py
```

Imports that omit `--database` also honor this value. AI Questions and Interview explicitly use `Dataset/catalogs/interview.duckdb`, even when the override is set. Because Progress reads the override path while it is configured, AI Questions and Interview records written to the dedicated interview catalog will not appear there until the override is removed. For normal unified operation, leave it unset so each activity uses its dedicated catalog.

## Verify a development checkout

```powershell
uv sync --locked
uv run pytest -q
```

Provider calls are mocked in tests, and database tests use temporary or in-memory DuckDB instances.

## Troubleshoot common problems

| Symptom | Action |
| --- | --- |
| `uv` is unavailable | Install it from the URL printed by `launch_app.cmd`, open a new process, and retry. |
| Port 8551 is in use | Stop the existing process on that port before launching another unified app. |
| Provider is not configured | Set the exact environment variable and restart Streamlit. |
| Provider action fails | Check connectivity, quota, model entitlement, and provider status; there is no automatic provider fallback. |
| No local question matches | Relax filters, import the appropriate catalog, or use an AI-generated source. |
| Firecrawl remains keyless | Restart the terminal and Streamlit after setting the user environment variable. |
| PDF/DOCX/TXT cannot be read | Confirm it is 5 MB or smaller, unencrypted, undamaged, and contains selectable text. |
| DuckDB cannot be opened | Stop Streamlit and confirm the catalog directory is writable; do not delete the existing database. |
| There is no Run button | This is expected: learner code is never executed. |

For detailed recovery procedures, see [Troubleshooting](TROUBLESHOOTING.md).
