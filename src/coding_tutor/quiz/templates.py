"""Language-appropriate starter templates for the learning editor."""

EDITOR_TEMPLATES = {
    "python": "def solution():\n    # Write your solution here\n    pass\n",
    "javascript/typescript": (
        "function solution() {\n"
        "  // Write your JavaScript or TypeScript solution here\n"
        "}\n"
    ),
    "java": (
        "class Solution {\n"
        "    public Object solve() {\n"
        "        // Write your solution here\n"
        "        return null;\n"
        "    }\n"
        "}\n"
    ),
    "cpp": (
        "#include <bits/stdc++.h>\n"
        "using namespace std;\n\n"
        "class Solution {\n"
        "public:\n"
        "    void solve() {\n"
        "        // Write your solution here\n"
        "    }\n"
        "};\n"
    ),
    "sql": "-- Write your SQL query here\nSELECT \n",
    "pandas": (
        "import pandas as pd\n\n"
        "def solution(df: pd.DataFrame) -> pd.DataFrame:\n"
        "    # Write your Pandas solution here\n"
        "    return df\n"
    ),
    "pyspark": (
        "from pyspark.sql import DataFrame\n\n"
        "def solution(spark, df: DataFrame) -> DataFrame:\n"
        "    # Write your PySpark solution here\n"
        "    return df\n"
    ),
    "polars": (
        "import polars as pl\n\n"
        "def solution(df: pl.DataFrame) -> pl.DataFrame:\n"
        "    # Write your Polars solution here\n"
        "    return df\n"
    ),
}


def get_editor_template(method: str) -> str:
    try:
        return EDITOR_TEMPLATES[method]
    except KeyError as exc:
        raise ValueError(f"Unsupported solution method: {method}") from exc
