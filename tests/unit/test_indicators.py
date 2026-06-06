import numpy as np
import pandas as pd
import pytest

from quant_platform.indicators import find_swing_lows, return_over_days, sma


def test_sma():
    s = pd.Series([1, 2, 3, 4, 5])
    result = sma(s, 3)
    assert np.isnan(result.iloc[1])
    assert result.iloc[-1] == 4.0


def test_return_over_days():
    s = pd.Series([100, 110, 120])
    assert return_over_days(s, 2) == pytest.approx(0.2)


def test_find_swing_lows():
    lows = pd.Series([5, 4, 3, 4, 5, 4, 3, 4, 5])
    swings = find_swing_lows(lows, order=1)
    assert len(swings) >= 2
