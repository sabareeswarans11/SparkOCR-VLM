# 01 — Scaffold

## Goal
Empty project skeleton with `pyproject.toml`, `.env.template`, `.gitignore`, `LICENSE`, and import-clean Python modules.

## Outputs
- `pyproject.toml`
- `.env.template`
- `.gitignore`
- `LICENSE` (MIT)
- `src/sparkocr_vlm/__init__.py` (exports `OCRPipeline`, `__version__`)
- All other `src/sparkocr_vlm/*.py` exist as empty stubs.

## Steps
1. Use the `pyproject.toml` template from `CLAUDE.md` § Dependencies.
2. Pin Python 3.11.
3. `src/sparkocr_vlm/__init__.py`:
   ```python
   from sparkocr_vlm.pipeline import OCRPipeline
   __version__ = "0.1.0"
   __all__ = ["OCRPipeline", "__version__"]
   ```
4. Create `.gitignore` (cover `.venv`, `__pycache__`, `*.egg-info`, `tests/fixtures/*.pdf`, `tests/fixtures/local_only/`, `.env`, `output_delta/`, `mlruns/`).
5. Copy MIT `LICENSE`.

## DoD
- `uv sync --extra dev` succeeds.
- `python -c "import sparkocr_vlm"` succeeds (after pipeline stub exists).
