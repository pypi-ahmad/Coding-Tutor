---
type: overview
title: Repository guide
description: A short, evidence-backed map of Coding Tutor and links to its architecture, workflow, operations, and testing pages.
tags: [overview, architecture, onboarding, navigation]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:17:19.981Z
sources:
  - id: openwiki-source-196170e31ff8ec60a116165b
    resource: repo://docs/README.md
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "codex", at: "2026-09-23T14:17:19.981Z" }
---

# Repository guide

Coding Tutor is a local Streamlit application backed by DuckDB catalogs. It brings together coding practice, quizzes, AI Questions, timed interviews, and progress review. Learner code and stored tests are not executed; provider-returned scores and corrections are estimates. (Sources: `repo://README.md#L1-L18`, `repo://README.md#L52-L62`.)

## Find the right page

| If you are working on… | Start with… |
| --- | --- |
| App startup, profiles, page/database selection | [Runtime and profile routing](architecture/runtime-routing.md) |
| Schema, DB paths, migrations, persisted records | [Persistence and migrations](architecture/persistence-and-migrations.md) |
| Curated or generated coding questions and submissions | [Coding practice](workflows/coding-practice.md) |
| Quiz preparation, drafts, scoring, retries | [Quiz lifecycle](workflows/quizzes.md) |
| AI Questions modes or bounded Firecrawl use | [AI Questions](workflows/ai-questions.md) |
| Technical or job-description interview sessions | [Interview sessions](workflows/interviews.md) |
| Dataset normalization, catalog routing, provenance | [Datasets and catalogs](workflows/datasets-and-catalogs.md) |
| Provider gates, prompts, validation, generation metadata | [Provider and prompt contract](concepts/provider-and-prompt-contract.md) |
| Assessment and code-execution limits | [Assessment boundary](concepts/assessment-and-execution-boundary.md) |
| Setup, launch, and test commands | [Local development](operations/local-development.md) |
| Dataset import commands and recovery boundaries | [Data import operations](operations/data-import.md) |
| What automated tests cover | [Testing strategy](testing/verification-strategy.md) |

## System shape

The main entry point is `app.py`. Application services and persistence live under `src/coding_tutor/`, split into database, dataset, evaluation, generation, interview, prompts, providers, quiz, and UI modules. `tests/` contains unit and Streamlit `AppTest` coverage. (Sources: `repo://README.md#L190-L212`, `repo://docs/README.md#L1-L25`.)

At a high level, raw datasets are imported into local DuckDB catalogs; Streamlit modes query those catalogs; original learner attempts are persisted before static AI review. Optional Firecrawl supplies bounded research context only on eligible question-generation paths. (Source: `repo://README.md#L174-L188`.)

## Start and verify

For the documented Windows setup and launch flow, see [Local development](operations/local-development.md). The repository documents `uv run pytest -q` for the suite; see [Testing and verification strategy](testing/verification-strategy.md) for what test fixtures establish and where live-provider or corpus-import evidence is absent. (Sources: `repo://README.md#L73-L84`, `repo://README.md#L215-L222`.)

## Evidence boundary

Treat current source and focused tests as the authority for behavior. The public README summarizes the system but does not replace implementation evidence for edge cases; generated question/prompt behavior and its verification boundaries are linked above. (Sources: `repo://README.md#L174-L188`, `repo://docs/README.md#L3-L18`.)
