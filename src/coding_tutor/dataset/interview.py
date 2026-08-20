"""Normalization and persistence for licensed interview-question sources."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb

from coding_tutor.dataset.normalization import SourceMetadata


@dataclass(frozen=True)
class InterviewItem:
    source: SourceMetadata
    domain: str
    topic: str
    prompt: str
    answer_format: str = "theory"
    prompt_style: str = "direct"
    difficulty: str = "Medium"
    reference_answer: str | None = None
    rubric: object | None = None
    method: str | None = None
    options: object | None = None
    correct_option: str | None = None
    tags: tuple[str, ...] = ()

    @property
    def content_hash(self) -> str:
        text = re.sub(r"\s+", " ", self.prompt).strip().casefold()
        return hashlib.sha256(f"{self.domain}\0{text}".encode()).hexdigest()


def persist_interview_item(conn: duckdb.DuckDBPyConnection, item: InterviewItem) -> tuple[bool, bool]:
    """Insert one interview item and its provenance atomically."""
    prompt = item.prompt.strip()
    if not prompt:
        return False, True
    if conn.execute("SELECT 1 FROM interview_items WHERE content_hash=?", [item.content_hash]).fetchone():
        return True, True
    conn.begin()
    try:
        source = conn.execute(
            """INSERT INTO question_sources
               (dataset_name, original_id, source_key, source_file, source_revision,
                source_record_index, license, attribution, import_run_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (dataset_name, source_key) DO NOTHING RETURNING id""",
            [item.source.dataset_name, item.source.original_id, item.source.source_key,
             item.source.source_file, item.source.source_revision,
             item.source.source_record_index, item.source.license,
             item.source.attribution, item.source.import_run_id],
        ).fetchone()
        if source is None:
            conn.rollback()
            return True, True
        conn.execute(
            """INSERT INTO interview_items
               (source_id, domain, topic, answer_format, prompt_style, difficulty,
                prompt, reference_answer, rubric, method, options, correct_option,
                tags, content_hash, is_complete)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [source[0], item.domain, item.topic, item.answer_format, item.prompt_style,
             item.difficulty, prompt, item.reference_answer,
             json.dumps(item.rubric) if item.rubric is not None else None, item.method,
             json.dumps(item.options) if item.options is not None else None,
             item.correct_option, json.dumps(item.tags), item.content_hash,
             bool(item.reference_answer or item.answer_format == "coding")],
        )
        conn.commit()
        return True, False
    except Exception:
        conn.rollback()
        raise


def parse_30_seconds(path: Path, revision: str | None, run_id: str) -> list[InterviewItem]:
    records = json.loads(path.read_text(encoding="utf-8"))
    levels = {0: "Beginner", 1: "Medium", 2: "Hard"}
    items = []
    for index, record in enumerate(records):
        prompt = record.get("question", "").strip()
        if not prompt:
            continue
        source = _source("30-seconds-of-interviews", path, revision, run_id, index, "MIT", prompt)
        answer = record.get("answer")
        if isinstance(answer, list):
            answer = "\n\n".join(map(str, answer))
        items.append(InterviewItem(source, "software-engineering", _first_tag(record), prompt,
            difficulty=levels.get(record.get("expertise"), "Medium"), reference_answer=answer,
            tags=tuple(str(tag) for tag in record.get("tags", []))))
    return items


def parse_markdown(path: Path, dataset: str, revision: str | None, run_id: str,
                   license_name: str, domain: str) -> list[InterviewItem]:
    """Conservative Markdown parser: headings establish topics; bold/numbered lines are prompts."""
    topic = path.stem.replace("-", " ")
    items: list[InterviewItem] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        heading = re.match(r"^#{2,4}\s+(.+)", line)
        if heading:
            topic = re.sub(r"[*_`]", "", heading.group(1)).strip()
            continue
        match = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(?:\*\*)?(.+?)(?:\*\*)?\s*$", line)
        bold = re.match(r"^\s*\*\*(.+?\??)\*\*\s*$", line)
        prompt = (match or bold).group(1).strip() if (match or bold) else ""
        prompt = re.sub(r"\*\*|`", "", prompt).strip()
        if len(prompt) < 15 or not ("?" in prompt or re.match(r"(?i)^(design|describe|explain|tell|how|what|why)", prompt)):
            continue
        style = "scenario" if re.match(r"(?i)^(design|tell me|imagine|suppose|you are)", prompt) else "direct"
        fmt = "coding" if re.search(r"(?i)\b(code|implement|query|function|algorithm)\b", prompt) else "theory"
        method = "sql" if re.search(r"(?i)\bsql\b", prompt) else None
        source = _source(dataset, path, revision, run_id, index, license_name, prompt)
        items.append(InterviewItem(source, domain, topic, prompt, fmt, style, method=method))
    return items


def _first_tag(record: dict) -> str:
    tags = record.get("tags") or []
    return str(tags[0]) if tags else "general"


def _source(dataset: str, path: Path, revision: str | None, run_id: str, index: int,
            license_name: str, prompt: str) -> SourceMetadata:
    key = hashlib.sha256(f"{dataset}\0{path.as_posix()}\0{index}\0{prompt}".encode()).hexdigest()
    return SourceMetadata(dataset, key, path.as_posix(), str(index), revision, index,
                          license_name, dataset, run_id)
