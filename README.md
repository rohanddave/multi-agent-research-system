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

## Optional LLM Judge

Add an LLM-as-judge layer to score semantic quality with a blind rubric:

```bash
PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/benchmark-openai-judged.json \
  --llm-provider openai \
  --model gpt-5.1 \
  --judge-provider openai \
  --judge-model gpt-5.1
```

Judge scores are added as `judge_correctness`, `judge_completeness`, `judge_grounding`, `judge_clarity`, `judge_citation_usefulness`, and `judge_overall`. The judge is not told whether an answer came from the single-agent or multi-agent system.

## Run All Experiments

This command runs the local sanity check plus three OpenAI judged experiments and saves each run in its own folder under `results/`. The OpenAI runs make paid API calls.

```bash
mkdir -p \
  results/exp0-local \
  results/exp1-same-model-architecture-test \
  results/exp2-mixed-model-cost-aware-test \
  results/exp3-all-mini-test \
&& PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/exp0-local/benchmark-local.json \
&& PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/exp1-same-model-architecture-test/benchmark-openai-shared-gpt51-judged.json \
  --llm-provider openai \
  --model gpt-5.1 \
  --judge-provider openai \
  --judge-model gpt-5.1 \
&& PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/exp2-mixed-model-cost-aware-test/benchmark-openai-mixed-cost-aware-judged.json \
  --llm-provider openai \
  --single-model gpt-5.1 \
  --summarizer-model gpt-5-mini \
  --orchestrator-model gpt-5.1 \
  --fact-checker-model gpt-5.1 \
  --judge-provider openai \
  --judge-model gpt-5.1 \
&& PYTHONPATH=src python -m research_assistant.run_benchmark \
  --dataset data/questions.json \
  --out results/exp3-all-mini-test/benchmark-openai-all-mini-judged.json \
  --llm-provider openai \
  --single-model gpt-5.1 \
  --summarizer-model gpt-5-mini \
  --orchestrator-model gpt-5-mini \
  --fact-checker-model gpt-5-mini \
  --judge-provider openai \
  --judge-model gpt-5.1
```

## Evaluation Outputs

Each benchmark run writes:

- JSON report: full outputs, scores, model metadata, citations, retrieved sources, and per-question latency.
- CSV table: one row per question and system for spreadsheet analysis.
- PNG plots:
  - `summary_metrics.png`
  - `latency.png`
  - `unsupported_claim_rate.png`
  - `claim_support.png`
  - `judge_scores.png`, when `--judge-provider` is enabled.

The evaluator compares systems using retrieval recall, citation precision, citation recall, claim support, unsupported claim rate, reference overlap, answer conciseness, overall score, and latency. With judge mode enabled, it also records judge rationale and judge latency.

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
- `judge_overall`: optional 1-5 semantic quality score from the LLM judge.
- `overall`: aggregate quality score emphasizing citation quality, claim support, and reference overlap.

These are lightweight proxy metrics for the project prototype. A stronger final report should add human evaluation for correctness, completeness, and citation usefulness.

## Suggested Final Deliverables

- Working demo comparing single-agent and multi-agent outputs.
- Quantitative benchmark table across 8-15 research questions.
- Qualitative error analysis of hallucinations, missed evidence, and unsupported claims.
- Short report discussing whether specialization helped and where orchestration failed.
