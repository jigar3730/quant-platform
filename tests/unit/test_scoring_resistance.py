from tests.helpers import make_uptrend_df


def test_resistance_near(date_index):
    df = make_uptrend_df(date_index)
    resistance = df["High"].tail(50).max()
    df.loc[df.index[-1], "Close"] = resistance * 0.99
    from quant_platform.scoring.resistance import score_resistance

    assert score_resistance(df) == 5.0


def test_resistance_far(date_index):
    df = make_uptrend_df(date_index)
    from quant_platform.scoring.resistance import score_resistance

    df.loc[df.index[-1], "Close"] = df["Close"].iloc[-1] * 0.5
    assert score_resistance(df) == 0.0
