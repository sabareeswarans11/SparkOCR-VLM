# 03 — PageExtractor

## Goal
Convert PDF bytes into a list of per-page PNG bytes using `pymupdf`. Works on Intel Mac without external binaries beyond what `pymupdf` ships.

## Outputs
- `src/sparkocr_vlm/page_extractor.py`

## API
```python
class PageExtractor:
    def __init__(self, dpi: int = 200, max_pages: int | None = None): ...
    def extract(self, pdf_bytes: bytes) -> list[bytes]:
        """Return list of PNG bytes, one per page."""
```

## Implementation notes
- Use `fitz.open(stream=pdf_bytes, filetype="pdf")`.
- For each page: `page.get_pixmap(dpi=dpi).tobytes("png")`.
- Respect `max_pages` to cap large docs in dev.
- Raise `ValueError("empty PDF")` on zero-page docs.

## Tests (write alongside, in tests/test_page_extractor.py)
- `extract` returns N PNG byte strings for an N-page input (use the synthetic report PDF).
- PNG header bytes start with `\x89PNG`.
- `max_pages=1` truncates correctly.

## DoD
- Unit tests green.
