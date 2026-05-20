"""Tests for the test harness itself."""

from __future__ import annotations

import hashlib


def test_synthetic_pdfs_deterministic(tmp_path):
    from tests.harness.synthetic_pdf import SyntheticPDFBuilder

    a = SyntheticPDFBuilder(out_dir=tmp_path / "a").build_all()
    b = SyntheticPDFBuilder(out_dir=tmp_path / "b").build_all()
    for pa, pb in zip(a, b, strict=False):
        assert hashlib.sha256(pa.read_bytes()).hexdigest() == hashlib.sha256(pb.read_bytes()).hexdigest()


def test_perf_writes_bench(tmp_path):
    from tests.harness.perf import run_perf

    out = tmp_path / "BENCH.md"
    report = run_perf(pages=5, backend="mock", model="mock-model", output=out)
    assert report["pages"] == 5
    assert out.exists()
    text = out.read_text()
    assert "BENCH" in text and "Pages:" in text


def test_assert_golden_md_passes(fixtures_dir, mock_pipeline):
    from tests.harness.golden import assert_golden_md

    df = mock_pipeline.parse_single(fixtures_dir / "synth_table.pdf")
    assert_golden_md(df.iloc[0]["markdown"], "synth_table", tol=0.05)
