from __future__ import annotations

from collections import Counter

from .models import Document, Evidence, ResearchAnswer
from .utils import compact_sentence, content_tokens, extract_claims, tokenize


class SearchAgent:
    """Lexical retriever used as a deterministic local search agent."""

    def __init__(self, corpus: list[Document]):
        self.corpus = corpus

    def search(self, question: str, top_k: int = 3) -> list[Evidence]:
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
        cutoff = ranked[0].score * 0.4
        return [item for item in ranked if item.score >= cutoff][:top_k]


class SummarizationAgent:
    """Creates short source-grounded notes from retrieved evidence."""

    def summarize(self, question: str, evidence: list[Evidence]) -> list[str]:
        notes = []
        for item in evidence:
            sentence = compact_sentence(item.document.text)
            notes.append(f"[{item.document.id}] {sentence}")
        return notes


class FactCheckingAgent:
    """Checks whether generated claims have token support in the retrieved evidence."""

    def check(self, answer: str, evidence: list[Evidence]) -> tuple[list[str], list[str]]:
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


class SingleAgentBaseline:
    """One-pass baseline that combines retrieval and answer writing."""

    def __init__(self, search_agent: SearchAgent):
        self.search_agent = search_agent

    def answer(self, question: str) -> ResearchAnswer:
        evidence = self.search_agent.search(question, top_k=2)
        if not evidence:
            return ResearchAnswer(
                question=question,
                answer="I could not find enough evidence to answer confidently.",
                citations=[],
                evidence=[],
                pipeline="single",
            )

        citations = [item.document.id for item in evidence]
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
