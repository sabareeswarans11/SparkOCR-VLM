# MODELS.md — DeepSeek-OCR-v2 + Qwen3-VL

The library targets two primary VLMs. This doc captures the prompts, parameters, and quirks for each, plus the OpenRouter / Together / Gemini model IDs.

## DeepSeek-OCR-v2

**Strengths:** strong on dense scanned documents, tables, multilingual. Token-efficient compared to general VLMs.

**Weaknesses:** weaker on free-form natural images.

### Model IDs
| Provider | Model ID |
|---|---|
| OpenRouter | `deepseek-ai/DeepSeek-OCR-v2` (also `:free` variant when available) |
| Together.ai | `deepseek-ai/DeepSeek-OCR-v2` |
| Hugging Face (Modal) | `deepseek-ai/DeepSeek-OCR-v2` |

### Default prompt
```
You are a document OCR engine. Read the image and emit the document content
as well-structured Markdown. Preserve headings, paragraphs, lists, and tables.
Tables MUST be valid Markdown tables. Do not summarize. Do not add commentary.
Return ONLY the Markdown.
```

### Default sampling params
```python
temperature = 0.0
max_tokens  = 4096   # bump for dense pages
top_p       = 1.0
```

### Quirks
- Sometimes wraps output in ```` ```markdown ... ``` ```` fences. The backend strips them.
- Returns blank output if the page is mostly whitespace — we treat blank as a valid empty page (not an error).
- Table boundaries occasionally drop trailing pipes. The schema validator does NOT reject this; the evaluator scores tables permissively.

## Qwen3-VL

**Strengths:** strong general reasoning, decent on scanned docs, very good on receipts and natural images.

**Weaknesses:** higher token usage; more "helpful" preamble unless prompted strictly.

### Model IDs
| Provider | Model ID |
|---|---|
| OpenRouter | `qwen/qwen3-vl-instruct` (also `:free`) |
| Together.ai | `Qwen/Qwen3-VL-Instruct` |
| Hugging Face (Modal) | `Qwen/Qwen3-VL-Instruct` |

### Default prompt
Same as DeepSeek's, but with stricter "no preamble" suffix:
```
... Return ONLY the Markdown. Do not write "Here is the markdown:" or any
similar preface. Begin directly with the document content.
```

### Default sampling params
```python
temperature = 0.0
max_tokens  = 4096
top_p       = 0.95   # Qwen behaves slightly better with this
```

### Quirks
- Will occasionally still add a preamble — the backend post-processor strips known leading phrases.
- Reading order on multi-column pages is sometimes column-major instead of row-major. We log this in the evaluator's `reading_order_edit_distance` metric.

## Switching models at runtime

`OCRPipeline(backend="openrouter", model="<model_id>")` is enough. The backend dispatches per model:

```python
class OpenRouterBackend(VLMBackend):
    def parse_image(self, image_bytes, prompt=None):
        prompt = prompt or DEFAULT_PROMPT_BY_MODEL[self.model]
        params = SAMPLING_PARAMS_BY_MODEL[self.model]
        ...
```

The constants are defined in `backends/openrouter.py`:

```python
DEFAULT_PROMPT_BY_MODEL = {
    "deepseek-ai/DeepSeek-OCR-v2": DEEPSEEK_PROMPT,
    "qwen/qwen3-vl-instruct": QWEN_PROMPT,
}

SAMPLING_PARAMS_BY_MODEL = {
    "deepseek-ai/DeepSeek-OCR-v2": {"temperature": 0.0, "max_tokens": 4096, "top_p": 1.0},
    "qwen/qwen3-vl-instruct":      {"temperature": 0.0, "max_tokens": 4096, "top_p": 0.95},
}
```

## Cost estimates (May 2026, OpenRouter free tier)

| Model | Free? | Approx $/1M tokens (paid) | Notes |
|---|---|---|---|
| `deepseek-ai/DeepSeek-OCR-v2:free` | yes (rate-limited) | $0 | First choice for dev. |
| `qwen/qwen3-vl-instruct:free` | yes (rate-limited) | $0 | Fallback if DeepSeek rate-limits. |
| `deepseek-ai/DeepSeek-OCR-v2` (paid) | no | ~$0.10 input / $0.30 output | Cheap. |
| `qwen/qwen3-vl-instruct` (paid) | no | ~$0.20 input / $0.60 output | Higher token use. |

These numbers are baked into `utils/cost.py::PRICE_TABLE`. Update when OpenRouter pricing shifts.

## Adding a new model

1. Add an entry to `DEFAULT_PROMPT_BY_MODEL` and `SAMPLING_PARAMS_BY_MODEL` in the relevant backend.
2. Add a row to `PRICE_TABLE` in `utils/cost.py`.
3. Add an integration test (skip-marked if no API key).
4. Document quirks here.
