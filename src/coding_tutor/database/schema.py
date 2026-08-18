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
    source_file     TEXT,
    license         TEXT,
    attribution     TEXT,
    import_run_id   UUID REFERENCES import_runs(id),
    imported_at     TIMESTAMPTZ DEFAULT now()
);

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
"""
