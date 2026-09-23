---
type: operations
title: Local development
description: Repository-documented setup and commands for running Coding Tutor and its tests locally.
tags: [windows, uv, streamlit, development]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-51639ec4f9dc3fb84f820c05
    resource: repo://docs/RUNBOOK.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Local development

The project requires Python 3.11 or newer, `uv`, and Git. Its documented setup syncs locked dependencies and launches Streamlit from the repository root:

```powershell
uv sync --locked
uv run --locked streamlit run app.py
```

On Windows, `launch_app.cmd` is the alternative documented launcher; it checks for `uv`, creates `.venv` when needed, syncs the locked dependencies, and starts the same app. (Sources: `repo://README.md#L66-L84`, `repo://docs/RUNBOOK.md#L5-L17`.)

The default app address is `http://127.0.0.1:8551`. The runbook describes that listener as local-only and says the app is not designed for public or multi-user deployment. (Source: `repo://docs/RUNBOOK.md#L19-L26`.)

## Provider configuration

AI-backed actions require a provider credential in the environment that starts Streamlit. The documented variables are `OPENAI_API_KEY`, `AGNES_API_KEY`, and `GOOGLE_API_KEY`; `OPENAI_BASE_URL` and `FIRECRAWL_API_KEY` are optional. The app does not load `.env` files. A configured status only means a non-blank variable was found; it does not verify authentication, quota, network access, or model entitlement. Never put real credentials in `.env.example`. (Sources: `repo://README.md#L86-L98`, `repo://docs/RUNBOOK.md#L32-L50`.)

## Test command

The README documents `uv sync --locked` followed by `uv run pytest -q` for development verification. This page records the repository's command, not a claim that the full suite was run during wiki initialization. (Source: `repo://README.md#L215-L230`.)

## Related pages

- [Repository guide](../quickstart.md)
- [Data import operations](data-import.md)
- [Testing and verification strategy](../testing/verification-strategy.md)
