# Datasets

The importer supports seven Hugging Face sources. The downloaded files are present locally in the expected layouts, and read-only schema inspection passed during this documentation review. Automated tests use small fixtures; a complete seven-source import was not run.

| Key/source | Official card and license | Imported fields and normalization | Completeness/caution |
| --- | --- | --- | --- |
| `leetcode` / LeetCodeDataset | [newfacade/LeetCodeDataset](https://huggingface.co/datasets/newfacade/LeetCodeDataset), Apache-2.0 on card | Requires `task_id`, `problem_description`; reads difficulty, tags, starter, completion, and up to 50 `input_output` cases. Python algorithm. | Reference/tests are stored when present, never executed. Review underlying problem-content rights separately. |
| `apps` / APPS | [codeparrot/apps](https://huggingface.co/datasets/codeparrot/apps), MIT; cite Hendrycks et al. (2021) | Requires `id`, `question`; decodes solutions and input/output, maps introductory/interview/competition to Easy/Medium/Hard. Python algorithm. | Stores up to three solutions and 50 cases. |
| `taco` / TACO | [BAAI/TACO](https://huggingface.co/datasets/BAAI/TACO), Apache-2.0 for authored dataset | Uses question, URL identity, difficulty, tags, starter, solutions, input/output. Python algorithm. | Card states mixed upstream licenses and unresolved HackerRank rights; preserve source-specific terms. |
| `codecontests` / CodeContests | [open-thoughts/CodeContests](https://huggingface.co/datasets/open-thoughts/CodeContests); no license declared on card | Reads `path` and an in-memory tar in `task_binary`; uses `instruction.md`, `task.toml`, and up to 10 test pairs. Python algorithm. | No reference solution imported. Redistribution permission is unresolved; citation alone is not a license. |
| `spider` / Spider | [xlangai/spider](https://huggingface.co/datasets/xlangai/spider), CC BY-SA 4.0; cite Yu et al. (2018) | Uses `db_id`, question, and SQL query. Stores SQL reference and database identifier. | No schema rows/fixtures/expected result are imported; record is incomplete and not selectable. |
| `sqlctx` / sql-create-context | [b-mc2/sql-create-context](https://huggingface.co/datasets/b-mc2/sql-create-context), CC BY 4.0; cite b-mc2 and its WikiSQL/Spider sources | Uses question, CREATE TABLE context, and SQL answer. | Card explicitly provides no actual data rows. Schema alone cannot create Pandas/PySpark/Polars exercises; record remains incomplete. |
| `querypls` / QueryPls Prompt2SQL | [samadpls/querypls-prompt2sql-dataset](https://huggingface.co/datasets/samadpls/querypls-prompt2sql-dataset), Apache-2.0 on card | Uses `autotrain_text`, CREATE TABLE context, and answer. | No fixture rows or expected result; record remains incomplete and not selectable. |

## Layout and commands

See [dataset setup](dataset-setup.md) for exact subdirectories and CLI options. Importers never rename, move, overwrite, or extract files into source directories. Hugging Face revision metadata is recorded when download metadata exists.

```powershell
uv run python scripts/download_datasets.py --list
uv run python scripts/import_datasets.py --datasets leetcode apps
```

Each record receives a stable key. Reruns skip matching `(dataset_name, source_key)` rows. An import run records completion/failure and counts; a process interruption can leave that run marked `running`, while already committed questions remain deduplicated.

Licenses shown here reflect the official cards reviewed on 2026-08-19. Recheck the linked card and upstream repository before use or redistribution.

At minimum, preserve Apache/MIT copyright and license notices when their terms require it; credit CC BY material; preserve attribution and the same-license obligations for adapted CC BY-SA material; and retain the paper/dataset citations named above. TACO requires record-source awareness because its card describes mixed upstream terms. Do not redistribute CodeContests-derived material until the applicable permission is resolved.
