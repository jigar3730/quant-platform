from pathlib import Path
from unittest.mock import patch

from quant_platform.data.tickers import load_tickers_file, resolve_universe


def test_load_tickers_txt_ignores_comments_and_blanks(tmp_path: Path):
    path = tmp_path / "tickers.txt"
    path.write_text(
        "# VSMAX watchlist\n"
        "aapl\n"
        "\n"
        "MSFT, nvda  # inline comment\n"
        "# trailing\n"
    )
    assert load_tickers_file(path) == ["AAPL", "MSFT", "NVDA"]


def test_load_tickers_json(tmp_path: Path):
    path = tmp_path / "tickers.json"
    path.write_text('{"tickers": ["mu", "PLUG", "MU"]}')
    assert load_tickers_file(path) == ["MU", "PLUG"]


def test_resolve_universe_prefers_cli_override(tmp_path: Path):
    path = tmp_path / "tickers.txt"
    path.write_text("AAA\nBBB\n")
    with patch("quant_platform.data.universe.fetch_universe") as mock_fetch:
        tickers = resolve_universe(["ZZZ"], tickers_file=path)
    assert tickers == ["ZZZ"]
    mock_fetch.assert_not_called()


def test_resolve_universe_uses_config_file(tmp_path: Path):
    path = tmp_path / "tickers.txt"
    path.write_text("AAA\nBBB\nCCC\n")
    with patch("quant_platform.data.universe.fetch_universe") as mock_fetch:
        tickers = resolve_universe(tickers_file=path)
    assert tickers == ["AAA", "BBB", "CCC"]
    mock_fetch.assert_not_called()


def test_resolve_universe_dynamic_skips_config_file(tmp_path: Path):
    path = tmp_path / "tickers.txt"
    path.write_text("AAA\nBBB\n")
    with patch(
        "quant_platform.data.universe.fetch_universe",
        return_value=["NVDA", "TSLA"],
    ) as mock_fetch:
        tickers = resolve_universe(tickers_file=path, dynamic=True)
    assert tickers == ["NVDA", "TSLA"]
    mock_fetch.assert_called_once()


def test_resolve_universe_falls_back_when_config_missing(tmp_path: Path):
    missing = tmp_path / "missing.txt"
    with patch("quant_platform.data.universe.fetch_universe", return_value=["SPY"]) as mock_fetch:
        tickers = resolve_universe(tickers_file=missing)
    assert tickers == ["SPY"]
    mock_fetch.assert_called_once()
