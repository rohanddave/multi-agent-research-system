from __future__ import annotations

import argparse

from .agents import SearchAgent, SingleAgentBaseline
from .orchestrator import ResearchOrchestrator
from .utils import load_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the research assistant a question.")
    parser.add_argument("question")
    parser.add_argument("--corpus", default="data/corpus.json")
    parser.add_argument("--mode", choices=["single", "multi"], default="multi")
    args = parser.parse_args()

    corpus = load_corpus(args.corpus)
    if args.mode == "single":
        system = SingleAgentBaseline(SearchAgent(corpus))
    else:
        system = ResearchOrchestrator(corpus)

    answer = system.answer(args.question)
    print(answer.answer)
    print("\nCitations:", ", ".join(answer.citations) or "none")
    if answer.supported_claims or answer.unsupported_claims:
        print(f"Supported claims: {len(answer.supported_claims)}")
        print(f"Unsupported claims: {len(answer.unsupported_claims)}")


if __name__ == "__main__":
    main()
