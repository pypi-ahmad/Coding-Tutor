"""Application profiles for the consolidated algorithm and data-analysis catalogs."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping, Any


@dataclass(frozen=True)
class CatalogProfile:
    key: str
    title: str
    question_type: str | None
    learning_modes: tuple[str, ...]
    database: Path
    port: int


_PROFILES = {
    "all": CatalogProfile(
        "all", "Coding Tutor", None,
        ("dataset", "ai_generated", "mixed"),
        Path("coding_tutor.duckdb"), 8551,
    ),
    "algorithm": CatalogProfile(
        "algorithm", "Algorithm Coding Tutor", "algorithm",
        ("dataset", "ai_generated", "mixed"),
        Path("Dataset/catalogs/algorithm.duckdb"), 8551,
    ),
    "data_analysis": CatalogProfile(
        "data_analysis", "Data Analysis Coding Tutor", "data_analysis",
        ("ai_generated",),
        Path("Dataset/catalogs/data_analysis.duckdb"), 8552,
    ),
}

_METHODS = {
    "algorithm": ("python",),
    "data_analysis": ("sql", "pandas", "pyspark", "polars"),
}


def get_catalog_profile(value: str | None = None) -> CatalogProfile:
    key = value or os.environ.get("CODING_TUTOR_CATALOG", "all")
    try:
        return _PROFILES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown catalog profile: {key}") from exc


def apply_catalog_profile(
    state: MutableMapping[str, Any], profile: CatalogProfile,
) -> None:
    """Lock session controls to a fixed catalog without resetting valid choices."""
    if profile.question_type is None:
        return

    question_type = profile.question_type
    state["question_type"] = question_type
    state["question_type_control"] = question_type

    if state.get("question_source") not in profile.learning_modes:
        state["question_source"] = profile.learning_modes[0]

    methods = _METHODS[question_type]
    method = state.get("method")
    if method not in methods:
        method = methods[0]
        state["method"] = method
    if state.get("method_control") not in methods:
        state["method_control"] = method
