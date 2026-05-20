"""VLMBackend abstract base. FROZEN — do not change after task 04."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from sparkocr_vlm.schema import OCROutput

DEFAULT_PROMPT = (
    "You are a document OCR engine. Read the image and emit the document content "
    "as well-structured Markdown. Preserve headings, paragraphs, lists, and tables. "
    "Tables MUST be valid Markdown tables. Do not summarize. Do not add commentary. "
    "Return ONLY the Markdown."
)

QWEN_PROMPT_SUFFIX = (
    ' Do not write "Here is the markdown:" or any similar preface. '
    "Begin directly with the document content."
)


_FENCE_RE = re.compile(r"^```(?:markdown|md)?\s*\n(.*?)\n```\s*$", re.DOTALL)
_PREAMBLE_RES = [
    re.compile(r"^\s*here(?:'s| is)[^.\n:]*[.:]\s*", re.IGNORECASE),
    re.compile(r"^\s*sure[!,]?[^.\n:]*[.:]\s*", re.IGNORECASE),
    re.compile(r"^\s*of course[!,]?[^.\n:]*[.:]\s*", re.IGNORECASE),
]


def clean_markdown(text: str) -> str:
    """Strip code fences and common preambles from a VLM markdown response."""
    if not text:
        return ""
    s = text.strip()
    m = _FENCE_RE.match(s)
    if m:
        s = m.group(1).strip()
    for r in _PREAMBLE_RES:
        s = r.sub("", s, count=1)
    return s.strip()


class VLMBackend(ABC):
    """Abstract VLM backend. All concrete backends share this interface."""

    name: str = "abstract"
    model: str = ""

    @abstractmethod
    def parse_image(self, image_bytes: bytes, prompt: str | None = None) -> OCROutput:
        """Run OCR on a single PNG image. Must never raise on transient errors —
        return ``OCROutput`` with ``error`` populated instead.
        """
        ...

    @abstractmethod
    def estimate_cost(self, page_count: int) -> float:
        """Rough USD cost for ``page_count`` pages."""
        ...
