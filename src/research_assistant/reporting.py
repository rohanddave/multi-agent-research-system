from __future__ import annotations

import csv
import os
from pathlib import Path


def write_results_csv(report: dict, path: str | Path) -> None:
    rows = []
    for system_name, examples in report["examples"].items():
        for example in examples:
            row = {
                "system": system_name,
                "id": example["id"],
                "question": example["question"],
                "answer": example["answer"],
                "citations": ";".join(example["citations"]),
                "retrieved_sources": ";".join(example["retrieved_sources"]),
                "expected_sources": ";".join(example["expected_sources"]),
                "latency_seconds": example["latency_seconds"],
            }
            row.update(example["scores"])
            rows.append(row)

    if not rows:
        return

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_plots(report: dict, out_dir: str | Path) -> list[str]:
    cache_dir = Path(os.getenv("MPLCONFIGDIR", "/tmp/cs6180-matplotlib"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/cs6180-cache")
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        _plot_summary_metrics(report, output_dir, plt),
        _plot_latency(report, output_dir, plt),
        _plot_unsupported_claims(report, output_dir, plt),
        _plot_claim_support(report, output_dir, plt),
    ]
    return [str(path) for path in paths]


def _plot_summary_metrics(report: dict, output_dir: Path, plt) -> Path:
    metrics = [
        "overall",
        "citation_precision",
        "citation_recall",
        "retrieval_recall",
        "claim_support",
        "reference_overlap",
    ]
    systems = list(report["summary"])
    x = range(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 5))
    for offset, system in enumerate(systems):
        values = [report["summary"][system].get(metric, 0.0) for metric in metrics]
        positions = [index + (offset - 0.5) * width for index in x]
        ax.bar(positions, values, width=width, label=system)

    ax.set_title("Single-Agent vs Multi-Agent Quality Metrics")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(list(x))
    ax.set_xticklabels([metric.replace("_", "\n") for metric in metrics])
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    path = output_dir / "summary_metrics.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _plot_latency(report: dict, output_dir: Path, plt) -> Path:
    systems = list(report["summary"])
    values = [report["summary"][system].get("latency_seconds", 0.0) for system in systems]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(systems, values, color=["#4c78a8", "#f58518"])
    ax.set_title("Average Latency Per Question")
    ax.set_ylabel("Seconds")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    path = output_dir / "latency.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _plot_unsupported_claims(report: dict, output_dir: Path, plt) -> Path:
    systems = list(report["summary"])
    values = [report["summary"][system].get("unsupported_claim_rate", 0.0) for system in systems]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(systems, values, color=["#e45756", "#54a24b"])
    ax.set_title("Unsupported Claim Rate")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)

    for bar, value in zip(bars, values):
        label_y = max(value + 0.03, 0.04)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            label_y,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    if all(value == 0 for value in values):
        ax.text(
            0.5,
            0.55,
            "No unsupported claims detected\nby the current evaluator.",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#999999"},
        )

    fig.tight_layout()

    path = output_dir / "unsupported_claim_rate.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _plot_claim_support(report: dict, output_dir: Path, plt) -> Path:
    systems = list(report["summary"])
    values = [report["summary"][system].get("claim_support", 0.0) for system in systems]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(systems, values, color=["#4c78a8", "#54a24b"])
    ax.set_title("Claim Support")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            min(value + 0.03, 1.02),
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()

    path = output_dir / "claim_support.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
