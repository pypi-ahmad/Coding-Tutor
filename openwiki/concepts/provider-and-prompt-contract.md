---
type: concept
title: Provider and prompt contract
description: Provider selection, verified model checks, prompt/context construction, and generation persistence.
tags: [providers, prompts, generation, provenance]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-b9875be30b2d0da9dd8824c3
    resource: repo://src/coding_tutor/generation/generator.py
  - id: openwiki-source-8b8ec15f65156ed179c53ea7
    resource: repo://src/coding_tutor/prompts/__init__.py
  - id: openwiki-source-6ff34ffaf8282eba1fe0d186
    resource: repo://src/coding_tutor/providers/base.py
  - id: openwiki-source-61272994c6a3543822f21d62
    resource: repo://src/coding_tutor/providers/registry.py
  - id: openwiki-source-9dd1c269b639dfa34bd360e7
    resource: repo://tests/test_generation.py
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Provider and prompt contract

Provider integrations share a small interface: report whether credentials are configured, list available model options, and send chat messages. A model option records its provider, model ID, and verification status; the registry currently maps `openai`, `agnes`, and `gemini` to provider adapters. (Sources: `repo://src/coding_tutor/providers/base.py#L13-L59`, `repo://src/coding_tutor/providers/registry.py#L1-L23`.)

## Generation gates and context

Question generation rejects unsupported question type, difficulty, method, invalid topic, unverified model, or provider/model mismatch before making a provider call. It also requires the selected provider to be configured. (Source: `repo://src/coding_tutor/generation/generator.py#L71-L101`.)

The generator loads matching local catalog context first. If that lookup fails it logs the failure and continues with no local references. Optional web research runs only when enabled for a non-general topic that is absent from local context; returned excerpts and source URLs are added to the references sent into the question prompt. (Source: `repo://src/coding_tutor/generation/generator.py#L103-L137`.)

Prompt templates are loaded from a known allowlist, and rendering rejects missing, extra, or non-text values. Generation parses the provider response as JSON and validates the question contract; malformed or incomplete output is returned as a failure rather than saved. (Sources: `repo://src/coding_tutor/prompts/__init__.py#L24-L42`, `repo://src/coding_tutor/generation/generator.py#L149-L160`.)

## Provenance and atomic save

On success, question content, its assets, and provider/model/prompt-version/context-source metadata are saved together in a database transaction. The tests check that generation provenance is recorded, that the local reference context remains bounded, and that invalid provider output creates no question rows. They also exercise rejection of unverified or mismatched models, secret-free provider errors, and rollback after a mid-save failure. (Sources: `repo://src/coding_tutor/generation/generator.py#L199-L276`, `repo://tests/test_generation.py#L185-L218`, `repo://tests/test_generation.py#L246-L264`, `repo://tests/test_generation.py#L365-L430`.)

## Related pages

- [Coding practice and question generation](../workflows/coding-practice.md)
- [AI Questions and bounded web research](../workflows/ai-questions.md)
- [Interview sessions](../workflows/interviews.md)
