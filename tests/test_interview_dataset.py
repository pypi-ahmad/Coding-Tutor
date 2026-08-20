import json

from coding_tutor.database.connection import get_test_db
from coding_tutor.dataset.interview import InterviewItem, parse_30_seconds, persist_interview_item
from coding_tutor.dataset.normalization import SourceMetadata


def source() -> SourceMetadata:
    return SourceMetadata("licensed", "key", "questions.md", "1", "abc", 1, "MIT", "Author")


def test_persist_interview_item_is_idempotent():
    conn = get_test_db()
    item = InterviewItem(source(), "llm", "rag", "How would you evaluate retrieval?", reference_answer="Use recall@k.")
    assert persist_interview_item(conn, item) == (True, False)
    assert persist_interview_item(conn, item) == (True, True)
    assert conn.execute("SELECT count(*) FROM interview_items").fetchone()[0] == 1


def test_parse_30_seconds_maps_fields(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([{
        "question": "What is event delegation?", "answer": "Use event bubbling.",
        "expertise": 2, "tags": ["javascript", "events"]
    }]), encoding="utf-8")
    item = parse_30_seconds(path, "revision", "run")[0]
    assert (item.difficulty, item.topic, item.reference_answer) == ("Hard", "javascript", "Use event bubbling.")


def test_unlicensed_sources_are_raw_only():
    from coding_tutor.dataset.interview_catalog import SOURCES
    assert all(source.ingestion_allowed == bool(source.license) for source in SOURCES)
