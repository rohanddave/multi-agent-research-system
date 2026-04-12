from __future__ import annotations

from statistics import mean

from .models import ResearchAnswer
from .utils import extract_claims, tokenize


def citation_coverage(answer: ResearchAnswer) -> float:
    if not answer.citations:
        return 0.0
    retrieved_ids = {item.document.id for item in answer.evidence}
    valid = sum(1 for citation in answer.citations if citation in retrieved_ids)
    return valid / len(answer.citations)


def claim_support(answer: ResearchAnswer) -> float:
    claims = extract_claims(answer.answer)
    if not claims:
        return 0.0

    evidence_tokens = set()
    for item in answer.evidence:
        evidence_tokens.update(tokenize(item.document.text))

    scores = []
    for claim in claims:
        claim_tokens = set(tokenize(claim))
        if not claim_tokens:
            continue
        scores.append(len(claim_tokens & evidence_tokens) / len(claim_tokens))
    return mean(scores) if scores else 0.0


def reference_overlap(answer_text: str, reference_answer: str) -> float:
    answer_tokens = set(tokenize(answer_text))
    reference_tokens = set(tokenize(reference_answer))
    if not reference_tokens:
        return 0.0
    return len(answer_tokens & reference_tokens) / len(reference_tokens)


def evaluate_answer(answer: ResearchAnswer, reference_answer: str) -> dict[str, float]:
    scores = {
        "citation_coverage": citation_coverage(answer),
        "claim_support": claim_support(answer),
        "reference_overlap": reference_overlap(answer.answer, reference_answer),
    }
    scores["overall"] = mean(scores.values())
    return scores


def aggregate_scores(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {}
    metric_names = rows[0]["scores"].keys()
    return {
        metric: mean(row["scores"][metric] for row in rows)
        for metric in metric_names
    }
