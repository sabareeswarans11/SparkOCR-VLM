# ARCHITECTURE.md — SparkOCR-VLM

## Goals
1. Process millions of PDF pages on a Spark cluster with one user-facing API.
2. Stay portable: same code on local Spark, Databricks Free Edition, and any OSS Spark.
3. Be cost-conscious: every API call is logged with USD estimate; the pipeline can hard-cap spend.
4. Keep the model layer pluggable — switching DeepSeek-OCR-v2 → Qwen3-VL is a config flip.

## Non-Goals
- Self-hosted GPU inference inside this library. We hit APIs.
- Beating closed-source OCR on every benchmark. We want to be in the ballpark and infinitely cheaper to operate.

## Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PDF source  │───▶│ PageExtractor│───▶│   Bronze     │───▶│ OCRProcessor │
│ (S3 / Volume │    │ pymupdf      │    │ (page bytes  │    │ pandas_udf   │
│  / local FS) │    │ per-page PNG │    │  + metadata) │    │ + VLM API    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                                   ▼
                                              ┌──────────────────────────────┐
                                              │  Silver Delta table          │
                                              │  (markdown, doc_type, cost,  │
                                              │   tokens, model, ts)         │
                                              └──────────┬───────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────────────┐
                                              │  Gold (optional)             │
                                              │  - entity extraction         │
                                              │  - table normalization       │
                                              └──────────────────────────────┘
```

## Bronze / Silver / Gold

### Bronze
`spark.read.format("binaryFile")` over the input path produces rows of `(path, modificationTime, length, content)`. We unpack `content` (PDF bytes) into one row per page using `PageExtractor`, then write to `<output>/bronze/`. Mode: `overwrite`.

Schema:
```
path: string
filename: string
page_num: int
page_png: binary
extracted_at: timestamp
```

### Silver
The Spark UDF reads `page_png`, calls the VLM backend, and produces a structured `OCROutput`. We write to `<output>/silver/`. Mode: `merge` on `(path, page_num)` so retries are idempotent.

Schema:
```
path: string
filename: string
page_num: int
model: string
markdown: string
doc_type: string         # invoice | report | scan | form | other | unknown
confidence: double
prompt_tokens: int
completion_tokens: int
cost_usd: double
processed_at: timestamp
error: string            # null on success
```

### Gold (optional)
User-defined. Common patterns: extract structured fields with a second LLM call, or build a KG. Not in scope for v0.1.

## UDF Strategy

We use `pandas_udf` for Arrow-based batching:

```python
@pandas_udf(OCR_OUTPUT_SPARK_SCHEMA)
def ocr_udf(image_series: pd.Series) -> pd.DataFrame:
    backend = get_or_create_backend()       # executor-local singleton
    out = [backend.parse_image(b) for b in image_series]
    return pd.DataFrame([o.model_dump() for o in out])
```

**Why singleton-per-executor:** httpx clients reuse connections; cold-starting per row would kill throughput.

**Why not `mapInPandas`:** we may switch to it for rate-limited backends so we can sleep across the whole batch. Decision tracked in `runtime/DECISIONS.md`.

**Serializability:** the UDF closes only over `OCROutput` schema constants. Backend state is rehydrated from env vars on each executor.

## Backend Layer

`backends/base.py` defines:

```python
class VLMBackend(ABC):
    name: str
    def parse_image(self, image_bytes: bytes, prompt: str | None = None) -> OCROutput: ...
    def estimate_cost(self, page_count: int) -> float: ...
```

Concrete backends:
- `mock.py` — returns canned `OCROutput` from `tests/harness/golden.py` lookup tables.
- `openrouter.py` — POSTs to `https://openrouter.ai/api/v1/chat/completions` with `image_url` data URI.
- `together.py` — same shape, different base URL + model IDs.
- `gemini.py` — Google AI Studio REST endpoint with inline image bytes.
- `modal_backend.py` — invokes a Modal stub function (optional extra).

All backends use `httpx.AsyncClient` internally + `asyncio.run()` to stay sync for Spark.

## Spark Session

`utils/spark_helpers.py::build_local_spark()` returns a Delta-enabled `SparkSession` configured for `local[*]`. On Databricks Free Edition we skip this and use the workspace's pre-built `spark`.

```python
def build_local_spark() -> SparkSession:
    return (
        SparkSession.builder
        .master("local[*]")
        .appName("sparkocr-vlm")
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.1")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
```

## Cost Tracking

`utils/cost.py` exposes `record_cost(model: str, prompt_tok: int, completion_tok: int) -> float`. Each backend calls it on every successful response. The pipeline aggregates costs after each batch and aborts when `max_cost_usd` is exceeded — raising `BudgetExceeded` mid-run. The same number is appended to `runtime/COSTS.md`.

## Failure Handling

- Per-page errors get caught and written to the silver row's `error` column. The page row is still emitted (markdown null) so we can audit.
- Network/5xx errors are retried with `tenacity` (3 attempts, exponential backoff).
- Truly fatal errors (auth, 400) are raised; the pipeline records them in `runtime/ERRORS.md`.

## Observability

- `structlog` JSON logs to stdout.
- MLflow run per pipeline invocation: params (model, batch size, input path), metrics (pages/sec, $/page, total cost, edit distance vs ground truth if available).
- `runtime/BENCH.md` updated by the perf harness on demand.

## Deployment Targets

| Target | Cluster | Storage | Notes |
|---|---|---|---|
| Local dev | `local[*]` | local FS or MinIO | Default in tests. |
| Databricks Free Edition | Serverless notebook | Volumes | See `DATABRICKS_FREE.md`. |
| Any OSS Spark 3.5 | Stand-alone or k8s | S3 / GCS / ABFS | `pip install sparkocr-vlm`. |
