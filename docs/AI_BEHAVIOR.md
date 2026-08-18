# AI Behavior

This document explains the AI behavior implemented by Coding Tutor. It describes current provider adapters, model selection, request content, validation, persistence, and failure handling—not planned capabilities.

> The editor is a text editor. Learner code is reviewed through AI static analysis and is not executed by the application. Any correctness percentage or mark is an AI estimate, not a verified test result.

## Providers and configuration status

The application implements three providers behind a common interface with methods for configuration status, model options, and chat requests.

| Provider | Configuration variable | Implemented request path |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | OpenAI Chat Completions |
| Agnes AI | `AGNES_API_KEY` | OpenAI-compatible Chat Completions using the fixed Agnes API base URL |
| Google Gemini | `GOOGLE_API_KEY` | Google Gen AI Interactions |

OpenAI also reads the optional `OPENAI_BASE_URL`. `GEMINI_API_KEY` is not read.

Configuration status is only a local presence check: the provider reports configured when its required credential variable contains non-whitespace text. The check returns a Boolean and does not display the credential, contact the provider, verify authentication, check quota, or confirm model availability.

## Models exposed in the UI

The sidebar first selects a provider and then shows that provider's model options marked `verified=True` in the application registry.

| Provider | Model ID | Request setting |
| --- | --- | --- |
| OpenAI | `gpt-5.6-luna` | `reasoning_effort=medium` |
| Agnes AI | `agnes-2.5-flash` | Fixed Agnes model |
| Google Gemini | `gemini-3.5-flash-lite` | `thinking_level=medium` |
| Google Gemini | `gemini-3.7-flash` | `thinking_level=medium` |

Gemini requests also set provider-side interaction storage to false. The request shapes and settings above are covered by mocked tests; the test suite does not make live provider calls. A model being listed does not guarantee that a particular account can access it.

The UI does not offer registry entries marked unverified. Provider-backed assessment, teaching-solution, and quiz paths also confirm that the selected model belongs to the provider's verified option list. Question generation checks the selected model's verified flag and provider association; normal UI use supplies that model from the same registry.

## Implemented AI actions

### Generate questions

Practice and Quiz modes can call the selected provider to generate a question. The request includes the selected question type, difficulty, method, and topic. Topic input is limited to 100 characters.

Algorithm and data-analysis generation use different structured contracts. Returned JSON is parsed and validated before it is shown or stored. Generated data-analysis questions must contain a consistent schema, fixture rows, deterministic expected result, starter templates, and reference solutions for SQL, Pandas, PySpark, and Polars. Missing, malformed, or inconsistent content is rejected rather than completed with invented data.

Saving an accepted question is transactional: the question, assets, references, test cases, and generation metadata are committed together or rolled back together.

### Review learner submissions

Selecting **Done** first stores an immutable local attempt, then requests a static teacher-style review. The provider returns structured fields for:

- estimated percentage correct;
- identified mistakes;
- an explanation;
- a suggested correction; and
- optional corrected code.

The application validates the response and calculates the mark out of 10 as the estimated percentage divided by 10. It does not accept a provider-supplied mark independently.

No learner submission is executed, compiled, queried, or tested. Stored test cases and expected results are context for the model only.

### Apply corrected code

When a valid assessment contains corrected code, the UI displays it before offering **Apply correction to editor**. Applying it saves the current editor text in Streamlit session state so **Restore pre-correction code** can reverse the change.

The saved attempt always retains the original submitted text. Applying or restoring an editor correction does not update that attempt.

### Provide teaching solutions

**Show Solution** can display stored dataset or AI-generated reference solutions without making a new provider request. An explicit teaching-solution request can ask the selected provider for:

- up to three commented Python approaches for an algorithm question; or
- one commented solution for the currently selected data-analysis method.

The provider response must match the exact solution schema and include commented code, an explanation, and theory. Data-analysis generation requires schema, fixture data, and expected-result context. Invalid responses are not displayed or cached.

Teaching solutions are not executed, and equivalence between methods is not deterministically verified.

### Prepare and score quizzes

Quiz Mode uses AI in three places:

1. AI-source quiz questions use the same validated question-generation pipeline as Practice mode.
2. Multiple-choice items are sent together for option generation. Each returned question must have exactly four unique, non-empty options, one valid correct option ID, a prompt, and an explanation.
3. Non-blank coding answers use the same static assessment path as Practice submissions.

MCQ scoring itself does not call a provider. The selected option ID is compared with the stored correct option ID and receives 100 or 0. Blank coding answers receive 0 without an AI review. Non-blank coding scores remain AI estimates.

## Prompt templates

Runtime prompts are version-controlled Markdown resources under `src/coding_tutor/prompts/`. A restricted loader accepts only registered filenames, and the renderer rejects missing, extra, or non-text placeholder values.

| Template | Implemented use |
| --- | --- |
| `shared_rules.md` | Common system instruction for static reasoning, untrusted input, structured JSON, and no code-execution claims |
| `algorithm_question_generator.md` | Algorithm question generation |
| `data_analysis_question_generator.md` | Data-analysis question generation |
| `static_code_reviewer.md` | Learner-submission assessment |
| `solution_teacher.md` | Commented solutions and teaching explanations |
| `quiz_generator.md` | Batched MCQ option generation |
| `dataset_record_converter.md` | Registered and rendering-tested, but not called by the deterministic dataset importer |

Prompt text is not reproduced here. Embedded question, dataset, and learner content is identified as untrusted input for the provider.

### Version metadata

- Question generation uses prompt version `v3`, stored with each generated question.
- Teaching-solution generation uses `solution-v2` in its Streamlit cache key.
- Practice assessments do not store a prompt name or version with the attempt.
- Quiz records do not store a general prompt-version field.

Therefore, prompt files are version-controlled in Git, but prompt-version persistence is not uniform across every AI interaction.

## Content sent to providers

The application sends only the context assembled for the requested operation. It does not send environment-variable values or the DuckDB database file itself.

### Question generation

- selected difficulty;
- selected topic;
- selected method; and
- a question-type-specific structured generation contract.

### Submission assessment

- question title, type, difficulty, tags, examples, problem statement, and constraints;
- selected method;
- learner submission, limited to 12,000 characters;
- the first stored reference solution for that method, when available;
- up to 10 matching schema, fixture-data, and expected-result assets; and
- up to 10 stored test cases.

Large text fields are clipped before request construction: the problem statement to 6,000 characters, constraints to 3,000, reference solution to 12,000, and each included asset to 4,000.

### Teaching solutions

- bounded question fields, including title, type, difficulty, tags, statement, examples, constraints, and expected-output format;
- the selected method;
- stored question assets, with one value retained per asset type and content clipped to 20,000 characters;
- up to 20 test cases; and
- up to 12 reference solutions, each clipped to 12,000 characters.

### Quiz preparation and scoring

For MCQ preparation, the app sends each MCQ item's question ID, title, selected method, problem statement clipped to 8,000 characters, constraints clipped to 3,000, and up to five examples. All MCQ items for that quiz are batched into one request.

For a non-blank coding answer, Quiz Mode sends the same assessment context described above.

## Local persistence after AI interactions

| Interaction | Local persistence |
| --- | --- |
| Accepted generated question | `questions`, applicable `question_assets`, `reference_solutions`, `question_test_cases`, and `ai_generated_questions` |
| Practice submission and review | Original text, method, provider/model, assessment status, estimated percentage, derived mark, parsed feedback, optional correction, or a bounded error in `attempts` |
| Teaching-solution request | Parsed result in Streamlit session state only; viewing a displayed method is recorded in `solution_views` |
| Quiz creation/preparation | Quiz settings and provider/model in `quiz_attempts`; question snapshots, MCQ options, correct option ID, explanation, and provider/model in `quiz_items` |
| Quiz coding review | Estimated percentage/mark, parsed feedback, provider/model, or bounded error in `quiz_items` |

Generated-question metadata contains the provider, model ID, prompt version, prompt-template label, question type, difficulty, method, and topic. It does not contain credentials.

Raw provider responses are not stored as a general audit log. Validated fields are persisted for the interaction that needs them. Practice and quiz errors are stored as user-safe messages truncated to 2,000 characters.

## Error behavior

| Condition | Implemented behavior |
| --- | --- |
| Missing or blank credential | Provider status is unavailable and no request is made. |
| Unknown provider | The operation returns or displays an unavailable/invalid-selection error. |
| Unverified or mismatched model | The request is rejected before the provider call. Assessment, solution, and quiz paths also check the provider's registered verified models. |
| Provider exception | The UI receives a generic message about configuration, connectivity, quota, access, or retry; raw exception text is not displayed. Generation logs only the exception type. |
| Malformed JSON | The response is rejected and no usable generated content is saved or displayed. |
| Missing, extra, or invalid response fields | Exact-schema validation rejects the response. |
| Incomplete data-analysis context | Question generation is rejected, and a teaching-solution request reports incomplete context. |
| Generated-question storage failure | The transaction is rolled back and a storage failure is reported. |
| Assessment persistence failure | The original attempt remains saved with an error status when that status update succeeds. |
| Quiz preparation or scoring failure | The durable quiz records an error state and exposes a retry path. |

## Known limitations

- AI output can be incomplete or incorrect even when it passes structural validation.
- Provider configuration status does not prove that authentication or a live request will succeed.
- Provider request construction is mock-tested; live provider access is not part of the automated suite.
- Static review can miss syntax, runtime, performance, data-type, ordering, or edge-case failures that execution would reveal.
- Generated tests and expected results are model output; they are validated structurally but not executed.
- Applying a correction changes only the active editor and does not prove the correction is correct.
- Teaching solutions are cached only for the current Streamlit session.
- Assessment and quiz persistence do not record a uniform prompt version, so not every historical AI result can be tied to an exact prompt revision from database data alone.

For implementation details, see [Technical Reference](TECHNICAL_REFERENCE.md). For user workflows, see [Usage](USAGE.md).
