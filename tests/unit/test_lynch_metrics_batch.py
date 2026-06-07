from unittest.mock import patch

from quant_platform.lynch.metrics import fetch_lynch_metrics_batch


def test_fetch_lynch_metrics_batch_preserves_order():
    calls: list[str] = []

    def fake_fetch(ticker: str) -> dict:
        calls.append(ticker)
        return {"ticker": ticker, "pe_ratio": 10.0}

    with patch("quant_platform.lynch.metrics.fetch_lynch_metrics", side_effect=fake_fetch):
        result = fetch_lynch_metrics_batch(["C", "A", "B"], max_workers=2)

    assert [row["ticker"] for row in result] == ["C", "A", "B"]
    assert set(calls) == {"A", "B", "C"}
