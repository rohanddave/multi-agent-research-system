from research_assistant.run_benchmark import run_benchmark


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
