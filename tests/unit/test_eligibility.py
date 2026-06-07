from quant_platform.filters.eligibility import check_eligibility
from tests.helpers import make_ohlcv, make_uptrend_df


def test_insufficient_history(date_index):
    df = make_ohlcv(date_index[:100])
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "insufficient_history"


def test_low_liquidity(date_index):
    df = make_uptrend_df(date_index)
    df["Volume"] = 100_000
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "low_liquidity"


def test_price_below_minimum(date_index):
    df = make_uptrend_df(date_index)
    df["Close"] = 5.0
    df["Open"] = 5.0
    df["High"] = 5.5
    df["Low"] = 4.5
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "price_below_minimum"


def test_trend_misaligned(date_index):
    df = make_uptrend_df(date_index)
    df.loc[df.index[-30]:, "Close"] = 10.0
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "trend_misaligned"


def test_too_close_to_52w_low(date_index):
    import numpy as np

    n = len(date_index)
    close = np.linspace(95, 100, n)
    df = make_uptrend_df(date_index)
    df["Close"] = close
    df["Open"] = close
    df["High"] = close + 2
    df["Low"] = 95.0
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "too_close_to_52w_low"


def test_too_far_from_52w_high(date_index):
    df = make_uptrend_df(date_index)
    df.loc[df.index[-30]:, "High"] = 200.0
    df.loc[df.index[-30]:, "Close"] = 100.0
    df.loc[df.index[-30]:, "Low"] = 95.0
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "too_far_from_52w_high"


def test_uptrend_passes(date_index):
    df = make_uptrend_df(date_index)
    eligible, reason = check_eligibility(df)
    assert eligible
    assert reason == "eligible"


def test_price_data_anomaly(date_index):
    df = make_uptrend_df(date_index)
    df.loc[df.index[-1], "Close"] = df["Close"].iloc[-2] * 5
    df.loc[df.index[-1], "Open"] = df["Close"].iloc[-1]
    df.loc[df.index[-1], "High"] = df["Close"].iloc[-1]
    df.loc[df.index[-1], "Low"] = df["Close"].iloc[-1]
    eligible, reason = check_eligibility(df)
    assert not eligible
    assert reason == "price_data_anomaly"
