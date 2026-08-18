"""DuckDB connection management."""
import os
import duckdb
from pathlib import Path

_DB_PATH = os.environ.get("CODING_TUTOR_DB", "coding_tutor.duckdb")
_connection: duckdb.DuckDBPyConnection | None = None


def get_db(path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Return the app-level DuckDB connection (singleton per process)."""
    global _connection
    if _connection is None:
        db_path = path or _DB_PATH
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _connection = duckdb.connect(db_path)
        from coding_tutor.database.migrations import run_migrations
        run_migrations(_connection)
    return _connection


def get_test_db() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection for tests."""
    conn = duckdb.connect(":memory:")
    from coding_tutor.database.migrations import run_migrations
    run_migrations(conn)
    return conn


def reset_connection():
    """Reset the singleton — used in tests."""
    global _connection
    if _connection:
        try:
            _connection.close()
        except Exception:
            pass
    _connection = None
