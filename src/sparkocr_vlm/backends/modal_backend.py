"""Modal serverless GPU backend (optional extra)."""

from __future__ import annotations

from sparkocr_vlm.backends.base import VLMBackend
from sparkocr_vlm.schema import OCROutput
from sparkocr_vlm.utils.cost import estimate_cost


class ModalBackend(VLMBackend):
    """Stub. Requires the ``modal`` extra and a deployed Modal stub function.

    Out of scope for v0.1 but the class exists so the factory + tests can
    reference it. Implement when needed.
    """

    name = "modal"

    def __init__(self, model: str = "Qwen/Qwen3-VL-Instruct", stub_name: str | None = None) -> None:
        self.model = model
        self.stub_name = stub_name

    def parse_image(
        self, image_bytes: bytes, prompt: str | None = None
    ) -> OCROutput:
        return OCROutput(
            markdown="",
            model=self.model,
            error="ModalBackend not yet implemented",
        )

    def estimate_cost(self, page_count: int) -> float:
        # Modal pricing is per-second, not per-token. Rough $/page estimate.
        return 0.0005 * page_count
