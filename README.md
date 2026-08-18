# Coding Tutor

A local, privacy-first AI coding tutor that runs entirely on your machine. Practice algorithm and data-analysis problems, get teacher-style AI feedback, and track your progress in an embedded database — without sending anything except API calls to an AI provider of your choice.

**GitHub:** https://github.com/pypi-ahmad/Coding-Tutor  
**Local URL:** `http://127.0.0.1:8551`

---

## Overview

Coding Tutor is a Streamlit application you run locally with your own API credentials. It presents algorithm questions (Python) and data-analysis questions (SQL, Pandas, PySpark, Polars) with an integrated code editor, automated test runner, and AI teacher feedback. Progress is stored in a local DuckDB database that belongs entirely to you.

Curated practice questions are imported from public research datasets into the local database. Additional questions can be generated on demand by the selected AI provider.

> **Your data, your responsibility.** Code you submit for evaluation is executed locally. Anything you send to an external AI API (prompts, code, questions) is subject to that provider's terms of service. You are fully responsible for the data you choose to process with this application. See [DISCLAIMER.md](DISCLAIMER.md).

---

## Features

- **LeetCode-style problem interface** — algorithm questions (Python) and data-analysis questions (SQL, Pandas, PySpark, Polars) in a single UI
- **Multi-provider AI support** — Agnes AI, OpenAI, and Google Gemini, selectable at runtime; unverified model IDs are disabled with a clear message rather than silently substituted
- **Curated datasets** — questions imported from LeetCodeDataset, APPS, TACO, Spider, sql-create-context, and querypls (~125,000 problems across six sources)
- **AI question generation** — generate new problems at any difficulty on demand; generated questions are validated before saving, and incomplete responses are rejected
- **Isolated code evaluation** — submissions run in a subprocess with an empty environment (no secrets exposure), isolated temp directory, and a strict timeout; SQL is evaluated against an in-memory DuckDB instance separate from the app database
- **Teacher-style feedback** — after evaluation the selected AI model provides percentage correctness, marks, identified mistakes, an explanation, and an optional corrected code snippet
- **Show Solution** — view reference solutions (from datasets or AI-generated) for all supported methods; solution views are recorded in progress history
- **Full attempt history** — every submission is stored separately in DuckDB, never overwritten; progress page with filtering by type, difficulty, and method

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io/) ≥ 1.37 |
| Local database | [DuckDB](https://duckdb.org/) ≥ 1.0 |
| Data handling | pandas ≥ 2.1, pyarrow ≥ 15.0 |
| AI providers | OpenAI SDK ≥ 1.40, Google Generative AI ≥ 0.7, Agnes AI (OpenAI-compatible endpoint) |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Testing | pytest ≥ 8.0, pytest-mock |
| Language | Python ≥ 3.11 |

---

## Project Structure

```
coding-tutor/
├── app.py                        # Streamlit entry point, session state init
├── launch_app.cmd                # Windows double-click launcher
├── pyproject.toml                # Dependencies and project metadata (uv/hatch)
├── .streamlit/config.toml        # Server host (127.0.0.1) and port (8551)
├── .env.example                  # Environment variable template
├── Dataset/                      # Raw datasets (gitignored — download separately)
│   ├── algorithm_problems/       # LeetCodeDataset, APPS, CodeContests, TACO
│   └── data_analysis_problems/   # Spider, sql-create-context, querypls
├── src/coding_tutor/
│   ├── providers/                # AI provider abstraction layer
│   │   ├── base.py               # BaseProvider ABC, ModelOption, ChatMessage
│   │   ├── config.py             # Model registry with verified/unverified flags
│   │   ├── registry.py
│   │   ├── openai_provider.py
│   │   ├── agnes_provider.py     # Uses OpenAI-compatible endpoint
│   │   └── gemini_provider.py
│   ├── database/
│   │   ├── connection.py         # Singleton DuckDB connection, get_test_db()
│   │   ├── schema.py             # DDL for all 10 application tables
│   │   ├── migrations.py         # Version-tracked, idempotent migration runner
│   │   └── progress.py           # Progress summary and attempt history queries
│   ├── dataset/
│   │   ├── importer.py           # Orchestrator with import_runs tracking
│   │   ├── leetcode.py
│   │   ├── apps_dataset.py
│   │   ├── taco.py
│   │   ├── codecontests.py       # Graceful skip (binary archive format)
│   │   ├── spider.py
│   │   ├── sql_create_context.py
│   │   └── querypls.py
│   ├── generation/
│   │   ├── prompts.py            # Versioned prompt templates (PROMPT_VERSION)
│   │   ├── validator.py          # Structural validation before saving
│   │   └── generator.py          # Provider call → validate → persist
│   ├── evaluation/
│   │   ├── runner.py             # Isolated subprocess runner (Python, SQL, Pandas, Polars, PySpark)
│   │   ├── feedback.py           # AI teacher feedback dataclass and parser
│   │   └── persistence.py        # save_attempt(), mark_solution_viewed()
│   ├── quiz/
│   │   └── session.py            # Streamlit session state helpers
│   └── ui/
│       ├── sidebar.py            # Provider, model, question type, difficulty, method
│       ├── main_page.py          # Question picker + LeetCode-style display + editor
│       ├── submit_handler.py     # Done button: run → feedback → save → display
│       ├── evaluation_view.py    # Test results + teacher feedback panel
│       ├── solution_view.py      # Reference and AI-generated solutions by method
│       └── progress_page.py      # Attempt history with filtering
└── tests/                        # 46 tests — pytest + pytest-mock
    ├── fixtures/                 # Minimal sample files for import pipeline tests
    ├── test_config.py
    ├── test_providers.py
    ├── test_database.py
    ├── test_import.py
    ├── test_generation.py
    ├── test_evaluation.py
    └── test_ui.py
```

---

## Prerequisites

- **Python 3.11** or later
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — the Python package manager used by this project
- At least one AI provider API key (see [Environment Variables](#environment-variables))

---

## Installation and Setup

### Option A: Windows double-click launcher

Double-click `launch_app.cmd` in the project root. It will:
1. Verify that `uv` is installed and guide you to install it if not.
2. Synchronise all dependencies.
3. Start the app at `http://127.0.0.1:8551`.

### Option B: Command line

```bash
# 1. Clone the repository
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor

# 2. Install dependencies
uv sync

# 3. Create your environment file
cp .env.example .env
# Edit .env and add API keys for the provider(s) you want to use

# 4. Start the app
uv run streamlit run app.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values for the AI providers you want to use. At least one provider key is required to use AI features.

| Variable | Provider | Notes |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | Required for OpenAI models |
| `OPENAI_BASE_URL` | OpenAI | Optional — for proxies or alternative endpoints |
| `AGNES_API_KEY` | Agnes AI | Required for Agnes 2.5 Flash |
| `GOOGLE_API_KEY` | Google Gemini | Required for Gemini models |
| `CODING_TUTOR_DB` | — | Optional — override the default DuckDB file path |

> [!WARNING]
> Never commit `.env`. It is listed in `.gitignore`. Only `.env.example` (empty values) belongs in version control. The application reads API keys only from environment variables and never logs, stores, or displays them.

---

## Dataset Setup

The raw datasets are not included in the repository (they total ~8 GB). A downloader script fetches them directly from Hugging Face. See [docs/dataset-setup.md](docs/dataset-setup.md) for the full guide including troubleshooting and license notes.

```bash
# Download all datasets (CodeContests excluded by default — 7 GB, binary)
uv run python scripts/download_datasets.py

# Download specific datasets only
uv run python scripts/download_datasets.py --datasets leetcode taco spider

# Then import into DuckDB
uv run python -c "
from coding_tutor.database.connection import get_db
from coding_tutor.dataset.importer import run_import
run_import(get_db())
"
```

Import is **idempotent** — re-running skips already-imported records. Each run is logged in the `import_runs` table.

### Included datasets

| Dataset | Type | License | Notes |
|---|---|---|---|
| [LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset) | Algorithm (Python) | Apache-2.0 | Includes reference solutions and test cases |
| [APPS](https://huggingface.co/datasets/codeparrot/apps) | Algorithm (Python) | MIT | Includes I/O test cases |
| [TACO](https://huggingface.co/datasets/BAAI/TACO) | Algorithm (Python) | Apache-2.0 | Includes I/O test cases |
| [CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests) | Algorithm | MIT | Skipped — binary archive format |
| [Spider](https://huggingface.co/datasets/xlangai/spider) | Data Analysis | CC BY-SA 4.0 | Schema only; no fixture data rows |
| [sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context) | Data Analysis | CC BY 4.0 | Schema + SQL answer; no fixture data rows |
| [querypls](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset) | Data Analysis | Apache-2.0 | Schema + SQL answer; no fixture data rows |

> [!NOTE]
> Data-analysis questions without fixture data rows are imported with `is_complete = false`. They support reference study but not automated test execution. Fully executable data-analysis questions can be generated through the AI generation feature.

---

## Usage

1. Start the app (`uv run streamlit run app.py` or double-click `launch_app.cmd`).
2. Open `http://127.0.0.1:8551` in your browser.
3. In the **sidebar**, select your AI provider and model, question type, difficulty, and coding method.
4. Use the **Practice** page to browse questions, write code in the editor, and submit.
5. Review deterministic test results and AI teacher feedback.
6. Use **Show Solution** to view reference solutions (labeled by source) or request an AI-generated solution.
7. Track all attempts on the **Progress** page, with filtering by type, difficulty, and method.

---

## How the App Works

### Provider model

Each AI provider implements a common `BaseProvider` interface. Models carry a `verified` flag — set to `True` only when the model ID has been confirmed in official provider documentation. Unverified models are shown in the sidebar but cannot be called.

**Verified at implementation date:**

| Provider | Model | Notes |
|---|---|---|
| Agnes AI | `agnes-2.5-flash` | OpenAI-compatible endpoint |

**Disabled (unverified at implementation date):** `gpt-5.6-luna` (OpenAI), `gemini-3.5-flash-lite` and `gemini-3.7-flash` (Google Gemini).

### Code evaluation

Submitted code runs in a child process with `env={}` (empty environment), an isolated temp directory, and a 10-second timeout. SQL runs against `duckdb.connect(":memory:")` — a fresh instance with no connection to the app database. PySpark checks for a local Java installation before attempting to run; if absent, it returns a clear error rather than silently substituting another method.

> [!CAUTION]
> On Windows, isolation is at the process level only. Linux namespace isolation, seccomp, and cgroup limits are not available. Do not expose this application to untrusted code from other users.

### Database schema

All data is persisted in `coding_tutor.duckdb`. The schema is applied idempotently at startup via a version-tracked migration runner. Every submission is stored as a new row — previous attempts are never overwritten.

**Tables:** `schema_versions`, `import_runs`, `question_sources`, `questions`, `question_assets`, `reference_solutions`, `question_test_cases`, `ai_generated_questions`, `attempts`, `solution_views`

---

## Documentation

| Document | Description |
|---|---|
| [docs/dataset-setup.md](docs/dataset-setup.md) | Full dataset download guide — downloader script, expected directory structure, import API, troubleshooting |

---

## Testing

```bash
uv run pytest
```

No API keys or dataset files are required — all provider calls are mocked and database tests use an in-memory DuckDB instance.

---

## Privacy, Responsibility, and Security Limitations

- **API calls.** When you use AI features (question generation, teacher feedback, solution generation), the relevant content is sent to the external AI provider whose API key you supply. Review the provider's privacy policy before use.
- **Local execution.** Practice questions, attempt history, and the DuckDB database are stored on your machine only.
- **Code execution security.** See the security model described above and in [SECURITY.md](SECURITY.md).
- **User responsibility.** You are fully responsible for the data you process with this application. See [DISCLAIMER.md](DISCLAIMER.md).

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code guidelines, and the pull request process.

This project is free and community-driven. No financial contributions, donations, or sponsorships are requested or accepted.

---

## License

[MIT License](LICENSE) — Copyright (c) 2026 Ahmad Mujtaba

---

## Acknowledgements

Practice questions are sourced from the following public datasets:

- [LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset) — Apache-2.0
- [APPS](https://huggingface.co/datasets/codeparrot/apps) (Hendrycks et al., 2021) — MIT
- [TACO](https://huggingface.co/datasets/BAAI/TACO) — Apache-2.0
- [CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests) — MIT
- [Spider](https://huggingface.co/datasets/xlangai/spider) (Yu et al., 2018) — CC BY-SA 4.0
- [sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context) — CC BY 4.0
- [querypls prompt2sql dataset](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset) — Apache-2.0

---

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
