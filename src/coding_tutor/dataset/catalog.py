"""Verified metadata and source layouts for supported downloaded datasets."""
from __future__ import annotations

from dataclasses import dataclass

from coding_tutor.methods import ALGORITHM_METHODS, DATA_ANALYSIS_METHODS


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    dataset_name: str
    module: str
    question_type: str
    source_format: str
    file_pattern: str
    required_fields: frozenset[str]
    license: str | None
    attribution: str
    supported_methods: tuple[str, ...]


DATASET_SPECS = (
    DatasetSpec("leetcode", "LeetCodeDataset", "coding_tutor.dataset.leetcode", "algorithm", "jsonl", "algorithm_problems/LeetCodeDataset/*.jsonl", frozenset({"task_id", "problem_description"}), "Apache-2.0", "LeetCodeDataset by newfacade via Hugging Face", ALGORITHM_METHODS),
    DatasetSpec("apps", "apps", "coding_tutor.dataset.apps_dataset", "algorithm", "jsonl", "algorithm_problems/apps/*.jsonl", frozenset({"id", "question"}), "MIT", "APPS Dataset (Hendrycks et al., 2021) via Hugging Face", ALGORITHM_METHODS),
    DatasetSpec("codecontests", "CodeContests", "coding_tutor.dataset.codecontests", "algorithm", "parquet", "algorithm_problems/CodeContests/tasks.parquet", frozenset({"path", "task_binary"}), None, "CodeContests repackaged by open-thoughts from the DeepMind CodeContests dataset", ALGORITHM_METHODS),
    DatasetSpec("taco", "TACO", "coding_tutor.dataset.taco", "algorithm", "parquet", "algorithm_problems/TACO/ALL/*.parquet", frozenset({"question", "url", "input_output"}), "Apache-2.0", "TACO Dataset (BAAI) via Hugging Face", ALGORITHM_METHODS),
    DatasetSpec("spider", "spider", "coding_tutor.dataset.spider", "data_analysis", "parquet", "data_analysis_problems/spider/spider/*.parquet", frozenset({"db_id", "query", "question"}), "CC BY-SA 4.0", "Spider Dataset (Yu et al., 2018) via Hugging Face", DATA_ANALYSIS_METHODS),
    DatasetSpec("sqlctx", "sql-create-context", "coding_tutor.dataset.sql_create_context", "data_analysis", "json_array", "data_analysis_problems/sql-create-context/sql_create_context_v4.json", frozenset({"question", "context", "answer"}), "CC BY 4.0", "sql-create-context by b-mc2 via Hugging Face", DATA_ANALYSIS_METHODS),
    DatasetSpec("querypls", "querypls-prompt2sql-dataset", "coding_tutor.dataset.querypls", "data_analysis", "parquet", "data_analysis_problems/querypls-prompt2sql-dataset/data/*.parquet", frozenset({"context", "answer", "autotrain_text"}), "Apache-2.0", "QueryPls Prompt2SQL Dataset via Hugging Face", DATA_ANALYSIS_METHODS),
)

SPECS_BY_KEY = {spec.key: spec for spec in DATASET_SPECS}
SPECS_BY_NAME = {spec.dataset_name: spec for spec in DATASET_SPECS}
