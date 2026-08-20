# Datasets

Coding Tutor supports seven downloaded Hugging Face dataset sources through deterministic, source-specific import adapters. This reference describes the current catalog, importer behavior, locally present snapshots, and metadata available in the project. It does not grant permission to use or redistribute third-party data.

## Verification status

For this documentation update:

- all seven configured source layouts were present under `Dataset/`;
- representative JSONL, JSON-array, and Parquet schemas were inspected read-only and contained the importer-required fields;
- Hugging Face revision metadata was present for the imported file patterns;
- the default `coding_tutor.duckdb` contained no dataset import runs or normalized dataset questions; and
- a complete import of the downloaded corpora was not run.

“Supported” below means an adapter and tests exist. “Complete” means the adapter can create a selectable normalized exercise when a source record contains its expected content. It does not mean the full local snapshot has been imported or every record is usable.

## Raw sources and normalized records

Downloaded files remain under the gitignored `Dataset/` tree:

```text
Dataset/
├── algorithm_problems/
└── data_analysis_problems/
```

The importer reads configured paths without renaming, moving, overwriting, or extracting files into their source directories. CodeContests archives are read in memory.

Normalized data is stored separately in DuckDB:

- `question_sources` records the dataset, stable source key, available original identifier, relative source file, revision, record index, license, attribution, import run, and timestamp;
- `questions` stores the normalized type, difficulty, statement, methods, tags, and completeness;
- `question_assets` stores schemas, fixture data, expected results, and starter code;
- `reference_solutions` stores method-specific source solutions; and
- `question_test_cases` stores input and expected-output context.

Each adapter generates a stable source key. The unique `(dataset_name, source_key)` identity makes reruns idempotent. Each question and its related source, assets, references, and cases are committed in one transaction. `import_runs` records run status and imported/skipped counts.

> [!IMPORTANT]
> A SQL answer and `CREATE TABLE` statements are not enough to create a complete SQL/Pandas/PySpark/Polars exercise. The same task needs usable fixture rows and a deterministic expected result. The importer does not invent either. Records without schema, fixture data, and expected result remain incomplete and are excluded from the curated question picker.

The application does not execute imported tests, SQL, Python, Pandas, PySpark, or Polars code. Source tests and expected outputs are stored as static question or AI-review context.

## Source summary

| Key | Source | Category | Format | Adapter result |
| --- | --- | --- | --- | --- |
| `leetcode` | LeetCodeDataset | Algorithm | JSONL | Complete Python questions when a statement is present; stores available starter, reference, and cases. |
| `apps` | APPS | Algorithm | JSONL | Complete Python questions when a statement is present; stores available starter, references, and cases. |
| `taco` | TACO | Algorithm | Parquet | Complete Python questions when URL identity and statement are present; stores available starter, references, and cases. |
| `codecontests` | CodeContests | Algorithm | Parquet containing tar blobs | Complete Python questions when required archive members are valid; stores up to 10 case pairs. |
| `spider` | Spider | Data analysis | Parquet | Incomplete; stores the natural-language question, database ID, and SQL reference but no shared analytical assets. |
| `sqlctx` | sql-create-context | Data analysis | JSON array | Incomplete; stores `CREATE TABLE` context and SQL reference but no fixture rows or expected result. |
| `querypls` | QueryPls Prompt2SQL | Data analysis | Parquet | Incomplete; stores context and SQL reference but no fixture rows or expected result. |

## LeetCodeDataset

- **Configured source:** [newfacade/LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset)
- **Category and methods:** `algorithm`; Python only.
- **Local source:** `Dataset/algorithm_problems/LeetCodeDataset/*.jsonl`
- **Inspected snapshot revision:** `215604aeed660029df7de2fea5a4d7b6ed476a08`
- **Required fields:** `task_id`, `problem_description`
- **Other fields used when present:** `question_id`, `difficulty`, `tags`, `starter_code`, `completion`, `input_output`
- **License in the downloaded card and catalog:** Apache-2.0
- **Stored attribution:** “LeetCodeDataset by newfacade via Hugging Face.” The downloaded card also links the dataset repository and paper.

The adapter derives identity from `task_id` or `question_id`, maps Easy/Medium/Hard difficulty, and stores tags. It can store a Python starter template, one Python reference solution from `completion`, and up to 50 `input_output` cases. It does not use the available `test`, `entry_point`, `prompt`, `query`, or `response` fields.

The importer does not execute or validate the semantic correctness of references or cases. The dataset card's Apache-2.0 declaration does not cause Coding Tutor to assess the rights attached to each underlying problem statement; review the source terms before redistribution.

## APPS

- **Configured source:** [codeparrot/apps](https://huggingface.co/datasets/codeparrot/apps)
- **Category and methods:** `algorithm`; Python only.
- **Local source:** `Dataset/algorithm_problems/apps/*.jsonl`
- **Inspected snapshot revision:** `21e74ddf8de1a21436da12e3e653065c5213e9d1`
- **Required fields:** `id`, `question`
- **Other fields used when present:** `problem_id`, `problem`, `name`, `difficulty`, `tags`, `starter_code`, `solutions`, `input_output`
- **License in the downloaded card and catalog:** MIT
- **Stored attribution:** “APPS Dataset (Hendrycks et al., 2021) via Hugging Face.” The downloaded card provides the Hendrycks et al. citation.

The adapter scopes reused IDs by source file, maps introductory/interview/competition to Easy/Medium/Hard, and decodes JSON-encoded `solutions` and `input_output`. It stores a starter template when available, up to three Python reference solutions, and up to 50 paired cases.

The downloaded card notes that limited test coverage can produce false positives during execution-based evaluation. Coding Tutor does not execute those tests, so it makes no independent quality claim. Preserve applicable MIT notices and the source citation when required by the intended use.

## TACO

- **Configured source:** [BAAI/TACO](https://huggingface.co/datasets/BAAI/TACO)
- **Category and methods:** `algorithm`; Python only.
- **Local source:** `Dataset/algorithm_problems/TACO/ALL/*.parquet`
- **Inspected snapshot revision:** `d593ed0a2becbbc952230bb89be09189bf1056dc`
- **Required fields:** `question`, `url`, `input_output`
- **Other fields used when present:** `problem_id`, `id`, `name`, `difficulty`, `tags`, `raw_tags`, `starter_code`, `solutions`
- **License metadata:** Apache-2.0 for the TACO-authored dataset; the downloaded card describes mixed upstream licensing.
- **Stored attribution:** “TACO Dataset (BAAI) via Hugging Face.” The downloaded card provides the TACO paper citation.

The adapter uses the source URL as its normal identity, maps all five application difficulty levels when recognizable, decodes tags, solutions, and case data, and stores a starter, up to three Python references, and up to 50 case pairs when present.

The local card states that the corpus also contains material under other permissive terms or CC BY 4.0 and says the rights for HackerRank material are unknown. Source-level rights are therefore not established by the catalog's Apache-2.0 value. Preserve record provenance and review the applicable upstream terms before use or redistribution.

## CodeContests

- **Configured source:** [open-thoughts/CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests)
- **Upstream sources recorded in the downloaded card:** [DCAgent/code-contests-sandboxes-with-tests](https://huggingface.co/datasets/DCAgent/code-contests-sandboxes-with-tests) and [deepmind/code_contests](https://huggingface.co/datasets/deepmind/code_contests)
- **Category and methods:** `algorithm`; Python only.
- **Local source:** `Dataset/algorithm_problems/CodeContests/tasks.parquet`
- **Inspected snapshot revision:** `11f66f5e81d8035f44c3a576ed6772994d1ed90b`
- **Required and inspected fields:** `path`, `task_binary`
- **License:** Not verified in the current project
- **Stored attribution:** “CodeContests repackaged by open-thoughts from the DeepMind CodeContests dataset.” The downloaded card requests citation of the original CodeContests paper and OpenThoughts-Agent.

Each `task_binary` is a tar archive. The adapter reads only `instruction.md`, `task.toml`, and `tests/test_data.json`, with per-member size checks, and does not extract the archive into the dataset directory. It uses `path` as identity, reads difficulty and tags from task metadata, and stores up to 10 test pairs. It does not import a starter template, reference solution, Dockerfile, or verifier implementation.

The source is still treated only as static question content; its sandbox material is not used to execute learner code. Because neither the downloaded card nor the project catalog declares a license, citation metadata is not redistribution permission.

## Spider

- **Configured source:** [xlangai/spider](https://huggingface.co/datasets/xlangai/spider)
- **Upstream repository recorded in the card:** [taoyds/spider](https://github.com/taoyds/spider)
- **Category and declared methods:** `data_analysis`; SQL, Pandas, PySpark, and Polars.
- **Local source:** `Dataset/data_analysis_problems/spider/spider/*.parquet`
- **Inspected snapshot revision:** `0c350918f3f29ec754f1181c65cdce76cd6c133c`
- **Required and used fields:** `db_id`, `query`, `question`
- **Available but unused inspected fields:** `query_toks`, `query_toks_no_value`, `question_toks`
- **License in the downloaded card and catalog:** CC BY-SA 4.0
- **Stored attribution:** “Spider Dataset (Yu et al., 2018) via Hugging Face.” The downloaded card supplies the Yu et al. paper citation.

The adapter stores the natural-language question, database ID, and SQL query as a reference solution. It does not import the referenced database schema, database rows, fixture data, or a deterministic expected result. Every imported Spider record is therefore marked incomplete and is not selectable as a curated learner exercise.

Preserve the required attribution and share-alike obligations for CC BY-SA 4.0 material and the recorded citation when using adapted content.

## sql-create-context

- **Configured source:** [b-mc2/sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context)
- **Source datasets recorded in the downloaded card:** WikiSQL and Spider
- **Category and declared methods:** `data_analysis`; SQL, Pandas, PySpark, and Polars.
- **Local source:** `Dataset/data_analysis_problems/sql-create-context/sql_create_context_v4.json`
- **Inspected snapshot revision:** `9d80a6a118b838d9defc3798d659a54a2ac2ff37`
- **Required and used fields:** `question`, `context`, `answer`
- **License in the downloaded card and catalog:** CC BY 4.0
- **Stored attribution:** “sql-create-context by b-mc2 via Hugging Face.” The downloaded card provides citations for this dataset, WikiSQL, and Spider.

The adapter stores the natural-language question, `context` as a schema asset, and `answer` as an SQL reference. The source card explicitly describes `CREATE TABLE` context without actual rows. It also notes that column types were inferred and may be imperfect.

Because no fixture rows or deterministic expected result are available, records remain incomplete and are not selectable. Preserve CC BY 4.0 attribution and the recorded source-dataset citations when required.

## QueryPls Prompt2SQL

- **Configured source:** [samadpls/querypls-prompt2sql-dataset](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset)
- **Category and declared methods:** `data_analysis`; SQL, Pandas, PySpark, and Polars.
- **Local source:** `Dataset/data_analysis_problems/querypls-prompt2sql-dataset/data/*.parquet`
- **Inspected snapshot revision:** `bec23c96e91f9b67cc11a503a0caf46e0381816a`
- **Required and used fields:** `context`, `answer`, `autotrain_text`
- **License in the downloaded card and catalog:** Apache-2.0
- **Stored attribution:** “QueryPls Prompt2SQL Dataset via Hugging Face.” Specific author/citation requirements: Not verified in the current project.

The adapter derives the problem statement from `autotrain_text`, stores `context` as a schema asset, and stores `answer` as an SQL reference. Its stable identity is based on the question, context, and answer, so duplicate records across local train and validation files are skipped.

The source provides no fixture rows or deterministic expected result to the adapter. Imported records remain incomplete and are not selectable as curated exercises. Preserve applicable Apache-2.0 notices; no additional citation requirement is verified by the downloaded card.

## Verified commands

List configured dataset keys:

```powershell
uv run python scripts/download_datasets.py --list
```

Download the default set. CodeContests is skipped unless explicitly included:

```powershell
uv run python scripts/download_datasets.py
uv run python scripts/download_datasets.py --include-codecontests
```

Import every configured source found under the default dataset root:

```powershell
uv run python scripts/import_datasets.py
```

Import selected sources:

```powershell
uv run python scripts/import_datasets.py --datasets leetcode apps taco
```

The import CLI also implements `--dataset-root` and `--database`. Omitting `--database` uses `CODING_TUTOR_DB` when set and otherwise uses `coding_tutor.duckdb`. See [Dataset Setup](dataset-setup.md) for the command reference and [Troubleshooting](TROUBLESHOOTING.md) for verified import failures.

## Interview question sources

Interview material is downloaded to `Dataset/interview_sources/raw` and normalized into `Dataset/catalogs/interview.duckdb`. The downloader uses authenticated GitHub CLI requests, pins each source revision, calculates file hashes, and writes license and ingestion decisions to `Dataset/interview_sources/manifest.json`.

```powershell
gh auth status
uv run python scripts/download_interview_sources.py --list
uv run python scripts/download_interview_sources.py
uv run python scripts/import_interview_sources.py
uv run python scripts/import_user_ai_interview_questions.py
```

Only sources marked `ingestion_allowed` are normalized. Raw-only sources remain local research inputs and do not become application questions. RecruitView is deferred because its non-commercial/access constraints require separate approval. Repeated imports skip stable source identities.

## Runtime catalogs

| Catalog | Imported material |
| --- | --- |
| `Dataset/catalogs/algorithm.duckdb` | LeetCodeDataset, APPS, TACO, and CodeContests algorithm records |
| `Dataset/catalogs/data_analysis.duckdb` | Spider, sql-create-context, and QueryPls reference records |
| `Dataset/catalogs/interview.duckdb` | Allowed interview sources and project-maintained AI interview questions |

Raw dataset directories are import inputs and are not queried during normal app use.

## Licensing and redistribution cautions

The Coding Tutor MIT license covers this project's source code only. It does not relicense downloaded or normalized dataset content.

Before using or redistributing dataset-derived records:

1. review the downloaded card, upstream source, and applicable license;
2. preserve license notices, attribution, citations, and share-alike terms as applicable;
3. retain the provenance stored by the importer;
4. treat mixed or missing license metadata as unresolved; and
5. do not assume that structural import validation proves accuracy, safety, or redistribution rights.

In particular, TACO describes mixed upstream terms and unresolved HackerRank rights, while CodeContests has no verified license declaration in the current project.
