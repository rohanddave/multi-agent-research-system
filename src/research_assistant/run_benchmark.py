from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .agents import SearchAgent, SingleAgentBaseline
from .evaluation import aggregate_scores, evaluate_answer
from .llm import AgentModelConfig, build_agent_llms
from .orchestrator import ResearchOrchestrator
from .reporting import write_plots, write_results_csv
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
    model_config = AgentModelConfig(
        default=model,
        single=single_model,
        summarizer=summarizer_model,
        orchestrator=orchestrator_model,
        fact_checker=fact_checker_model,
    )
    corpus = load_corpus(corpus_path)
    questions = load_questions(dataset_path)
    llms = build_agent_llms(llm_provider, model_config)
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
            started = time.perf_counter()
            answer = system.answer(row["question"])
            latency_seconds = time.perf_counter() - started
            expected_sources = row.get("expected_sources", [])
            scores = evaluate_answer(answer, row["reference_answer"], expected_sources)
            scores["latency_seconds"] = latency_seconds
            results[name].append(
                {
                    "id": row["id"],
                    "question": row["question"],
                    "answer": answer.answer,
                    "citations": answer.citations,
                    "retrieved_sources": [item.document.id for item in answer.evidence],
                    "expected_sources": expected_sources,
                    "supported_claims": answer.supported_claims,
                    "unsupported_claims": answer.unsupported_claims,
                    "latency_seconds": latency_seconds,
                    "scores": scores,
                }
            )

    return {
        "metadata": {
            "llm_provider": llm_provider,
            "models": {
                "default": model_config.default,
                "single": model_config.model_for("single"),
                "summarizer": model_config.model_for("summarizer"),
                "orchestrator": model_config.model_for("orchestrator"),
                "fact_checker": model_config.model_for("fact_checker"),
            },
            "num_questions": len(questions),
        },
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
    parser.add_argument("--no-plots", action="store_true", help="Skip matplotlib plot generation.")
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
    csv_path = out_path.with_suffix(".csv")
    write_results_csv(report, csv_path)
    plot_paths = []
    if not args.no_plots:
        plot_paths = write_plots(report, out_path.parent)

    print(json.dumps(report["summary"], indent=2))
    print(f"\nWrote full report to {out_path}")
    print(f"Wrote CSV results to {csv_path}")
    for plot_path in plot_paths:
        print(f"Wrote plot to {plot_path}")


if __name__ == "__main__":
    main()
