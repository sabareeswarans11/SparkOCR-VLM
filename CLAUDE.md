# CLAUDE.md — SparkOCR-VLM

> **For Claude Code running inside PyCharm.** This file is the source of truth for how to build, test, deploy, and reason about this project. Read this BEFORE editing anything. Read it AGAIN if you get confused.

## Project Overview
SparkOCR-VLM is an open-source PySpark library that enables distributed VLM-based OCR at scale. It wraps modern Vision-Language Models — primarily **DeepSeek-OCR-v2** and **Qwen3-VL** — as PySpark UDFs so teams can process millions of document pages using Spark's distributed engine with Delta Lake for structured output.

**The gap this fills:** Everyone runs VLM OCR with `vllm serve` + a Python loop. Nobody has a clean Spark-native batch OCR framework. Databricks `ai_parse_document` exists but is closed-source and Databricks-only. This library works on OSS Spark, **Databricks Free Edition**, and any Spark cluster.

## Hard Constraints (read these first)
1. **Local dev = MacBook Pro 16" 2019, Intel CPU, no NVIDIA GPU.** All inference is via API calls — never via local `torch`/`transformers`.
2. **The only managed Spark we have is Databricks Free Edition.** No paid workspaces. Everything must run on the Free plan's serverless compute or local Spark.
3. **Default model gateway is OpenRouter free tier.** DeepSeek-OCR-v2 and Qwen3-VL are both reachable through OpenRouter. Together.ai, Gemini, and Modal are alternate backends but never required.
4. **Tests must pass with no API keys.** Mock backend + synthetic fixtures must cover every code path.
5. **No torch, transformers, vllm, flash-attn, or any GPU package** in `pyproject.toml` (`mock` and `dev` extras only — see Dependencies).

## Target User
Data/ML engineers at enterprises who have millions of PDFs in a data lake and want to OCR them at scale without writing boilerplate Spark + VLM glue every time.

## Tech Stack
- **Language**: Python 3.11
- **Core**: PySpark 3.5.x (local mode for dev, Databricks Free Edition for "cluster" demo)
- **Storage**: Delta Lake (`delta-spark`) — bronze (raw pages) → silver (parsed markdown) → gold (extracted entities)
- **VLM Backends**: OpenRouter (default), Together.ai, Google Gemini, Modal, Mock
- **Tracking**: MLflow for experiment tracking + eval metrics
- **Eval**: OmniDocBench v1.5 / olmOCR-Bench compatible scoring (subset)
- **Testing**: pytest + custom harness (`tests/harness/`)
- **Packaging**: `pyproject.toml` with `uv`

## Architecture
```
                        ┌─────────────────────────────────┐
                        │       SparkOCR Pipeline         │
                        ├─────────────────────────────────┤
Input:                  │                                 │
  Delta Table           │  1. PageExtractor               │
  (PDFs/images as       │     PDF → per-page PNG images   │
   binary column)       │                                 │
        │               │  2. OCRProcessor (pandas_udf)   │
        ▼               │     image bytes → VLM API call  │
  ┌──────────┐          │     → structured markdown       │
  │ Bronze   │──────────│                                 │
  │ Table    │          │  3. SchemaValidator             │
  └──────────┘          │     pydantic v2 validation      │
        │               │                                 │
        ▼               │  4. DeltaWriter                 │
  ┌──────────┐          │     write to silver table       │
  │ Silver   │──────────│                                 │
  │ Table    │          │  5. Evaluator (optional)        │
  └──────────┘          │     score vs ground truth       │
        │               └─────────────────────────────────┘
        ▼
  ┌──────────┐
  │ Gold     │  (optional: entity extraction)
  │ Table    │
  └──────────┘
```

See **ARCHITECTURE.md** for the deep dive.

## Companion Docs
Every doc lives at the project root unless noted. Read the one that matches your current task:

| Doc | When to read it |
|---|---|
| `README.md` | Public-facing project intro and quickstart. |
| `ARCHITECTURE.md` | Internal data flow, UDF strategy, Delta layout. |
| `MAC_INTEL_SETUP.md` | Local dev setup on Intel Mac (no GPU). |
| `DATABRICKS_FREE.md` | Running on Databricks Free Edition end-to-end. |
| `MODELS.md` | DeepSeek-OCR-v2 + Qwen3-VL prompts, params, quirks. |
| `TESTING.md` | Test data strategy, synthetic fixtures, harness layout. |
| `AGENTS.md` | Parallel subagent workflow used by Claude Code. |
| `HARNESS.md` | Test harness internals + how to extend it. |
| `RUNTIME.md` | Markdown files Claude Code generates at runtime in `runtime/`. |
| `tasks/00-overview.md` | Build-order index — read first when starting fresh. |

## Directory Structure
```
sparkocr-vlm/
├── CLAUDE.md                       # This file
├── README.md
├── ARCHITECTURE.md
├── MAC_INTEL_SETUP.md
├── DATABRICKS_FREE.md
├── MODELS.md
├── TESTING.md
├── AGENTS.md
├── HARNESS.md
├── RUNTIME.md
├── pyproject.toml
├── docker-compose.yml              # MinIO (S3-compat) for local Delta
├── .env.template
├── .gitignore
├── LICENSE                         # MIT
├── src/sparkocr_vlm/
│   ├── __init__.py                 # Public API
│   ├── config.py                   # Pydantic settings from .env
│   ├── pipeline.py                 # OCRPipeline orchestrator
│   ├── page_extractor.py           # PDF → per-page PNG (pymupdf)
│   ├── processor.py                # pandas_udf wrapping backend
│   ├── schema.py                   # OCROutput / PipelineConfig (pydantic v2)
│   ├── evaluator.py                # Edit-distance + unit-test scoring
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py                 # VLMBackend ABC
│   │   ├── mock.py                 # Canned responses for tests
│   │   ├── openrouter.py           # DEFAULT — DeepSeek-OCR-v2 + Qwen3-VL
│   │   ├── together.py             # Together.ai (alt)
│   │   ├── gemini.py               # Google Gemini (alt)
│   │   └── modal_backend.py        # Modal serverless GPU (alt)
│   └── utils/
│       ├── __init__.py
│       ├── delta.py                # Delta read/write helpers
│       ├── image.py                # Resize / encode / preprocess
│       ├── spark_helpers.py        # Local SparkSession builder
│       └── cost.py                 # Per-call cost tracking
├── tests/
│   ├── conftest.py                 # Shared fixtures (SparkSession, sample data)
│   ├── harness/
│   │   ├── __init__.py
│   │   ├── synthetic_pdf.py        # Build deterministic test PDFs
│   │   ├── golden.py               # Golden output assertions
│   │   └── perf.py                 # Throughput / cost benchmarking
│   ├── test_page_extractor.py
│   ├── test_processor.py
│   ├── test_pipeline.py
│   ├── test_evaluator.py
│   ├── test_backends_mock.py
│   ├── test_backends_openrouter.py # @pytest.mark.integration
│   ├── test_harness.py
│   └── fixtures/                   # generated at runtime by synthetic_pdf
├── notebooks/
│   ├── 01_quickstart.ipynb
│   ├── 02_databricks_free.ipynb
│   └── 03_evaluation.ipynb
├── tasks/                          # Claude Code build-order files
│   ├── 00-overview.md
│   ├── 01-scaffold.md
│   ├── 02-schema-config.md
│   ├── 03-page-extractor.md
│   ├── 04-backends-base.md
│   ├── 05-backend-openrouter.md
│   ├── 06-backend-together.md
│   ├── 07-backend-gemini.md
│   ├── 08-processor-udf.md
│   ├── 09-pipeline.md
│   ├── 10-evaluator.md
│   ├── 11-tests-harness.md
│   ├── 12-notebooks.md
│   ├── 13-databricks-deploy.md
│   └── 14-readme-demo.md
├── runtime/                        # Files Claude Code writes during a session
│   ├── PROGRESS.md
│   ├── DECISIONS.md
│   ├── ERRORS.md
│   ├── COSTS.md
│   └── BENCH.md
├── .claude/
│   ├── skills/
│   │   ├── sparkocr-build/SKILL.md
│   │   ├── sparkocr-test/SKILL.md
│   │   └── sparkocr-databricks-deploy/SKILL.md
│   └── agents/
│       ├── spark-udf-engineer.md
│       ├── vlm-backend-engineer.md
│       ├── test-harness-engineer.md
│       ├── databricks-deployer.md
│       ├── eval-scorer.md
│       └── doc-scribe.md
└── scripts/
    ├── setup_local.sh              # uv venv + install dev extras
    ├── run_smoke.sh                # local pipeline smoke test
    └── push_databricks.sh          # databricks bundles deploy
```

## Conventions
- Absolute imports: `from sparkocr_vlm.pipeline import OCRPipeline`
- Type hints on EVERY function signature.
- Google-style docstrings on all public methods.
- `httpx` for all HTTP. Never `requests`.
- `pydantic` v2 for all config and data models.
- `structlog` for logs. Never `print` outside of CLI scripts.
- API keys ONLY from env vars via `config.py`. Never hardcoded.
- Every backend call logs estimated USD cost (`runtime/COSTS.md` accumulates totals).
- PySpark UDFs MUST be serializable — no closures over non-picklable state.
- Delta writes: `overwrite` for bronze, `merge` for silver/gold.

## Key Design Decisions

### 1. Backend Abstraction
```python
class VLMBackend(ABC):
    @abstractmethod
    def parse_image(self, image_bytes: bytes, prompt: str | None = None) -> OCROutput: ...
    @abstractmethod
    def estimate_cost(self, page_count: int) -> float: ...
```
All backends share the same interface. Switching from OpenRouter to Together is one config flag.

### 2. PySpark UDF Strategy
- Use `pandas_udf` (Arrow-based) for throughput.
- Backend instances are module-level singletons per executor — `get_or_create_backend()`.
- API keys read from executor env vars (set via Spark config in `spark_helpers.py`).
- Async HTTP inside the UDF uses `asyncio.run()` to stay synchronous from Spark's POV.

```python
@pandas_udf(OCR_OUTPUT_SCHEMA)
def ocr_udf(image_series: pd.Series) -> pd.DataFrame:
    backend = get_or_create_backend()
    results = [backend.parse_image(img) for img in image_series]
    return pd.DataFrame([r.model_dump() for r in results])
```

### 3. Pipeline API
```python
from sparkocr_vlm import OCRPipeline

pipeline = OCRPipeline(
    backend="openrouter",
    model="deepseek-ai/DeepSeek-OCR-v2",   # or "qwen/qwen3-vl-instruct"
    input_path="./sample_pdfs/",
    output_path="./output_delta/",
    batch_size=8,
    max_cost_usd=2.0,
)
pipeline.run(spark)
```

### 4. Local Development (Intel Mac, no GPU)
Full details in `MAC_INTEL_SETUP.md`. TL;DR:
- `SparkSession.builder.master("local[*]")` with `local[2]` for tests.
- `delta-spark` pip package — no Databricks needed for dev.
- Mock backend for unit tests. OpenRouter free tier for integration tests.
- Optional MinIO via `docker-compose up` for S3-compat local storage.

### 5. Databricks Free Edition Path
Full details in `DATABRICKS_FREE.md`. TL;DR:
- Free Edition gives you serverless SQL + a small notebook-driven compute.
- We ship a `02_databricks_free.ipynb` that uploads sample PDFs to a Volume, runs the pipeline, writes to a Delta table.
- No cluster config required — uses the default Free Edition runtime.

### 6. Evaluation
- Normalized edit distance (character-level) vs ground truth markdown.
- Binary unit tests (olmOCR-Bench style): `assert "INV-2024-001" in output_md`.
- Table-cell F1 when ground truth includes tables.
- Reading-order edit distance on line sequence.
- MLflow logs every metric.

## Parallel Agents + Harness Engineering
This project is built using **multiple Claude subagents working in parallel** when possible. The harness (`tests/harness/`) is the contract between them — every agent's output must pass the same fixtures and golden checks.

Subagents live in `.claude/agents/`:
- `spark-udf-engineer` — UDF and Spark plumbing.
- `vlm-backend-engineer` — Backend implementations.
- `test-harness-engineer` — Fixtures, synthetic PDFs, golden assertions.
- `databricks-deployer` — Free Edition deployment.
- `eval-scorer` — Benchmark scoring.
- `doc-scribe` — Keeps `runtime/` markdown current.

See `AGENTS.md` for the orchestration pattern and `HARNESS.md` for the harness contract.

## Testing Data Strategy
See `TESTING.md` for the full plan. Highlights:
- **Synthetic PDFs** generated deterministically via `tests/harness/synthetic_pdf.py` (uses `reportlab` — pure Python, runs on Intel Mac).
- **Golden outputs** committed to `tests/fixtures/golden/` once a real backend produces verified output.
- **No real customer data ever** lands in the repo.
- Three permanent synthetic samples: `synth_invoice.pdf`, `synth_report.pdf`, `synth_table.pdf`.

## Runtime Markdown Files
While Claude Code is working in PyCharm, it writes status to `runtime/`:
- `PROGRESS.md` — current task + percentage complete.
- `DECISIONS.md` — ADR-lite log of choices made mid-flight.
- `ERRORS.md` — anything that failed and how it was resolved.
- `COSTS.md` — running tally of API spend during dev.
- `BENCH.md` — perf numbers from the last harness run.

See `RUNTIME.md` for the format spec.

## Dependencies (pyproject.toml)
```toml
dependencies = [
    "pyspark>=3.5.0,<4.0",
    "delta-spark>=3.2.0",
    "httpx>=0.28.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "structlog>=24.4.0",
    "Pillow>=11.0.0",
    "pymupdf>=1.25.0",
    "mlflow>=2.18.0",
    "python-dotenv>=1.0.0",
    "tenacity>=9.0.0",
    "pandas>=2.2.0",
    "pyarrow>=18.0.0",
]

[project.optional-dependencies]
modal = ["modal>=0.73.0"]
dev = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
    "reportlab>=4.2.0",   # synthetic PDF generation
]
```

## Do NOT
- Install `torch`, `transformers`, `vllm`, or any GPU-dependent package.
- Use `requests` — always `httpx`.
- Run actual Spark clusters in tests — always `local[*]` / `local[2]`.
- Hardcode paths.
- Make UDFs async — use `asyncio.run()` inside if needed.
- Spend real API credits in unit tests — always mock backend.
- Commit anything to `tests/fixtures/` except generated synthetic outputs and golden files.

## Environment Variables
```
OPENROUTER_API_KEY=...     # DEFAULT — for openrouter backend
TOGETHER_API_KEY=...       # Optional
GEMINI_API_KEY=...         # Optional
MODAL_TOKEN_ID=...         # Optional
MODAL_TOKEN_SECRET=...     # Optional
DATABRICKS_HOST=...        # For free-edition push
DATABRICKS_TOKEN=...
```

## Build Order (short version)
Full per-task specs in `tasks/`. Order:
1. Scaffold → 2. Schema+Config → 3. PageExtractor → 4. Backend ABC → 5. OpenRouter backend → 6. Together backend → 7. Gemini backend → 8. Processor UDF → 9. Pipeline → 10. Evaluator → 11. Tests+Harness → 12. Notebooks → 13. Databricks deploy → 14. README+demo.

## Repo
Push to `https://github.com/sabareeswarans11/SparkOCR-VLM`. See `scripts/setup_local.sh` for the one-time push helper.
