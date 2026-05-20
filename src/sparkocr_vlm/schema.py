"""Data models. FROZEN — do not change after task 02."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


DocType = Literal["invoice", "report", "scan", "form", "other", "unknown"]


class OCROutput(BaseModel):
    """Single-page OCR result emitted by any VLMBackend."""

    model_config = ConfigDict(extra="forbid")

    markdown: str = ""
    doc_type: DocType = "unknown"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: str | None = None


class PipelineConfig(BaseModel):
    """Frozen config passed to OCRPipeline.__init__."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = "openrouter"
    model: str = "deepseek-ai/DeepSeek-OCR-v2"
    input_path: str | None = None
    output_path: str | None = None
    batch_size: int = 8
    max_cost_usd: float | None = None
    dpi: int = 200
    max_pages_per_doc: int | None = None


# Spark schema definition — kept lazy so importing this module
# does not require pyspark to be present.
def get_ocr_output_spark_schema():
    """Return the Spark StructType matching OCROutput. Imported lazily."""
    from pyspark.sql.types import (
        StructType,
        StructField,
        StringType,
        DoubleType,
        IntegerType,
    )

    return StructType(
        [
            StructField("markdown", StringType(), nullable=True),
            StructField("doc_type", StringType(), nullable=True),
            StructField("confidence", DoubleType(), nullable=True),
            StructField("prompt_tokens", IntegerType(), nullable=True),
            StructField("completion_tokens", IntegerType(), nullable=True),
            StructField("cost_usd", DoubleType(), nullable=True),
            StructField("model", StringType(), nullable=True),
            StructField("error", StringType(), nullable=True),
        ]
    )
