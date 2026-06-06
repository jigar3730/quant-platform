import pandas as pd
import pytest

from quant_platform.regime.market import MarketRegime
from quant_platform.scoring.aggregate import assign_tier, build_results_table


def test_normalization_and_multiplier():
    rows = [
        {
            "ticker": "AAA",
            "eligible": True,
            "filter_reason": "eligible",
            "rs_market_score": 20,
            "rs_sector_score": 15,
            "accumulation_score": 12,
            "relative_volume_score": 8,
            "compression_score": 15,
            "pattern_score": 5,
            "resistance_score": 5,
            "revenue_score": 15,
            "eps_score": 15,
        }
    ]
    regime = MarketRegime("neutral", 0.85)
    df = build_results_table(rows, regime)
    assert df.iloc[0]["raw_score"] == 110
    assert df.iloc[0]["normalized_score"] == pytest.approx(110 / 120 * 100)
    assert df.iloc[0]["final_adjusted_score"] == pytest.approx(110 / 120 * 100 * 0.85)


def test_tier1():
    row = pd.Series(
        {
            "eligible": True,
            "normalized_score": 85,
            "final_adjusted_score": 75,
            "compression_score": 10,
            "accumulation_score": 9,
            "relative_volume_score": 0,
        }
    )
    assert assign_tier(row) == "Tier 1"


def test_tier2():
    row = pd.Series(
        {
            "eligible": True,
            "normalized_score": 70,
            "final_adjusted_score": 60,
            "compression_score": 5,
            "accumulation_score": 3,
            "relative_volume_score": 0,
        }
    )
    assert assign_tier(row) == "Tier 2"


def test_tier3():
    row = pd.Series(
        {
            "eligible": True,
            "normalized_score": 50,
            "final_adjusted_score": 42,
            "compression_score": 5,
            "accumulation_score": 3,
            "relative_volume_score": 0,
        }
    )
    assert assign_tier(row) == "Tier 3"


def test_filtered_tier():
    row = pd.Series({"eligible": False})
    assert assign_tier(row) == "filtered"


def test_sort_order():
    rows = [
        {
            "ticker": "LOW",
            "eligible": True,
            "filter_reason": "eligible",
            "rs_market_score": 5,
            "rs_sector_score": 5,
            "accumulation_score": 5,
            "relative_volume_score": 5,
            "compression_score": 5,
            "pattern_score": 5,
            "resistance_score": 5,
            "revenue_score": 5,
            "eps_score": 5,
        },
        {
            "ticker": "HIGH",
            "eligible": True,
            "filter_reason": "eligible",
            "rs_market_score": 15,
            "rs_sector_score": 15,
            "accumulation_score": 15,
            "relative_volume_score": 15,
            "compression_score": 15,
            "pattern_score": 15,
            "resistance_score": 15,
            "revenue_score": 15,
            "eps_score": 15,
        },
    ]
    df = build_results_table(rows, MarketRegime("strong", 1.0))
    assert df.iloc[0]["ticker"] == "HIGH"
