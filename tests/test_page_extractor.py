"""Tests for PageExtractor."""

from __future__ import annotations

import pytest

from sparkocr_vlm.page_extractor import PageExtractor


def test_extract_invoice_returns_png(synth_invoice_bytes):
    pages = PageExtractor(dpi=150).extract(synth_invoice_bytes)
    assert len(pages) == 1
    assert pages[0][:8] == b"\x89PNG\r\n\x1a\n"


def test_extract_report_two_pages(synth_report_bytes):
    pages = PageExtractor(dpi=150).extract(synth_report_bytes)
    assert len(pages) == 2
    for p in pages:
        assert p.startswith(b"\x89PNG")


def test_max_pages_truncates(synth_report_bytes):
    pages = PageExtractor(dpi=150, max_pages=1).extract(synth_report_bytes)
    assert len(pages) == 1


def test_empty_pdf_raises():
    # Minimal PDF with zero pages is hard to forge; pass invalid bytes instead.
    with pytest.raises(Exception):
        PageExtractor().extract(b"not a pdf")
