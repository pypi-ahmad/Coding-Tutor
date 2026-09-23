---
type: concept
title: Assessment and code-execution boundary
description: How learner submissions are reviewed as text and how assessment status is persisted.
tags: [assessment, code-execution, privacy, persistence]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-9491608a8f9bd88c871407fe
    resource: repo://docs/SECURITY_AND_PRIVACY.md
  - id: openwiki-source-79d24d8d153d03672a3bd9fb
    resource: repo://src/coding_tutor/evaluation/feedback.py
  - id: openwiki-source-087540d06cdd6ccd78626ace
    resource: repo://src/coding_tutor/evaluation/persistence.py
  - id: openwiki-source-c105c623359955ec0bd2c62c
    resource: repo://tests/test_progress.py
  - id: openwiki-source-dd61b439e43007c24fc72d70
    resource: repo://tests/test_quiz.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Assessment and code-execution boundary

Learner code is treated as text. The application does not execute, import, compile, evaluate, or query learner submissions. Stored test cases may be supplied to the configured provider as static context, but the application does not run them; returned correctness percentages and marks are AI estimates. (Source: `repo://docs/SECURITY_AND_PRIVACY.md#L144-L152`.)

## What the assessment receives

Before calling a provider, assessment validates that the submission is non-empty and within the configured size limit, that the method is supported, and that the selected model is verified, belongs to the selected provider, and is configured. The request context can include the question, learner submission, a reference solution, selected question assets, and stored reference cases. The question statement, constraints, solution, and assets are clipped to defined limits, and asset/case queries are bounded. (Sources: `repo://src/coding_tutor/evaluation/feedback.py#L42-L79`, `repo://src/coding_tutor/evaluation/feedback.py#L82-L149`.)

Because the provider may receive the learner submission and related question context, this is not an offline-only assessment path. The privacy guide identifies provider-backed actions as sending selected question and learner context to the configured external provider. (Source: `repo://docs/SECURITY_AND_PRIVACY.md#L9-L13`.)

## Attempt and assessment state

The attempt row is created before assessment with the submitted text, `deterministic_test_result='not_run'`, and `assessment_status='pending'`. A successful response updates the assessment fields; a failure records an error state while leaving the deterministic test result as `not_run`. (Source: `repo://src/coding_tutor/evaluation/persistence.py#L9-L39`.)

Tests verify that repeated submissions create distinct attempt records, that each retains its submitted code and `not_run` test status, and that an unconfigured-provider failure is persisted as an error. Quiz tests also verify that a blank coding response scores zero without calling the AI assessment function. (Sources: `repo://tests/test_progress.py#L20-L37`, `repo://tests/test_progress.py#L39-L79`, `repo://tests/test_quiz.py#L190-L210`.)

The absence of an application code runner also means the project does not provide a learner-code sandbox or process/network/filesystem isolation. Provider feedback and corrected code should therefore be treated as estimates and reviewed before use elsewhere. (Source: `repo://docs/SECURITY_AND_PRIVACY.md#L148-L152`.)

## Related pages

- [Coding practice and question generation](../workflows/coding-practice.md)
- [Quiz lifecycle](../workflows/quizzes.md)
- [Interview sessions](../workflows/interviews.md)
