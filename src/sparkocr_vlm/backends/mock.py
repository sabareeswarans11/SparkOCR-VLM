"""Mock backend — returns canned OCROutput keyed by sha256(image_bytes).

The test harness pre-populates ``MOCK_TABLE`` with the hashes of the synthetic
PDFs' page images. Any unknown input gets ``DEFAULT_MOCK_MARKDOWN``.
"""

from __future__ import annotations

import hashlib

from sparkocr_vlm.backends.base import VLMBackend
from sparkocr_vlm.schema import OCROutput

DEFAULT_MOCK_MARKDOWN = "# Mock Document\n\nThis is canned OCR output for testing.\n"


# Populated by the test harness on import. (See tests/harness/golden.py.)
MOCK_TABLE: dict[str, OCROutput] = {}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class MockBackend(VLMBackend):
    """Zero-cost backend that returns canned outputs."""

    name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def parse_image(
        self, image_bytes: bytes, prompt: str | None = None
    ) -> OCROutput:
        h = sha256(image_bytes)
        if h in MOCK_TABLE:
            out = MOCK_TABLE[h].model_copy(update={"model": self.model})
            return out
        return OCROutput(
            markdown=DEFAULT_MOCK_MARKDOWN,
            doc_type="other",
            confidence=1.0,
            model=self.model,
        )

    def estimate_cost(self, page_count: int) -> float:
        return 0.0
