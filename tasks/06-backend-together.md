# 06 — Together.ai Backend (Alt)

## Goal
Alt backend pointed at Together's OpenAI-compatible API. Same wire format as OpenRouter; different base URL and model IDs.

## Outputs
- `src/sparkocr_vlm/backends/together.py`

## API
```python
class TogetherBackend(VLMBackend):
    name = "together"
    BASE_URL = "https://api.together.xyz/v1"
    def __init__(self, model="deepseek-ai/DeepSeek-OCR-v2", api_key=None, timeout=60.0): ...
```

## Implementation
- 90% reuse from OpenRouter: factor shared helpers into a private `_oai_compatible.py` if needed.
- Header: `Authorization: Bearer $TOGETHER_API_KEY`.

## DoD
- Unit tests pass with mocked transport.
- Integration test gated on `TOGETHER_API_KEY` (optional, skip if missing).
