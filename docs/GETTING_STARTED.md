# Getting Started

This tutorial takes a new local user from a fresh clone to a first Coding submission and introduces the other application modes.

## 1. Install prerequisites

Install Git, Python 3.11 or newer, and `uv`. Windows 11 is the tested launcher platform. AI-backed actions require your own provider credential.

## 2. Clone and install

```powershell
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
uv sync --locked
```

On Windows, `launch_app.cmd` can create `.venv`, synchronize locked dependencies, and launch the app. It reports installation links and exits if `uv` is unavailable.

## 3. Configure one provider

Set one key in the terminal that will launch Streamlit:

```powershell
$env:OPENAI_API_KEY = "<your-key>"
# or: $env:AGNES_API_KEY = "<your-key>"
# or: $env:GOOGLE_API_KEY = "<your-key>"
```

`OPENAI_BASE_URL` is optional. `.env.example` documents variable names but is not loaded. The sidebar's configuration status checks only for a non-blank value; it does not test credentials, quota, connectivity, or model access.

## 4. Prepare local question catalogs

Datasets are optional when you use AI generation. To prepare local coding questions:

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/download_datasets.py
uv run python scripts/import_datasets.py --datasets leetcode codecontests apps taco --database Dataset/catalogs/algorithm.duckdb
uv run python scripts/import_datasets.py --datasets spider sqlctx querypls --database Dataset/catalogs/data_analysis.duckdb
```

To prepare local AI and interview questions:

```powershell
gh auth status
uv run python scripts/download_interview_sources.py --list
uv run python scripts/download_interview_sources.py
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

Raw files are import inputs. Normal app use reads the consolidated files under `Dataset/catalogs`.

## 5. Start the app

```powershell
uv run --locked streamlit run app.py
```

Open <http://127.0.0.1:8551>.

## 6. Complete a Coding question

1. Select **Coding**.
2. Select a provider and verified model.
3. Choose **Curated questions** if you imported algorithm data, or **AI generated**.
4. Select **Algorithm**, a difficulty, an optional topic, and Python.
5. Load or generate a question and write an answer.
6. Select **Submit solution**.

The app saves the exact answer before requesting static review. The displayed score and mark are AI estimates; no tests execute. Applying a suggested correction changes only the active editor, not the saved submission.

## 7. Explore the other modes

- **Quiz** creates a resumable mix of coding and MCQ items.
- **AI Questions** provides theory, coding, MCQ, direct, and scenario questions across AI domains.
- **Interview** runs a timed tech or JD-based interview for 30, 45, 60, or 90 minutes.
- **Progress** shows an overview and activity-specific history across all three catalogs.

JD-based interviews can parse PDF, DOCX, or TXT files up to 5 MB. Raw JD/resume content is not stored locally, but extracted text is sent to the selected provider to create the interview plan.

## 8. Know where data is stored

| Catalog | Content |
| --- | --- |
| `Dataset/catalogs/algorithm.duckdb` | Algorithm questions, attempts, quizzes, and solution views |
| `Dataset/catalogs/data_analysis.duckdb` | Data-analysis questions, attempts, quizzes, and solution views |
| `Dataset/catalogs/interview.duckdb` | AI Questions, interview sessions, turns, and reports |

Leave `CODING_TUTOR_DB` unset for normal unified operation. It is an advanced/test override for intentionally routing activity to one path.

## Next steps

- Follow [How to Use Coding Tutor](USAGE.md) for task recipes.
- Read [Security and Privacy](SECURITY_AND_PRIVACY.md) before submitting sensitive material.
- Use [Troubleshooting](TROUBLESHOOTING.md) for verified failure recovery.
