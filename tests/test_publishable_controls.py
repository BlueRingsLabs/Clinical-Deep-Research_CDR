from __future__ import annotations

import asyncio
import logging

import httpx
import pytest

from cdr.verification import publishable_controls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start_status", "run_status", "expected_failure"),
    [
        (202, "unpublishable", "PUB-TEST (Visible failure case) failed: unpublishable"),
        (
            500,
            None,
            "PUB-TEST (Visible failure case) failed to start (HTTP 500): unavailable",
        ),
    ],
)
async def test_harness_logs_readable_failure_and_summary(
    monkeypatch, caplog, start_status, run_status, expected_failure
):
    query = publishable_controls.PublishableQuery(
        query_id="PUB-TEST",
        name="Visible failure case",
        research_question="example question",
        expected_status="publishable",
        anchor_trials=[],
        anchor_pmids=[],
        expected_study_types=[],
        expected_comparator="placebo",
        expected_population="adults",
        if_fails_check=(
            ["Check if PubMed retrieval includes PMID 18997196"] if start_status == 202 else []
        ),
    )
    monkeypatch.setattr(publishable_controls, "PUBLISHABLE_QUERIES", [query])

    class Response:
        def __init__(self, status_code, payload=None, text=""):
            self.status_code = status_code
            self.payload = payload or {}
            self.text = text

        def json(self):
            return self.payload

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, *_args, **_kwargs):
            if start_status == 202:
                return Response(202, {"run_id": "run-1"})
            return Response(start_status, text="unavailable")

        async def get(self, *_args, **_kwargs):
            return Response(200, {"status": run_status})

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: Client())
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    caplog.set_level(logging.INFO, logger=publishable_controls.__name__)

    result = await publishable_controls.run_publishable_harness(verbose=False)

    assert result["total"] == 1
    assert result["failed"] == 1
    assert expected_failure in caplog.text
    assert "publishable harness: 0/1 passed, 1 failed" in caplog.text
    if start_status == 202:
        assert "started run run-1" in caplog.text
        assert "Check if PubMed retrieval includes PMID 18997196" in caplog.text
