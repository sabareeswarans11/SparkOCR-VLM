# 08 — Processor UDF

## Goal
`pandas_udf` wrapper around the active backend. Singleton per executor. Arrow-batched. Cost-aware.

## Outputs
- `src/sparkocr_vlm/processor.py`

## API
```python
def make_ocr_udf(backend_name: str, model: str, **backend_kwargs) -> Callable:
    """Returns a pandas_udf bound to the given backend."""
```

## Implementation pattern
```python
def make_ocr_udf(backend_name, model, **kw):
    @pandas_udf(OCR_OUTPUT_SPARK_SCHEMA)
    def _udf(image_series: pd.Series) -> pd.DataFrame:
        backend = _get_or_create(backend_name, model, **kw)
        rows = []
        for img in image_series:
            try:
                rows.append(backend.parse_image(img).model_dump())
            except Exception as e:
                rows.append(OCROutput(markdown="", model=model, error=str(e)).model_dump())
        return pd.DataFrame(rows)
    return _udf
```

`_get_or_create` is a module-level `dict`-backed singleton (lives on each executor naturally because Python modules are re-imported per executor process).

## Constraints
- No closures over backend instances at module load — only on first UDF call.
- API keys come from executor env via `Settings`.
- Errors NEVER raise out of the UDF; they become `error=<msg>` rows.

## DoD
- Unit test that runs a 3-row DataFrame of mock PNGs through the UDF and gets back 3 markdown strings.
