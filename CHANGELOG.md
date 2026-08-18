# Changelog

All notable user-facing changes to Coding Tutor are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.2] - 2026-08-19

### Added

- Added an expanded learner guide covering local setup, practice, quizzes, progress, privacy, and troubleshooting.
- Added a contributor and maintainer reference covering runtime contracts, persistence, scoring, security boundaries, and extension points.
- Added focused references for AI behavior, security and privacy, repeatable troubleshooting, and accepted architecture decisions.

### Changed

- Standardized the changelog structure and verified release comparison links.

### Security

- Documented environment-based credential handling, local DuckDB storage, external provider request boundaries, dataset logging, and the absence of learner-code execution or sandboxing.

## [0.1.1] - 2026-08-19

### Changed

- Reworked the public README and documentation index around verified application behavior.
- Added focused getting-started, usage, architecture, dataset, and technical-reference guides.
- Updated the Windows launcher to require an existing `uv` installation, synchronize locked dependencies, and report setup or startup failures clearly.
- Strengthened contribution, issue, pull-request, support, disclaimer, conduct, and security guidance for public collaboration.

### Security

- Clarified that AI-backed actions send selected content to the configured provider and that users remain responsible for the data they process.
- Documented the private GitHub vulnerability-reporting path without inventing a security contact address.

## [0.1.0] - 2026-08-19

### Added

- Local Streamlit learning interface for algorithm and data-analysis practice.
- Curated dataset, AI-generated, and mixed question-source modes.
- SQL, Pandas, PySpark, Polars, and Python solution-method support without local learner-code execution.
- AI-estimated static assessment, teaching solutions, Quiz Mode, and local progress history.
- DuckDB persistence with schema migrations and source provenance.
- OpenAI, Agnes AI, and Google Gemini provider configuration through system environment variables.
- Version-controlled Markdown prompts with strict structured-response validation.
- One-click Windows setup and launch through `launch_app.cmd`.

### Security

- API credentials remain in the user's system environment and are never rendered by the app.
- Learner code is sent only to the explicitly selected AI provider and is never executed locally.
- Questions and progress are stored in the local DuckDB database. Explicit AI-backed actions send only the relevant question and learner context assembled for that request.

[Unreleased]: https://github.com/pypi-ahmad/Coding-Tutor/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/pypi-ahmad/Coding-Tutor/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/pypi-ahmad/Coding-Tutor/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/pypi-ahmad/Coding-Tutor/releases/tag/v0.1.0
