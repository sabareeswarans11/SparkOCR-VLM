"""Google Gemini backend — uses generateContent REST API."""

from __future__ import annotations

import asyncio

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from sparkocr_vlm.backends.base import (
    DEFAULT_PROMPT,
    VLMBackend,
    clean_markdown,
)
from sparkocr_vlm.config import settings
from sparkocr_vlm.schema import OCROutput
from sparkocr_vlm.utils.cost import estimate_cost, record_cost
from sparkocr_vlm.utils.image import encode_png_b64


class GeminiBackend(VLMBackend):
    """Google AI Studio Gemini API."""

    name = "gemini"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        if api_key is None:
            sk = settings().gemini_api_key
            api_key = sk.get_secret_value() if sk else ""
        self.api_key = api_key
        self.timeout = timeout

    def parse_image(
        self, image_bytes: bytes, prompt: str | None = None
    ) -> OCROutput:
        if not self.api_key:
            return OCROutput(markdown="", model=self.model, error="missing API key")

        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt or DEFAULT_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": encode_png_b64(image_bytes),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "topP": 1.0,
                "maxOutputTokens": 4096,
            },
        }

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5.0),
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)
            ),
        )
        async def _do() -> dict:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=self.timeout)
                if r.status_code >= 500:
                    raise httpx.RemoteProtocolError(f"{r.status_code}: {r.text[:200]}")
                r.raise_for_status()
                return r.json()

        try:
            data = asyncio.run(_do())
        except httpx.HTTPStatusError as e:
            return OCROutput(
                markdown="",
                model=self.model,
                error=f"http {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:  # noqa: BLE001
            return OCROutput(
                markdown="", model=self.model, error=f"{type(e).__name__}: {e}"
            )

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata") or {}
            pt = int(usage.get("promptTokenCount", 0))
            ct = int(usage.get("candidatesTokenCount", 0))
        except (KeyError, IndexError, TypeError) as e:
            return OCROutput(markdown="", model=self.model, error=f"parse: {e}")

        md = clean_markdown(text)
        cost = record_cost(self.model, pt, ct, pages=1)
        return OCROutput(
            markdown=md,
            doc_type="unknown",
            confidence=1.0,
            prompt_tokens=pt,
            completion_tokens=ct,
            cost_usd=cost,
            model=self.model,
        )

    def estimate_cost(self, page_count: int) -> float:
        return estimate_cost(self.model, 800 * page_count, 1200 * page_count)
