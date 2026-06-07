import pandas as pd

from quant_platform.data.fetch import _yoy_growth
from quant_platform.data.quality import has_price_spike, sanitize_growth_rate


def test_sanitize_growth_rate_caps_extremes():
    assert sanitize_growth_rate(0.25) == 0.25
    assert sanitize_growth_rate(3.5) is None
    assert sanitize_growth_rate(None) is None


def test_yoy_growth_rejects_negative_prior():
    series = pd.Series([-0.05, 0.1, 0.12, 0.14, 0.16])
    assert _yoy_growth(series) is None


def test_yoy_growth_rejects_extreme_positive():
    series = pd.Series([0.01, 0.02, 0.03, 0.04, 0.50])
    assert _yoy_growth(series) is None


def test_has_price_spike():
    df = pd.DataFrame({"Close": [100.0] * 20 + [350.0]})
    assert has_price_spike(df)
