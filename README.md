# Coding Tutor

A local AI-powered Streamlit coding tutor for algorithm and data-analysis practice.

**Repository:** [github.com/pypi-ahmad/Coding-Tutor](https://github.com/pypi-ahmad/Coding-Tutor)

## Overview

Coding Tutor provides a local question bank, structured AI question generation, a browser editor, teacher-style AI feedback, guided solutions, quizzes, and DuckDB progress history. It is a learning aid, not a code judge: learner Python, SQL, Pandas, PySpark, and Polars submissions are never executed.

## Features

- Python algorithm practice.
- Data-analysis authoring templates for SQL, Pandas, PySpark, and Polars.
- Curated dataset, AI-generated, and Mixed question sources.
- Strict validation and local persistence of accepted AI-generated questions.
- AI-estimated correctness, marks out of 10, mistakes, explanations, and suggested corrections.
- Reversible application of AI-proposed code while the submitted attempt remains unchanged.
- Stored references and explicitly requested AI teaching solutions.
- Separate practice and resumable quiz history, plus progress filters and repeated attempts.
- Versioned DuckDB schema and source provenance for imported questions.

## Technology stack

| Area | Implementation |
| --- | --- |
| UI | Streamlit |
| Language and packaging | Python 3.11+, Hatchling, `uv` |
| Local persistence | Embedded DuckDB |
| AI clients | OpenAI Python SDK and Google Gen AI SDK |
| Dataset handling | PyArrow, pandas, Hugging Face Hub |
| Tests | pytest, pytest-mock, Streamlit AppTest |

## Project structure

```text
Coding-Tutor/
├── app.py                    # Streamlit entry point
├── launch_app.cmd            # Windows setup and launcher
├── pyproject.toml            # Package and dependency configuration
├── uv.lock                   # Locked dependencies
├── scripts/                  # Dataset download and import commands
├── src/coding_tutor/
│   ├── database/             # DuckDB schema, migrations, progress
│   ├── dataset/              # Inspection and normalization adapters
│   ├── evaluation/           # Static AI assessment and solutions
│   ├── generation/           # Generated-question validation/storage
│   ├── prompts/              # Versioned Markdown prompt contracts
│   ├── providers/            # Provider abstractions and adapters
│   ├── quiz/                 # Quiz rules and persistence
│   └── ui/                   # Streamlit pages and controls
├── tests/                    # Automated tests and small fixtures
└── docs/                     # Tutorial, how-to, reference, explanation
```

> [!IMPORTANT]
> The app does not run learner code or stored tests. All marks, correctness percentages, and coding-quiz scores are AI estimates. Stored test cases and expected results are context for the model, not executed evidence.

## Privacy and responsibility

The database, editor drafts in the active Streamlit session, questions, and progress are local by default. The app has no file-upload feature. Content leaves the machine when you request an AI-backed action: generation, assessment, teaching solutions, and MCQ preparation send bounded relevant context to the selected provider.

API keys are read from process environment variables and are not stored in DuckDB or rendered by the app. You are responsible for the data you provide, provider terms, dataset licenses, backups, and access to the local database. Do not use sensitive or proprietary material unless you are authorized to send it to the selected provider.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/).
- Windows 11 for the tested launcher workflow. Other platforms may use the manual commands.
- Your own API key for any AI-backed action.

## Install and run

```powershell
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
uv sync --locked
uv run --locked streamlit run app.py
```

Open <http://127.0.0.1:8551>. The tracked Streamlit configuration fixes the address and port. On Windows, `launch_app.cmd` checks for `uv`, creates the root `.venv` when needed, synchronizes the lock file, and starts the app. If `uv` is missing, it prints official installation links and exits without installing software.

## Environment variables

Set credentials in the environment that launches Streamlit. `.env.example` is a names-only reference and is not loaded by the application. Never put real values in that file.

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI provider credential |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible base URL |
| `AGNES_API_KEY` | Agnes AI provider credential |
| `GOOGLE_API_KEY` | Google Gemini provider credential |

Only one provider key is needed. `OPENAI_BASE_URL` is optional; blank uses the OpenAI SDK default. Additional implemented variables are documented in [the technical reference](docs/TECHNICAL_REFERENCE.md#environment-variables).

Provider status means only that the expected key contains a non-blank value. It does not test authentication, quota, network access, or model entitlement.

## First use

1. Start the app and select **Practice**.
2. Choose a provider/model, question source, question type, difficulty, topic, and method.
3. Import datasets first for **Curated dataset**, or configure a provider for **AI generated**.
4. Load or generate a question and write an answer.
5. Click **Done**. The original answer is saved before configuration validation, then sent for static AI review when a provider is available.
6. Review the explicitly labelled AI estimate. Apply a correction only if wanted; it can be restored.
7. Use **Show Solution** or open **Progress** to review local history.

See [Getting Started](docs/GETTING_STARTED.md) for a guided tutorial and [Usage](docs/USAGE.md) for task-oriented instructions.

## Datasets

Downloaded datasets are gitignored and expected under:

```text
Dataset/
├── data_analysis_problems/
└── algorithm_problems/
```

List and download the supported sources:

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py
```

Import all supported sources, or select keys:

```powershell
uv run python scripts/import_datasets.py
uv run python scripts/import_datasets.py --datasets leetcode apps taco
```

Source files are inspected before parsing and are not renamed, overwritten, or extracted into. Repeated records are skipped by stable source identity. Spider, sql-create-context, and QueryPls do not supply the complete shared fixture and expected-result context required by the UI, so their imported records remain incomplete and are not offered as curated exercises. See [Datasets](docs/DATASETS.md).

## Provider/model status

The following options are implemented in the registry and their request construction is covered by mocked tests. This does not prove that a live account can access them.

| Provider | Implemented option | Request setting |
| --- | --- | --- |
| OpenAI | `gpt-5.6-luna` | `reasoning_effort="medium"` |
| Agnes AI | `agnes-2.5-flash` | fixed OpenAI-compatible model and base URL |
| Google Gemini | `gemini-3.5-flash-lite`, `gemini-3.7-flash` | `thinking_level="medium"`, Interactions API, `store=False` |

The model names and parameters are linked to official sources in [Technical Reference](docs/TECHNICAL_REFERENCE.md#providers-and-models). Availability can change and is checked by the provider, not by the sidebar.

## How it works

1. Streamlit stores current controls and editor drafts in session state.
2. Curated source adapters inspect and normalize downloaded records into DuckDB without changing the source files; accepted AI questions use strict JSON validation and atomic storage.
3. **Done** creates an immutable attempt before requesting static feedback from the selected provider.
4. Validated AI feedback and optional corrections are stored locally. Applying a correction changes only the active editor value.
5. Practice attempts, solution views, quiz records, and migrations remain in the configured DuckDB file.

## Configuration

| Setting | Implemented value |
| --- | --- |
| Address and port | `127.0.0.1:8551` |
| Default database | `coding_tutor.duckdb` |
| Question types | Algorithm, data analysis |
| Difficulties | Beginner, Easy, Medium, Hard, Very Hard |
| Algorithm method | Python |
| Data-analysis methods | SQL, Pandas, PySpark, Polars authoring/AI review |
| Question sources | Curated dataset, AI generated, Mixed |

## Verification

```powershell
uv run pytest -q
uv run python scripts/download_datasets.py --list
uv run python scripts/import_datasets.py --help
```

Tests mock network calls and use in-memory or temporary DuckDB databases; they do not prove live provider connectivity or a complete production-dataset import.

## Limitations

- There is no local runner, sandbox, container, timeout, memory limit, or deterministic submission verification because submissions are not executed.
- PySpark is only an editor template and AI-review method. `pyspark`, Java, and Spark are not project dependencies or runtime checks.
- Pandas is installed for the app UI, but learner Pandas code is not run. Polars is not installed.
- Dataset licenses belong to their sources. CodeContests has no license declared on the supported Hugging Face card; treat redistribution as unresolved.
- AI output can be wrong, incomplete, or unsafe. Generated corrections and solutions are validated for structure, not executed for correctness.

## Documentation

- [Documentation index](docs/README.md)
- [Getting Started tutorial](docs/GETTING_STARTED.md)
- [Usage how-to guide](docs/USAGE.md)
- [Expanded learner how-to guide](docs/how-to-use.md)
- [Technical Reference](docs/TECHNICAL_REFERENCE.md)
- [Contributor and maintainer reference](docs/technical-reference.md)
- [Architecture explanation](docs/ARCHITECTURE.md)
- [Architecture blueprint](Project_Architecture_Blueprint.md)
- [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md)
- [AI behavior](docs/AI_BEHAVIOR.md)
- [Security and privacy](docs/SECURITY_AND_PRIVACY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Datasets and attribution](docs/DATASETS.md)
- [Detailed dataset setup](docs/dataset-setup.md)
- [Open-source checklist](docs/OPEN_SOURCE_CHECKLIST.md)
- [Release history](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), [Security](SECURITY.md), [Disclaimer](DISCLAIMER.md), and [Code of Conduct](CODE_OF_CONDUCT.md)

## Contributing

Bug reports, focused feature suggestions, tests, documentation improvements, and pull requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), follow the [Code of Conduct](CODE_OF_CONDUCT.md), and use [SECURITY.md](SECURITY.md) for private vulnerability reports.

## License

Coding Tutor is distributed under the [MIT License](LICENSE). Dataset licenses and attribution requirements remain separate.

## Acknowledgements

The optional question bank can normalize LeetCodeDataset, APPS, TACO, CodeContests, Spider, sql-create-context, and QueryPls. Their maintainers and original authors retain their own license and attribution terms; see [Datasets](docs/DATASETS.md) before use or redistribution.

This project is free and community-driven. Financial support, donations, and sponsorships are neither needed nor requested.

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
