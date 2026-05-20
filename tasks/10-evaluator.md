# 10 — Evaluator

## Goal
Score pipeline outputs against ground-truth markdown. Logs to MLflow.

## Outputs
- `src/sparkocr_vlm/evaluator.py`

## API
```python
class Evaluator:
    def __init__(self, ground_truth_dir: Path): ...
    def score_df(self, df: DataFrame | pd.DataFrame) -> dict[str, float]:
        """Returns {edit_distance, exact_token_recall, table_f1, reading_order_ed}."""
    def log_to_mlflow(self, metrics: dict, run_name: str = "eval"): ...
```

## Metrics
- `edit_distance` — mean normalized Levenshtein per page (lower is better).
- `exact_token_recall` — fraction of "anchor strings" (per-doc keyword list) present.
- `table_f1` — cell-level F1 if ground truth contains a Markdown table.
- `reading_order_ed` — edit distance on line sequence (proxy for column order).

## DoD
- `Evaluator(...).score_df(...)` returns all four metrics.
- MLflow run produced when `log_to_mlflow=True`.
