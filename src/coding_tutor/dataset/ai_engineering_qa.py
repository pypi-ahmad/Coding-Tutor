"""Importer for the Apache-2.0 AI Engineering Interview Questions repository."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from coding_tutor.dataset.interview import InterviewItem
from coding_tutor.dataset.normalization import SourceMetadata


CATEGORIES = {
    "LLM Fundamentals", "Prompt Engineering", "Retrieval-Augmented Generation (RAG)",
    "AI Agents and Agentic Systems", "Fine-Tuning and Model Adaptation",
    "Vector Databases and Embeddings", "AI System Design", "LLMOps and Production AI",
    "Evaluation and Testing", "AI Safety, Ethics, and Responsible AI", "Multimodal AI",
    "AI Infrastructure and Scalability", "Coding and Practical Implementation",
    "Behavioral and Scenario-Based Questions",
}


def parse_ai_engineering_qa(path: Path, revision: str, run_id: str) -> list[InterviewItem]:
    category = ""
    pending: tuple[int, str, str | None] | None = None
    items: list[InterviewItem] = []

    def flush() -> None:
        nonlocal pending
        if pending is None:
            return
        index, prompt, answer = pending
        fmt = "coding" if category == "Coding and Practical Implementation" else "theory"
        scenario = bool(re.match(
            r"(?i)^(your|you |design|build|implement|write|describe|tell|a user|an external|one |radiologists)",
            prompt,
        ))
        key = hashlib.sha256(f"ai-engineering-qa\0{index}\0{prompt}".encode()).hexdigest()
        source = SourceMetadata(
            "ai-engineering-interview-questions", key, path.as_posix(), str(index),
            revision, index, "Apache-2.0",
            "AI Engineering Interview Questions by Amit Shekhar / Outcome School", run_id,
        )
        items.append(InterviewItem(
            source, "ai-engineering", category, prompt, fmt,
            "scenario" if scenario else "direct", "Medium", answer,
            tags=("ai-engineering", category),
        ))
        pending = None

    for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines()):
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            flush()
            candidate = _plain(heading.group(1))
            category = candidate if candidate in CATEGORIES else ""
            continue
        question = re.match(r"^-\s+(.+?)\s*$", line)
        answer = re.match(r"^\s{2,}-\s+Answer:\s*(.+?)\s*$", line)
        if answer and pending:
            pending = (pending[0], pending[1], _answer(answer.group(1)))
        elif question and category:
            flush()
            prompt = _plain(question.group(1))
            if len(prompt) >= 8:
                pending = (index, prompt, None)
    flush()
    return items


def _plain(value: str) -> str:
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    return re.sub(r"[*_`]", "", value).strip()


def _answer(value: str) -> str:
    return re.sub(r"\[([^]]+)]\(([^)]+)\)", r"\1 (\2)", value).strip()
