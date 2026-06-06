from unittest.mock import patch

from quant_platform.data.universe import fetch_universe


@patch("quant_platform.data.universe.yf.screen")
def test_fetch_universe_most_actives(mock_screen):
    mock_screen.return_value = {
        "quotes": [{"symbol": "NVDA"}, {"symbol": "AAPL"}, {"symbol": "TSLA"}],
    }
    tickers = fetch_universe(size=3)
    mock_screen.assert_called_once_with("most_actives", count=3)
    assert tickers == ["NVDA", "AAPL", "TSLA"]


@patch("quant_platform.data.universe.yf.screen")
def test_fetch_universe_fallback_on_error(mock_screen):
    mock_screen.side_effect = RuntimeError("network error")
    tickers = fetch_universe(size=3)
    assert len(tickers) == 3
    assert tickers[0] == "AAPL"
