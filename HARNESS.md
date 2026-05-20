# HARNESS.md — Test Harness Engineering

> The harness is the **contract** between feature code and confidence. Every subagent's output is validated through it. This doc is the harness reference.

## Goals

1. Generate deterministic, byte-identical test data on any machine.
2. Provide a single `assert_golden_md(actual, name=...)` helper that all tests use.
3. Provide a perf benchmark CLI that emits a Markdown report.
4. Stay zero-dependency beyond what `pyproject.toml [dev]` already pulls.

## Components

### 1. `tests/harness/synthetic_pdf.py`

Builds the three permanent synthetic PDFs using `reportlab`. Seeded — same bytes every run.

```python
class SyntheticPDFBuilder:
    def __init__(self, out_dir: Path, seed: int = 42): ...
    def build_invoice(self) -> Path: ...
    def build_report(self) -> Path: ...
    def build_table(self) -> Path: ...
    def build_all(self) -> list[Path]: ...
```

CLI:
```bash
python -m tests.harness.synthetic_pdf --out tests/fixtures
```

### 2. `tests/harness/golden.py`

```python
GOLDEN_DIR = Path("tests/fixtures/golden")

def load_golden(name: str) -> str:
    return (GOLDEN_DIR / f"{name}.md").read_text()

def normalize_md(md: str) -> str:
    """Lower, strip ```fences, collapse whitespace, drop trailing punctuation."""
    ...

def edit_distance(a: str, b: str) -> float:
    """Normalized Levenshtein distance, 0.0 = identical."""
    ...

def assert_golden_md(actual: str, name: str, tol: float = 0.05) -> None:
    expected = normalize_md(load_golden(name))
    actual_n = normalize_md(actual)
    d = edit_distance(actual_n, expected)
    assert d <= tol, f"golden mismatch for {name}: edit_distance={d:.3f} > tol={tol}"
```

### 3. `tests/harness/perf.py`

```bash
python -m tests.harness.perf --pages 20 --backend mock --output runtime/BENCH.md
```

Emits to `runtime/BENCH.md`:

```
# BENCH.md — last run 2026-05-19T14:22Z

Backend: mock
Pages:   20
Wall:    4.12s
PPS:     4.85 pages/sec
Cost:    $0.000
```

## Contract for builders

Any new code path MUST:

1. **Have a unit test** that uses `mock_backend` and `assert_golden_md` (or a simpler assertion if no markdown is produced).
2. **Run under `pytest tests/ -m "not integration"`** with no API keys.
3. **Not introduce new top-level dependencies** without updating `pyproject.toml`.
4. **Not break** `python -m tests.harness.perf --backend mock` — perf must still complete.

## Extending the harness

### Add a new synthetic doc
1. Add a `build_<name>()` method to `SyntheticPDFBuilder`.
2. Register it in `build_all()`.
3. Generate the golden:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-... \
   python -m tests.harness.golden --regen synth_<name>
   ```
4. Commit the resulting `tests/fixtures/golden/synth_<name>.md`.
5. Add a test in `tests/test_processor.py`.

### Add a new metric to perf
1. Edit `tests/harness/perf.py::PerfRun.measure`.
2. Append to the markdown template in `PerfRun.to_markdown`.
3. Run `python -m tests.harness.perf --backend mock` and verify `runtime/BENCH.md` updates.

## Golden regeneration policy

Regenerating a golden file is a meaningful change. The workflow:
1. Make sure your change is intentional (e.g., the prompt changed).
2. Run the regen CLI with a real backend.
3. Diff the new golden against the old; eyeball it.
4. Commit both the source change and the golden in the same commit, with a message explaining the regen.

`runtime/DECISIONS.md` should also get an ADR-lite entry from `doc-scribe`.

## Why edit distance + tolerance

VLMs aren't deterministic across providers (even at `temperature=0`). A normalized edit distance ≤ 5% catches real regressions while tolerating cosmetic drift. If you need stricter checks for a specific test, do exact string match on key tokens:

```python
assert "INV-2024-001" in md_output
assert "Total: $1,234.56" in md_output
```

## What the harness does NOT do

- It does not run a real Spark cluster. Always `local[2]`.
- It does not hit real APIs in unit tests. Integration tests do, and they're marked.
- It does not test Databricks deployment — that's a manual smoke run via `02_databricks_free.ipynb`.
