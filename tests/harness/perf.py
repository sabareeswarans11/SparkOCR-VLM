"""Throughput / cost benchmark. Writes results to runtime/BENCH.md.

Usage:
    python -m tests.harness.perf --pages 20 --backend mock
"""

from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime
from pathlib import Path

from sparkocr_vlm.backends import get_backend


def run_perf(pages: int, backend: str, model: str, output: Path) -> dict:
    be = get_backend(backend, model=model)

    # 1x1 transparent PNG (smallest valid)
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x9b\x9b\xa9\xa6\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    t0 = time.perf_counter()
    total_cost = 0.0
    n_err = 0
    for _ in range(pages):
        out = be.parse_image(tiny_png)
        total_cost += out.cost_usd or 0.0
        if out.error:
            n_err += 1
    wall = time.perf_counter() - t0
    pps = pages / wall if wall > 0 else 0.0
    mean_lat = wall / pages if pages else 0.0

    report = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
        "backend": backend,
        "model": model,
        "pages": pages,
        "wall_s": round(wall, 3),
        "pages_per_sec": round(pps, 3),
        "mean_latency_s": round(mean_lat, 4),
        "total_cost_usd": round(total_cost, 6),
        "errors": n_err,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"# BENCH — last run {report['ts']}\n\n"
        f"Backend:    {report['backend']}\n"
        f"Model:      {report['model']}\n"
        f"Pages:      {report['pages']}\n"
        f"Wall:       {report['wall_s']}s\n"
        f"PPS:        {report['pages_per_sec']} pages/sec\n"
        f"Mean lat:   {report['mean_latency_s']}s/page\n"
        f"Cost:       ${report['total_cost_usd']}\n"
        f"Errors:     {report['errors']}\n"
    )
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=20)
    ap.add_argument("--backend", default="mock")
    ap.add_argument("--model", default="mock-model")
    ap.add_argument("--output", default="runtime/BENCH.md")
    args = ap.parse_args()
    report = run_perf(args.pages, args.backend, args.model, Path(args.output))
    print(report)


if __name__ == "__main__":
    main()
