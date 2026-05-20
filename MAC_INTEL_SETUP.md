# MAC_INTEL_SETUP.md — Local Dev on MacBook Pro 16" 2019 (Intel)

> Hardware target: 16" 2019 MBP, Intel Core i7/i9, 16–32 GB RAM, **no NVIDIA GPU**. Apple Silicon users — most of this still works, but a few notes are flagged.

## TL;DR

```bash
# 1. Python + uv
brew install python@3.11 uv openjdk@17

# 2. JDK on PATH (Spark needs it)
echo 'export JAVA_HOME=$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# 3. Project
cd ~/Projects_26/SparkOCR-VLM
uv sync --extra dev
cp .env.template .env   # add OPENROUTER_API_KEY

# 4. Smoke test
./scripts/run_smoke.sh
```

## Why no local model

Intel MBP 2019 = no CUDA. Apple Silicon = no CUDA either, and MPS support in `transformers` for VLMs is patchy (DeepSeek-OCR-v2 is not officially MPS-tested). Pulling a 7B+ VLM onto a laptop and running CPU inference is unusable (~minutes per page). Therefore: **all inference is via HTTP API**.

## Java / Spark prerequisites

PySpark 3.5 runs on Java 17. Use Homebrew's openjdk@17.

```bash
brew install openjdk@17
# Make sure it's first on PATH
java -version    # should say OpenJDK 17
```

If you see `Unsupported class file major version 65` errors, you're on Java 21+ — downgrade.

## Memory tuning

The Intel MBP can run `local[*]` Spark but you should cap memory or it'll swap:

```python
SparkSession.builder.master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "4") \
    ...
```

For tests, we use `local[2]` and `2g` driver memory — comfortable on 16 GB RAM.

## Apple Silicon notes

If you happen to be on M1/M2/M3:
- Use `arch -x86_64 brew install ...` only if you hit native arm issues with `pymupdf` (rare).
- `delta-spark` 3.2 has native arm wheels via `delta-spark_2.12`. No special steps.

## Test data (synthetic)

Synthetic PDFs are generated on first test run by `tests/harness/synthetic_pdf.py`. They use `reportlab` (pure Python, works on Intel). You don't need to commit any real PDFs.

```bash
# Generate them manually:
python -m tests.harness.synthetic_pdf --out tests/fixtures
```

This produces:
- `synth_invoice.pdf` — single-page invoice with known totals.
- `synth_report.pdf` — two-page report with headings + paragraphs.
- `synth_table.pdf` — single-page document with a 5x4 table.

Golden outputs (`tests/fixtures/golden/*.md`) get generated the first time a real backend is hit, then committed.

## OpenRouter API key

1. Sign up at https://openrouter.ai/
2. Generate an API key. Free tier covers basic dev usage — Qwen3-VL and DeepSeek-OCR-v2 free variants exist.
3. Drop into `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

## Optional: MinIO for S3 testing

```bash
docker compose up -d
# MinIO console at http://localhost:9001 (minio / minio12345)
```

Then in `.env`:
```
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio12345
```

`utils/spark_helpers.py::build_local_spark(s3=True)` will wire the hadoop-aws conf for you.

## Running the test suite

```bash
# Unit tests only (no API keys needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (needs OPENROUTER_API_KEY)
uv run pytest tests/ -m integration -v

# Perf harness
uv run python -m tests.harness.perf --pages 20 --backend mock
```

Expected unit-test run time on a 2019 MBP: ~25–45 s (Spark session startup dominates).

## PyCharm setup

1. Open `~/Projects_26/SparkOCR-VLM` as a project.
2. Configure the interpreter: `~/Projects_26/SparkOCR-VLM/.venv/bin/python` (created by `uv sync`).
3. Mark `src/` as Sources Root.
4. Mark `tests/` as Test Sources Root.
5. In Run/Debug configurations → Python tests → pytest, point at `tests/`.
6. Install the Claude Code plugin; it will pick up `CLAUDE.md` automatically.

## Common pitfalls on Intel Mac

| Symptom | Fix |
|---|---|
| `JAVA_HOME` not set | `brew --prefix openjdk@17` + export. |
| `pymupdf` build error | `brew install mupdf`, retry. |
| `pyspark` hangs on `getOrCreate` | Kill orphan `java` processes (`pkill -9 java`). |
| Tests OOM | Lower `spark.driver.memory` to `2g`, use `local[2]`. |
| `httpx` SSL errors against OpenRouter | `pip install --upgrade certifi`. |
