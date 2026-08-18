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

### Code execution isolation

Learner-submitted code runs in an isolated child process with:
- An empty environment (`env={}`) — no inherited secrets, paths, or credentials.
- A dedicated temporary working directory, deleted after each run.
- A strict timeout (10 seconds by default).
- SQL evaluated against an isolated in-memory DuckDB instance separate from the app database.

**Windows limitation:** On Windows, isolation is at the process level only. Linux namespace isolation, seccomp filtering, and cgroup memory limits are not available. Do not expose this application to untrusted code submitted by other users.

### API keys

API keys are read only from environment variables. They are never logged, committed, or stored in the application database.

### Data responsibility

Users are fully responsible for the data they choose to provide to external AI APIs. See `DISCLAIMER.md`.
