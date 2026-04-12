# Project Proposal

## Title

Multi-Agent Research Assistant: Measuring the Effect of Agent Specialization on Research Quality and Accuracy

## Motivation

LLMs are increasingly used as research assistants, but single-agent systems often mix several tasks at once: searching for evidence, summarizing information, checking claims, and writing a final answer. This can lead to weak source grounding, missed contradictions, and unsupported statements. Multi-agent systems propose an alternative: break the research workflow into specialized agents and coordinate them through an orchestrator.

This project asks whether specialization actually improves research quality in a measurable way.

## Research Question

How does a specialized multi-agent research assistant compare to a single-agent baseline on answer quality, factual accuracy, and citation grounding?

## System Design

The multi-agent system contains:

- Search agent: retrieves relevant evidence from a corpus or search backend.
- Summarization agent: compresses retrieved evidence into concise notes.
- Fact-checking agent: verifies final claims against retrieved evidence.
- Orchestrator: coordinates agents, passes intermediate artifacts, and produces the final answer.

The baseline contains:

- Single research agent: retrieves evidence and produces an answer in one pass.

## Hypotheses

1. The multi-agent system will produce answers with better citation coverage than the single-agent baseline.
2. The multi-agent system will produce fewer unsupported claims.
3. The multi-agent system may be slower and more complex because it requires more intermediate steps.

## Methodology

1. Build both systems using the same evidence corpus and question set.
2. Run both systems on the same benchmark questions.
3. Evaluate outputs using automatic proxy metrics:
   - citation coverage,
   - claim support,
   - reference answer overlap,
   - overall score.
4. Add human qualitative analysis for a subset of answers:
   - factual correctness,
   - completeness,
   - clarity,
   - usefulness of citations.

## Expected Results

The expected outcome is that specialization improves factual grounding and traceability, especially for questions requiring multiple supporting sources. However, the multi-agent system may still fail when search retrieval misses key evidence or when the summarizer drops important details.

## Risks and Limitations

- Automatic metrics are imperfect proxies for research quality.
- A small local corpus may not capture open-web research complexity.
- If all agents use the same underlying LLM, improvements may come from workflow structure rather than truly independent reasoning.
- More agents can introduce error propagation between steps.

## Final Report Structure

1. Introduction and motivation
2. Related work on RAG, agents, and factuality
3. System design
4. Experimental setup
5. Quantitative results
6. Qualitative error analysis
7. Discussion and conclusion
