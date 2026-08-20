"""Tests for fixed catalog application profiles."""
from pathlib import Path


def test_algorithm_catalog_profile(monkeypatch):
    from coding_tutor.catalog import get_catalog_profile

    monkeypatch.setenv("CODING_TUTOR_CATALOG", "algorithm")

    profile = get_catalog_profile()

    assert profile.key == "algorithm"
    assert profile.question_type == "algorithm"
    assert profile.learning_modes == ("dataset", "ai_generated", "mixed")
    assert profile.database == Path("Dataset/catalogs/algorithm.duckdb")
    assert profile.port == 8551


def test_data_analysis_catalog_profile(monkeypatch):
    from coding_tutor.catalog import get_catalog_profile

    monkeypatch.setenv("CODING_TUTOR_CATALOG", "data_analysis")

    profile = get_catalog_profile()

    assert profile.key == "data_analysis"
    assert profile.question_type == "data_analysis"
    assert profile.learning_modes == ("ai_generated",)
    assert profile.database == Path("Dataset/catalogs/data_analysis.duckdb")
    assert profile.port == 8552


def test_default_profile_preserves_existing_app(monkeypatch):
    from coding_tutor.catalog import get_catalog_profile

    monkeypatch.delenv("CODING_TUTOR_CATALOG", raising=False)

    profile = get_catalog_profile()

    assert profile.key == "all"
    assert profile.question_type is None
    assert profile.learning_modes == ("dataset", "ai_generated", "mixed")
    assert profile.database == Path("coding_tutor.duckdb")


def test_apply_catalog_profile_locks_type_without_overwriting_valid_method(monkeypatch):
    from coding_tutor.catalog import apply_catalog_profile, get_catalog_profile

    monkeypatch.setenv("CODING_TUTOR_CATALOG", "data_analysis")
    state = {
        "question_type": "algorithm",
        "question_type_control": "algorithm",
        "question_source": "dataset",
        "method": "pandas",
        "method_control": "pandas",
    }

    apply_catalog_profile(state, get_catalog_profile())

    assert state["question_type"] == "data_analysis"
    assert state["question_type_control"] == "data_analysis"
    assert state["question_source"] == "ai_generated"
    assert state["method"] == "pandas"
    assert state["method_control"] == "pandas"
