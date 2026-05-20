# 11 — Tests + Harness

## Goal
Everything in `tests/`: conftest, harness, unit + integration tests, fixture generator. Read `HARNESS.md` and `TESTING.md` before starting.

## Outputs
- `tests/conftest.py`
- `tests/harness/__init__.py`
- `tests/harness/synthetic_pdf.py`
- `tests/harness/golden.py`
- `tests/harness/perf.py`
- `tests/test_page_extractor.py`
- `tests/test_backends_mock.py`
- `tests/test_backends_openrouter.py` (integration-marked)
- `tests/test_processor.py`
- `tests/test_pipeline.py`
- `tests/test_evaluator.py`
- `tests/test_harness.py`
- `tests/fixtures/golden/synth_invoice.md`
- `tests/fixtures/golden/synth_report.md`
- `tests/fixtures/golden/synth_table.md`

## Synthetic PDFs
`SyntheticPDFBuilder` uses `reportlab`. Seed = 42. Three builders described in TESTING.md.

## Golden initial values
Until a real backend run is verified, the golden files contain the EXPECTED text of the synthetic doc (since the synthetic doc's source is deterministic, we know what text the OCR should recover). The mock backend's lookup table is keyed off the synthetic PDF PNG hashes and returns these markdowns verbatim — so unit tests pass exactly.

## DoD
- `pytest tests/ -m "not integration"` is green with no API keys set.
- Synthetic PDFs regenerate identically across runs (sha256 match).
- `python -m tests.harness.perf --backend mock --pages 20` writes `runtime/BENCH.md`.
