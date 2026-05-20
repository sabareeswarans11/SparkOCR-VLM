"""Golden output loading + assertion helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sparkocr_vlm.backends import mock as mock_mod
from sparkocr_vlm.evaluator import normalized_edit_distance
from sparkocr_vlm.schema import OCROutput

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "golden"


def load_golden(name: str) -> str:
    """Return the markdown content of ``tests/fixtures/golden/<name>.md``."""
    return (GOLDEN_DIR / f"{name}.md").read_text()


def assert_golden_md(actual: str, name: str, tol: float = 0.05) -> None:
    """Assert ``actual`` matches the named golden within normalized edit distance ``tol``."""
    expected = load_golden(name)
    d = normalized_edit_distance(actual, expected)
    assert d <= tol, (
        f"golden mismatch for {name}: edit_distance={d:.3f} > tol={tol}\n"
        f"--- expected ---\n{expected[:400]}\n"
        f"--- actual ---\n{actual[:400]}"
    )


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_mock_table_from_fixtures(fixtures_dir: Path) -> None:
    """Populate ``MockBackend.MOCK_TABLE`` so synthetic PDFs map to their goldens.

    For each synthetic PDF, render page 1 to PNG (sha256 → golden markdown).
    Called once from conftest.py.
    """
    from sparkocr_vlm.page_extractor import PageExtractor

    extractor = PageExtractor(dpi=200)
    mapping = {
        "synth_invoice.pdf": "synth_invoice",
        "synth_report.pdf": "synth_report",
        "synth_table.pdf": "synth_table",
    }
    for pdf_name, golden_name in mapping.items():
        pdf_path = fixtures_dir / pdf_name
        if not pdf_path.exists():
            continue
        pages = extractor.extract(pdf_path.read_bytes())
        try:
            md = load_golden(golden_name)
        except FileNotFoundError:
            continue
        # Map every page of multi-page docs to the same golden — fine for tests
        # since the mock's job is to provide deterministic markdown, not realism.
        for png in pages:
            h = hashlib.sha256(png).hexdigest()
            mock_mod.MOCK_TABLE[h] = OCROutput(
                markdown=md,
                doc_type="other",
                confidence=1.0,
                model="mock-model",
            )
