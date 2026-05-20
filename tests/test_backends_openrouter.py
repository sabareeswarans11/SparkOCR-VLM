"""Integration test for OpenRouter backend. Skipped unless -m integration."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="no API key")
def test_openrouter_single_page(synth_invoice_bytes):
    from sparkocr_vlm.backends.openrouter import OpenRouterBackend
    from sparkocr_vlm.page_extractor import PageExtractor

    pages = PageExtractor(dpi=200).extract(synth_invoice_bytes)
    be = OpenRouterBackend(model="deepseek-ai/DeepSeek-OCR-v2:free")
    out = be.parse_image(pages[0])
    # Don't be strict — free tier may rate-limit. We just want non-error.
    assert out.error is None or "rate" in (out.error or "").lower()
    if out.error is None:
        assert out.markdown
