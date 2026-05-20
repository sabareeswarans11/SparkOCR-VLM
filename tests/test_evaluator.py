"""Tests for evaluator metrics."""

from __future__ import annotations

from sparkocr_vlm.evaluator import (
    Evaluator,
    anchor_recall,
    normalized_edit_distance,
    reading_order_edit_distance,
    table_cell_f1,
)


def test_edit_distance_identical():
    assert normalized_edit_distance("abc", "abc") == 0.0


def test_edit_distance_partial():
    d = normalized_edit_distance("hello world", "hallo world")
    assert 0 < d < 0.2


def test_anchor_recall():
    assert anchor_recall("foo bar baz", ["bar", "baz"]) == 1.0
    assert anchor_recall("foo", ["bar", "baz"]) == 0.0
    assert anchor_recall("Foo Bar", ["bar"]) == 1.0


def test_reading_order():
    assert reading_order_edit_distance("a\nb", "a\nb") == 0.0


def test_table_f1_perfect():
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    assert table_cell_f1(md, md) == 1.0


def test_evaluator_against_golden(fixtures_dir, mock_pipeline):
    df = mock_pipeline.parse_single(fixtures_dir / "synth_invoice.pdf")
    ev = Evaluator(ground_truth_dir=fixtures_dir / "golden")
    metrics = ev.score_df(df)
    assert metrics["n_pages_scored"] >= 1
    assert metrics["edit_distance"] <= 0.05
