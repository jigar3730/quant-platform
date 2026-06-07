import pandas as pd

from quant_platform.viz.breakout_filters import (
    BreakoutFilters,
    apply_breakout_filters,
    scatter_dataframe,
)


def test_apply_breakout_filters():
    df = pd.DataFrame(
        [
            {"ticker": "AAA", "tier": "Tier 1", "eligible": True, "final_score": 80},
            {"ticker": "BBB", "tier": "Tier 3", "eligible": True, "final_score": 50},
            {"ticker": "CCC", "tier": "filtered", "eligible": False, "final_score": 10},
        ]
    )
    filters = BreakoutFilters(tier="Tier 1", eligible_only=True, min_score=70, search="AA")
    result = apply_breakout_filters(df, filters)
    assert list(result["ticker"]) == ["AAA"]


def test_scatter_dataframe():
    tickers = [
        {
            "ticker": "AAA",
            "eligible": True,
            "tier": "Tier 1",
            "scores": {
                "compression": {"score": 10},
                "rs_market": {"score": 15},
            },
            "summary": {"final_adjusted_score": 75},
        },
        {"ticker": "BBB", "eligible": False, "tier": "filtered"},
    ]
    scatter = scatter_dataframe(tickers)
    assert len(scatter) == 1
    assert scatter.iloc[0]["ticker"] == "AAA"
