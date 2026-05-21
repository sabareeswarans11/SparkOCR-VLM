"""Shared logic for OpenAI-compatible chat/completions vision endpoints
(used by OpenRouter and Together)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from sparkocr_vlm.backends.base import (
    DEFAULT_PROMPT,
    QWEN_PROMPT_SUFFIX,
    clean_markdown,
)
from sparkocr_vlm.schema import OCROutput
from sparkocr_vlm.utils.cost import record_cost
from sparkocr_vlm.utils.image import encode_png_data_uri

SAMPLING_PARAMS_BY_MODEL: dict[str, dict[str, Any]] = {
    "deepseek-ai/DeepSeek-OCR-v2":         {"temperature": 0.0, "max_tokens": 4096, "top_p": 1.0},
    "deepseek-ai/DeepSeek-OCR-v2:free":    {"temperature": 0.0, "max_tokens": 4096, "top_p": 1.0},
    "qwen/qwen3-vl-instruct":              {"temperature": 0.0, "max_tokens": 4096, "top_p": 0.95},
    "qwen/qwen3-vl-instruct:free":         {"temperature": 0.0, "max_tokens": 4096, "top_p": 0.95},
    "Qwen/Qwen3-VL-Instruct":              {"temperature": 0.0, "max_tokens": 4096, "top_p": 0.95},
}


def prompt_for(model: str, override: str | None) -> str:
    if override:
        return override
    if "qwen" in model.lower():
        return DEFAULT_PROMPT + QWEN_PROMPT_SUFFIX
    return DEFAULT_PROMPT


def sampling_for(model: str) -> dict[str, Any]:
    return SAMPLING_PARAMS_BY_MODEL.get(
        model, {"temperature": 0.0, "max_tokens": 4096, "top_p": 1.0}
    )


class _RateLimit(Exception):
    """Raised on HTTP 429 so tenacity retries with longer backoff."""


@retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_exception_type(
        (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError, _RateLimit)
    ),
)
async def _post(client: httpx.AsyncClient, url: str, headers: dict, payload: dict) -> dict:
    r = await client.post(url, headers=headers, json=payload, timeout=60.0)
    if r.status_code == 429:
        raise _RateLimit(f"429 rate-limited: {r.text[:120]}")
    if r.status_code >= 500:
        raise httpx.RemoteProtocolError(f"{r.status_code}: {r.text[:200]}")
    r.raise_for_status()
    return r.json()


def call_oai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    image_bytes: bytes,
    prompt: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> OCROutput:
    """Run one vision call against an OpenAI-compatible endpoint. Returns OCROutput."""
    if not api_key:
        return OCROutput(
            markdown="",
            model=model,
            error="missing API key",
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    params = sampling_for(model)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_for(model, prompt)},
                    {"type": "image_url", "image_url": {"url": encode_png_data_uri(image_bytes)}},
                ],
            }
        ],
        **params,
    }

    async def _run() -> dict:
        async with httpx.AsyncClient() as client:
            return await _post(client, f"{base_url}/chat/completions", headers, payload)

    try:
        data = asyncio.run(_run())
    except httpx.HTTPStatusError as e:
        return OCROutput(markdown="", model=model, error=f"http {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:  # noqa: BLE001
        return OCROutput(markdown="", model=model, error=f"{type(e).__name__}: {e}")

    try:
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        pt = int(usage.get("prompt_tokens", 0))
        ct = int(usage.get("completion_tokens", 0))
    except (KeyError, IndexError, TypeError) as e:
        return OCROutput(markdown="", model=model, error=f"parse: {e}")

    md = clean_markdown(text)
    cost = record_cost(model, pt, ct, pages=1)

    return OCROutput(
        markdown=md,
        doc_type="unknown",
        confidence=1.0,
        prompt_tokens=pt,
        completion_tokens=ct,
        cost_usd=cost,
        model=model,
    )
