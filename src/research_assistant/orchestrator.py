from __future__ import annotations

from .agents import FactCheckingAgent, SearchAgent, SummarizationAgent, format_evidence
from .llm import LLMClient
from .models import Document, ResearchAnswer


class ResearchOrchestrator:
    """Coordinates specialized agents for the multi-agent research workflow."""

    def __init__(
        self,
        corpus: list[Document],
        llm: LLMClient | None = None,
        summarizer_llm: LLMClient | None = None,
        orchestrator_llm: LLMClient | None = None,
        fact_checker_llm: LLMClient | None = None,
    ):
        self.llm = orchestrator_llm or llm
        self.search_agent = SearchAgent(corpus)
        self.summarization_agent = SummarizationAgent(llm=summarizer_llm or llm)
        self.fact_checking_agent = FactCheckingAgent(llm=fact_checker_llm or llm)

    def answer(self, question: str) -> ResearchAnswer:
        evidence = self.search_agent.search(question, top_k=4, min_score_ratio=0.55)
        notes = self.summarization_agent.summarize(question, evidence)
        citations = [item.document.id for item in evidence]

        if not notes:
            draft = "I could not find enough evidence to answer confidently."
        elif self.llm:
            draft = self._synthesize_with_llm(question, notes, evidence)
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

    def _synthesize_with_llm(self, question: str, notes: list[str], evidence) -> str:
        note_text = "\n".join(f"- {note}" for note in notes)
        return self.llm.complete(
            system=(
                "You are the orchestrator for a multi-agent research assistant. "
                "Write a concise answer using the summarizer notes and the original evidence. "
                "Every factual sentence should cite source ids in square brackets. "
                "Do not use information outside the evidence."
            ),
            user=(
                f"Question: {question}\n\n"
                f"Summarizer notes:\n{note_text}\n\n"
                f"Original evidence:\n{format_evidence(evidence)}"
            ),
        )
