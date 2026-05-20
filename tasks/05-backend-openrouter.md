# 05 — OpenRouter Backend (DEFAULT)

## Goal
Production backend hitting OpenRouter's OpenAI-compatible chat/completions endpoint with vision. Routes both DeepSeek-OCR-v2 and Qwen3-VL.

## Outputs
- `src/sparkocr_vlm/backends/openrouter.py`

## API
```python
class OpenRouterBackend(VLMBackend):
    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"
    def __init__(self, model: str = "deepseek-ai/DeepSeek-OCR-v2", api_key: str | None = None, timeout: float = 60.0): ...
    def parse_image(self, image_bytes, prompt=None) -> OCROutput: ...
    def estimate_cost(self, page_count) -> float: ...
```

## Wire format
- POST `/chat/completions` with messages containing `image_url` of `data:image/png;base64,<b64>`.
- Headers: `Authorization: Bearer $OPENROUTER_API_KEY`, `HTTP-Referer: https://github.com/sabareeswarans11/SparkOCR-VLM`, `X-Title: SparkOCR-VLM`.
- Use `httpx.AsyncClient` + `asyncio.run` for Spark sync compatibility.
- Retry with `tenacity` on 5xx / connection errors (3 attempts, exp backoff).

## Per-model defaults
From `MODELS.md`:
- DeepSeek-OCR-v2 → temp=0.0, top_p=1.0, max_tokens=4096
- Qwen3-VL → temp=0.0, top_p=0.95, max_tokens=4096

## Post-processing
- Strip ```` ```markdown ... ``` ```` fences if present.
- Strip known Qwen preambles ("Here is the markdown:", "Sure! Here is...", etc.).
- Populate `prompt_tokens`/`completion_tokens` from response `usage` block.
- Compute `cost_usd` via `utils/cost.py::estimate_cost`.

## DoD
- Mock-mode unit tests pass (use respx or `httpx.MockTransport`).
- Integration test (gated on `OPENROUTER_API_KEY`) returns non-empty markdown for `synth_invoice.pdf` page 1.
