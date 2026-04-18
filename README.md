# CS6180 Project: Multi-Agent Research Assistant

This project studies whether specialized LLM-style agents improve research quality over a single-agent baseline.

The system compares two pipelines:

- `single`: one agent retrieves evidence and drafts an answer in one pass.
- `multi`: an orchestrator coordinates specialized agents for search, summarization, and fact-checking.

The default implementation is deterministic and runs locally, which makes the benchmark reproducible for class demos. The same interfaces can be swapped for real LLM calls later.

## Research Question

Do specialized agents coordinated by an orchestrator produce more accurate, better-supported research answers than a single general-purpose agent?

## Hypothesis

Agent specialization will improve citation coverage and factual support, but may increase latency and orchestration complexity.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m research_assistant.run_benchmark --dataset data/questions.json --out results/benchmark.json
```

View a single example:

```bash
PYTHONPATH=src python -m research_assistant.cli "How does retrieval augmented generation reduce hallucination?"
```

## Optional LLM Mode

The project can also use OpenAI models for the single-agent writer, summarization agent, orchestrator, and fact-checking agent.

```bash
cp .env.example .env
# Then edit .env and set OPENAI_API_KEY.

PYTHONPATH=src python -m research_assistant.cli \
  "How does retrieval augmented generation reduce hallucination?" \
  --llm-provider openai \
  --model gpt-5.1
```

Run the full benchmark with LLM-generated answers:

```bash
PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/benchmark-openai.json \
  --llm-provider openai \
  --model gpt-5.1
```

You can also use different models for different agents:

```bash
PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/benchmark-openai-mixed.json \
  --llm-provider openai \
  --single-model gpt-5.1 \
  --summarizer-model gpt-5-mini \
  --orchestrator-model gpt-5.1 \
  --fact-checker-model gpt-5.1
```

`--model` acts as the default for every LLM-backed agent. The role-specific flags override it. Use model ids that are available for your OpenAI account.

Keep `--llm-provider local` for fully deterministic, no-cost runs.

## Evaluation Outputs

Each benchmark run writes:

- JSON report: full outputs, scores, model metadata, citations, retrieved sources, and per-question latency.
- CSV table: one row per question and system for spreadsheet analysis.
- PNG plots:
  - `summary_metrics.png`
  - `latency.png`
  - `unsupported_claim_rate.png`
  - `claim_support.png`

The evaluator compares systems using retrieval recall, citation precision, citation recall, claim support, unsupported claim rate, reference overlap, answer conciseness, overall score, and latency.

## Project Layout

```text
data/
  corpus.json        Evidence snippets used by the local retriever
  questions.json     Benchmark questions and reference answers
docs/
  proposal.md        Course-ready project proposal
  methodology.md     Experimental design and evaluation plan
src/research_assistant/
  agents.py          Search, summarization, fact-checking, and baseline agents
  llm.py             Optional OpenAI Responses API integration
  orchestrator.py    Multi-agent workflow
  evaluation.py      Benchmark metrics
  run_benchmark.py   CLI benchmark runner
tests/
  test_benchmark.py  Smoke tests for the benchmark pipeline
```

## Metrics

The included evaluator reports:

- `retrieval_recall`: fraction of expected sources retrieved.
- `citation_precision`: fraction of citations that match expected sources.
- `citation_recall`: fraction of expected sources cited.
- `claim_support`: average lexical support for extracted answer claims.
- `unsupported_claim_rate`: fraction of claims with weak evidence support.
- `reference_overlap`: token overlap against the reference answer.
- `answer_conciseness`: score for staying near a target answer length.
- `latency_seconds`: runtime per question and system.
- `overall`: aggregate quality score emphasizing citation quality, claim support, and reference overlap.

These are lightweight proxy metrics for the project prototype. A stronger final report should add human evaluation for correctness, completeness, and citation usefulness.

## Suggested Final Deliverables

- Working demo comparing single-agent and multi-agent outputs.
- Quantitative benchmark table across 8-15 research questions.
- Qualitative error analysis of hallucinations, missed evidence, and unsupported claims.
- Short report discussing whether specialization helped and where orchestration failed.
