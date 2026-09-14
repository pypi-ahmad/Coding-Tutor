# Runbook

Operational quick-reference for starting, stopping, and recovering Coding Tutor. For step-by-step diagnostic flows, see [Troubleshooting](TROUBLESHOOTING.md).

## Start

**Standard (any platform with `uv` on `PATH`):**

```powershell
uv run --locked streamlit run app.py
```

**Windows launcher** (verifies `uv`, creates `.venv` if absent, syncs locked deps, then starts):

```cmd
launch_app.cmd
```

**Catalog-fixed profile** (bypasses the unified all-catalogs view):

```powershell
uv run python scripts/run_catalog.py algorithm
uv run python scripts/run_catalog.py data_analysis
```

The app binds to `127.0.0.1:8551` as configured in `.streamlit/config.toml`. That address is local-only; the app is not designed for public or multi-user deployment.

## Stop

Press **Ctrl+C** in the terminal that is running Streamlit. There is no graceful-shutdown command; open DuckDB connections close when the process exits.

## Environment variables required for AI actions

Browsing local catalogs requires no key. Every generation, assessment, and interview action requires exactly one of:

| Variable | Provider |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI |
| `AGNES_API_KEY` | Agnes AI |
| `GOOGLE_API_KEY` | Google Gemini |

Set the variable in the environment that starts Streamlit, then restart the process. The app does not load `.env` files.

Optional:

| Variable | Effect |
| --- | --- |
| `OPENAI_BASE_URL` | Route OpenAI requests to a compatible endpoint |
| `FIRECRAWL_API_KEY` | Authenticated Firecrawl MCP; absent means keyless access is attempted |
| `CODING_TUTOR_DB` | Override the active DuckDB path for Coding, Quiz, and Progress (AI Questions and Interview always use the interview catalog) |

## Logs

There is no log file. All output goes to the terminal that launched Streamlit. Keep that terminal open to read Streamlit tracebacks, DuckDB errors, and provider error messages.

## Common error strings and immediate actions

| Error string | Immediate action |
| --- | --- |
| `uv is not installed or is not available on PATH` | Install `uv` and reopen the terminal so `PATH` is updated. |
| `The project virtual environment could not be created` | Confirm the repository directory is writable; read the `uv` error above the launcher message. |
| `Dependency setup failed` | Confirm `pyproject.toml` and `uv.lock` exist; run `uv sync --locked` directly to see the full error. Do not edit the lock file. |
| `Streamlit failed to start` | Run `uv run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8551` directly and read the first error line. |
| `The selected provider is not configured. Set its API key in the system environment.` | Set the correct `*_API_KEY` variable and restart Streamlit. |
| `The provider request failed. Check network access, credentials, quota, and model access.` | Verify network, credential validity, provider quota, and that the selected model is accessible on the account. No automatic fallback exists. |
| `The original attempt could not be saved locally. Assessment was not requested.` | DuckDB write failed. Confirm the catalog directory is writable; see [Troubleshooting: The app cannot open or write DuckDB data](TROUBLESHOOTING.md). |
| `The valid question could not be saved locally. No partial question was kept.` | DuckDB write failed during generation. Same resolution as above. |
| `No source files match ...` | Dataset not downloaded. Run `uv run python scripts/download_datasets.py` then the relevant import command. |
| `Only N matching curated questions are available; M are required` | Insufficient imported data for the current quiz filters. Import additional authorized dataset records and retry from the quiz UI. |

## Port conflict

The default port is **8551**. If another process holds it, either stop that process or override:

```powershell
uv run --locked streamlit run app.py --server.port <other-port>
```

Update `.streamlit/config.toml` for a persistent change.

## Database recovery

DuckDB files are not encrypted, backed up, or repaired by the application.

- Do not delete an existing catalog to fix a startup failure; it contains learner data.
- To isolate a database problem from the rest of the app, set `CODING_TUTOR_DB` to a new file path and restart.
- If a catalog is corrupted, the only recovery path is restoring from a user-managed backup.

## Dataset maintenance

Imports are idempotent; rerunning the same command will not create duplicate records.

```powershell
# Rebuild algorithm and data-analysis catalogs from downloaded raw data
uv run python scripts/import_datasets.py --datasets leetcode apps taco --database Dataset/catalogs/algorithm.duckdb
uv run python scripts/import_datasets.py --datasets spider sqlctx querypls --database Dataset/catalogs/data_analysis.duckdb

# Rebuild interview catalog
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

For full download and import sequences, see [Dataset Setup](dataset-setup.md).
