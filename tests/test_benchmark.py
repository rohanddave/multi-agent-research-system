from research_assistant.run_benchmark import run_benchmark
from research_assistant.judge import LLMJudge
from research_assistant.llm import AgentModelConfig, OpenAIResponsesLLM, build_agent_llms, build_llm


def test_benchmark_runs_for_both_systems():
    report = run_benchmark("data/corpus.json", "data/questions.json")

    assert set(report["summary"]) == {"single", "multi"}
    assert len(report["examples"]["single"]) == 5
    assert len(report["examples"]["multi"]) == 5
    assert "overall" in report["summary"]["multi"]


def test_multi_agent_returns_citations():
    report = run_benchmark("data/corpus.json", "data/questions.json")
    first = report["examples"]["multi"][0]

    assert first["citations"]
    assert first["scores"]["citation_coverage"] == 1.0


def test_local_llm_provider_is_deterministic_mode():
    assert build_llm("local") is None


def test_can_configure_different_models_per_agent():
    llms = build_agent_llms(
        "openai",
        AgentModelConfig(
            default="default-model",
            single="single-model",
            summarizer="summarizer-model",
            orchestrator="orchestrator-model",
            fact_checker="fact-checker-model",
        ),
    )

    assert isinstance(llms.single, OpenAIResponsesLLM)
    assert llms.single.model == "single-model"
    assert llms.summarizer.model == "summarizer-model"
    assert llms.orchestrator.model == "orchestrator-model"
    assert llms.fact_checker.model == "fact-checker-model"


class FakeJudgeLLM:
    def complete(self, system: str, user: str) -> str:
        return """
        {
          "correctness": 4,
          "completeness": 5,
          "grounding": 4,
          "clarity": 5,
          "citation_usefulness": 4,
          "overall": 4.4,
          "rationale": "Good answer with useful citations."
        }
        """


def test_llm_judge_parses_json_scores():
    judge = LLMJudge(FakeJudgeLLM())
    result = judge._parse_response(FakeJudgeLLM().complete("", ""))

    assert result.scores["judge_correctness"] == 4
    assert result.scores["judge_overall"] == 4.4
    assert "useful citations" in result.rationale
