"""Per-call cost estimation + dev-time logging to runtime/COSTS.md."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from sparkocr_vlm.config import settings

# Prices per 1M tokens, USD. Update when providers change pricing.
# (input_price, output_price)
PRICE_TABLE: dict[str, tuple[float, float]] = {
    # OpenRouter (paid tier baseline; ":free" variants are $0)
    "deepseek-ai/DeepSeek-OCR-v2": (0.10, 0.30),
    "deepseek-ai/DeepSeek-OCR-v2:free": (0.0, 0.0),
    "qwen/qwen3-vl-instruct": (0.20, 0.60),
    "qwen/qwen3-vl-instruct:free": (0.0, 0.0),
    # Together.ai (rough)
    "Qwen/Qwen3-VL-Instruct": (0.20, 0.60),
    # Gemini
    "gemini-2.0-flash": (0.075, 0.30),
    # Mock
    "mock-model": (0.0, 0.0),
}


_COST_LOCK = Lock()


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Return USD cost for a single call given token counts."""
    p_in, p_out = PRICE_TABLE.get(model, (0.0, 0.0))
    return (prompt_tokens / 1_000_000) * p_in + (completion_tokens / 1_000_000) * p_out


def record_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pages: int = 1,
    runtime_dir: Path | None = None,
) -> float:
    """Compute the cost and (optionally) append a row to runtime/COSTS.md.

    Args:
        model: Model identifier.
        prompt_tokens: Tokens in the prompt.
        completion_tokens: Tokens in the completion.
        pages: Pages this call covered (almost always 1).
        runtime_dir: Override for tests. Defaults to ``runtime/`` next to cwd.

    Returns:
        The USD cost for this call.
    """
    cost = estimate_cost(model, prompt_tokens, completion_tokens)
    if not settings().log_costs:
        return cost

    dirpath = runtime_dir or Path(os.environ.get("SPARKOCR_RUNTIME_DIR", "runtime"))
    dirpath.mkdir(parents=True, exist_ok=True)
    path = dirpath / "COSTS.md"
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    with _COST_LOCK:
        if not path.exists():
            path.write_text(
                "# COSTS\n\nTotal dev spend so far: $0.0000\n\n"
                "| Date (UTC) | Model | Pages | Cost USD |\n"
                "|---|---|---|---|\n"
            )
        line = f"| {ts} | {model} | {pages} | ${cost:.4f} |\n"
        with path.open("a") as f:
            f.write(line)

    return cost
