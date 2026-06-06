import pytest

from quant_platform.data.fetch import download_prices

pytestmark = pytest.mark.integration


def test_download_live_prices():
    df = download_prices(["AAPL", "MSFT", "SPY"], use_cache=False)
    assert not df.empty
    assert df["ticker"].nunique() >= 2
    for ticker in df["ticker"].unique():
        sub = df[df["ticker"] == ticker]
        assert len(sub) >= 200
