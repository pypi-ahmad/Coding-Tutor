---
type: workflow
title: Coding practice and question generation
description: The path from filtered catalog or generated question to editor submission and AI-estimated feedback.
tags: [coding-practice, question-generation, submissions, workflow]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-9491608a8f9bd88c871407fe
    resource: repo://docs/SECURITY_AND_PRIVACY.md
  - id: openwiki-source-087540d06cdd6ccd78626ace
    resource: repo://src/coding_tutor/evaluation/persistence.py
  - id: openwiki-source-b9875be30b2d0da9dd8824c3
    resource: repo://src/coding_tutor/generation/generator.py
  - id: openwiki-source-8ae972475c65ebdc7efa669a
    resource: repo://src/coding_tutor/quiz/session.py
  - id: openwiki-source-46e4a842664aecf3f34f4c4b
    resource: repo://src/coding_tutor/ui/main_page.py
  - id: openwiki-source-83a4ce3e923144ac41176585
    resource: repo://src/coding_tutor/ui/submit_handler.py
  - id: openwiki-source-0720c5a3812dee82f153074a
    resource: repo://tests/test_ui.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Coding practice and question generation

## Choosing a question

Curated questions are filtered by question type, difficulty, supported method, completeness, and optionally topic. Generated questions require a configured provider and verified model. In mixed mode, the app randomly chooses between an eligible curated question and a fresh generated question when both are available; otherwise it uses whichever source is available. (Sources: `repo://src/coding_tutor/ui/main_page.py#L128-L139`, `repo://src/coding_tutor/ui/main_page.py#L154-L185`, `repo://src/coding_tutor/ui/main_page.py#L218-L320`.)

Generation validates the provider response before saving a question and stores provider/model, prompt version, and context-source provenance. See [Provider and prompt contract](../concepts/provider-and-prompt-contract.md) for its validation and transaction boundaries. (Source: `repo://src/coding_tutor/generation/generator.py#L149-L175`, `repo://src/coding_tutor/generation/generator.py#L199-L276`.)

## Loading and editing

Loading a question puts its normalized question data, source/provenance details, and display examples into Streamlit session state. If authored examples are absent, the loader can use up to three stored test cases as a display fallback. The editor is a text area keyed by question and method; it is not a code runner. (Sources: `repo://src/coding_tutor/quiz/session.py#L179-L205`, `repo://src/coding_tutor/ui/main_page.py#L459-L477`, `repo://tests/test_ui.py#L209-L253`.)

When a learner changes method or another learning setting while the editor has unsaved changes, the UI asks whether to keep, discard, or cancel the change. Tests verify that keeping preserves the draft and cancel restores the previous selection. (Sources: `repo://src/coding_tutor/quiz/session.py#L134-L162`, `repo://tests/test_ui.py#L143-L191`.)

## Submission and feedback

Submission first checks that answer text is non-empty and the method is supported. It then persists the submitted attempt before validating provider configuration or requesting assessment; if local persistence fails, assessment is not requested. A successful assessment updates the attempt; provider or persistence errors are recorded against it. (Sources: `repo://src/coding_tutor/ui/submit_handler.py#L15-L84`, `repo://src/coding_tutor/evaluation/persistence.py#L9-L39`.)

The configured model estimates correctness from static question and reference context; learner code and stored test cases are not executed. See [Assessment and code-execution boundary](../concepts/assessment-and-execution-boundary.md). (Sources: `repo://src/coding_tutor/evaluation/feedback.py#L82-L149`, `repo://docs/SECURITY_AND_PRIVACY.md#L144-L152`.)

## Related pages

- [Provider and prompt contract](../concepts/provider-and-prompt-contract.md)
- [Assessment and code-execution boundary](../concepts/assessment-and-execution-boundary.md)
- [Quiz lifecycle](quizzes.md)
