import numpy as np
import pandas as pd

from quant_platform.regime.market import compute_market_regime


def _spy_df(close_values: list[float]) -> pd.DataFrame:
    n = len(close_values)
    close = np.array(close_values, dtype=float)
    return pd.DataFrame(
        {
            "Close": close,
            "High": close + 1,
            "Low": close - 1,
            "Open": close,
            "Volume": np.full(n, 1_000_000),
        }
    )


def test_strong_regime():
    n = 260
    close = np.linspace(400, 500, n)
    df = _spy_df(close.tolist())
    regime = compute_market_regime(df)
    assert regime.label == "strong"
    assert regime.multiplier == 1.0


def test_weak_regime_below_200sma():
    n = 260
    close = np.concatenate([np.linspace(500, 450, n - 30), np.full(30, 420)])
    df = _spy_df(close.tolist())
    regime = compute_market_regime(df)
    assert regime.label == "weak"
    assert regime.multiplier == 0.6


def test_neutral_regime():
    n = 260
    # Above 200 SMA but 50 SMA below 200 SMA and flat recent returns.
    close = np.concatenate([np.linspace(400, 480, n - 40), np.full(40, 470)])
    df = _spy_df(close.tolist())
    regime = compute_market_regime(df)
    assert regime.label == "neutral"
    assert regime.multiplier == 0.85
