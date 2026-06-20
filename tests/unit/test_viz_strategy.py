"""Unit tests for viz strategy registry, reports, and filters."""

from __future__ import annotations

import pandas as pd

from quant_platform.viz.strategy.filters import ScanFilters, apply_filters, scatter_dataframe
from quant_platform.viz.strategy.registry import get_viz_strategy
from quant_platform.viz.strategy.reports import (
    full_universe_dataframe,
    list_report_paths,
    report_to_dataframe,
    validate_report_strategy,
)


def test_list_report_paths_includes_swing_archives(tmp_path, monkeypatch):
    history = tmp_path / "history"
    archive_dir = history / "2026-06-19"
    archive_dir.mkdir(parents=True)
    report_file = archive_dir / "swing_scan_report.json"
    report_file.write_text("{}")

    monkeypatch.setattr("quant_platform.viz.strategy.reports.HISTORY_DIR", history)

    config = get_viz_strategy("swing")
    paths = list_report_paths(config)
    assert str(report_file) in paths
    assert paths[str(report_file)].startswith("Archive")


def test_report_to_dataframe_includes_filtered_scores():
    config = get_viz_strategy("breakout")
    tickers = [
        {
            "ticker": "AAA",
            "eligible": False,
            "tier": "filtered",
            "eligibility": {"fail_reason": "trend_misaligned"},
            "summary": {"final_adjusted_score": 42.0, "normalized_score": 42.0, "raw_score": 50.0},
            "scores": {
                "rs_market": {"score": 12.0, "max": 20},
                "compression": {"score": 8.0, "max": 15},
            },
        }
    ]
    df = report_to_dataframe({"tickers": tickers}, config)
    row = df.iloc[0]
    assert row["ticker"] == "AAA"
    assert not row["eligible"]
    assert row["final_score"] == 42.0
    assert row["filter_reason"] == "trend_misaligned"


def test_full_universe_dataframe_swing_labels():
    config = get_viz_strategy("swing")
    tickers = [
        {
            "ticker": "MU",
            "eligible": True,
            "tier": "A",
            "sector_etf": "SOXX",
            "eligibility": {"fail_reason": None},
            "summary": {"final_adjusted_score": 80.0, "normalized_score": 80.0, "raw_score": 90.0},
            "scores": {
                "trend": {"score": 25.0, "max": 30},
                "pullback": {"score": 20.0, "max": 25},
                "relative_strength": {"score": 18.0, "max": 20},
                "volume": {"score": 10.0, "max": 15},
            },
        }
    ]
    df = full_universe_dataframe(tickers, config)
    mu = df.iloc[0]
    assert mu["Weekly Trend"] == 25.0
    assert mu["Pullback Quality"] == 20.0
    assert "Pullback" in mu["top_signal"] or "Weekly" in mu["top_signal"]


def test_apply_filters_actionable_tiers_differ_by_strategy():
    df = pd.DataFrame(
        [
            {"ticker": "A", "tier": "Tier 1", "eligible": True, "final_score": 80},
            {"ticker": "B", "tier": "Tier 3", "eligible": True, "final_score": 50},
            {"ticker": "C", "tier": "A", "eligible": True, "final_score": 70},
            {"ticker": "D", "tier": "C", "eligible": True, "final_score": 40},
        ]
    )
    breakout = get_viz_strategy("breakout")
    swing = get_viz_strategy("swing")

    breakout_result = apply_filters(
        df,
        ScanFilters(actionable_only=True),
        breakout,
    )
    assert set(breakout_result["ticker"]) == {"A"}

    swing_df = pd.DataFrame(
        [
            {"ticker": "C", "tier": "A", "eligible": True, "final_score": 70},
            {"ticker": "D", "tier": "C", "eligible": True, "final_score": 40},
        ]
    )
    swing_result = apply_filters(
        swing_df,
        ScanFilters(actionable_only=True),
        swing,
    )
    assert set(swing_result["ticker"]) == {"C"}


def test_scatter_dataframe_uses_config_axes():
    config = get_viz_strategy("swing")
    tickers = [
        {
            "ticker": "AAA",
            "eligible": True,
            "tier": "A",
            "scores": {
                "pullback": {"score": 10},
                "relative_strength": {"score": 15},
            },
            "summary": {"final_adjusted_score": 75},
        },
        {"ticker": "BBB", "eligible": False, "tier": "filtered"},
    ]
    scatter = scatter_dataframe(tickers, config)
    assert len(scatter) == 1
    assert "pullback" in scatter.columns
    assert "relative_strength" in scatter.columns


def test_validate_report_strategy_mismatch():
    config = get_viz_strategy("breakout")
    msg = validate_report_strategy({"strategy_id": "swing"}, config)
    assert msg is not None
    assert "swing" in msg


def test_tier_chart_keys_match_config():
    breakout = get_viz_strategy("breakout")
    swing = get_viz_strategy("swing")
    assert breakout.tiers == ("Tier 1", "Tier 2", "Tier 3")
    assert swing.tiers == ("A", "B", "C")
    assert breakout.actionable_tiers == ("Tier 1", "Tier 2")
    assert swing.actionable_tiers == ("A", "B")
