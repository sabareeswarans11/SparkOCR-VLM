"""Tests for the pandas_udf processor."""

from __future__ import annotations

import pandas as pd

from sparkocr_vlm.processor import parse_batch
from sparkocr_vlm.page_extractor import PageExtractor


def test_parse_batch_mock(synth_invoice_bytes, synth_table_bytes):
    pages = PageExtractor(dpi=150).extract(synth_invoice_bytes)
    pages += PageExtractor(dpi=150).extract(synth_table_bytes)
    rows = parse_batch("mock", "mock-model", pages)
    assert len(rows) == len(pages)
    for r in rows:
        assert r["error"] is None
        assert r["markdown"]


def test_pandas_udf_runs_on_spark(spark, synth_invoice_bytes):
    from sparkocr_vlm.processor import make_ocr_udf
    from pyspark.sql.functions import col

    pages = PageExtractor(dpi=150).extract(synth_invoice_bytes)
    pdf = pd.DataFrame({"png": pages})
    sdf = spark.createDataFrame(pdf)
    udf = make_ocr_udf("mock", "mock-model")
    out = sdf.withColumn("ocr", udf(col("png"))).select("ocr.markdown").toPandas()
    assert len(out) == len(pages)
    assert all(m for m in out["markdown"])
