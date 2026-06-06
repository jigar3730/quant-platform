from unittest.mock import MagicMock, patch

import pandas as pd

from quant_platform.data.fetch import download_fundamentals, download_prices


@patch("quant_platform.data.fetch.yf.download")
def test_download_prices_shape(mock_download):
    dates = pd.bdate_range("2023-01-01", periods=5)
    mock_download.return_value = pd.DataFrame(
        {
            ("AAPL", "Open"): [1, 2, 3, 4, 5],
            ("AAPL", "High"): [2, 3, 4, 5, 6],
            ("AAPL", "Low"): [0.5, 1.5, 2.5, 3.5, 4.5],
            ("AAPL", "Close"): [1.5, 2.5, 3.5, 4.5, 5.5],
            ("AAPL", "Volume"): [1e6, 1e6, 1e6, 1e6, 1e6],
        },
        index=dates,
    )
    mock_download.return_value.columns = pd.MultiIndex.from_tuples(
        [
            ("AAPL", "Open"),
            ("AAPL", "High"),
            ("AAPL", "Low"),
            ("AAPL", "Close"),
            ("AAPL", "Volume"),
        ]
    )

    df = download_prices(["AAPL"], use_cache=False)
    assert set(df.columns) >= {"Date", "Open", "High", "Low", "Close", "Volume", "ticker"}
    assert df["ticker"].iloc[0] == "AAPL"


@patch("quant_platform.data.fetch.yf.Ticker")
def test_download_fundamentals(mock_ticker_cls):
    mock_ticker = MagicMock()
    mock_ticker_cls.return_value = mock_ticker
    dates = pd.to_datetime(["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31", "2024-03-31"])
    mock_ticker.quarterly_income_stmt = pd.DataFrame(
        {
            dates[0]: [100, 1],
            dates[1]: [110, 1.1],
            dates[2]: [120, 1.2],
            dates[3]: [130, 1.3],
            dates[4]: [150, 1.5],
        },
        index=["Total Revenue", "Diluted EPS"],
    )

    df = download_fundamentals(["AAPL"], use_cache=False)
    assert "ticker" in df.columns
    assert df.iloc[0]["ticker"] == "AAPL"
