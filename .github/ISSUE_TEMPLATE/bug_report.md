---
name: Bug report
about: Report a reproducible problem
title: "[Bug] "
labels: bug
assignees: ""
---

## Checklist

- [ ] I searched existing issues.
- [ ] I removed keys, personal data, proprietary code, database contents, and private dataset records.

## Problem

Describe expected and actual behavior. Include the exact sanitized error text.

## Reproduction

1. Provide the smallest sequence of steps.
2. State the learning mode, source, type, difficulty, method, and provider/model when relevant.
3. State whether it reproduces with a new `CODING_TUTOR_DB` path.

## Environment

- Coding Tutor commit/tag:
- OS:
- `python --version`:
- `uv --version`:
- `uv run python -c "import streamlit; print(streamlit.__version__)"`:

## Evidence

Add sanitized logs/screenshots and a minimal fixture only when safe to share. Do not attach a real DuckDB database or downloaded dataset.

## Regression, documentation, and dataset impact

- Does an existing automated test cover this behavior, or can you suggest a focused regression test?
- Is any documentation now inaccurate?
- If a dataset is involved, name the source/revision and describe the license or provenance concern without attaching source records.
