"""DuckDB DDL statements — one CREATE TABLE IF NOT EXISTS per table."""

SCHEMA_SQL = """
-- Tracks applied migrations
CREATE TABLE IF NOT EXISTS schema_versions (
    version       INTEGER PRIMARY KEY,
    applied_at    TIMESTAMPTZ DEFAULT now(),
    description   TEXT
);

-- Tracks each import run
CREATE TABLE IF NOT EXISTS import_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name      TEXT NOT NULL,
    started_at        TIMESTAMPTZ DEFAULT now(),
    completed_at      TIMESTAMPTZ,
    records_imported  INTEGER DEFAULT 0,
    records_skipped   INTEGER DEFAULT 0,
    status            TEXT NOT NULL DEFAULT 'running',
    error_message     TEXT
);

-- Source provenance per question
CREATE TABLE IF NOT EXISTS question_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name    TEXT NOT NULL,
    original_id     TEXT,
    source_key      TEXT,
    source_file     TEXT,
    source_revision TEXT,
    source_record_index BIGINT,
    license         TEXT,
    attribution     TEXT,
    import_run_id   UUID REFERENCES import_runs(id),
    imported_at     TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS question_sources_identity_idx
    ON question_sources (dataset_name, source_key);

-- Normalized question model
CREATE TABLE IF NOT EXISTS questions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title               TEXT NOT NULL,
    question_type       TEXT NOT NULL CHECK (question_type IN ('algorithm','data_analysis')),
    difficulty          TEXT NOT NULL CHECK (difficulty IN ('Beginner','Easy','Medium','Hard','Very Hard')),
    problem_statement   TEXT NOT NULL,
    constraints         TEXT,
    examples            JSON,
    supported_methods   JSON NOT NULL DEFAULT '[]',
    tags                JSON DEFAULT '[]',
    source_id           UUID REFERENCES question_sources(id),
    is_ai_generated     BOOLEAN DEFAULT false,
    is_complete         BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Licensed interview material is kept separate from executable practice questions.
CREATE TABLE IF NOT EXISTS interview_items (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id        UUID NOT NULL REFERENCES question_sources(id),
    domain           TEXT NOT NULL,
    topic            TEXT NOT NULL,
    answer_format    TEXT NOT NULL CHECK (answer_format IN ('theory','coding','mcq')),
    prompt_style     TEXT NOT NULL CHECK (prompt_style IN ('direct','scenario')),
    difficulty       TEXT NOT NULL CHECK (difficulty IN ('Beginner','Easy','Medium','Hard','Very Hard')),
    prompt           TEXT NOT NULL,
    reference_answer TEXT,
    rubric           JSON,
    method           TEXT,
    options          JSON,
    correct_option   TEXT,
    tags             JSON NOT NULL DEFAULT '[]',
    content_hash     TEXT NOT NULL UNIQUE,
    is_complete      BOOLEAN NOT NULL DEFAULT true,
    created_at       TIMESTAMPTZ DEFAULT now()
);

-- Schema + fixture data for data-analysis questions
CREATE TABLE IF NOT EXISTS question_assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     UUID NOT NULL REFERENCES questions(id),
    asset_type      TEXT NOT NULL CHECK (asset_type IN ('schema','fixture_data','expected_result','starter_code')),
    method          TEXT,
    content         TEXT NOT NULL,
    content_type    TEXT NOT NULL DEFAULT 'text'
);

-- Reference solutions
CREATE TABLE IF NOT EXISTS reference_solutions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id      UUID NOT NULL REFERENCES questions(id),
    method           TEXT NOT NULL,
    code             TEXT NOT NULL,
    language         TEXT NOT NULL DEFAULT 'python',
    is_from_dataset  BOOLEAN DEFAULT true,
    explanation      TEXT
);

-- Test cases
CREATE TABLE IF NOT EXISTS question_test_cases (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id      UUID NOT NULL REFERENCES questions(id),
    input_data       JSON,
    expected_output  JSON,
    is_example       BOOLEAN DEFAULT false
);

-- AI-generated question metadata
CREATE TABLE IF NOT EXISTS ai_generated_questions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         UUID NOT NULL REFERENCES questions(id),
    provider            TEXT NOT NULL,
    model_id            TEXT NOT NULL,
    generated_at        TIMESTAMPTZ DEFAULT now(),
    prompt_version      TEXT,
    generation_metadata JSON
);

-- Learner attempts
CREATE TABLE IF NOT EXISTS attempts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         UUID NOT NULL REFERENCES questions(id),
    attempted_at        TIMESTAMPTZ DEFAULT now(),
    method              TEXT NOT NULL,
    submitted_code      TEXT NOT NULL,
    deterministic_test_result TEXT NOT NULL DEFAULT 'not_run',
    test_result         TEXT CHECK (test_result IN ('passed','failed','error','timeout','pending')),
    tests_passed        INTEGER,
    tests_total         INTEGER,
    percentage_correct  DOUBLE,
    marks               DOUBLE,
    ai_feedback         TEXT,
    error_details       TEXT,
    solution_viewed     BOOLEAN DEFAULT false,
    provider            TEXT,
    model_id            TEXT
);

-- Records when a learner views a solution
CREATE TABLE IF NOT EXISTS solution_views (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     UUID NOT NULL REFERENCES questions(id),
    attempt_id      UUID REFERENCES attempts(id),
    viewed_at       TIMESTAMPTZ DEFAULT now(),
    methods_viewed  JSON DEFAULT '[]'
);

-- Quiz attempts are intentionally separate from normal practice attempts
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'preparing',
    question_source TEXT NOT NULL,
    question_type   TEXT NOT NULL,
    difficulty      TEXT NOT NULL,
    topic           TEXT NOT NULL DEFAULT 'general',
    method          TEXT NOT NULL,
    total_items     INTEGER NOT NULL,
    coding_items    INTEGER NOT NULL,
    mcq_items       INTEGER NOT NULL,
    percentage_correct DOUBLE,
    marks           DOUBLE,
    passed          BOOLEAN,
    provider        TEXT,
    model_id        TEXT,
    error_details   TEXT
);

CREATE TABLE IF NOT EXISTS quiz_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_attempt_id     UUID NOT NULL REFERENCES quiz_attempts(id),
    position            INTEGER NOT NULL,
    question_id         UUID NOT NULL REFERENCES questions(id),
    answer_format       TEXT NOT NULL,
    method              TEXT NOT NULL,
    prompt_snapshot     TEXT,
    options             JSON,
    correct_option_id   TEXT,
    explanation         TEXT,
    answer_text         TEXT,
    selected_option_id  TEXT,
    item_status         TEXT NOT NULL DEFAULT 'pending',
    percentage_correct  DOUBLE,
    marks               DOUBLE,
    ai_feedback         TEXT,
    provider            TEXT,
    model_id            TEXT,
    error_details       TEXT,
    UNIQUE (quiz_attempt_id, position),
    UNIQUE (quiz_attempt_id, question_id)
);
"""
