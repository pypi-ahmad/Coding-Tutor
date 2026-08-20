# Coding Tutor

<div align="center">

**Local coding practice, AI-engineering questions, and timed technical interviews in one Streamlit app.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![DuckDB](https://img.shields.io/badge/Data-DuckDB-FFF000?logo=duckdb&logoColor=black)](https://duckdb.org/)

[Get started](#get-started) · [Explore the modes](#application-modes) · [Prepare datasets](#data-catalogs) · [Read the docs](#documentation)

</div>

Coding Tutor combines local DuckDB question catalogs with optional AI generation and review. Practice algorithms and data analysis, study scenario-based AI topics, run a timed interview, and revisit progress without sending learner code to an execution service.

> [!IMPORTANT]
> Coding Tutor never executes learner code or stored test cases. Scores, correctness percentages, corrections, and coding-quiz results are AI estimates—not deterministic judge results.

## What you can do

- Practice Python algorithms and author SQL, Pandas, PySpark, or Polars solutions.
- Study LLMs, RAG, agents, LangChain, LangGraph, ML, NLP, deep learning, evaluation, safety, and infrastructure.
- Choose curated, AI-generated, or mixed question sources.
- Answer theory, coding, MCQ, direct, and scenario-based questions.
- Run tech interviews or generate an interview plan from a job description and optional resume.
- Select 30, 45, 60, or 90-minute interview sessions with adaptive follow-up questions.
- Receive structured AI review, suggested corrections, teaching solutions, and final interview coaching reports.
- Keep questions, attempts, quiz history, and progress in local DuckDB catalogs.
- Optionally research current source material through Firecrawl when the local catalog is insufficient.

## Application modes

| Mode | Purpose | Primary catalog |
| --- | --- | --- |
| **Coding** | Algorithm and data-analysis practice with static AI review | `algorithm.duckdb`, `data_analysis.duckdb` |
| **Quiz** | Resumable coding and MCQ sessions | Catalog matching the selected activity |
| **AI Questions** | Theory, coding, MCQ, and scenario questions across AI domains | `interview.duckdb` |
| **Interview** | Timed tech or JD-based interviews with a final report | `interview.duckdb` |
| **Progress** | Review practice, quiz, AI-question, and interview history | All three catalogs |

AI Questions supports Python, JavaScript/TypeScript, Java, C++, and SQL. Coding responses are reviewed as text and are never run.

## Get started

### Requirements

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Git
- An API key for AI-backed actions; catalog browsing remains local

### Install and run

```powershell
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
uv sync --locked
uv run --locked streamlit run app.py
```

Open <http://127.0.0.1:8551>.

On Windows, you can instead run `launch_app.cmd`. It verifies `uv`, creates `.venv` when needed, synchronizes the locked dependencies, and launches the same local app.

### Configure an AI provider

Set credentials in the environment that starts Streamlit. The project does not load `.env.example`; it is a names-only reference and must never contain real credentials.

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI credential |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible endpoint |
| `AGNES_API_KEY` | Agnes AI credential |
| `GOOGLE_API_KEY` | Google Gemini credential |
| `FIRECRAWL_API_KEY` | Optional authenticated Firecrawl MCP access |

Only one AI provider key is required. A configured status means a non-blank value was found; it does not verify authentication, quota, network access, or model entitlement.

## Typical workflow

1. Choose **Coding**, **Quiz**, **AI Questions**, **Interview**, or **Progress**.
2. Select the question source, topic, difficulty, format, and provider where applicable.
3. Load a curated question or generate one with AI.
4. Write your response and select **Submit solution** or the mode-specific submit action.
5. Review the labelled AI estimate, explanation, and suggested correction.
6. Revisit saved activity from **Progress**.

For a guided walkthrough, see [Getting Started](docs/GETTING_STARTED.md) and [Usage](docs/USAGE.md).

## Interview mode

**Tech interview** uses role, level, topic, and format preferences. **JD-based interview** requires pasted or uploaded job-description text and accepts an optional resume. Supported uploads are PDF, DOCX, and TXT up to 5 MB; scanned documents are not OCR-processed.

The generated interview plan is editable before the timer starts. During a session, the app presents one question at a time and may adapt later questions to earlier answers. The final result is a coaching report, not a hiring recommendation.

> [!CAUTION]
> JD and resume text is extracted in memory and not stored in DuckDB, but it is sent to the selected AI provider to create the interview plan. Do not submit confidential or personal information unless you are authorized to share it with that provider.

## Data catalogs

Normal app use reads the consolidated DuckDB files, not the raw dataset directories.

| Catalog | Runtime content |
| --- | --- |
| `Dataset/catalogs/algorithm.duckdb` | Algorithm questions, attempts, and related progress |
| `Dataset/catalogs/data_analysis.duckdb` | SQL/data-analysis questions, attempts, and related progress |
| `Dataset/catalogs/interview.duckdb` | AI questions, interview items, sessions, and reports |

`Dataset/algorithm_problems`, `Dataset/data_analysis_problems`, and `Dataset/interview_sources` are download/import inputs used to build those catalogs.

### Download and import coding datasets

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py

uv run python scripts/import_datasets.py --datasets leetcode codecontests apps taco --database Dataset/catalogs/algorithm.duckdb
uv run python scripts/import_datasets.py --datasets spider sqlctx querypls --database Dataset/catalogs/data_analysis.duckdb
```

### Download and import interview sources

The downloader uses an authenticated GitHub CLI session and records revisions, hashes, licenses, and ingestion decisions in the local manifest.

```powershell
gh auth status
uv run python scripts/download_interview_sources.py --list
uv run python scripts/download_interview_sources.py
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

Imports are idempotent: stable source identities prevent duplicate records. Some data-analysis sources remain reference context because they do not contain the complete fixtures and expected results required for curated exercises. Dataset-specific licenses and restrictions still apply; review [Datasets and attribution](docs/DATASETS.md) before redistribution.

## Optional web research

Web research is off by default. When enabled for AI-generated or mixed questions, the app connects to the hosted Firecrawl MCP endpoint, searches only when local references are insufficient, and retains source links with generated material.

- Web content is treated as untrusted input.
- Research is used for question generation, never grading.
- Raw job descriptions, resumes, candidate answers, and secrets are not sent to Firecrawl.
- Without `FIRECRAWL_API_KEY`, limited keyless access may be available.

See [Security and privacy](docs/SECURITY_AND_PRIVACY.md) for the complete trust boundaries.

## How it works

```text
Raw datasets ──import──> Three DuckDB catalogs ──query──> Streamlit modes
                                                   │
User response ──persist original attempt───────────┤
                                                   └──> Selected AI provider
                                                        generation / static review

Optional Firecrawl MCP ──bounded research sources──> question generation only
```

The app uses versioned schema migrations, normalized source provenance, strict generated-question validation, and atomic persistence. Applying an AI correction updates only the active editor; the submitted attempt remains unchanged.

## Project layout

```text
Coding-Tutor/
├── app.py                         # Unified Streamlit entry point
├── launch_app.cmd                 # Windows setup and launcher
├── Dataset/
│   ├── catalogs/                  # Runtime DuckDB files
│   └── */                         # Raw import inputs
├── scripts/                       # Download, import, and catalog commands
├── src/coding_tutor/
│   ├── database/                  # Schema, migrations, and connections
│   ├── dataset/                   # Source inspection and normalization
│   ├── evaluation/                # Static assessment and solutions
│   ├── generation/                # AI question validation and storage
│   ├── interview/                 # AI-question and interview services
│   ├── providers/                 # AI provider adapters
│   ├── quiz/                      # Quiz state and persistence
│   └── ui/                        # Streamlit pages and controls
├── tests/                         # Unit and Streamlit AppTest coverage
└── docs/                          # Tutorials, how-to guides, and reference
```

## Development and verification

Install locked development dependencies and run the test suite:

```powershell
uv sync --locked
uv run pytest -q
```

Useful command checks:

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/import_datasets.py --help
uv run python scripts/download_interview_sources.py --list
```

Tests mock network calls and use in-memory or temporary DuckDB databases. They verify application contracts but do not prove live provider access or a full production-dataset import.

## Current limitations

- There is no code runner, sandbox, timeout, or deterministic submission judge.
- AI feedback can be incomplete, incorrect, or unsafe; generated code is structurally validated but not executed.
- PySpark and Polars are authoring/review targets, not installed learner-code runtimes.
- Interview uploads do not include OCR, voice input, or proctoring.
- Local DuckDB files are not encrypted or automatically backed up.
- Provider and dataset terms remain the user's responsibility.

## Documentation

Start with the [documentation index](docs/README.md), or go directly to:

- [Getting Started](docs/GETTING_STARTED.md)
- [Usage](docs/USAGE.md)
- [Technical Reference](docs/TECHNICAL_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [AI behavior](docs/AI_BEHAVIOR.md)
- [Security and privacy](docs/SECURITY_AND_PRIVACY.md)
- [Datasets and attribution](docs/DATASETS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

<p align="center">Made by Ahmad Mujtaba</p>
