from __future__ import annotations

from collections import Counter

from .llm import LLMClient
from .models import Document, Evidence, ResearchAnswer
from .utils import compact_sentence, content_tokens, extract_claims, tokenize


class SearchAgent:
    """Lexical retriever used as a deterministic local search agent."""

    def __init__(self, corpus: list[Document]):
        self.corpus = corpus

    def search(self, question: str, top_k: int = 3, min_score_ratio: float = 0.4) -> list[Evidence]:
        query_terms = Counter(content_tokens(question))
        scored = []
        for doc in self.corpus:
            doc_terms = Counter(content_tokens(" ".join([doc.title, doc.text, " ".join(doc.tags)])))
            overlap = sum(min(count, doc_terms[term]) for term, count in query_terms.items())
            if overlap:
                score = overlap / max(1, len(query_terms))
                scored.append(Evidence(document=doc, score=score))
        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        if not ranked:
            return []
        cutoff = ranked[0].score * min_score_ratio
        return [item for item in ranked if item.score >= cutoff][:top_k]


class SummarizationAgent:
    """Creates short source-grounded notes from retrieved evidence."""

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm

    def summarize(self, question: str, evidence: list[Evidence]) -> list[str]:
        if self.llm:
            return self._summarize_with_llm(question, evidence)

        notes = []
        for item in evidence:
            sentence = compact_sentence(item.document.text)
            notes.append(f"[{item.document.id}] {sentence}")
        return notes

    def _summarize_with_llm(self, question: str, evidence: list[Evidence]) -> list[str]:
        if not evidence:
            return []

        evidence_text = format_evidence(evidence)
        response = self.llm.complete(
            system=(
                "You are a source-grounded summarization agent. "
                "Write one concise note per source. Preserve source ids in square brackets. "
                "Do not add facts that are not in the evidence."
            ),
            user=f"Question: {question}\n\nEvidence:\n{evidence_text}\n\nReturn bullet notes only.",
        )
        return [line.lstrip("- ").strip() for line in response.splitlines() if line.strip()]


class FactCheckingAgent:
    """Checks whether generated claims have token support in the retrieved evidence."""

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm

    def check(self, answer: str, evidence: list[Evidence]) -> tuple[list[str], list[str]]:
        if self.llm:
            llm_result = self._check_with_llm(answer, evidence)
            if llm_result:
                return llm_result

        evidence_tokens = set()
        for item in evidence:
            evidence_tokens.update(tokenize(item.document.text))

        supported = []
        unsupported = []
        for claim in extract_claims(answer):
            claim_tokens = set(tokenize(claim))
            if not claim_tokens:
                continue
            overlap = len(claim_tokens & evidence_tokens) / len(claim_tokens)
            if overlap >= 0.45:
                supported.append(claim)
            else:
                unsupported.append(claim)
        return supported, unsupported

    def _check_with_llm(self, answer: str, evidence: list[Evidence]) -> tuple[list[str], list[str]] | None:
        claims = extract_claims(answer)
        if not claims:
            return [], []

        evidence_text = format_evidence(evidence)
        claim_text = "\n".join(f"- {claim}" for claim in claims)
        response = self.llm.complete(
            system=(
                "You are a strict fact-checking agent. Classify each claim as SUPPORTED "
                "only when the evidence directly supports it. Otherwise classify it as UNSUPPORTED. "
                "Return one line per claim in the format: SUPPORTED: claim text"
            ),
            user=f"Evidence:\n{evidence_text}\n\nClaims:\n{claim_text}",
        )

        supported = []
        unsupported = []
        for line in response.splitlines():
            normalized = line.strip()
            if normalized.upper().startswith("SUPPORTED:"):
                supported.append(normalized.split(":", maxsplit=1)[1].strip())
            elif normalized.upper().startswith("UNSUPPORTED:"):
                unsupported.append(normalized.split(":", maxsplit=1)[1].strip())

        if len(supported) + len(unsupported) != len(claims):
            return None
        return supported, unsupported


class SingleAgentBaseline:
    """One-pass baseline that combines retrieval and answer writing."""

    def __init__(self, search_agent: SearchAgent, llm: LLMClient | None = None):
        self.search_agent = search_agent
        self.llm = llm

    def answer(self, question: str) -> ResearchAnswer:
        evidence = self.search_agent.search(question, top_k=1, min_score_ratio=0.8)
        if not evidence:
            return ResearchAnswer(
                question=question,
                answer="I could not find enough evidence to answer confidently.",
                citations=[],
                evidence=[],
                pipeline="single",
            )

        citations = [item.document.id for item in evidence]
        if self.llm:
            answer = self.llm.complete(
                system=(
                    "You are a single-agent research assistant. Answer using only the evidence. "
                    "Cite source ids in square brackets, and do not invent sources."
                ),
                user=f"Question: {question}\n\nEvidence:\n{format_evidence(evidence)}",
            )
            return ResearchAnswer(
                question=question,
                answer=answer,
                citations=citations,
                evidence=evidence,
                pipeline="single",
            )

        source_bits = [compact_sentence(item.document.text, max_words=18) for item in evidence]
        answer = " ".join(source_bits)
        answer += " " + " ".join(f"[{citation}]" for citation in citations)
        return ResearchAnswer(
            question=question,
            answer=answer,
            citations=citations,
            evidence=evidence,
            pipeline="single",
        )


def format_evidence(evidence: list[Evidence]) -> str:
    return "\n".join(
        f"[{item.document.id}] {item.document.title}: {item.document.text}" for item in evidence
    )
