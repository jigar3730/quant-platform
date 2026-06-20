import pandas as pd

from quant_platform.viz.strategy.filters import ScanFilters, apply_filters, scatter_dataframe
from quant_platform.viz.strategy.registry import get_viz_strategy


def test_apply_breakout_filters():
    config = get_viz_strategy("breakout")
    df = pd.DataFrame(
        [
            {"ticker": "AAA", "tier": "Tier 1", "eligible": True, "final_score": 80},
            {"ticker": "BBB", "tier": "Tier 3", "eligible": True, "final_score": 50},
            {"ticker": "CCC", "tier": "filtered", "eligible": False, "final_score": 10},
        ]
    )
    filters = ScanFilters(tier="Tier 1", eligible_only=True, min_score=70, search="AA")
    result = apply_filters(df, filters, config)
    assert list(result["ticker"]) == ["AAA"]


def test_scatter_dataframe():
    config = get_viz_strategy("breakout")
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
    scatter = scatter_dataframe(tickers, config)
    assert len(scatter) == 1
    assert scatter.iloc[0]["ticker"] == "AAA"
