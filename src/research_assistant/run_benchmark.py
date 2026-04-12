from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import SearchAgent, SingleAgentBaseline
from .evaluation import aggregate_scores, evaluate_answer
from .orchestrator import ResearchOrchestrator
from .utils import load_corpus, load_questions


def run_benchmark(corpus_path: str, dataset_path: str) -> dict:
    corpus = load_corpus(corpus_path)
    questions = load_questions(dataset_path)
    baseline = SingleAgentBaseline(SearchAgent(corpus))
    multi_agent = ResearchOrchestrator(corpus)

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
    args = parser.parse_args()

    report = run_benchmark(args.corpus, args.dataset)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(f"\nWrote full report to {out_path}")


if __name__ == "__main__":
    main()
