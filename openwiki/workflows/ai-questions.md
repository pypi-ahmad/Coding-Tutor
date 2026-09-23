---
type: workflow
title: AI Questions and bounded web research
description: How local, generated, and mixed AI Questions sessions work and when optional web research is used.
tags: [ai-questions, web-research, firecrawl, workflow]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-b9875be30b2d0da9dd8824c3
    resource: repo://src/coding_tutor/generation/generator.py
  - id: openwiki-source-ed974524d3689e855945a768
    resource: repo://src/coding_tutor/interview/service.py
  - id: openwiki-source-7702380813bde4f147618148
    resource: repo://src/coding_tutor/web_research.py
  - id: openwiki-source-5bf5d615e5204731b92ac41c
    resource: repo://tests/test_interview_modes.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# AI Questions and bounded web research

An AI Questions session stores its source mode, topic/domain filters, difficulty, answer format, prompt style, method, web-research setting, provider, and model. For each next question, local mode selects an unused matching catalog item and never falls back to generation; mixed mode uses local questions at odd positions and generates on the alternating positions. Generated and selected items are stored with a prompt snapshot and any returned web sources. (Sources: `repo://src/coding_tutor/interview/service.py#L197-L244`, `repo://tests/test_interview_modes.py#L19-L71`.)

## Answer scoring

Multiple-choice answers are scored locally against the stored correct option. Non-MCQ answers are sent through the configured answer assessor, and the resulting score and feedback are saved on the question item. A blank answer is rejected before scoring. (Source: `repo://src/coding_tutor/interview/service.py#L260-L278`.)

## When web research runs

Web research is optional, not the default for every question. In AI Questions, the generated-item path calls Firecrawl only when `web_enabled` is true and fewer than three local references are available. If research raises the expected `WebResearchError`, generation continues with a warning. In coding-question generation, web research requires the setting to be enabled, a non-general topic, and that topic to be absent from the local reference context. (Sources: `repo://src/coding_tutor/interview/service.py#L169-L194`, `repo://src/coding_tutor/generation/generator.py#L103-L131`.)

The Firecrawl client requests at most five search candidates, scrapes no more than three pages, and clips each saved excerpt to 6,000 characters. A Firecrawl key changes the access mode to authenticated; without it, the client attempts keyless access. The access-mode helper returns only the mode, not the key. (Source: `repo://src/coding_tutor/web_research.py#L1-L13`, `repo://src/coding_tutor/web_research.py#L30-L32`, `repo://src/coding_tutor/web_research.py#L61-L119`.)

Tests verify that local mode does not invoke generation, that mocked AI question flow persists/scorers a generated item, and that the Firecrawl result parser handles nested payloads. They do not establish that a live Firecrawl request succeeds. (Sources: `repo://tests/test_interview_modes.py#L19-L71`, `repo://tests/test_interview_modes.py#L163-L176`.)

## Related pages

- [Provider and prompt contract](../concepts/provider-and-prompt-contract.md)
- [Coding practice and question generation](coding-practice.md)
- [Interview sessions](interviews.md)
