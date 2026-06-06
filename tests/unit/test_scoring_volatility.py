from quant_platform.scoring.volatility import score_bollinger_compression, score_pattern_quality
from tests.helpers import make_uptrend_df


def test_bollinger_compression_low_width_scores_high(date_index):
    df = make_uptrend_df(date_index)
    # Tight range at end compresses bands
    df.loc[df.index[-30]:, "Close"] = 100.0
    df.loc[df.index[-30]:, "High"] = 100.5
    df.loc[df.index[-30]:, "Low"] = 99.5
    score = score_bollinger_compression(df)
    assert score > 0


def test_pattern_quality_partial(date_index):
    df = make_uptrend_df(date_index)
    high_52w = df["High"].tail(252).max()
    df.loc[df.index[-1], "Close"] = high_52w * 0.95
    score = score_pattern_quality(df)
    assert score >= 1.0
