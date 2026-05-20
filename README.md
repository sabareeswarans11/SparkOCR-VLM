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
    model="nvidia/nemotron-nano-12b-v2-vl:free",  # free tier
    input_path="./sample_pdfs/",
    output_path="./output_delta/",
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

## Real pipeline results

Ran the full Spark pipeline (`local[2]`, Delta Lake output) against three synthetic
documents using **`nvidia/nemotron-nano-12b-v2-vl:free`** via OpenRouter.
**4 pages · $0.00 total cost.**

### synth_invoice.pdf — 1 page

```markdown
# Invoice INV-2024-001

Bill to: ACME Corp
Date: 2024-01-15

| Item        | Qty | Price   | Total    |
|:------------|:----|:--------|:---------|
| Widget A    | 10  | $25.00  | $250.00  |
| Widget B    | 5   | $50.00  | $250.00  |
| Service Fee | 1   | $734.56 | $734.56  |
| **Total:**  |     |         | **$1,234.56** |
```

### synth_report.pdf — 2 pages

```markdown
# Q1 2025 Quarterly Report

Prepared by: Finance Team

## Executive Summary

Revenue grew 18% year over year, driven by enterprise contracts.
Operating margin improved to 22.4%.

---

# Detailed Results

- Revenue: $42.1M
- Gross margin: 71%
- Net income: $9.4M
- Headcount: 312
- Key risks: foreign exchange, supplier consolidation.
```

### synth_table.pdf — 1 page

```markdown
# Sales by Region

| Region | Q1  | Q2  | Q3  |
|:-------|:----|:----|:----|
| North  | 100 | 120 | 140 |
| South  | 80  | 90  | 110 |
| East   | 60  | 70  | 85  |
| West   | 150 | 160 | 175 |
```

### Spark run stats

| File | Pages | Tokens (in/out) | Cost |
|---|---|---|---|
| synth_invoice.pdf | 1 | 311 / 150 | $0.00 |
| synth_report.pdf  | 2 | 3402 / 50 + 3402 / 52 | $0.00 |
| synth_table.pdf   | 1 | 3402 / 117 | $0.00 |
| **Total** | **4** | | **$0.00** |

> Free-tier models share upstream quota — parallel Spark executors can hit rate limits.
> For production, use a paid OpenRouter key or add credits to Together.ai.

---

## Mock mode (no API keys)

```python
pipeline = OCRPipeline(backend="mock", input_path="./sample_pdfs/", output_path="./out/")
pipeline.run(spark)
```

Every unit test runs on the mock backend — zero API spend.

## Backends

| Backend | Recommended model | Free tier? | Notes |
|---|---|---|---|
| `openrouter` (default) | `nvidia/nemotron-nano-12b-v2-vl:free` | ✅ Yes | Verified working; sign up at openrouter.ai |
| `openrouter` | `google/gemma-4-31b-it:free` | ✅ Yes | Alt free vision model |
| `gemini` | `gemini-2.0-flash` | ✅ Yes (rate-limited) | Google AI Studio free key |
| `together` | `meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo` | 💳 Credits | Pay-per-token, very cheap |
| `modal` | Any HF vision model | 💳 Pay per second | Self-hosted GPU |
| `mock` | n/a | ✅ Free | Unit tests + dry runs |

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
