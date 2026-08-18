# Contributing

Thank you for helping Coding Tutor. This is a free, community-driven project, and focused bug reports, tests, documentation, dataset corrections, and code improvements are welcome. No donation, sponsorship, or financial contribution is required or requested.

## Local setup

```powershell
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
uv sync --locked
uv run pytest -q
uv run streamlit run app.py
```

Tests require no real provider key and must not make live provider calls.

## Before opening a pull request

- Discuss substantial features in an issue first.
- Keep one small, coherent change per pull request and preserve unrelated work.
- Add the narrowest tests for changed behavior and run the full suite.
- Update the relevant tutorial, how-to, reference, or explanation document.
- Describe manual verification and anything not tested.

## Secrets and local data

Never commit or post `.env`, credentials, provider responses containing private data, `*.duckdb`, `Dataset/`, `.venv/`, or logs with user content. `.env.example` must contain supported names with blank values only. Check `git diff --staged` before committing.

## Providers

Do not add a model ID, endpoint, SDK parameter, or verification flag without current official provider documentation. Tests must mock network access. Distinguish request-construction coverage from live availability.

## Datasets and licenses

- Keep downloaded source files untouched and outside Git.
- Add catalog metadata, format inspection, provenance, idempotency, fixture tests, and documentation for any adapter.
- Verify licenses and attribution against the official dataset card/upstream repository.
- Do not infer exercise completeness from a folder name or invent fixture data.
- Treat absent or unclear redistribution permission as unresolved.

## Pull request content

Explain the problem, scope, implementation, tests, documentation impact, privacy/security impact, and dataset/license impact. Link the relevant issue when one exists. Follow the [Code of Conduct](CODE_OF_CONDUCT.md) and report vulnerabilities through [SECURITY.md](SECURITY.md), not a public issue.
