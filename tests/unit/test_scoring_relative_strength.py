import pandas as pd

from quant_platform.scoring.relative_strength import (
    compute_rs_market_ratio,
    score_rs_market,
    score_rs_sector,
)


def _price_df(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Close": closes, "High": closes, "Low": closes, "Volume": 1_000_000})


def test_rs_market_ratio():
    stock = _price_df([100] * 130 + list(range(100, 130)))
    spy = _price_df([100] * 130 + list(range(100, 115)))
    ratio = compute_rs_market_ratio(stock, spy)
    assert ratio is not None
    assert ratio > 1.0


def test_score_rs_market():
    ratios = pd.Series({"A": 1.5, "B": 1.0, "C": 0.5})
    scores = score_rs_market(ratios)
    assert scores.max() == 20.0
    assert scores.min() > 0


def test_score_rs_sector_within_group():
    ratios = pd.Series({"A": 1.5, "B": 1.0, "C": 0.8, "D": 1.2})
    sectors = pd.Series({"A": "XLK", "B": "XLK", "C": "XLF", "D": "XLF"})
    scores = score_rs_sector(ratios, sectors)
    assert scores["A"] == 15.0
    assert scores["C"] == 7.5
