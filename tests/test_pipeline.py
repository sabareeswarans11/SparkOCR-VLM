"""Tests for OCRPipeline."""

from __future__ import annotations


def test_parse_single_mock(synth_invoice_bytes, mock_pipeline):
    df = mock_pipeline.parse_single(synth_invoice_bytes)
    assert len(df) == 1
    assert "filename" in df.columns
    assert "page_num" in df.columns
    assert df.iloc[0]["page_num"] == 1
    assert "INV-2024-001" in df.iloc[0]["markdown"]
    assert df.iloc[0]["error"] is None


def test_run_pipeline_on_directory(tmp_path, spark, fixtures_dir):
    from sparkocr_vlm import OCRPipeline

    # Copy 2 synth PDFs into a fresh dir so we control input
    src = tmp_path / "input"
    src.mkdir()
    for name in ("synth_invoice.pdf", "synth_table.pdf"):
        (src / name).write_bytes((fixtures_dir / name).read_bytes())

    out = tmp_path / "out"
    pipeline = OCRPipeline(
        backend="mock",
        model="mock-model",
        input_path=str(src),
        output_path=str(out),
        batch_size=2,
    )
    silver = pipeline.run(spark)
    rows = silver.toPandas()
    assert len(rows) == 2
    assert set(rows["filename"]) == {"synth_invoice.pdf", "synth_table.pdf"}
    assert all(r is None for r in rows["error"])
