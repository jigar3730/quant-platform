from unittest.mock import MagicMock, patch

from quant_platform.data.news import fetch_ticker_news, fetch_ticker_snapshot


def test_fetch_ticker_news_normalizes_articles():
    mock_news = [
        {
            "content": {
                "title": "Earnings beat expectations",
                "summary": "Company reported strong Q2 results.",
                "pubDate": "2026-06-06T15:30:00Z",
                "provider": {"displayName": "Reuters"},
                "clickThroughUrl": {
                    "url": "https://finance.yahoo.com/news/earnings-beat.html",
                },
            }
        }
    ]
    mock_ticker = MagicMock()
    mock_ticker.get_news.return_value = mock_news

    with patch("quant_platform.data.news.yf.Ticker", return_value=mock_ticker):
        articles = fetch_ticker_news("MU", count=5)

    assert len(articles) == 1
    assert articles[0]["title"] == "Earnings beat expectations"
    assert articles[0]["publisher"] == "Reuters"
    assert articles[0]["url"] == "https://finance.yahoo.com/news/earnings-beat.html"
    assert "2026-06-06" in articles[0]["published"]


def test_fetch_ticker_news_handles_errors():
    with patch("quant_platform.data.news.yf.Ticker", side_effect=RuntimeError("network")):
        assert fetch_ticker_news("MU") == []


def test_fetch_ticker_snapshot_computes_change():
    mock_fi = MagicMock()
    mock_fi.last_price = 100.0
    mock_fi.previous_close = 95.0
    mock_fi.regular_market_previous_close = 95.0
    mock_fi.market_cap = 5_000_000_000
    mock_fi.year_change = 0.25
    mock_fi.day_high = 101.0
    mock_fi.day_low = 99.0
    mock_fi.currency = "USD"

    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fi

    with patch("quant_platform.data.news.yf.Ticker", return_value=mock_ticker):
        snap = fetch_ticker_snapshot("MU")

    assert snap is not None
    assert snap["price"] == 100.0
    assert round(snap["change_pct"], 2) == 5.26
    assert snap["year_change_pct"] == 25.0
