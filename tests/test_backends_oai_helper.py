"""Unit tests for the _oai_compatible helper using respx-style mocking via httpx.MockTransport."""

from __future__ import annotations

import httpx

from sparkocr_vlm.backends import _oai_compatible as oai


def test_call_handles_missing_key():
    out = oai.call_oai_compatible(
        base_url="https://example.com/v1",
        api_key="",
        model="qwen/qwen3-vl-instruct",
        image_bytes=b"\x89PNG\r\n",
    )
    assert out.error == "missing API key"


def test_call_parses_success(monkeypatch):
    """Patch httpx.AsyncClient.post to return a canned response."""

    fake_response = {
        "choices": [{"message": {"content": "# Title\n\nbody"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    class FakeResp:
        status_code = 200
        text = ""
        def json(self):
            return fake_response
        def raise_for_status(self):
            return None

    async def fake_post(self, url, headers=None, json=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    out = oai.call_oai_compatible(
        base_url="https://example.com/v1",
        api_key="sk-test",
        model="deepseek-ai/DeepSeek-OCR-v2",
        image_bytes=b"\x89PNG\r\n",
    )
    assert out.error is None
    assert out.markdown == "# Title\n\nbody"
    assert out.prompt_tokens == 100
    assert out.completion_tokens == 50
