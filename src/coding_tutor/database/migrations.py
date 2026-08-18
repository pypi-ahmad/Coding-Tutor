"""Schema migration system for DuckDB."""
import duckdb
from coding_tutor.database.schema import SCHEMA_SQL


MIGRATIONS: list[tuple[int, str, str]] = [
    (
        1,
        "initial schema",
        SCHEMA_SQL,
    ),
    # Future migrations appended here as (version, description, sql)
]


def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Apply any unapplied migrations idempotently."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version       INTEGER PRIMARY KEY,
            applied_at    TIMESTAMPTZ DEFAULT now(),
            description   TEXT
        )
    """)

    applied = {row[0] for row in conn.execute("SELECT version FROM schema_versions").fetchall()}

    for version, description, sql in MIGRATIONS:
        if version in applied:
            continue
        conn.execute(sql)
        conn.execute(
            "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
            [version, description],
        )

    conn.commit()


def get_schema_version(conn: duckdb.DuckDBPyConnection) -> int:
    """Return the highest applied migration version."""
    result = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_versions").fetchone()
    return result[0] if result else 0
