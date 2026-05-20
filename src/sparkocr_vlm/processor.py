"""PySpark UDF wrapping a VLM backend. Executor-local singleton.

Importable without pyspark installed — the UDF is only constructed on demand.
"""

from collections.abc import Callable
from typing import Any

from sparkocr_vlm.backends import VLMBackend, get_backend
from sparkocr_vlm.schema import OCROutput

# Per-executor (= per-Python-process) singleton store.
_BACKEND_CACHE: dict[tuple[str, str], VLMBackend] = {}


def _get_or_create(backend_name: str, model: str, **kwargs: Any) -> VLMBackend:
    key = (backend_name, model)
    if key not in _BACKEND_CACHE:
        _BACKEND_CACHE[key] = get_backend(backend_name, model=model, **kwargs)
    return _BACKEND_CACHE[key]


def parse_batch(
    backend_name: str,
    model: str,
    images: list[bytes],
    **kwargs: Any,
) -> list[dict]:
    """Synchronous batch parser. Used by both the UDF and parse_single."""
    backend = _get_or_create(backend_name, model, **kwargs)
    out: list[dict] = []
    for img in images:
        try:
            out.append(backend.parse_image(img).model_dump())
        except Exception as e:  # noqa: BLE001
            out.append(
                OCROutput(
                    markdown="", model=model, error=f"{type(e).__name__}: {e}"
                ).model_dump()
            )
    return out


def make_ocr_udf(backend_name: str, model: str, **kwargs: Any) -> Callable:
    """Return a ``pandas_udf`` bound to the given backend.

    The returned UDF accepts a ``pd.Series[bytes]`` and emits a ``pd.DataFrame``
    matching ``OCR_OUTPUT_SPARK_SCHEMA``.
    """
    import pandas as pd
    from pyspark.sql.functions import PandasUDFType, pandas_udf

    from sparkocr_vlm.schema import get_ocr_output_spark_schema

    def _impl(image_series: pd.Series) -> pd.DataFrame:
        rows = parse_batch(backend_name, model, list(image_series.values), **kwargs)
        return pd.DataFrame(rows)

    return pandas_udf(_impl, returnType=get_ocr_output_spark_schema(), functionType=PandasUDFType.SCALAR)
