"""Unit tests for Finqube layout helpers."""

from __future__ import annotations

import pandas as pd

from quant_platform.viz.layout.cards import (
    build_key_insight_html,
    build_score_strip_html,
    build_universe_context_html,
    rank_factor_insights,
    score_pills_from_ticker,
)
from quant_platform.viz.strategy.registry import get_viz_strategy


def _sample_ticker() -> dict:
    return {
        "ticker": "AAA",
        "eligible": True,
        "tier": "Tier 1",
        "scores": {
            "rs_market": {"score": 18.0, "max": 20, "meaning": "Strong RS"},
            "compression": {"score": 4.0, "max": 15, "meaning": "Weak compression"},
            "volume": {"score": 12.0, "max": 15, "meaning": "Good volume"},
        },
    }


def test_rank_factor_insights_top_and_watch():
    config = get_viz_strategy("breakout")
    ticker = _sample_ticker()
    strengths, watches = rank_factor_insights(ticker, config)
    assert strengths
    assert any("RS vs Market" in item for item in strengths)
    assert any("Compression" in item for item in watches)


def test_score_pills_from_ticker_breakout_count():
    config = get_viz_strategy("breakout")
    pills = score_pills_from_ticker(_sample_ticker(), config)
    assert len(pills) == 3
    assert pills[0]["label"]
    assert 0 <= pills[0]["pct"] <= 100


def test_score_pills_from_ticker_swing_labels():
    config = get_viz_strategy("swing")
    ticker = {
        "scores": {
            "trend": {"score": 25.0, "max": 30},
            "pullback": {"score": 20.0, "max": 25},
            "relative_strength": {"score": 18.0, "max": 20},
            "volume": {"score": 10.0, "max": 15},
        }
    }
    pills = score_pills_from_ticker(ticker, config)
    assert len(pills) == 4
    labels = {pill["label"] for pill in pills}
    assert "Weekly Trend" in labels
    assert "Pullback Quality" in labels


def test_build_universe_context_percentile():
    config = get_viz_strategy("breakout")
    df = pd.DataFrame(
        [
            {"ticker": "AAA", "eligible": True, "final_score": 90, "tier": "Tier 1"},
            {"ticker": "BBB", "eligible": True, "final_score": 70, "tier": "Tier 2"},
            {"ticker": "CCC", "eligible": True, "final_score": 50, "tier": "Tier 3"},
        ]
    )
    html = build_universe_context_html(
        ticker="AAA",
        final_score=90.0,
        tier="Tier 1",
        df=df,
        config=config,
    )
    assert "top" in html.lower()
    assert "AAA" in html
    assert "90.0" in html


def test_build_score_strip_html_renders_pills():
    html = build_score_strip_html(
        final_score=82.5,
        regime_multiplier=0.95,
        pills=[
            {"label": "RS", "score": 18, "max": 20, "pct": 90},
            {"label": "Volume", "score": 10, "max": 15, "pct": 67},
        ],
    )
    assert "82.5" in html
    assert "Regime" in html
    assert "score-pill" in html


def test_build_key_insight_html_includes_strengths():
    config = get_viz_strategy("breakout")
    html = build_key_insight_html(_sample_ticker(), config)
    assert "Key insight" in html
    assert "Strengths" in html or "Watch" in html
