from __future__ import annotations

from .agents import FactCheckingAgent, SearchAgent, SummarizationAgent
from .models import Document, ResearchAnswer


class ResearchOrchestrator:
    """Coordinates specialized agents for the multi-agent research workflow."""

    def __init__(self, corpus: list[Document]):
        self.search_agent = SearchAgent(corpus)
        self.summarization_agent = SummarizationAgent()
        self.fact_checking_agent = FactCheckingAgent()

    def answer(self, question: str) -> ResearchAnswer:
        evidence = self.search_agent.search(question, top_k=4)
        notes = self.summarization_agent.summarize(question, evidence)
        citations = [item.document.id for item in evidence]

        if not notes:
            draft = "I could not find enough evidence to answer confidently."
        else:
            draft = self._synthesize(question, notes)

        supported, unsupported = self.fact_checking_agent.check(draft, evidence)
        if unsupported:
            draft += " Fact-check note: some claims need stronger evidence."

        return ResearchAnswer(
            question=question,
            answer=draft,
            citations=citations,
            evidence=evidence,
            supported_claims=supported,
            unsupported_claims=unsupported,
            pipeline="multi",
        )

    def _synthesize(self, question: str, notes: list[str]) -> str:
        clean_notes = []
        for note in notes:
            source, text = note.split("] ", maxsplit=1)
            clean_notes.append(f"{text} {source}]")

        return " ".join(clean_notes)
