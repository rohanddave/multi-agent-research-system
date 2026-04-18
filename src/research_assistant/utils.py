from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Document

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "how",
    "in",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
    "with",
}
TOKEN_EXPANSIONS = {
    "accuracy": ["factuality", "correctness", "evaluation"],
    "accurate": ["factual", "correct"],
    "assistant": ["assistants"],
    "assistants": ["assistant"],
    "evaluate": ["evaluation", "evaluating", "metrics"],
    "evaluating": ["evaluate", "evaluation", "metrics"],
    "evaluation": ["evaluate", "evaluating", "metrics"],
    "fact": ["factuality", "verification"],
    "factual": ["factuality", "accuracy"],
    "factuality": ["factual", "accuracy"],
    "specialized": ["specialization"],
    "specialization": ["specialized"],
}


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    tokens = [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]
    expanded = []
    for token in tokens:
        expanded.append(token)
        if token == "rag":
            expanded.extend(["retrieval", "augmented", "generation"])
        expanded.extend(TOKEN_EXPANSIONS.get(token, []))
    return expanded


def load_corpus(path: str | Path) -> list[Document]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Document(**row) for row in rows]


def load_questions(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compact_sentence(text: str, max_words: int = 28) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,") + "."


def extract_claims(answer: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    claims = []
    for sentence in sentences:
        cleaned = re.sub(r"\[[^\]]+\]", "", sentence).strip()
        if len(tokenize(cleaned)) >= 5:
            claims.append(cleaned)
    return claims
