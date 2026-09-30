"""Offline PDF parser regressions using synthetic documents, not patient data."""

from pathlib import Path
from unittest.mock import MagicMock

import fitz
import pytest

from cdr.core.exceptions import ParsingError
from cdr.parsing import Parser, PDFParser


def make_pdf(path: Path, texts: tuple[str, ...]) -> None:
    with fitz.open() as document:
        for text in texts:
            page = document.new_page()
            if text:
                page.insert_text((72, 72), text)
        document.save(path)


@pytest.mark.parametrize(
    "texts", [("Synthetic first page",), ("Synthetic first page", "Synthetic second page"), ("",)]
)
def test_pdf_parse_retains_page_count_after_close(tmp_path, monkeypatch, texts):
    path = tmp_path / "sample.pdf"
    make_pdf(path, texts)
    document = fitz.open(path)
    parser = PDFParser()
    tracer = MagicMock()
    monkeypatch.setattr(parser, "_tracer", tracer)
    monkeypatch.setattr(fitz, "open", lambda _path: document)

    parsed = parser.parse(path)

    assert document.is_closed
    assert parsed.source_path == str(path)
    assert parsed.metadata["page_count"] == len(texts)
    assert [(element.text, element.page) for element in parsed.elements] == [
        (text, page) for page, text in enumerate(texts, start=1) if text
    ]
    tracer.span.return_value.__enter__.return_value.set_attribute.assert_any_call(
        "page_count", len(texts)
    )


def test_pdf_parse_closes_document_on_extraction_error(tmp_path, monkeypatch):
    path = tmp_path / "sample.pdf"
    make_pdf(path, ("Synthetic page",))
    document = fitz.open(path)
    monkeypatch.setattr(fitz, "open", lambda _path: document)

    def fail_extraction(*args, **kwargs):
        raise RuntimeError("synthetic extraction error")

    monkeypatch.setattr(fitz.Page, "get_text", fail_extraction)
    try:
        with pytest.raises(ParsingError, match="synthetic extraction error") as exc_info:
            PDFParser().parse(path)
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert document.is_closed
    finally:
        if not document.is_closed:
            document.close()


def test_pdf_parser_public_entry_points(tmp_path):
    path = tmp_path / "sample.pdf"
    make_pdf(path, ("Synthetic parser sample",))

    assert PDFParser().extract_text(path) == "Synthetic parser sample"
    assert Parser().parse(path).metadata["page_count"] == 1


def test_pdf_parser_missing_file(tmp_path):
    with pytest.raises(ParsingError, match="File not found"):
        PDFParser().parse(tmp_path / "missing.pdf")
