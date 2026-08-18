# Security Policy

## Supported versions

This project is under active development. Security fixes are applied to the latest version on the `main` branch only.

## Reporting a vulnerability

If you discover a security vulnerability, please **do not open a public GitHub issue** for it.

Instead:

1. Describe the vulnerability in as much detail as you can, including steps to reproduce.
2. Report it by opening a **GitHub private security advisory** on this repository:
   [Security advisories](https://github.com/pypi-ahmad/Coding-Tutor/security/advisories/new)

   *(If this channel is unavailable, create a regular issue marked `[SECURITY]` in the title and note that it contains sensitive information.)*

3. You will receive a response as quickly as possible. This is a community-maintained project with no guaranteed SLA.

---

## Security model and known limitations

This application is designed to run **locally on your own machine** for personal use. It is not hardened for multi-user, public, or production deployment.

### Learner submissions

The application does not execute learner-submitted Python, SQL, Pandas, PySpark, or Polars code. When the learner requests assessment, the question, selected method, and editor text are sent to the selected external AI provider for static review.

### API keys

API keys are read only from environment variables. They are never logged, committed, or stored in the application database.

### Data responsibility

Users are fully responsible for the data they choose to provide to external AI APIs. See `DISCLAIMER.md`.
