import numpy as np
import pandas as pd


def make_ohlcv(
    dates: pd.DatetimeIndex,
    *,
    start_price: float = 100.0,
    trend: float = 0.05,
    volume: float = 1_000_000,
    noise: float = 0.2,
) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = len(dates)
    close = start_price + np.arange(n) * trend + rng.normal(0, noise, n).cumsum() * 0.1
    high = close + rng.uniform(0.2, 1.0, n)
    low = close - rng.uniform(0.2, 1.0, n)
    open_ = close + rng.uniform(-0.3, 0.3, n)
    vol = np.full(n, volume) + rng.integers(-50_000, 50_000, n)
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": vol,
        }
    )


def make_uptrend_df(dates: pd.DatetimeIndex) -> pd.DataFrame:
    n = len(dates)
    close = 20 + np.linspace(0, 80, n) + np.sin(np.linspace(0, 8, n)) * 0.5
    high = close + 1.0
    low = close - 1.0
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": np.full(n, 2_000_000),
        }
    )
