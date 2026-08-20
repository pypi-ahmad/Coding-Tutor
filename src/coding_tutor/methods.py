"""Canonical solution methods and their user-facing presentation."""

ALGORITHM_METHODS = ("python", "javascript/typescript", "java", "cpp")
DATA_ANALYSIS_METHODS = ("sql", "pandas", "pyspark", "polars")
METHODS_BY_QUESTION_TYPE = {
    "algorithm": ALGORITHM_METHODS,
    "data_analysis": DATA_ANALYSIS_METHODS,
}
ALL_METHODS = frozenset((*ALGORITHM_METHODS, *DATA_ANALYSIS_METHODS))
INTERVIEW_LANGUAGES = (*ALGORITHM_METHODS, "sql")

METHOD_LABELS = {
    "python": "Python",
    "javascript/typescript": "JavaScript/TypeScript",
    "java": "Java",
    "cpp": "C++",
    "sql": "SQL",
    "pandas": "Pandas",
    "pyspark": "PySpark",
    "polars": "Polars",
}

SYNTAX_LANGUAGES = {
    "javascript/typescript": "javascript",
    "cpp": "cpp",
    "sql": "sql",
}


def method_label(method: str) -> str:
    """Return a stable user-facing label for a solution method."""
    return METHOD_LABELS.get(method, method)


def syntax_language(method: str) -> str:
    """Return the Streamlit syntax-highlighting language for a method."""
    return SYNTAX_LANGUAGES.get(method, "python" if method in {"pandas", "pyspark", "polars"} else method)


def comment_tokens(method: str) -> tuple[str, ...]:
    """Return comment markers accepted in generated teaching code."""
    if method == "sql":
        return ("--", "/*")
    if method in {"javascript/typescript", "java", "cpp"}:
        return ("//", "/*")
    return ("#", "'''", '\"\"\"')
