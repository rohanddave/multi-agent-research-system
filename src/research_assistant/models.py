from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Evidence:
    document: Document
    score: float


@dataclass(frozen=True)
class ResearchAnswer:
    question: str
    answer: str
    citations: list[str]
    evidence: list[Evidence]
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    pipeline: str = "unknown"
