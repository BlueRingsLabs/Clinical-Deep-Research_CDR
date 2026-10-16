"""Regression tests for Case File settings passed to online evaluation."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def test_online_evaluation_passes_case_cutoff_to_runner(monkeypatch):
    module_path = Path(__file__).parents[1] / "eval" / "eval_runner.py"
    spec = importlib.util.spec_from_file_location("cdr_eval_runner", module_path)
    assert spec is not None and spec.loader is not None
    eval_runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eval_runner)

    captured = {}
    report = {
        "status": "completed",
        "run_kpis": {},
        "prisma_counts": {},
        "claims": [],
    }

    class FakeRunner:
        def __init__(self, llm):
            assert llm == "fake-llm"

        async def run(self, question, **kwargs):
            captured["question"] = question
            captured.update(kwargs)
            return SimpleNamespace(report=report)

    monkeypatch.setattr("cdr.llm.factory.create_provider_with_fallback", lambda: "fake-llm")
    monkeypatch.setattr("cdr.orchestration.graph.CDRRunner", FakeRunner)

    result = eval_runner.evaluate_question_online(
        {
            "id": "CF-RETRO-TEST",
            "question": "What did evidence show by 1987?",
            "literature_cutoff_year": 1987,
        }
    )

    assert result["status"] == "completed"
    assert captured["question"] == "What did evidence show by 1987?"
    assert captured["literature_cutoff_year"] == 1987
