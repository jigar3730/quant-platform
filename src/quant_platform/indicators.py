import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def return_over_days(series: pd.Series, days: int) -> float | None:
    if len(series) <= days:
        return None
    start = series.iloc[-days - 1]
    end = series.iloc[-1]
    if start == 0 or pd.isna(start) or pd.isna(end):
        return None
    return (end / start) - 1


def range_52w(df: pd.DataFrame, lookback: int = 252) -> tuple[float, float]:
    window = df.tail(lookback)
    return float(window["High"].max()), float(window["Low"].min())


def distance_from_high_pct(price: float, high: float) -> float | None:
    if high == 0:
        return None
    return (high - price) / high


def pct_above_low(price: float, low: float) -> float | None:
    if low == 0:
        return None
    return (price - low) / low


def bollinger_width(close: pd.Series, window: int = 20) -> pd.Series:
    mid = sma(close, window)
    std = close.rolling(window, min_periods=window).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return (upper - lower) / mid


def find_swing_lows(lows: pd.Series, order: int = 2) -> list[tuple[int, float]]:
    """Local minima using a symmetric window of `order` bars on each side."""
    values = lows.to_numpy()
    swings: list[tuple[int, float]] = []
    for i in range(order, len(values) - order):
        window = values[i - order : i + order + 1]
        if values[i] == np.min(window):
            swings.append((i, float(values[i])))
    return swings


def is_rising(series: pd.Series, lookback: int = 5) -> bool:
    if len(series) < lookback + 1:
        return False
    return float(series.iloc[-1]) > float(series.iloc[-lookback - 1])
