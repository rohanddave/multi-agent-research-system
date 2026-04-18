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
    support = claim_support_breakdown(answer)
    return support["claim_support"]


def claim_support_breakdown(answer: ResearchAnswer) -> dict[str, float | int]:
    claims = extract_claims(answer.answer)
    if not claims:
        return {
            "claim_support": 0.0,
            "supported_claim_count": 0,
            "unsupported_claim_count": 0,
            "unsupported_claim_rate": 0.0,
        }

    evidence_tokens = set()
    for item in answer.evidence:
        evidence_tokens.update(tokenize(item.document.text))

    scores = []
    unsupported = 0
    for claim in claims:
        claim_tokens = set(tokenize(claim))
        if not claim_tokens:
            continue
        score = len(claim_tokens & evidence_tokens) / len(claim_tokens)
        scores.append(score)
        if score < 0.45:
            unsupported += 1

    supported = max(0, len(scores) - unsupported)
    return {
        "claim_support": mean(scores) if scores else 0.0,
        "supported_claim_count": supported,
        "unsupported_claim_count": unsupported,
        "unsupported_claim_rate": unsupported / len(scores) if scores else 0.0,
    }


def reference_overlap(answer_text: str, reference_answer: str) -> float:
    answer_tokens = set(tokenize(answer_text))
    reference_tokens = set(tokenize(reference_answer))
    if not reference_tokens:
        return 0.0
    return len(answer_tokens & reference_tokens) / len(reference_tokens)


def retrieval_recall(answer: ResearchAnswer, expected_sources: list[str]) -> float:
    if not expected_sources:
        return 0.0
    retrieved_ids = {item.document.id for item in answer.evidence}
    expected = set(expected_sources)
    return len(retrieved_ids & expected) / len(expected)


def citation_recall(answer: ResearchAnswer, expected_sources: list[str]) -> float:
    if not expected_sources:
        return 0.0
    expected = set(expected_sources)
    cited = set(answer.citations)
    return len(cited & expected) / len(expected)


def citation_precision(answer: ResearchAnswer, expected_sources: list[str]) -> float:
    if not answer.citations:
        return 0.0
    if not expected_sources:
        return citation_coverage(answer)
    expected = set(expected_sources)
    useful = sum(1 for citation in answer.citations if citation in expected)
    return useful / len(answer.citations)


def answer_conciseness(answer_text: str, target_words: int = 90) -> float:
    words = tokenize(answer_text)
    if not words:
        return 0.0
    ratio = len(words) / target_words
    return min(ratio, 1 / ratio)


def evaluate_answer(
    answer: ResearchAnswer,
    reference_answer: str,
    expected_sources: list[str] | None = None,
) -> dict[str, float]:
    expected_sources = expected_sources or []
    support = claim_support_breakdown(answer)
    scores = {
        "citation_coverage": citation_coverage(answer),
        "retrieval_recall": retrieval_recall(answer, expected_sources),
        "citation_precision": citation_precision(answer, expected_sources),
        "citation_recall": citation_recall(answer, expected_sources),
        "claim_support": float(support["claim_support"]),
        "unsupported_claim_rate": float(support["unsupported_claim_rate"]),
        "reference_overlap": reference_overlap(answer.answer, reference_answer),
        "answer_conciseness": answer_conciseness(answer.answer),
    }
    scores["overall"] = mean(
        [
            scores["citation_precision"],
            scores["citation_recall"],
            scores["claim_support"],
            1 - scores["unsupported_claim_rate"],
            scores["reference_overlap"],
        ]
    )
    return scores


def aggregate_scores(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {}
    metric_names = rows[0]["scores"].keys()
    return {
        metric: mean(row["scores"][metric] for row in rows)
        for metric in metric_names
    }
