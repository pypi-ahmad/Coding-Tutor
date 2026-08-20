"""Curated interview sources and their license/import policy."""
from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewSource:
    key: str
    repo: str
    paths: tuple[str, ...]
    license: str | None
    ingestion_allowed: bool


SOURCES = (
    InterviewSource("tech-interview-handbook", "yangshun/tech-interview-handbook", (
        "LICENSE", "README.md", "apps/website/contents/behavioral-interview-questions.md",
        "apps/website/contents/behavioral-interview-rubrics.md", "apps/website/contents/system-design.md"), "MIT", True),
    InterviewSource("30-seconds-of-interviews", "Chalarangelo/30-seconds-of-interviews",
        ("LICENSE", "README.md", "data/questions.json"), "MIT", True),
    InterviewSource("data-science-interviews", "alexeygrigorev/data-science-interviews",
        ("LICENSE", "README.md", "theory.md", "technical.md", "contrib/probability.md"), "CC-BY-4.0", True),
    InterviewSource("interview-questions", "pwittchen/interview-questions", (
        "LICENSE", "README.md", "java-developer.md", "javascript-developer.md",
        "google-developer.md", "general-questions.md"), "Apache-2.0", True),
    InterviewSource("ai-engineering-field-guide", "alexeygrigorev/ai-engineering-field-guide", (
        "README.md", "interview/questions/01-theory.md", "interview/questions/02-coding.md",
        "interview/questions/03-project-deep-dive.md", "interview/questions/04-ai-system-design.md",
        "interview/questions/05-behavioral.md", "interview/questions/questions.md"), None, False),
    InterviewSource("system-design", "EasyDevLearning/System-design", (
        "README.md", "Categories-of-system-design-problems.md", "SDI questions at FAANG.md",
        "grokking-system-design-interview.md", "guide.md", "system-design-interview-questions.md.md"), None, False),
    InterviewSource("machine-learning-interview", "khangich/machine-learning-interview", (
        "README.md", "appliedml.md", "design.md", "extra.md", "faqs.md", "questions.md",
        "quiz.md", "interview_experiences.md", "leetcode.md"), None, False),
    InterviewSource("ai-engineer-interview-qa", "Nareshedagotti/AI-Engineer-Interview-QA", (
        "README.md", "Agentic_AI_Interview_Questions.md", "FASTAPI_QA.md", "LLM_Interview_Questions.md",
        "RAG_QA.md", "TRANSFORMERS_QA.md"), None, False),
    InterviewSource("llm-interview-questions", "llmgenai/LLMInterviewQuestions", ("README.md",), None, False),
)

SOURCES_BY_KEY = {source.key: source for source in SOURCES}
