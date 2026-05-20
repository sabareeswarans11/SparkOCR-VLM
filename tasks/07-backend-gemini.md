# 07 — Gemini Backend (Alt)

## Goal
Google AI Studio / Gemini API as fallback when OpenRouter rate-limits.

## Outputs
- `src/sparkocr_vlm/backends/gemini.py`

## API
```python
class GeminiBackend(VLMBackend):
    name = "gemini"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    def __init__(self, model="gemini-2.0-flash", api_key=None, timeout=60.0): ...
```

## Wire format
- POST `/models/<model>:generateContent?key=$GEMINI_API_KEY`.
- Inline image as base64 in `parts[].inline_data`.
- No "image_url" — Gemini uses its own shape.
- Extract markdown from `candidates[0].content.parts[0].text`.

## DoD
- Unit tests pass with mocked transport.
