"""Together.ai backend — alt path with the same OpenAI-compatible wire format."""

from __future__ import annotations

from sparkocr_vlm.backends._oai_compatible import call_oai_compatible
from sparkocr_vlm.backends.base import VLMBackend
from sparkocr_vlm.config import settings
from sparkocr_vlm.schema import OCROutput
from sparkocr_vlm.utils.cost import estimate_cost


class TogetherBackend(VLMBackend):
    """Together.ai inference cloud."""

    name = "together"
    BASE_URL = "https://api.together.xyz/v1"

    def __init__(
        self,
        model: str = "deepseek-ai/DeepSeek-OCR-v2",
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        if api_key is None:
            sk = settings().together_api_key
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
        )

    def estimate_cost(self, page_count: int) -> float:
        return estimate_cost(self.model, 800 * page_count, 1200 * page_count)
