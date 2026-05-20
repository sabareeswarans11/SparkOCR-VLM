# 09 — Pipeline Orchestrator

## Goal
`OCRPipeline` — the only class most users touch. Wires PageExtractor → Spark DataFrame → UDF → Delta write.

## Outputs
- `src/sparkocr_vlm/pipeline.py`

## API
```python
class OCRPipeline:
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
    ): ...
    def run(self, spark: SparkSession) -> DataFrame: ...
    def parse_single(self, pdf_bytes_or_path) -> pd.DataFrame: ...
```

## `run` flow
1. Read input directory as `binaryFile` DataFrame.
2. `mapInPandas` to explode each PDF into per-page rows (uses `PageExtractor`).
3. Apply `make_ocr_udf(...)` to the page column.
4. Cost-cap check before each batch (`BudgetExceeded` if exceeded).
5. Write silver Delta to `output_path/silver/` with merge mode.
6. Return the silver DataFrame.

## `parse_single`
Convenience for tests + notebooks: takes a file path or bytes, runs PageExtractor + backend directly (NO Spark), returns a small pandas DataFrame.

## DoD
- `pipeline.parse_single(synth_invoice.pdf).iloc[0]["markdown"]` returns a non-empty string with the mock backend.
- `pipeline.run(spark)` on a 3-PDF directory returns a DataFrame with 3+ rows.
