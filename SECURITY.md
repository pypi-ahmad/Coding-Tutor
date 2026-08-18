# Security Policy

Security fixes target the current `main` branch while the project is in early development.

## Report privately

Do not publish vulnerability details in an issue, discussion, pull request, log, or screenshot. Use the repository's [GitHub private security advisory](https://github.com/pypi-ahmad/Coding-Tutor/security/advisories/new) and include affected version/commit, impact, minimal reproduction, and suggested mitigation if known. Remove credentials and unrelated personal data.

If private advisories are unavailable, the repository owner must configure a valid private security contact before publication:

> **OWNER ACTION REQUIRED:** replace this notice with a monitored private contact or enable GitHub private vulnerability reporting. Do not substitute a public issue or a fabricated email address.

This community project has no response-time or remediation SLA.

## Security model

- The app binds to `127.0.0.1:8551` and is intended for a single local user, not public or multi-user deployment.
- Learner Python, SQL, Pandas, PySpark, and Polars text is never executed. There is no runner or sandbox.
- AI actions transmit bounded question/user context to the selected external provider.
- Keys come from process environment variables; the application does not store them in DuckDB or display their values.
- DuckDB can contain submissions and feedback. The user is responsible for filesystem access, backup, and deletion.
- Structured response validation reduces malformed application data; it does not prove AI output correct or safe.

See [Architecture](docs/ARCHITECTURE.md) and [the disclaimer](DISCLAIMER.md) for limitations.
