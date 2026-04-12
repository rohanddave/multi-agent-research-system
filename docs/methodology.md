# Methodology

## Experimental Setup

The project compares two research assistant workflows under the same conditions.

### Single-Agent Baseline

The baseline receives a question, retrieves top evidence snippets, and writes an answer directly from those snippets.

### Multi-Agent System

The orchestrated system runs four stages:

1. Search agent retrieves evidence.
2. Summarization agent converts evidence into source-grounded notes.
3. Orchestrator drafts an answer using the notes.
4. Fact-checking agent labels claims as supported or unsupported.

## Dataset

The prototype uses `data/questions.json`, a small benchmark of research questions paired with reference answers and expected source ids. The corpus is stored in `data/corpus.json`.

For the final project, expand the benchmark to 8-15 questions covering:

- retrieval augmented generation,
- hallucination and factuality,
- multi-agent collaboration,
- evaluation of LLM systems,
- prompt decomposition and tool use.

## Metrics

### Citation Coverage

Measures how many citations in an answer refer to retrieved evidence.

### Claim Support

Extracts answer claims and checks whether each claim has lexical support in the retrieved evidence.

### Reference Overlap

Computes token overlap between the generated answer and the reference answer.

### Overall Score

Mean of citation coverage, claim support, and reference overlap.

## Qualitative Evaluation

Automatic metrics should be supplemented with a small human rubric:

| Criterion | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Correctness | Mostly wrong | Partially correct | Fully correct |
| Completeness | Misses key points | Covers some points | Covers all key points |
| Grounding | Unsupported | Some citations useful | Claims clearly source-backed |
| Clarity | Hard to follow | Understandable | Clear and concise |

## Analysis Plan

Report average metric scores for each system, then inspect examples where:

- multi-agent wins clearly,
- single-agent performs similarly,
- multi-agent fails because of retrieval or summarization loss,
- fact-checking catches unsupported claims.
