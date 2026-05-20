# 04 — Backends Base + Mock

## Goal
The `VLMBackend` ABC and a `MockBackend` that returns canned `OCROutput` based on input bytes hash. Mock is the test bedrock — make it good.

## Outputs
- `src/sparkocr_vlm/backends/__init__.py` (factory `get_backend(name, **kwargs)`)
- `src/sparkocr_vlm/backends/base.py`
- `src/sparkocr_vlm/backends/mock.py`

## `base.py`
```python
class VLMBackend(ABC):
    name: str
    model: str
    @abstractmethod
    def parse_image(self, image_bytes: bytes, prompt: str | None = None) -> OCROutput: ...
    @abstractmethod
    def estimate_cost(self, page_count: int) -> float: ...
```

## `mock.py`
Lookup table keyed by sha256(image_bytes) → markdown. Falls back to a default "Lorem ipsum" output. Used in all unit tests.

```python
class MockBackend(VLMBackend):
    name = "mock"
    def __init__(self, model: str = "mock-model"):
        self.model = model
    def parse_image(self, image_bytes, prompt=None):
        sha = hashlib.sha256(image_bytes).hexdigest()
        md = MOCK_TABLE.get(sha, DEFAULT_MOCK_MARKDOWN)
        return OCROutput(markdown=md, model=self.model, doc_type="other", confidence=1.0)
    def estimate_cost(self, page_count): return 0.0
```

## DoD
- `MockBackend().parse_image(b"x").markdown` returns non-empty string.
- `get_backend("mock")` returns a `MockBackend`.
