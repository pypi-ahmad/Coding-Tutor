"""Parse the user-selected AI Engineering Field Guide interview sections."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from coding_tutor.dataset.interview import InterviewItem
from coding_tutor.dataset.normalization import SourceMetadata


SECTION_RULES = {
    "01-theory.md": {
        "LLM Practice", "RAG Systems", "Agents and Tool Use", "Testing and Evaluation",
        "Monitoring", "Cost and Latency Optimization", "Safety and Guardrails",
        "Fine-tuning and Training", "LLM Theory",
    },
    "02-coding.md": {"Implementation Rounds", "ML / AI Coding", "Algorithm Rounds"},
    "03-project-deep-dive.md": {"Questions", "Follow-up Probes"},
    "04-ai-system-design.md": {
        "Questions", "Typical AI System Design Questions",
        "Near-AI / AI Serving Systems / Platforms (more Engineering)",
        "ML system design", "Traditional system design",
    },
    "05-behavioral.md": {"Common Behavioral Questions"},
    "06-home-assignments.md": {"Assignment Examples", "June 2026 Additions"},
}

FILE_METADATA = {
    "01-theory.md": ("ai-theory", "theory", "direct"),
    "02-coding.md": ("coding", "coding", "direct"),
    "03-project-deep-dive.md": ("project-deep-dive", "theory", "scenario"),
    "04-ai-system-design.md": ("ai-system-design", "theory", "scenario"),
    "05-behavioral.md": ("behavioral", "theory", "scenario"),
    "06-home-assignments.md": ("home-assignment", "coding", "scenario"),
}


def parse_selected_ai_questions(path: Path, revision: str, run_id: str) -> list[InterviewItem]:
    """Extract only prompt bullets from explicitly selected sections."""
    allowed = SECTION_RULES[path.name]
    topic, answer_format, default_style = FILE_METADATA[path.name]
    h2 = h3 = ""
    items: list[InterviewItem] = []
    for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines()):
        heading = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if heading:
            value = _clean(heading.group(2))
            if len(heading.group(1)) == 2:
                h2, h3 = value, ""
            else:
                h3 = value
            continue
        bullet = re.match(r"^\s*-\s+(.+?)\s*$", line)
        section = h3 or h2
        if not bullet or h2 == "Sources" or not ({h2, h3} & allowed):
            continue
        if h3 == "Evaluation Criteria Found in Assignments":
            continue
        prompt = _clean(bullet.group(1))
        if len(prompt) < 8 or _is_non_prompt(prompt):
            continue
        style = default_style
        if re.match(r"(?i)^(how|what|when|why|explain|describe|tell|design|build|implement|refactor|debug|scale|estimate)", prompt):
            style = "scenario" if re.match(r"(?i)^(describe|tell|design|build|implement|refactor|debug|scale|estimate|your|you're)", prompt) else default_style
        key = hashlib.sha256(f"user-ai-interview\0{path.name}\0{index}\0{prompt}".encode()).hexdigest()
        source = SourceMetadata(
            dataset_name="user-provided-ai-engineering-interview-questions",
            source_key=key,
            source_file=f"interview_sources/raw/ai-engineering-field-guide/interview/questions/{path.name}",
            original_id=f"{path.stem}:{index}",
            source_revision=revision,
            source_record_index=index,
            license=None,
            attribution="User-selected local import; source: alexeygrigorev/ai-engineering-field-guide (no declared license)",
            import_run_id=run_id,
        )
        items.append(InterviewItem(
            source=source, domain="ai-engineering", topic=section or topic,
            prompt=prompt, answer_format=answer_format, prompt_style=style,
            difficulty="Medium", tags=(topic, section or topic),
        ))
    return items


def _clean(value: str) -> str:
    value = re.sub(r"\[\^.+?\]", "", value)
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    return re.sub(r"\s+", " ", value).strip().rstrip()


def _is_non_prompt(prompt: str) -> bool:
    prefixes = (
        "Implementation rounds (", "Algorithm rounds (", "Solve 75+", "Focus on data structures",
        "Traditional ML focuses", "AI/LLM system design focuses",
    )
    return prompt.startswith(prefixes)
