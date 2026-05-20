"""OpenRouter backend — the DEFAULT for SparkOCR-VLM.

Routes both DeepSeek-OCR-v2 and Qwen3-VL through OpenRouter's OpenAI-compatible
chat/completions endpoint. Use ``:free`` model IDs for the free tier.
"""

from __future__ import annotations

from sparkocr_vlm.backends._oai_compatible import call_oai_compatible
from sparkocr_vlm.backends.base import VLMBackend
from sparkocr_vlm.config import settings
from sparkocr_vlm.schema import OCROutput
from sparkocr_vlm.utils.cost import estimate_cost


class OpenRouterBackend(VLMBackend):
    """OpenRouter via OpenAI-compatible REST."""

    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        model: str = "deepseek-ai/DeepSeek-OCR-v2",
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        if api_key is None:
            sk = settings().openrouter_api_key
            api_key = sk.get_secret_value() if sk else ""
        self.api_key = api_key
        self.timeout = timeout

    def parse_image(
        self, image_bytes: bytes, prompt: str | None = None
    ) -> OCROutput:
        return call_oai_compatible(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            model=self.model,
            image_bytes=image_bytes,
            prompt=prompt,
            extra_headers={
                "HTTP-Referer": "https://github.com/sabareeswarans11/SparkOCR-VLM",
                "X-Title": "SparkOCR-VLM",
            },
        )

    def estimate_cost(self, page_count: int) -> float:
        # Rough heuristic: ~800 prompt tokens + ~1200 completion per page.
        return estimate_cost(self.model, 800 * page_count, 1200 * page_count)
