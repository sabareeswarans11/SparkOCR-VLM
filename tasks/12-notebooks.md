# 12 — Notebooks

## Outputs
- `notebooks/01_quickstart.ipynb`
- `notebooks/02_databricks_free.ipynb`
- `notebooks/03_evaluation.ipynb`

## 01 — Local quickstart
Self-contained on Intel Mac. Cells:
1. Install (`%pip install -e .`).
2. Build local Spark with `build_local_spark()`.
3. Generate synthetic PDFs (calls `SyntheticPDFBuilder`).
4. Run pipeline with mock backend.
5. Show silver DataFrame.
6. Swap to OpenRouter backend; re-run; show diff.

## 02 — Databricks Free
Follow `DATABRICKS_FREE.md`. Uses `/Volumes/...` paths.

## 03 — Evaluation
Calls `Evaluator` on a small olmOCR-Bench subset (lazy-downloaded; skip cell if offline). Plots edit-distance bar chart per doc with matplotlib.

## DoD
- All three notebooks execute top-to-bottom on a clean checkout (with mock backend) without errors.
