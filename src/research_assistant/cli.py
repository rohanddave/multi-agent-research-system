from __future__ import annotations

import argparse

from .agents import SearchAgent, SingleAgentBaseline
from .llm import AgentModelConfig, build_agent_llms
from .orchestrator import ResearchOrchestrator
from .utils import load_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the research assistant a question.")
    parser.add_argument("question")
    parser.add_argument("--corpus", default="data/corpus.json")
    parser.add_argument("--mode", choices=["single", "multi"], default="multi")
    parser.add_argument("--llm-provider", choices=["local", "openai"], default="local")
    parser.add_argument("--model", default=None, help="Default model for all LLM-backed agents.")
    parser.add_argument("--single-model", default=None, help="Model for the single-agent baseline.")
    parser.add_argument("--summarizer-model", default=None, help="Model for the summarization agent.")
    parser.add_argument("--orchestrator-model", default=None, help="Model for the multi-agent orchestrator.")
    parser.add_argument("--fact-checker-model", default=None, help="Model for the fact-checking agent.")
    args = parser.parse_args()

    corpus = load_corpus(args.corpus)
    llms = build_agent_llms(
        args.llm_provider,
        AgentModelConfig(
            default=args.model,
            single=args.single_model,
            summarizer=args.summarizer_model,
            orchestrator=args.orchestrator_model,
            fact_checker=args.fact_checker_model,
        ),
    )
    if args.mode == "single":
        system = SingleAgentBaseline(SearchAgent(corpus), llm=llms.single)
    else:
        system = ResearchOrchestrator(
            corpus,
            summarizer_llm=llms.summarizer,
            orchestrator_llm=llms.orchestrator,
            fact_checker_llm=llms.fact_checker,
        )

    answer = system.answer(args.question)
    print(answer.answer)
    print("\nCitations:", ", ".join(answer.citations) or "none")
    if answer.supported_claims or answer.unsupported_claims:
        print(f"Supported claims: {len(answer.supported_claims)}")
        print(f"Unsupported claims: {len(answer.unsupported_claims)}")


if __name__ == "__main__":
    main()
