"""Tests for MockBackend + factory."""

from __future__ import annotations

from sparkocr_vlm.backends import get_backend
from sparkocr_vlm.backends.mock import MockBackend


def test_factory_returns_mock():
    be = get_backend("mock")
    assert isinstance(be, MockBackend)


def test_mock_returns_default_for_unknown_bytes():
    be = MockBackend()
    out = be.parse_image(b"unknown bytes")
    assert out.markdown
    assert out.error is None
    assert out.cost_usd == 0.0
    assert out.model == "mock-model"


def test_mock_returns_golden_for_synthetic(synth_invoice_bytes):
    """After conftest installs the MOCK_TABLE, synthetic PDFs return goldens."""
    from sparkocr_vlm.page_extractor import PageExtractor

    pages = PageExtractor(dpi=200).extract(synth_invoice_bytes)
    out = MockBackend().parse_image(pages[0])
    assert "INV-2024-001" in out.markdown
