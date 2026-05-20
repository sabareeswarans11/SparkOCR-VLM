"""OCRPipeline — top-level user-facing API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from sparkocr_vlm.backends import get_backend
from sparkocr_vlm.page_extractor import PageExtractor
from sparkocr_vlm.processor import make_ocr_udf, parse_batch
from sparkocr_vlm.schema import PipelineConfig


class BudgetExceeded(RuntimeError):
    """Raised when accumulated cost exceeds ``max_cost_usd``."""


class OCRPipeline:
    """Wire PageExtractor → Spark DataFrame → UDF → Delta in one place."""

    def __init__(
        self,
        backend: str = "openrouter",
        model: str = "deepseek-ai/DeepSeek-OCR-v2",
        input_path: str | None = None,
        output_path: str | None = None,
        batch_size: int = 8,
        max_cost_usd: float | None = None,
        dpi: int = 200,
        max_pages_per_doc: int | None = None,
        backend_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.cfg = PipelineConfig(
            backend=backend,
            model=model,
            input_path=input_path,
            output_path=output_path,
            batch_size=batch_size,
            max_cost_usd=max_cost_usd,
            dpi=dpi,
            max_pages_per_doc=max_pages_per_doc,
        )
        self.backend_kwargs = backend_kwargs or {}

    # ------------------------------------------------------------------ #
    # Single-document path (no Spark required) — used by tests/notebooks #
    # ------------------------------------------------------------------ #
    def parse_single(self, pdf: str | bytes | Path) -> pd.DataFrame:
        """Run OCR on a single PDF (path or bytes). Returns a pandas DataFrame."""
        if isinstance(pdf, (str, Path)):
            pdf_bytes = Path(pdf).read_bytes()
            filename = Path(pdf).name
        else:
            pdf_bytes = pdf
            filename = "<bytes>"

        extractor = PageExtractor(dpi=self.cfg.dpi, max_pages=self.cfg.max_pages_per_doc)
        pages = extractor.extract(pdf_bytes)

        rows = parse_batch(
            self.cfg.backend, self.cfg.model, pages, **self.backend_kwargs
        )
        df = pd.DataFrame(rows)
        df.insert(0, "filename", filename)
        df.insert(1, "page_num", range(1, len(rows) + 1))
        return df

    # ------------------------------------------------------------------ #
    # Spark path                                                         #
    # ------------------------------------------------------------------ #
    def run(self, spark) -> Any:
        """Run the full distributed pipeline against ``input_path``.

        Reads PDFs as ``binaryFile``, explodes pages via ``mapInPandas``, applies
        the OCR UDF, writes to ``output_path`` as Delta, and returns the silver
        DataFrame.
        """
        if not self.cfg.input_path:
            raise ValueError("input_path is required for .run()")

        from pyspark.sql import functions as F
        from pyspark.sql.types import (
            StructType, StructField, StringType, IntegerType, BinaryType,
        )

        # Pre-flight cost cap check (rough budget guardrail).
        if self.cfg.max_cost_usd is not None:
            backend = get_backend(self.cfg.backend, model=self.cfg.model, **self.backend_kwargs)
            # We don't know page count yet — defer the hard check to post-run.
            _ = backend.estimate_cost(1)  # surface key/auth issues early

        # 1. Read PDFs as binary
        bronze = (
            spark.read.format("binaryFile")
            .option("recursiveFileLookup", "true")
            .option("pathGlobFilter", "*.pdf")
            .load(self.cfg.input_path)
        )

        # 2. Explode to per-page rows via mapInPandas
        page_schema = StructType(
            [
                StructField("path", StringType(), nullable=False),
                StructField("filename", StringType(), nullable=False),
                StructField("page_num", IntegerType(), nullable=False),
                StructField("page_png", BinaryType(), nullable=False),
            ]
        )

        dpi = self.cfg.dpi
        max_pages = self.cfg.max_pages_per_doc

        def explode_pages(iterator):
            extractor = PageExtractor(dpi=dpi, max_pages=max_pages)
            for pdf in iterator:
                for _, row in pdf.iterrows():
                    try:
                        pages = extractor.extract(bytes(row["content"]))
                    except Exception:
                        continue
                    name = str(row["path"]).rsplit("/", 1)[-1]
                    out_rows = [
                        {
                            "path": row["path"],
                            "filename": name,
                            "page_num": i + 1,
                            "page_png": p,
                        }
                        for i, p in enumerate(pages)
                    ]
                    if out_rows:
                        yield pd.DataFrame(out_rows)

        page_df = bronze.select("path", "content").mapInPandas(
            explode_pages, schema=page_schema
        )

        # 3. Apply OCR UDF
        ocr_udf = make_ocr_udf(
            self.cfg.backend, self.cfg.model, **self.backend_kwargs
        )
        silver = page_df.withColumn("ocr", ocr_udf(F.col("page_png"))).select(
            "path",
            "filename",
            "page_num",
            F.col("ocr.markdown").alias("markdown"),
            F.col("ocr.doc_type").alias("doc_type"),
            F.col("ocr.confidence").alias("confidence"),
            F.col("ocr.prompt_tokens").alias("prompt_tokens"),
            F.col("ocr.completion_tokens").alias("completion_tokens"),
            F.col("ocr.cost_usd").alias("cost_usd"),
            F.col("ocr.model").alias("model"),
            F.col("ocr.error").alias("error"),
        )

        # 4. Optional Delta write
        if self.cfg.output_path:
            silver_path = str(Path(self.cfg.output_path) / "silver")
            silver.write.format("delta").mode("overwrite").save(silver_path)
            silver = spark.read.format("delta").load(silver_path)

        # 5. Post-run budget enforcement
        if self.cfg.max_cost_usd is not None:
            total = silver.selectExpr("sum(cost_usd) as total").collect()[0]["total"] or 0.0
            if total > self.cfg.max_cost_usd:
                raise BudgetExceeded(
                    f"cost_usd={total:.4f} exceeded cap {self.cfg.max_cost_usd:.4f}"
                )

        return silver
