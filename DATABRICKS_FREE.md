# DATABRICKS_FREE.md — Running SparkOCR-VLM on Databricks Free Edition

> **Constraint:** we use the Databricks **Free Edition** (no paid workspace, no DLT, no Unity Catalog premium, no JOBS API on some Free tiers). Everything below assumes only what Free gives you: a notebook-driven serverless compute, Volumes, and Delta.

## Free Edition: what we get and what we don't

| Capability | Free Edition | What we do about it |
|---|---|---|
| Serverless notebook compute | ✅ | Run the pipeline inline in a notebook. |
| Delta tables | ✅ | Write silver Delta to a Volume path. |
| Volumes (managed file storage) | ✅ | Upload sample PDFs there. |
| Jobs / Workflows | ⚠️ limited | Stick to notebook-runs for the demo. |
| Cluster config | ❌ no init scripts on Free | `%pip install` inside the notebook. |
| MLflow tracking | ✅ (workspace-scoped) | Log eval metrics. |
| Foundation Model endpoints | ⚠️ varies | Default to OpenRouter to stay portable. |

## End-to-end recipe

### 1. Create a Volume
In the workspace UI: **Catalog → workspace → default → Create Volume → `sparkocr_demo`**.

### 2. Upload sample PDFs
Drag-drop into `/Volumes/workspace/default/sparkocr_demo/input/`.

Or, from your laptop:
```bash
databricks fs cp tests/fixtures/synth_invoice.pdf dbfs:/Volumes/workspace/default/sparkocr_demo/input/
```

### 3. Open the demo notebook
Open `notebooks/02_databricks_free.ipynb`. Top cells install the package and set keys:

```python
%pip install -q sparkocr-vlm
dbutils.library.restartPython()
```

```python
import os
os.environ["OPENROUTER_API_KEY"] = dbutils.secrets.get(scope="sparkocr", key="openrouter")
```

(If you don't have a secret scope on Free, paste the key directly during the demo — but never commit it.)

### 4. Run
```python
from sparkocr_vlm import OCRPipeline

pipeline = OCRPipeline(
    backend="openrouter",
    model="deepseek-ai/DeepSeek-OCR-v2",
    input_path="/Volumes/workspace/default/sparkocr_demo/input/",
    output_path="/Volumes/workspace/default/sparkocr_demo/silver/",
    batch_size=4,
    max_cost_usd=0.50,
)

df = pipeline.run(spark)
display(df)
```

### 5. Query the silver table
```python
spark.read.format("delta") \
    .load("/Volumes/workspace/default/sparkocr_demo/silver/") \
    .createOrReplaceTempView("ocr_silver")
```

```sql
SELECT filename, page_num, doc_type, cost_usd
FROM ocr_silver
ORDER BY cost_usd DESC
LIMIT 20;
```

## Why this works on Free

- We do not need GPUs — inference is offloaded to OpenRouter.
- We do not need init scripts — `%pip install` covers dependency setup.
- We do not need Jobs — the notebook is the entrypoint.
- We do not need premium catalog features — Volumes are enough.

## Cost on Free

The Free Edition gives you a small monthly compute quota. Our pipeline is API-bound — the workspace compute is barely used (Spark just orchestrates batches). Most of your "cost" is the OpenRouter API call, which has its own free tier for Qwen3-VL and DeepSeek-OCR-v2 variants.

Recommended caps for a demo:
- `batch_size=4`
- `max_cost_usd=0.50`
- Limit input to ~25 pages on the first run.

## If Foundation Model endpoints are available

When Databricks adds Qwen3-VL or DeepSeek-OCR-v2 to their hosted Foundation Models (variable by region/Free entitlement), you can route the backend at the endpoint directly. We plan to add a `databricks` backend in v0.2. Until then, OpenRouter is the path.

## Troubleshooting

| Issue | Fix |
|---|---|
| `%pip install` times out | Restart the workspace, retry; Free compute warms slowly. |
| `Cannot find module sparkocr_vlm` after install | `dbutils.library.restartPython()` and re-import. |
| Delta write fails on Volume path | Verify the Volume name in the UI matches the path exactly. |
| OpenRouter 401 | Re-paste the key; check it starts with `sk-or-v1-`. |
| Pages produce empty markdown | Likely a free model rate-limit. Lower `batch_size` to 2. |

## Pushing the demo notebook

```bash
databricks workspace import \
  /Users/<you>/sparkocr_free_demo \
  --file notebooks/02_databricks_free.ipynb \
  --format JUPYTER
```

Or just drag-drop the `.ipynb` into the workspace.
