"""Image preprocessing helpers (resize, encode)."""

from __future__ import annotations

import base64
import io


def encode_png_data_uri(png_bytes: bytes) -> str:
    """Return a ``data:image/png;base64,...`` URI for OpenAI-compatible vision APIs."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def encode_png_b64(png_bytes: bytes) -> str:
    """Return base64-encoded PNG bytes without the data: prefix (used by Gemini)."""
    return base64.b64encode(png_bytes).decode("ascii")


def maybe_downscale(png_bytes: bytes, max_side: int = 2048) -> bytes:
    """Downscale an image whose longest side exceeds ``max_side``.

    Many VLMs ignore very large images or charge per-pixel; downscaling
    moderately keeps cost predictable on dense documents.
    """
    try:
        from PIL import Image
    except ImportError:
        return png_bytes  # Pillow optional in some envs

    with Image.open(io.BytesIO(png_bytes)) as im:
        w, h = im.size
        if max(w, h) <= max_side:
            return png_bytes
        scale = max_side / max(w, h)
        new_size = (int(w * scale), int(h * scale))
        im2 = im.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        im2.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
