---
type: workflow
title: Interview sessions
description: Interview setup, document constraints, generated/adaptive turns, scoring, timing, and reports.
tags: [interviews, adaptive, documents, workflow]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-4f37c53f854f0fcf5bf79104
    resource: repo://src/coding_tutor/interview/ai.py
  - id: openwiki-source-0a1b05bbf22d00e7b68cfda8
    resource: repo://src/coding_tutor/interview/documents.py
  - id: openwiki-source-ed974524d3689e855945a768
    resource: repo://src/coding_tutor/interview/service.py
  - id: openwiki-source-5bf5d615e5204731b92ac41c
    resource: repo://tests/test_interview_modes.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Interview sessions

Interview setup can use a technical or job-description-based plan. The AI blueprint contract validates that generated topics and formats are present and that formats are supported; coding-language choices are also checked as text values. (Source: `repo://src/coding_tutor/interview/ai.py#L139-L152`.)

## Uploaded documents

Resume and job-description uploads are extracted in memory. The extractor accepts PDF, DOCX, and TXT files up to 5 MB and returns at most 100,000 characters. It rejects unreadable or empty documents; scanned PDFs need OCR before upload because this project does not perform OCR. A test verifies the interview-session table has no `jd`, `resume`, or `document_text` columns. (Sources: `repo://src/coding_tutor/interview/documents.py#L1-L40`, `repo://tests/test_interview_modes.py#L74-L100`.)

## Session and turn lifecycle

Starting a session stores the interview type, duration, source mode, blueprint, web setting, provider/model, and an absolute UTC deadline. Turns are generated from the blueprint's ordered formats and topics. Local mode selects catalog items; mixed mode uses local questions at odd positions and generated ones at alternating positions. A new question cannot be added while a prior turn remains pending. (Sources: `repo://src/coding_tutor/interview/service.py#L281-L293`, `repo://src/coding_tutor/interview/service.py#L346-L395`.)

Generated adaptive questions receive the blueprint and up to the last three scored turns, including each answer, score, identified gaps, and next focus. The test suite verifies that after four scored answers the next generated turn receives answers two through four. (Sources: `repo://src/coding_tutor/interview/service.py#L330-L344`, `repo://tests/test_interview_modes.py#L102-L133`.)

Multiple-choice turns are scored locally; other answer formats use the configured assessment provider. Answers and feedback are stored on the turn. Learners can skip a pending turn, then finish the session; finishing stores a report, with a local fallback report when no answers were submitted. (Sources: `repo://src/coding_tutor/interview/service.py#L398-L443`, `repo://tests/test_interview_modes.py#L74-L100`.)

## Related pages

- [Runtime and profile routing](../architecture/runtime-routing.md)
- [Provider and prompt contract](../concepts/provider-and-prompt-contract.md)
- [Assessment and code-execution boundary](../concepts/assessment-and-execution-boundary.md)
