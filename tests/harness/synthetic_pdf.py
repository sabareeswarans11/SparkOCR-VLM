"""Generate deterministic synthetic PDFs for tests.

Uses reportlab (pure Python, works on Intel Mac). Seeded; same bytes every run.
CLI:
    python -m tests.harness.synthetic_pdf --out tests/fixtures
"""

from __future__ import annotations

import argparse
import io
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SyntheticPDFBuilder:
    """Build three permanent synthetic PDFs deterministically."""

    out_dir: Path
    seed: int = 42

    def __post_init__(self) -> None:
        self.out_dir = Path(self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------- individual docs ---------------------------

    def build_invoice(self) -> Path:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas

        path = self.out_dir / "synth_invoice.pdf"
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER, invariant=1)
        w, h = LETTER

        c.setFont("Helvetica-Bold", 18)
        c.drawString(72, h - 72, "Invoice INV-2024-001")

        c.setFont("Helvetica", 11)
        c.drawString(72, h - 100, "Bill to: ACME Corp")
        c.drawString(72, h - 116, "Date: 2024-01-15")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, h - 160, "Item")
        c.drawString(280, h - 160, "Qty")
        c.drawString(360, h - 160, "Price")
        c.drawString(460, h - 160, "Total")

        c.setFont("Helvetica", 11)
        items = [
            ("Widget A", "10", "$25.00", "$250.00"),
            ("Widget B", "5", "$50.00", "$250.00"),
            ("Service Fee", "1", "$734.56", "$734.56"),
        ]
        y = h - 180
        for it in items:
            c.drawString(72, y, it[0])
            c.drawString(280, y, it[1])
            c.drawString(360, y, it[2])
            c.drawString(460, y, it[3])
            y -= 18

        c.setFont("Helvetica-Bold", 12)
        c.drawString(360, y - 18, "Total:")
        c.drawString(460, y - 18, "$1,234.56")

        c.showPage()
        c.save()
        path.write_bytes(buf.getvalue())
        return path

    def build_report(self) -> Path:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas

        path = self.out_dir / "synth_report.pdf"
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER, invariant=1)
        w, h = LETTER

        # Page 1
        c.setFont("Helvetica-Bold", 22)
        c.drawString(72, h - 100, "Q1 2025 Quarterly Report")
        c.setFont("Helvetica", 12)
        c.drawString(72, h - 130, "Prepared by: Finance Team")
        c.setFont("Helvetica", 11)
        c.drawString(72, h - 170, "Executive Summary")
        c.drawString(72, h - 188, "Revenue grew 18% year over year, driven by enterprise contracts.")
        c.drawString(72, h - 204, "Operating margin improved to 22.4%.")
        c.showPage()

        # Page 2
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, h - 100, "Detailed Results")
        c.setFont("Helvetica", 11)
        body = [
            "Revenue: $42.1M",
            "Gross margin: 71%",
            "Net income: $9.4M",
            "Headcount: 312",
            "Key risks: foreign exchange, supplier consolidation.",
        ]
        y = h - 130
        for line in body:
            c.drawString(72, y, line)
            y -= 18
        c.showPage()

        c.save()
        path.write_bytes(buf.getvalue())
        return path

    def build_table(self) -> Path:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

        path = self.out_dir / "synth_table.pdf"
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=LETTER, invariant=1)
        styles = getSampleStyleSheet()
        story = [Paragraph("Sales by Region", styles["Title"])]
        data = [
            ["Region", "Q1", "Q2", "Q3"],
            ["North", "100", "120", "140"],
            ["South", "80", "90", "110"],
            ["East", "60", "70", "85"],
            ["West", "150", "160", "175"],
        ]
        t = Table(data, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(t)
        doc.build(story)
        path.write_bytes(buf.getvalue())
        return path

    # --------------------------- bulk ---------------------------

    def build_all(self) -> list[Path]:
        """Build the three permanent synthetic PDFs; idempotent."""
        out = [self.build_invoice(), self.build_report(), self.build_table()]
        return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tests/fixtures", help="Output directory")
    args = ap.parse_args()
    paths = SyntheticPDFBuilder(out_dir=Path(args.out)).build_all()
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
