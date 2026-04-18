from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .agents import format_evidence
from .llm import LLMClient
from .models import Evidence


JUDGE_METRICS = [
    "correctness",
    "completeness",
    "grounding",
    "clarity",
    "citation_usefulness",
    "overall",
]


@dataclass(frozen=True)
class JudgeResult:
    scores: dict[str, float]
    rationale: str


class LLMJudge:
    """Blind LLM-as-judge evaluator for semantic answer quality."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def evaluate(
        self,
        question: str,
        answer: str,
        reference_answer: str,
        evidence: list[Evidence],
        expected_sources: list[str],
    ) -> JudgeResult:
        response = self.llm.complete(
            system=(
                "You are an impartial evaluator for a research assistant benchmark. "
                "Score the candidate answer using only the question, reference answer, "
                "expected source ids, and evidence. Do not infer which system produced it. "
                "Use the full 1-5 scale. Be strict: reserve 5 for answers with no meaningful "
                "omissions, no unsupported claims, and citations that cover the expected sources. "
                "Return only valid JSON."
            ),
            user=self._build_prompt(question, answer, reference_answer, evidence, expected_sources),
        )
        return self._parse_response(response)

    def _build_prompt(
        self,
        question: str,
        answer: str,
        reference_answer: str,
        evidence: list[Evidence],
        expected_sources: list[str],
    ) -> str:
        return f"""
Question:
{question}

Reference answer:
{reference_answer}

Expected source ids:
{", ".join(expected_sources) or "none"}

Evidence:
{format_evidence(evidence)}

Candidate answer:
{answer}

Rubric:
Score each item from 1 to 5. Use the full scale:
- 1 = poor or mostly wrong.
- 2 = weak; important errors, omissions, or unsupported claims.
- 3 = acceptable but incomplete or only partly grounded.
- 4 = good; minor omissions or citation weaknesses.
- 5 = excellent; complete, directly grounded, and citation-supported.

Important scoring rules:
- Penalize completeness when the answer misses important points from the reference answer.
- Penalize citation_usefulness when expected source ids are missing from citations or citations do not support nearby claims.
- Penalize grounding when the answer adds claims not directly supported by the evidence.
- Do not give a 5 for overall unless correctness, completeness, grounding, and citation usefulness are all near-perfect.

Criteria:
- correctness: factual accuracy relative to the evidence and reference answer.
- completeness: coverage of important points needed to answer the question.
- grounding: whether claims are supported by the provided evidence.
- clarity: readability and organization.
- citation_usefulness: whether citations identify useful supporting sources.
- overall: holistic answer quality.

Return exactly this JSON shape:
{{
  "correctness": 1,
  "completeness": 1,
  "grounding": 1,
  "clarity": 1,
  "citation_usefulness": 1,
  "overall": 1,
  "rationale": "one short explanation"
}}
""".strip()

    def _parse_response(self, response: str) -> JudgeResult:
        raw = response.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                raise ValueError(f"Judge did not return JSON: {response}") from None
            parsed = json.loads(match.group(0))

        scores = {}
        for metric in JUDGE_METRICS:
            value = float(parsed.get(metric, 0))
            scores[f"judge_{metric}"] = max(1.0, min(5.0, value))

        rationale = str(parsed.get("rationale", "")).strip()
        return JudgeResult(scores=scores, rationale=rationale)
