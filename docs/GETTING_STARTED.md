# Getting Started

This tutorial takes a new local user from a fresh clone to one algorithm attempt and one data-analysis attempt.

## 1. Install prerequisites

Install Git, Python 3.11 or newer, and `uv`. Windows 11 is the tested platform. You also need your own API key to generate a question, submit an answer for AI review, request an AI teaching solution, or start a quiz.

## 2. Clone and install

```powershell
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
uv sync --locked
```

On Windows, double-click `launch_app.cmd` instead. It checks for `uv`, creates `.venv` when needed, synchronizes dependencies, and launches the app. If `uv` is missing, it prints official installation links and exits without changing the machine.

## 3. Configure one provider

Set one key in the same terminal that will launch Streamlit:

```powershell
$env:OPENAI_API_KEY = "<your-key>"
# or: $env:AGNES_API_KEY = "<your-key>"
# or: $env:GOOGLE_API_KEY = "<your-key>"
```

`OPENAI_BASE_URL` is optional. `.env.example` documents names only; the app does not load it.

The sidebar displays “configuration available” when the selected provider's expected key is non-blank. This is not a connectivity or credential test. A missing key produces a configuration-unavailable warning and AI-backed actions remain unavailable.

## 4. Optionally prepare curated questions

Place source data under:

```text
Dataset/
├── data_analysis_problems/
└── algorithm_problems/
```

The supplied downloader creates the importer-specific subdirectories:

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py
uv run python scripts/import_datasets.py
```

Datasets are optional. The three implemented SQL-family adapters currently produce incomplete records because their sources do not contain a shared fixture and expected result; those records do not appear in the curated picker.

## 5. Start the app

```powershell
uv run --locked streamlit run app.py
```

Open <http://127.0.0.1:8551>.

## 6. Complete an algorithm question

1. Open **Practice**.
2. Select a provider and model.
3. Choose **Curated dataset** if algorithm data was imported, otherwise **AI generated**.
4. Select **Algorithm**, a difficulty from Beginner through Very Hard, a topic, and **Python**.
5. Load or generate a question and edit the Python template.
6. Click **Done**.

The app saves a new attempt before asking the model for feedback. The displayed percentage and mark are AI estimates; no tests run. If corrected code is returned, **Apply correction to editor** creates a session backup and **Restore pre-correction code** reverses it. The saved submission does not change.

## 7. Complete a data-analysis question

1. Choose **Data analysis**.
2. Select SQL, Pandas, PySpark, or Polars. These are authoring/AI-review methods, not installed execution runtimes.
3. Use **AI generated** to request a complete canonical task. Accepted tasks include schema, fixture rows, expected rows, all four starter templates, and all four references.
4. Write the answer and click **Done** for static review.

If generation returns incomplete structured data, the app displays a validation failure and saves no usable question.

## 8. Find local data

The default database is `coding_tutor.duckdb` in the project root. Set `CODING_TUTOR_DB` before starting the app to choose another local path. The database stores questions, attempts, assessments, solution views, quiz history, import runs, and migrations.

## Troubleshooting

| Message or symptom | Verified meaning |
| --- | --- |
| “configuration unavailable” | The expected provider key is missing or blank. Set it and restart. |
| “No curated ... questions” | No complete imported question matches type, difficulty, topic, and method. |
| “Select a configured, verified model” | The current provider/model cannot be used for the requested AI action. |
| “provider returned malformed JSON” | Structured validation failed; generated content is not saved or displayed as valid. |
| `No source files match ...` | The importer did not find the exact catalog path. Keep the source layout unchanged. |
| Port 8551 does not open | Read the Streamlit terminal output; confirm the process is running and another process is not using the port. |

For normal workflows, continue with [Usage](USAGE.md).
