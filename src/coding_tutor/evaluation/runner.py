"""
Isolated code execution runner.

SECURITY NOTE: On Windows, this runner provides PROCESS-level isolation only.
Full OS-level sandboxing (Linux namespaces, seccomp, cgroups, memory limits)
is NOT available. The subprocess runs with an empty environment (no inherited
secrets or database paths), in an isolated temp directory, with a strict timeout.
Network access and filesystem access are not enforced at the OS level.
Do not use this runner for untrusted code in a multi-user environment.
"""
from __future__ import annotations
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
MAX_OUTPUT_BYTES = 50_000


@dataclass
class RunResult:
    status: str  # passed | failed | error | timeout
    tests_passed: int = 0
    tests_total: int = 0
    percentage_correct: float = 0.0
    error_details: Optional[str] = None
    stdout: str = ""
    stderr: str = ""


def run_python(
    code: str,
    test_cases: list[dict],
    entry_point: Optional[str] = None,
) -> RunResult:
    """
    Run Python code against test cases in an isolated subprocess.
    test_cases: list of {input: dict, expected_output: any}
    entry_point: callable string, e.g. "Solution().solve"
    """
    if not test_cases:
        return RunResult(status="error", error_details="No test cases available for this question.")

    harness = _build_python_harness(code, test_cases, entry_point)
    return _run_subprocess(harness, language="python")


def run_sql(
    sql_code: str,
    schema_sql: str,
    fixture_data: list[dict],
    table_name: str,
    expected_result: list[dict],
) -> RunResult:
    """
    Run SQL against an isolated in-memory DuckDB instance.
    No connection to the app database.
    """
    harness = _build_sql_harness(sql_code, schema_sql, fixture_data, table_name, expected_result)
    return _run_subprocess(harness, language="python")


def run_pandas(
    code: str,
    fixture_data: list[dict],
    expected_result: list[dict],
) -> RunResult:
    """Run a Pandas solution against fixture data."""
    harness = _build_pandas_harness(code, fixture_data, expected_result)
    return _run_subprocess(harness, language="python")


def run_polars(
    code: str,
    fixture_data: list[dict],
    expected_result: list[dict],
) -> RunResult:
    """Run a Polars solution against fixture data."""
    harness = _build_polars_harness(code, fixture_data, expected_result)
    return _run_subprocess(harness, language="python")


def run_pyspark(
    code: str,
    fixture_data: list[dict],
    expected_result: list[dict],
) -> RunResult:
    """
    Run a PySpark solution — only if PySpark and Java are available locally.
    Returns status='error' with a clear unavailable message if not configured.
    """
    if not _pyspark_available():
        return RunResult(
            status="error",
            error_details=(
                "PySpark is not available in this environment. "
                "Install PySpark and Java, then restart the app. "
                "This result was NOT substituted with another method."
            ),
        )
    harness = _build_pyspark_harness(code, fixture_data, expected_result)
    return _run_subprocess(harness, language="python", timeout=30)


def _pyspark_available() -> bool:
    try:
        import importlib.util
        spec = importlib.util.find_spec("pyspark")
        if spec is None:
            return False
        java_home = os.environ.get("JAVA_HOME") or shutil.which("java")
        return java_home is not None
    except Exception:
        return False


def _run_subprocess(
    script: str,
    language: str = "python",
    timeout: int = TIMEOUT_SECONDS,
) -> RunResult:
    """Execute script in an isolated subprocess with empty environment."""
    tmpdir = tempfile.mkdtemp(prefix="coding_tutor_run_")
    try:
        script_path = Path(tmpdir) / "harness.py"
        script_path.write_text(script, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            timeout=timeout,
            cwd=tmpdir,
            env={},  # empty env — no secrets, no PYTHONPATH, no DB paths
        )

        stdout = result.stdout[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
        stderr = result.stderr[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")

        if result.returncode == 0:
            return _parse_result_output(stdout, stderr)
        else:
            return RunResult(
                status="error",
                stdout=stdout,
                stderr=stderr,
                error_details=stderr or stdout or "Process exited with non-zero code",
            )

    except subprocess.TimeoutExpired:
        return RunResult(
            status="timeout",
            error_details=f"Code execution timed out after {timeout} seconds.",
        )
    except Exception as exc:
        logger.error("Runner error: %s", exc)
        return RunResult(status="error", error_details=str(exc))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _parse_result_output(stdout: str, stderr: str) -> RunResult:
    """Parse structured JSON result from harness stdout."""
    try:
        data = json.loads(stdout.strip())
        passed = int(data.get("passed", 0))
        total = int(data.get("total", 0))
        pct = (passed / total * 100) if total > 0 else 0.0
        return RunResult(
            status="passed" if passed == total and total > 0 else "failed",
            tests_passed=passed,
            tests_total=total,
            percentage_correct=round(pct, 1),
            error_details=data.get("error"),
            stdout=stdout,
            stderr=stderr,
        )
    except Exception:
        return RunResult(
            status="error",
            error_details=f"Could not parse runner output: {stdout[:500]}",
            stdout=stdout,
            stderr=stderr,
        )


def _build_python_harness(code: str, test_cases: list, entry_point: Optional[str]) -> str:
    """Build a self-contained Python test harness."""
    tc_json = json.dumps(test_cases)
    ep = entry_point or "solution"
    harness = (
        'import json\n'
        'import sys\n'
        'import traceback\n'
        '\n'
        '# ---- Learner code start ----\n'
        + code +
        '\n# ---- Learner code end ----\n'
        '\n'
        'test_cases = ' + tc_json + '\n'
        '\n'
        'passed = 0\n'
        'total = len(test_cases)\n'
        'errors = []\n'
        '\n'
        'for i, tc in enumerate(test_cases):\n'
        '    try:\n'
        '        inp = tc.get("input", {})\n'
        '        expected = tc.get("expected_output")\n'
        '        fn = None\n'
        '        try:\n'
        '            fn = eval(' + repr(ep) + ')\n'
        '        except Exception:\n'
        '            pass\n'
        '        if fn is None:\n'
        '            errors.append("Entry point ' + ep + ' not found")\n'
        '            break\n'
        '        if isinstance(inp, dict):\n'
        '            actual = fn(**inp)\n'
        '        else:\n'
        '            actual = fn(inp)\n'
        '        if actual == expected:\n'
        '            passed += 1\n'
        '        else:\n'
        '            errors.append(f"TC{i+1}: got {actual!r}, expected {expected!r}")\n'
        '    except Exception:\n'
        '        errors.append(f"TC{i+1} error: {traceback.format_exc()}")\n'
        '\n'
        'print(json.dumps({"passed": passed, "total": total, "error": "; ".join(errors) if errors else None}))\n'
    )
    return harness


def _build_sql_harness(sql_code: str, schema_sql: str, fixture_data: list, table_name: str, expected: list) -> str:
    fixture_json = json.dumps(fixture_data)
    expected_json = json.dumps(expected)
    return (
        'import json\n'
        'import sys\n'
        'try:\n'
        '    import duckdb\n'
        'except ImportError:\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": "duckdb not installed in runner"}))\n'
        '    sys.exit(0)\n'
        '\n'
        'conn = duckdb.connect(":memory:")\n'
        'schema_sql = ' + repr(schema_sql) + '\n'
        'fixture_data = ' + fixture_json + '\n'
        'table_name = ' + repr(table_name) + '\n'
        'expected = ' + expected_json + '\n'
        'sql_code = ' + repr(sql_code) + '\n'
        '\n'
        'try:\n'
        '    conn.execute(schema_sql)\n'
        '    import pandas as pd\n'
        '    df = pd.DataFrame(fixture_data)\n'
        '    conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")\n'
        '    result_df = conn.execute(sql_code).df()\n'
        '    actual = result_df.to_dict(orient="records")\n'
        '\n'
        '    def normalize(rows):\n'
        '        return sorted([{str(k): v for k, v in r.items()} for r in rows], key=lambda x: str(sorted(x.items())))\n'
        '\n'
        '    if normalize(actual) == normalize(expected):\n'
        '        print(json.dumps({"passed": 1, "total": 1, "error": None}))\n'
        '    else:\n'
        '        print(json.dumps({"passed": 0, "total": 1, "error": f"Got {actual!r}, expected {expected!r}"}))\n'
        'except Exception as e:\n'
        '    import traceback\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": traceback.format_exc()}))\n'
    )


def _build_pandas_harness(code: str, fixture_data: list, expected: list) -> str:
    fixture_json = json.dumps(fixture_data)
    expected_json = json.dumps(expected)
    return (
        'import json\n'
        'import sys\n'
        'try:\n'
        '    import pandas as pd\n'
        'except ImportError:\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": "pandas not installed"}))\n'
        '    sys.exit(0)\n'
        '\n'
        'fixture_data = ' + fixture_json + '\n'
        'expected = ' + expected_json + '\n'
        '\n'
        '# ---- Learner code start ----\n'
        + code +
        '\n# ---- Learner code end ----\n'
        '\n'
        'try:\n'
        '    df = pd.DataFrame(fixture_data)\n'
        '    actual_df = solution(df)\n'
        '    actual = actual_df.to_dict(orient="records")\n'
        '\n'
        '    def normalize(rows):\n'
        '        return sorted([{str(k): v for k, v in r.items()} for r in rows], key=lambda x: str(sorted(x.items())))\n'
        '\n'
        '    if normalize(actual) == normalize(expected):\n'
        '        print(json.dumps({"passed": 1, "total": 1, "error": None}))\n'
        '    else:\n'
        '        print(json.dumps({"passed": 0, "total": 1, "error": f"Got {actual}, expected {expected}"}))\n'
        'except Exception:\n'
        '    import traceback\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": traceback.format_exc()}))\n'
    )


def _build_polars_harness(code: str, fixture_data: list, expected: list) -> str:
    fixture_json = json.dumps(fixture_data)
    expected_json = json.dumps(expected)
    return (
        'import json\n'
        'import sys\n'
        'try:\n'
        '    import polars as pl\n'
        'except ImportError:\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": "polars not installed"}))\n'
        '    sys.exit(0)\n'
        '\n'
        'fixture_data = ' + fixture_json + '\n'
        'expected = ' + expected_json + '\n'
        '\n'
        '# ---- Learner code start ----\n'
        + code +
        '\n# ---- Learner code end ----\n'
        '\n'
        'try:\n'
        '    df = pl.DataFrame(fixture_data)\n'
        '    actual_df = solution(df)\n'
        '    actual = actual_df.to_dicts()\n'
        '\n'
        '    def normalize(rows):\n'
        '        return sorted([{str(k): v for k, v in r.items()} for r in rows], key=lambda x: str(sorted(x.items())))\n'
        '\n'
        '    if normalize(actual) == normalize(expected):\n'
        '        print(json.dumps({"passed": 1, "total": 1, "error": None}))\n'
        '    else:\n'
        '        print(json.dumps({"passed": 0, "total": 1, "error": f"Got {actual}, expected {expected}"}))\n'
        'except Exception:\n'
        '    import traceback\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": traceback.format_exc()}))\n'
    )


def _build_pyspark_harness(code: str, fixture_data: list, expected: list) -> str:
    fixture_json = json.dumps(fixture_data)
    expected_json = json.dumps(expected)
    return (
        'import json\n'
        'import sys\n'
        'try:\n'
        '    from pyspark.sql import SparkSession\n'
        'except ImportError:\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": "pyspark not installed"}))\n'
        '    sys.exit(0)\n'
        '\n'
        'fixture_data = ' + fixture_json + '\n'
        'expected = ' + expected_json + '\n'
        '\n'
        '# ---- Learner code start ----\n'
        + code +
        '\n# ---- Learner code end ----\n'
        '\n'
        'try:\n'
        '    spark = SparkSession.builder.master("local[1]").appName("tutor").getOrCreate()\n'
        '    df = spark.createDataFrame(fixture_data)\n'
        '    actual_df = solution(spark, df)\n'
        '    actual = [row.asDict() for row in actual_df.collect()]\n'
        '\n'
        '    def normalize(rows):\n'
        '        return sorted([{str(k): v for k, v in r.items()} for r in rows], key=lambda x: str(sorted(x.items())))\n'
        '\n'
        '    if normalize(actual) == normalize(expected):\n'
        '        print(json.dumps({"passed": 1, "total": 1, "error": None}))\n'
        '    else:\n'
        '        print(json.dumps({"passed": 0, "total": 1, "error": f"Got {actual}, expected {expected}"}))\n'
        '    spark.stop()\n'
        'except Exception:\n'
        '    import traceback\n'
        '    print(json.dumps({"passed": 0, "total": 1, "error": traceback.format_exc()}))\n'
    )
