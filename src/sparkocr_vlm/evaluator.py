"""Evaluator — score pipeline output against ground-truth markdown."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd


# ---------- text helpers ----------

def _normalize(s: str) -> str:
    """Lowercase, strip code fences, collapse whitespace."""
    if not s:
        return ""
    s = re.sub(r"```(?:markdown|md)?\s*\n?|\n?```", "", s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def normalized_edit_distance(a: str, b: str) -> float:
    """Return Levenshtein distance / max(len(a), len(b)), in [0, 1]."""
    na, nb = _normalize(a), _normalize(b)
    m = max(len(na), len(nb))
    if m == 0:
        return 0.0
    return _levenshtein(na, nb) / m


def anchor_recall(actual: str, anchors: Iterable[str]) -> float:
    """Fraction of ``anchors`` (case-insensitive) present in ``actual``."""
    anchors = list(anchors)
    if not anchors:
        return 1.0
    low = actual.lower()
    hits = sum(1 for a in anchors if a.lower() in low)
    return hits / len(anchors)


def reading_order_edit_distance(actual: str, expected: str) -> float:
    """Edit distance on the sequence of line first-tokens (proxy for column order)."""
    def first_tokens(s: str) -> list[str]:
        out = []
        for line in s.splitlines():
            line = line.strip()
            if not line:
                continue
            tok = re.split(r"\s+", line, maxsplit=1)[0].lower()
            out.append(tok)
        return out

    a, b = first_tokens(actual), first_tokens(expected)
    if not a and not b:
        return 0.0
    # Treat tokens as characters by joining with a delimiter unlikely to appear.
    sa, sb = "|".join(a), "|".join(b)
    m = max(len(sa), len(sb))
    return _levenshtein(sa, sb) / max(m, 1)


def extract_tables(md: str) -> list[list[list[str]]]:
    """Extract markdown tables as nested lists [tables][rows][cells]."""
    tables: list[list[list[str]]] = []
    rows: list[list[str]] = []
    for line in md.splitlines():
        if "|" in line and re.search(r"\S", line):
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if all(re.match(r"^-+:?$|^:?-+:?$|^-+$", p) for p in parts):
                continue  # separator row
            rows.append(parts)
        elif rows:
            tables.append(rows)
            rows = []
    if rows:
        tables.append(rows)
    return tables


def table_cell_f1(actual: str, expected: str) -> float:
    """Macro cell-level F1 across all tables in the expected output."""
    e_tables = extract_tables(expected)
    if not e_tables:
        return 1.0  # nothing to score
    a_tables = extract_tables(actual)
    expected_cells = {c.lower() for t in e_tables for r in t for c in r if c}
    actual_cells = {c.lower() for t in a_tables for r in t for c in r if c}
    if not expected_cells:
        return 1.0
    tp = len(expected_cells & actual_cells)
    fp = len(actual_cells - expected_cells)
    fn = len(expected_cells - actual_cells)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


# ---------- evaluator ----------

class Evaluator:
    """Score pipeline outputs against per-document ground-truth markdown."""

    def __init__(
        self,
        ground_truth_dir: str | Path,
        anchors_by_doc: dict[str, list[str]] | None = None,
    ) -> None:
        self.gt_dir = Path(ground_truth_dir)
        self.anchors = anchors_by_doc or {}

    def _gt_for(self, filename: str, page_num: int) -> str | None:
        # Convention: <stem>.md for single-page, <stem>_p<N>.md for multi-page.
        stem = Path(filename).stem
        candidates = [
            self.gt_dir / f"{stem}_p{page_num}.md",
            self.gt_dir / f"{stem}.md",
        ]
        for c in candidates:
            if c.exists():
                return c.read_text()
        return None

    def score_df(self, df) -> dict[str, float]:
        """Score a pandas DataFrame with columns filename, page_num, markdown."""
        if hasattr(df, "toPandas"):  # PySpark DataFrame
            df = df.toPandas()
        eds: list[float] = []
        recs: list[float] = []
        f1s: list[float] = []
        ros: list[float] = []
        for _, row in df.iterrows():
            gt = self._gt_for(str(row["filename"]), int(row["page_num"]))
            if gt is None:
                continue
            actual = str(row.get("markdown") or "")
            eds.append(normalized_edit_distance(actual, gt))
            ros.append(reading_order_edit_distance(actual, gt))
            anchors = self.anchors.get(Path(str(row["filename"])).stem, [])
            recs.append(anchor_recall(actual, anchors))
            f1s.append(table_cell_f1(actual, gt))

        def mean(xs: list[float]) -> float:
            return sum(xs) / len(xs) if xs else 0.0

        return {
            "edit_distance": mean(eds),
            "exact_token_recall": mean(recs),
            "table_f1": mean(f1s),
            "reading_order_ed": mean(ros),
            "n_pages_scored": len(eds),
        }

    def log_to_mlflow(self, metrics: dict, run_name: str = "eval") -> None:
        try:
            import mlflow
        except ImportError:
            return
        with mlflow.start_run(run_name=run_name):
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    mlflow.log_metric(k, float(v))
