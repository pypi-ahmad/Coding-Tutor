# Contributing to Coding Tutor

Thank you for your interest in contributing! This project is free and community-driven. All meaningful contributions — bug reports, documentation improvements, code fixes, new features — are welcome.

> **No financial contribution is needed or expected.** This project does not accept donations, sponsorships, or any form of payment.

---

## Getting started

### 1. Fork and clone

```bash
git clone https://github.com/pypi-ahmad/Coding-Tutor.git
cd Coding-Tutor
```

### 2. Set up the environment

```bash
uv sync
cp .env.example .env
# Add at least one AI provider key to .env
```

### 3. Run the tests

```bash
uv run pytest
```

All tests must pass before you open a pull request. No API keys are required to run the test suite.

### 4. Start the app

```bash
uv run streamlit run app.py
```

---

## Ways to contribute

| Contribution type | Where to start |
|---|---|
| Bug report | [Open an issue](https://github.com/pypi-ahmad/Coding-Tutor/issues/new?template=bug_report.md) |
| Feature request | [Open an issue](https://github.com/pypi-ahmad/Coding-Tutor/issues/new?template=feature_request.md) |
| Code fix or improvement | Fork → branch → PR |
| Documentation improvement | Fork → branch → PR |
| Dataset or question quality | Fork → branch → PR |

---

## Code guidelines

- Keep changes focused: one logical change per pull request.
- Follow existing code style; run `uv run pytest` before submitting.
- Add or update tests for any behaviour change.
- Write clear commit messages that explain the **why**, not just the what.

---

## Important rules

### No secrets in commits
- Never commit `.env`, API keys, tokens, passwords, or any credentials.
- Never commit database files (`*.duckdb`), raw dataset files, or `.venv/`.
- Check your diff before committing: `git diff --staged`.

### Dataset and data responsibility
- Respect the license and provenance of each bundled dataset. See the Acknowledgements section of the README.
- Do not add datasets that you do not have the right to redistribute.
- Users are fully responsible for the data they choose to use with this application. See `DISCLAIMER.md`.

### AI provider accuracy
- Do not add model IDs or provider parameters unless they are confirmed in official provider documentation.
- Unverified models must be marked `verified=False` in `src/coding_tutor/providers/config.py` with a reason.

---

## Pull request process

1. Ensure all tests pass.
2. Reference the related issue in your PR description (e.g. `Closes #42`).
3. Describe what you changed and why.
4. A maintainer will review and merge, or ask for changes.

---

## Code of Conduct

Be respectful and constructive. Harassment, discrimination, and personal attacks are not tolerated.
