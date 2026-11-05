import logging
from unittest.mock import MagicMock, patch

import pytest

from cdr.core.enums import RecordSource, StudyType
from cdr.core.schemas import CDRState, Record, ScreeningDecision, StudyCard
from cdr.orchestration.nodes.analysis_nodes import assess_rob2_node, extract_data_node

LOGGER_NAME = "cdr.orchestration.nodes.analysis_nodes"
CONFIG = {"configurable": {}}


@pytest.mark.asyncio
async def test_extract_progress_logs_at_debug_without_writing_to_stdout(caplog, capsys):
    state = CDRState(run_id="run-1", question="Does treatment help?")

    with (
        patch("cdr.extraction.extractor.StudyCardExtractor", return_value=MagicMock()),
        caplog.at_level(logging.DEBUG, logger=LOGGER_NAME),
    ):
        result = await extract_data_node(state, CONFIG)

    assert result["study_cards"] == []
    assert [record.getMessage() for record in caplog.records] == [
        "Processing 0 records for extraction",
        "Extracted 0 study cards; 0 errors",
    ]
    assert all(record.levelno == logging.DEBUG for record in caplog.records)
    assert capsys.readouterr().out == ""


@pytest.mark.asyncio
async def test_extract_failure_logs_record_and_error_at_warning(caplog, capsys):
    record = Record(
        record_id="rec-1",
        source=RecordSource.PUBMED,
        content_hash="hash-1",
        title="Study",
        abstract="Study abstract",
    )
    state = CDRState(
        run_id="run-1",
        question="Does treatment help?",
        retrieved_records=[record],
        screened=[ScreeningDecision(record_id="rec-1", included=True)],
    )
    extractor = MagicMock()
    extractor.extract.side_effect = RuntimeError("provider unavailable")

    with (
        patch("cdr.extraction.extractor.StudyCardExtractor", return_value=extractor),
        caplog.at_level(logging.DEBUG, logger=LOGGER_NAME),
    ):
        result = await extract_data_node(state, CONFIG)

    warning = next(record for record in caplog.records if record.levelno == logging.WARNING)
    assert warning.getMessage() == "Extraction failed for rec-1: provider unavailable"
    assert result["errors"] == ["Extraction failed for rec-1: provider unavailable"]
    assert capsys.readouterr().out == ""


@pytest.mark.asyncio
async def test_assessment_failure_logs_record_and_error_at_warning(caplog, capsys):
    state = CDRState(
        run_id="run-1",
        question="Does treatment help?",
        study_cards=[StudyCard(record_id="rec-1", study_type=StudyType.RCT)],
    )
    assessor = MagicMock()
    assessor.assess.side_effect = RuntimeError("assessment unavailable")

    with (
        patch("cdr.rob2.assessor.RoB2Assessor", return_value=assessor),
        patch("cdr.rob2.robins_i_assessor.ROBINSIAssessor", return_value=MagicMock()),
        caplog.at_level(logging.DEBUG, logger=LOGGER_NAME),
    ):
        result = await assess_rob2_node(state, CONFIG)

    warning = next(record for record in caplog.records if record.levelno == logging.WARNING)
    assert warning.getMessage() == "RoB2 assessment failed for rec-1: assessment unavailable"
    assert result["errors"] == ["RoB2 assessment failed for rec-1: assessment unavailable"]
    assert capsys.readouterr().out == ""
