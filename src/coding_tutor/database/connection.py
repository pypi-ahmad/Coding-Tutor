"""DuckDB connection management for the independent application catalogs."""
from __future__ import annotations

import os
from contextvars import ContextVar
from pathlib import Path

import duckdb

_active_path: ContextVar[str | None] = ContextVar("coding_tutor_db_path", default=None)
_connections: dict[str, duckdb.DuckDBPyConnection] = {}


def set_active_db(path: str | Path | None) -> None:
    """Set the default database for the current Streamlit script run."""
    _active_path.set(str(path) if path is not None else None)


def _resolved_path(path: str | Path | None) -> str:
    selected = path or _active_path.get() or os.environ.get("CODING_TUTOR_DB") or "coding_tutor.duckdb"
    if str(selected) == ":memory:":
        return ":memory:"
    return str(Path(selected).resolve())


def get_db(path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return one migrated connection per resolved database path."""
    db_path = _resolved_path(path)
    if db_path not in _connections:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = duckdb.connect(db_path)
        from coding_tutor.database.migrations import run_migrations

        run_migrations(connection)
        _connections[db_path] = connection
    return _connections[db_path]


def get_test_db() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection for tests."""
    conn = duckdb.connect(":memory:")
    from coding_tutor.database.migrations import run_migrations
    run_migrations(conn)
    return conn


def reset_connection(path: str | Path | None = None) -> None:
    """Close one connection, or every cached connection when no path is supplied."""
    keys = [_resolved_path(path)] if path is not None else list(_connections)
    for key in keys:
        connection = _connections.pop(key, None)
        if connection is None:
            continue
        try:
            connection.close()
        except Exception:
            pass
