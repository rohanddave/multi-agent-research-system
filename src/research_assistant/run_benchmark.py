from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import SearchAgent, SingleAgentBaseline
from .evaluation import aggregate_scores, evaluate_answer
from .llm import AgentModelConfig, build_agent_llms
from .orchestrator import ResearchOrchestrator
from .utils import load_corpus, load_questions


def run_benchmark(
    corpus_path: str,
    dataset_path: str,
    llm_provider: str = "local",
    model: str | None = None,
    single_model: str | None = None,
    summarizer_model: str | None = None,
    orchestrator_model: str | None = None,
    fact_checker_model: str | None = None,
) -> dict:
    corpus = load_corpus(corpus_path)
    questions = load_questions(dataset_path)
    llms = build_agent_llms(
        llm_provider,
        AgentModelConfig(
            default=model,
            single=single_model,
            summarizer=summarizer_model,
            orchestrator=orchestrator_model,
            fact_checker=fact_checker_model,
        ),
    )
    baseline = SingleAgentBaseline(SearchAgent(corpus), llm=llms.single)
    multi_agent = ResearchOrchestrator(
        corpus,
        summarizer_llm=llms.summarizer,
        orchestrator_llm=llms.orchestrator,
        fact_checker_llm=llms.fact_checker,
    )

    results = {"single": [], "multi": []}
    for row in questions:
        for name, system in [("single", baseline), ("multi", multi_agent)]:
            answer = system.answer(row["question"])
            scores = evaluate_answer(answer, row["reference_answer"])
            results[name].append(
                {
                    "id": row["id"],
                    "question": row["question"],
                    "answer": answer.answer,
                    "citations": answer.citations,
                    "scores": scores,
                }
            )

    return {
        "summary": {
            "single": aggregate_scores(results["single"]),
            "multi": aggregate_scores(results["multi"]),
        },
        "examples": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CS6180 research assistant benchmark.")
    parser.add_argument("--corpus", default="data/corpus.json")
    parser.add_argument("--dataset", default="data/questions.json")
    parser.add_argument("--out", default="results/benchmark.json")
    parser.add_argument("--llm-provider", choices=["local", "openai"], default="local")
    parser.add_argument("--model", default=None, help="Default model for all LLM-backed agents.")
    parser.add_argument("--single-model", default=None, help="Model for the single-agent baseline.")
    parser.add_argument("--summarizer-model", default=None, help="Model for the summarization agent.")
    parser.add_argument("--orchestrator-model", default=None, help="Model for the multi-agent orchestrator.")
    parser.add_argument("--fact-checker-model", default=None, help="Model for the fact-checking agent.")
    args = parser.parse_args()

    report = run_benchmark(
        args.corpus,
        args.dataset,
        llm_provider=args.llm_provider,
        model=args.model,
        single_model=args.single_model,
        summarizer_model=args.summarizer_model,
        orchestrator_model=args.orchestrator_model,
        fact_checker_model=args.fact_checker_model,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(f"\nWrote full report to {out_path}")


if __name__ == "__main__":
    main()
