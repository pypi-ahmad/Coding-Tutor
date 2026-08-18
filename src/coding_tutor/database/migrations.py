"""Schema migration system for DuckDB."""
import duckdb
from coding_tutor.database.schema import SCHEMA_SQL


MIGRATIONS: list[tuple[int, str, str]] = [
    (
        1,
        "initial schema",
        SCHEMA_SQL,
    ),
    (
        2,
        "AI assessment lifecycle",
        """ALTER TABLE attempts ADD COLUMN assessment_status TEXT;
        UPDATE attempts SET assessment_status = CASE
          WHEN test_result IS NULL THEN NULL
          ELSE 'legacy_' || test_result
        END WHERE assessment_status IS NULL;""",
    ),
    (
        3,
        "dataset source identity and revision provenance",
        """ALTER TABLE question_sources ADD COLUMN IF NOT EXISTS source_key TEXT;
        ALTER TABLE question_sources ADD COLUMN IF NOT EXISTS source_revision TEXT;
        ALTER TABLE question_sources ADD COLUMN IF NOT EXISTS source_record_index BIGINT;
        UPDATE question_sources
        SET source_key = 'legacy:' || CAST(id AS VARCHAR)
        WHERE source_key IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS question_sources_identity_idx
            ON question_sources (dataset_name, source_key);""",
    ),
    (
        4,
        "explicit deterministic verification status",
        """ALTER TABLE attempts
               ADD COLUMN IF NOT EXISTS deterministic_test_result TEXT DEFAULT 'not_run';
           UPDATE attempts
               SET deterministic_test_result = 'not_run'
               WHERE deterministic_test_result IS NULL;""",
    ),
    (
        5,
        "separate resumable quiz attempts and items",
        """CREATE TABLE IF NOT EXISTS quiz_attempts (
               id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
               started_at TIMESTAMPTZ DEFAULT now(),
               completed_at TIMESTAMPTZ,
               status TEXT NOT NULL DEFAULT 'preparing',
               question_source TEXT NOT NULL,
               question_type TEXT NOT NULL,
               difficulty TEXT NOT NULL,
               topic TEXT NOT NULL DEFAULT 'general',
               method TEXT NOT NULL,
               total_items INTEGER NOT NULL,
               coding_items INTEGER NOT NULL,
               mcq_items INTEGER NOT NULL,
               percentage_correct DOUBLE,
               marks DOUBLE,
               passed BOOLEAN,
               provider TEXT,
               model_id TEXT,
               error_details TEXT
           );
           CREATE TABLE IF NOT EXISTS quiz_items (
               id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
               quiz_attempt_id UUID NOT NULL REFERENCES quiz_attempts(id),
               position INTEGER NOT NULL,
               question_id UUID NOT NULL REFERENCES questions(id),
               answer_format TEXT NOT NULL,
               method TEXT NOT NULL,
               prompt_snapshot TEXT,
               options JSON,
               correct_option_id TEXT,
               explanation TEXT,
               answer_text TEXT,
               selected_option_id TEXT,
               item_status TEXT NOT NULL DEFAULT 'pending',
               percentage_correct DOUBLE,
               marks DOUBLE,
               ai_feedback TEXT,
               provider TEXT,
               model_id TEXT,
               error_details TEXT,
               UNIQUE (quiz_attempt_id, position),
               UNIQUE (quiz_attempt_id, question_id)
           );""",
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
        conn.execute("BEGIN TRANSACTION")
        try:
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
                [version, description],
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_schema_version(conn: duckdb.DuckDBPyConnection) -> int:
    """Return the highest applied migration version."""
    result = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_versions").fetchone()
    return result[0] if result else 0
