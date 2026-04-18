# Findings Report

## Experiment Set

The benchmark was run on 5 questions comparing a single-agent baseline against a multi-agent research assistant. The multi-agent system uses specialized roles for summarization, orchestration, and fact-checking. OpenAI experiments also include an LLM-as-judge evaluation.

The `results/fix-smoke` folder is a verification artifact and is not part of the final experiment set.

| Experiment | Folder | Single Agent | Multi-Agent Models | Judge |
| --- | --- | --- | --- | --- |
| Exp0: Local sanity check | `results/exp0-local` | local deterministic | local deterministic | none |
| Exp1: Same-model architecture test | `results/exp1-same-model-architecture-test` | `gpt-5.1` | summarizer `gpt-5.1`, orchestrator `gpt-5.1`, fact-checker `gpt-5.1` | `gpt-5.1` |
| Exp2: Mixed-model cost-aware test | `results/exp2-mixed-model-cost-aware-test` | `gpt-5.1` | summarizer `gpt-5-mini`, orchestrator `gpt-5.1`, fact-checker `gpt-5.1` | `gpt-5.1` |
| Exp3: All-mini multi-agent test | `results/exp3-all-mini-test` | `gpt-5.1` | summarizer `gpt-5-mini`, orchestrator `gpt-5-mini`, fact-checker `gpt-5-mini` | `gpt-5.1` |

## Summary Results

| Experiment | System | Auto Overall | Retrieval Recall | Citation Precision | Citation Recall | Claim Support | Unsupported Claim Rate | Reference Overlap | Judge Overall | Generation Latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Exp0 | Single | 0.848 | 0.700 | 1.000 | 0.700 | 1.000 | 0.000 | 0.538 | N/A | 0.000s |
| Exp0 | Multi | 0.942 | 1.000 | 0.933 | 1.000 | 1.000 | 0.000 | 0.776 | N/A | 0.000s |
| Exp1 | Single | 0.727 | 0.700 | 1.000 | 0.700 | 0.351 | 0.192 | 0.779 | 4.400 | 7.702s |
| Exp1 | Multi | 0.746 | 1.000 | 0.933 | 1.000 | 0.392 | 0.400 | 0.806 | 5.000 | 5.529s |
| Exp2 | Single | 0.679 | 0.700 | 1.000 | 0.700 | 0.302 | 0.383 | 0.774 | 4.600 | 2.470s |
| Exp2 | Multi | 0.782 | 1.000 | 0.933 | 1.000 | 0.402 | 0.217 | 0.791 | 5.000 | 17.534s |
| Exp3 | Single | 0.703 | 0.700 | 1.000 | 0.700 | 0.378 | 0.324 | 0.763 | 4.600 | 2.191s |
| Exp3 | Multi | 0.867 | 1.000 | 0.933 | 1.000 | 0.711 | 0.090 | 0.780 | 4.800 | 26.771s |

## Main Findings

### 1. Multi-agent specialization consistently improves source coverage.

The clearest and most reliable result is retrieval and citation recall. The single-agent baseline retrieves only the strongest source, while the multi-agent system retrieves broader evidence.

| Experiment | Single Retrieval Recall | Multi Retrieval Recall | Single Citation Recall | Multi Citation Recall |
| --- | ---: | ---: | ---: | ---: |
| Exp0 | 0.700 | 1.000 | 0.700 | 1.000 |
| Exp1 | 0.700 | 1.000 | 0.700 | 1.000 |
| Exp2 | 0.700 | 1.000 | 0.700 | 1.000 |
| Exp3 | 0.700 | 1.000 | 0.700 | 1.000 |

This supports the core project claim: the main benefit of specialization is not just fluent answer writing, but more complete source coverage.

### 2. The same-model architecture test supports the core hypothesis, but the margin is modest.

Exp1 is the cleanest architecture comparison because model quality is controlled:

- Single-agent: `gpt-5.1`
- Multi-agent: `gpt-5.1` for summarizer, orchestrator, and fact-checker
- Judge: `gpt-5.1`

Results:

- Single auto overall: 0.727
- Multi auto overall: 0.746
- Single judge overall: 4.400
- Multi judge overall: 5.000
- Single retrieval recall: 0.700
- Multi retrieval recall: 1.000

The multi-agent system wins, but the automatic overall margin is not huge. The strongest evidence is in recall and judge preference, not in raw automatic overall score.

One surprising detail: Exp1 multi-agent generation latency is lower than single-agent latency:

- Single: 7.702s
- Multi: 5.529s

This is probably caused by a single-agent latency outlier, especially q4 at 30.46s. It should not be interpreted as proof that multi-agent is generally faster.

### 3. Mixed-model cost-aware setup improves quality but does not reduce latency.

Exp2 used `gpt-5-mini` for summarization and `gpt-5.1` for orchestration and fact-checking.

Results:

- Single auto overall: 0.679
- Multi auto overall: 0.782
- Single judge overall: 4.600
- Multi judge overall: 5.000
- Multi retrieval recall: 1.000
- Multi citation recall: 1.000

The multi-agent system clearly improves quality, but the cost-aware latency expectation does not hold:

- Single latency: 2.470s
- Multi latency: 17.534s

This does not make sense if interpreted as "smaller summarizer should reduce total latency." The likely explanation is that total latency is dominated by multiple serial LLM calls, output length, API variability, or slow calls in particular questions. The result should be framed as:

> Mixed-model specialization preserved or improved quality, but this run did not show a latency advantage.

### 4. All-mini multi-agent has the best automatic score, but the latency result is suspicious.

Exp3 uses `gpt-5-mini` for all multi-agent roles while keeping the single-agent baseline at `gpt-5.1`.

Results:

- Single auto overall: 0.703
- Multi auto overall: 0.867
- Single judge overall: 4.600
- Multi judge overall: 4.800
- Multi claim support: 0.711
- Multi unsupported claim rate: 0.090

This is the strongest automatic result. The all-mini multi-agent outputs are shorter on average than the Exp1/Exp2 multi-agent outputs:

- Exp1 multi word count: 87.0
- Exp2 multi word count: 77.8
- Exp3 multi word count: 58.6

This likely helps the lexical claim-support metric because shorter, more extractive answers make fewer unsupported or paraphrased claims.

The latency is the biggest red flag:

- Exp1 multi latency: 5.529s
- Exp2 multi latency: 17.534s
- Exp3 multi latency: 26.771s

The all-mini setup being the slowest does not match the intuitive expectation that smaller models should be faster. Per-question latency shows large outliers, including q2 at 50.91s. This should be treated as API/runtime variability, not as a stable model-speed conclusion.

## LLM Judge Findings

The stricter judge is more useful than before. It no longer gives every single-agent answer a perfect score.

| Experiment | Single Judge Overall | Multi Judge Overall |
| --- | ---: | ---: |
| Exp1 | 4.400 | 5.000 |
| Exp2 | 4.600 | 5.000 |
| Exp3 | 4.600 | 4.800 |

The judge generally prefers multi-agent answers, especially because they include more complete source coverage. The judge rationales repeatedly penalize single-agent answers for missing secondary limitations or criteria, even when the answers are factually correct.

However, judge scores are still somewhat high overall. This means the judge is useful as a semantic complement, but the benchmark needs harder questions if the judge is expected to strongly separate systems.

## Results That Still Do Not Fully Make Sense

### 1. Latency is unstable and should not be overinterpreted.

Several latency results are counterintuitive:

- Exp1 single is slower than Exp1 multi because q4 single took 30.46s.
- Exp2 multi is much slower than Exp1 multi despite using a smaller summarizer.
- Exp3 all-mini multi is the slowest configuration, with q2 taking 50.91s.
- Exp3 single judge latency averages 6.294s because q3 judge latency was 18.41s.

These are likely caused by API variability, serial multi-agent calls, output length, and occasional slow requests. The project should report latency as observed runtime for this run, not as a stable model-efficiency finding.

### 2. Automatic claim support still disagrees with the judge in some cases.

The revised claim-support metric is less extreme than before, but there are still disagreements. For example, Exp1 multi q2 has automatic unsupported claim rate of 1.0 while the judge gives it 5.0. This suggests the automatic metric still struggles with paraphrases or multi-sentence answers.

Safe interpretation:

> Automatic claim support is a reproducible lexical proxy, while the LLM judge is a semantic proxy. Disagreements between them should be analyzed rather than collapsed into one score.

### 3. Exp3's high automatic score may reflect answer style, not true model superiority.

Exp3 multi-agent has the highest automatic score and lowest unsupported claim rate. But its answers are also shorter. That can improve lexical metrics because there are fewer claims to verify and less paraphrasing.

Do not claim that all-mini is universally better. A safer claim is:

> In this run, the all-mini multi-agent condition produced shorter, more source-aligned answers that scored best on automatic metrics, but it was slower and only slightly better according to the judge.

### 4. Single-agent baselines differ across OpenAI experiments.

The single-agent baseline uses `gpt-5.1` in Exp1, Exp2, and Exp3, but scores vary:

- Exp1 single overall: 0.727
- Exp2 single overall: 0.679
- Exp3 single overall: 0.703

This is expected with live LLM calls, but it makes cross-experiment comparisons less clean. Future runs should cache the single-agent outputs or repeat each condition multiple times.

## Recommended Claims For The Final Report

The strongest claims supported by the regenerated results are:

1. Multi-agent specialization consistently improves retrieval recall and citation recall from 0.700 to 1.000.
2. With model quality controlled in Exp1, multi-agent improves automatic overall score from 0.727 to 0.746 and judge overall from 4.400 to 5.000.
3. The multi-agent advantage is strongest for completeness and source coverage, not necessarily for basic factual correctness.
4. Mixed-model specialization improves quality over the single-agent baseline, but this run does not show latency savings.
5. The all-mini multi-agent condition performs best on automatic metrics, but the result is confounded by shorter answers and unexpected latency.
6. LLM judge scores support the multi-agent preference, but the judge remains high-scoring overall, so automatic metrics and qualitative examples should also be reported.

## Recommended Final Table

Use this table in the report:

| Experiment | System | Auto Overall | Judge Overall | Retrieval Recall | Citation Recall | Unsupported Claim Rate | Latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exp1 Same Model | Single | 0.727 | 4.400 | 0.700 | 0.700 | 0.192 | 7.702s |
| Exp1 Same Model | Multi | 0.746 | 5.000 | 1.000 | 1.000 | 0.400 | 5.529s |
| Exp2 Mixed | Single | 0.679 | 4.600 | 0.700 | 0.700 | 0.383 | 2.470s |
| Exp2 Mixed | Multi | 0.782 | 5.000 | 1.000 | 1.000 | 0.217 | 17.534s |
| Exp3 All Mini | Single | 0.703 | 4.600 | 0.700 | 0.700 | 0.324 | 2.191s |
| Exp3 All Mini | Multi | 0.867 | 4.800 | 1.000 | 1.000 | 0.090 | 26.771s |

## Suggested Next Steps

1. Run each OpenAI experiment 3 times and report mean and standard deviation.
2. Cache single-agent outputs so the baseline is identical across Exp1, Exp2, and Exp3.
3. Add harder questions where the answer clearly requires both expected sources.
4. Make judge scoring pairwise as a second evaluation mode: show Answer A and Answer B without labels and ask which is better.
5. Report latency separately from quality because multi-agent runs use multiple serial LLM calls and show high variance.
