# SparkOCR-VLM

> Distributed VLM-based OCR for PySpark. DeepSeek-OCR-v2 + Qwen3-VL, with Delta Lake output, callable as a `pandas_udf`.

[![CI](https://github.com/sabareeswarans11/SparkOCR-VLM/actions/workflows/ci.yml/badge.svg)](https://github.com/sabareeswarans11/SparkOCR-VLM/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![PySpark 3.5](https://img.shields.io/badge/pyspark-3.5-orange.svg)](https://spark.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why

Everyone runs VLM OCR with `vllm serve` + a Python `for` loop. Nobody has a clean Spark-native batch OCR framework. Databricks `ai_parse_document` exists but is closed-source and Databricks-only.

**SparkOCR-VLM** wraps modern vision-language models — DeepSeek-OCR-v2 and Qwen3-VL — as PySpark UDFs so you can OCR millions of pages on any Spark cluster (including Databricks Free Edition) and land the results in a Delta table.

## Install

```bash
git clone https://github.com/sabareeswarans11/SparkOCR-VLM.git
cd SparkOCR-VLM
uv sync --extra dev
cp .env.template .env
# add OPENROUTER_API_KEY=... to .env
```

## Quickstart

```python
from pyspark.sql import SparkSession
from sparkocr_vlm import OCRPipeline
from sparkocr_vlm.utils.spark_helpers import build_local_spark

spark = build_local_spark()

pipeline = OCRPipeline(
    backend="openrouter",
    model="deepseek-ai/DeepSeek-OCR-v2",
    input_path="./sample_pdfs/",
    output_path="./output_delta/",
    batch_size=8,
    max_cost_usd=1.0,
)

df = pipeline.run(spark)
df.show(truncate=80)
```

```
+-----------------+--------+--------+------+-----------------------+
| filename        | page   | model  | cost | markdown              |
+-----------------+--------+--------+------+-----------------------+
| invoice_001.pdf | 1      | dsocr  | 0.001| # Invoice INV-2024... |
| report_q1.pdf   | 1      | dsocr  | 0.001| # Q1 2025 Report ...  |
+-----------------+--------+--------+------+-----------------------+
```

## Mock mode (no API keys)

```python
pipeline = OCRPipeline(backend="mock", input_path="./sample_pdfs/", output_path="./out/")
pipeline.run(spark)
```

Every unit test runs on the mock backend — zero API spend.

## Backends

| Backend | Models | Free tier? | Notes |
|---|---|---|---|
| `openrouter` (default) | `deepseek-ai/DeepSeek-OCR-v2`, `qwen/qwen3-vl-instruct` | Yes | Recommended |
| `together` | `deepseek-ai/DeepSeek-OCR-v2`, `Qwen/Qwen3-VL-Instruct` | Trial credits | OpenAI-compatible API |
| `gemini` | `gemini-2.0-flash` (vision) | Yes (rate-limited) | Use when DeepSeek/Qwen unavailable |
| `modal` | Any HF model | Pay per second | Self-hosted GPU |
| `mock` | n/a | n/a | Tests + dry runs |

## Where this runs

- **MacBook Pro 16" 2019 Intel** — local PySpark + OpenRouter API. No GPU needed. See `MAC_INTEL_SETUP.md`.
- **Databricks Free Edition** — drop the notebook into a Free workspace; see `DATABRICKS_FREE.md`.
- **Any Spark cluster** — `pip install sparkocr-vlm`, set the env var, go.

## Project layout

See `CLAUDE.md` for the full layout. The TL;DR map:

- `src/sparkocr_vlm/` — library code.
- `notebooks/` — quickstart, Databricks Free demo, eval benchmark.
- `tests/` + `tests/harness/` — pytest + synthetic-PDF harness.
- `tasks/` — Claude Code build-order specs.
- `.claude/skills/` + `.claude/agents/` — subagents that build/test/deploy in parallel.

## Develop with Claude Code in PyCharm

Open this folder in PyCharm, then run Claude Code. It will pick up `CLAUDE.md` automatically and follow the task files in `tasks/`. Subagents in `.claude/agents/` can be invoked for parallel work — see `AGENTS.md`.

## License

MIT. See `LICENSE`.
