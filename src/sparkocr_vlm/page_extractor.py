"""PDF → per-page PNG byte extraction using pymupdf.

Intel-Mac friendly: pymupdf ships its own MuPDF binaries, no system deps needed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PageExtractor:
    """Convert PDF bytes into a list of PNG bytes, one per page."""

    dpi: int = 200
    max_pages: int | None = None

    def extract(self, pdf_bytes: bytes) -> list[bytes]:
        """Return a list of PNG byte strings, one per page.

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            A list of PNG-encoded page images.

        Raises:
            ValueError: if the PDF has zero pages.
        """
        # Import lazily so this module can be imported in environments
        # where pymupdf isn't installed (e.g., docs build).
        import fitz  # pymupdf

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            n = doc.page_count
            if n == 0:
                raise ValueError("empty PDF: zero pages")
            limit = n if self.max_pages is None else min(n, self.max_pages)
            out: list[bytes] = []
            for i in range(limit):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=self.dpi, alpha=False)
                out.append(pix.tobytes("png"))
            return out
        finally:
            doc.close()
