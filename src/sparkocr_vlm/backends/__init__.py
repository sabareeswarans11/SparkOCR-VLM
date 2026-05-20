"""Backend factory + public re-exports."""

from __future__ import annotations

from sparkocr_vlm.backends.base import VLMBackend
from sparkocr_vlm.backends.mock import MockBackend


def get_backend(name: str, **kwargs) -> VLMBackend:
    """Return a backend instance by name.

    Args:
        name: One of "mock", "openrouter", "together", "gemini", "modal".
        **kwargs: Passed through to the backend constructor.
    """
    name = name.lower()
    if name == "mock":
        return MockBackend(**kwargs)
    if name == "openrouter":
        from sparkocr_vlm.backends.openrouter import OpenRouterBackend
        return OpenRouterBackend(**kwargs)
    if name == "together":
        from sparkocr_vlm.backends.together import TogetherBackend
        return TogetherBackend(**kwargs)
    if name == "gemini":
        from sparkocr_vlm.backends.gemini import GeminiBackend
        return GeminiBackend(**kwargs)
    if name == "modal":
        from sparkocr_vlm.backends.modal_backend import ModalBackend
        return ModalBackend(**kwargs)
    raise ValueError(f"Unknown backend: {name!r}")


__all__ = ["VLMBackend", "MockBackend", "get_backend"]
