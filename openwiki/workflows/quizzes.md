---
type: workflow
title: Quiz lifecycle
description: Durable quiz preparation, question and MCQ validation, draft persistence, scoring, retry, and resume.
tags: [quizzes, persistence, mcq, scoring]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-4c5121c6c3eb053e7b94065d
    resource: repo://src/coding_tutor/quiz/persistence.py
  - id: openwiki-source-6c95fa3de107f49cdb712f0f
    resource: repo://src/coding_tutor/quiz/service.py
  - id: openwiki-source-dd61b439e43007c24fc72d70
    resource: repo://tests/test_quiz.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Quiz lifecycle

## Start and prepare

Quiz setup accepts one to ten questions and validates the requested coding count. The service creates the durable quiz attempt before selecting questions or preparing MCQs, so preparation failures remain associated with a retryable attempt. Question source can be curated dataset, AI-generated, or mixed; curated questions are filtered by type, difficulty, completeness, method, and optional topic. (Sources: `repo://src/coding_tutor/quiz/service.py#L31-L50`, `repo://src/coding_tutor/quiz/service.py#L82-L95`, `repo://src/coding_tutor/quiz/service.py#L135-L153`.)

Selected question items are inserted transactionally. For MCQ items, the provider response must match the selected question IDs and contain exactly four unique options with one valid correct-option ID; validated MCQ content is saved as a separate preparation step. Failures set a preparation-error status, and retry resumes preparation using the stored quiz and provider/model settings. (Sources: `repo://src/coding_tutor/quiz/persistence.py#L12-L78`, `repo://src/coding_tutor/quiz/service.py#L53-L79`, `repo://src/coding_tutor/quiz/service.py#L156-L220`.)

## Drafts, resume, and scoring

Coding answers and MCQ selections are saved as drafts on their quiz items. Loading retrieves the attempt and ordered items, and the service can locate the latest unfinished quiz. (Source: `repo://src/coding_tutor/quiz/persistence.py#L81-L141`.)

MCQs are scored locally. A blank coding answer receives zero without an AI call; a nonblank coding answer uses the assessment provider. When coding assessment is needed, evaluation requires the same provider and model used to start the quiz. Already-scored items are retained if an AI call fails, leaving an evaluation-error state that can be retried; completion occurs after the required assessments succeed. (Sources: `repo://src/coding_tutor/quiz/service.py#L223-L270`, `repo://tests/test_quiz.py#L144-L210`.)

Tests verify that quiz attempts/items use their own tables rather than normal practice attempts, curated selection respects filters, MCQ response validation rejects malformed choices, and scoring/retry retains already-scored work. (Sources: `repo://tests/test_quiz.py#L32-L92`, `repo://tests/test_quiz.py#L144-L210`.)

## Related pages

- [Persistence and migrations](../architecture/persistence-and-migrations.md)
- [Assessment and code-execution boundary](../concepts/assessment-and-execution-boundary.md)
- [Provider and prompt contract](../concepts/provider-and-prompt-contract.md)
