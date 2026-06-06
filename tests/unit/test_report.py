import json
from pathlib import Path

from quant_platform.filters.eligibility import eligibility_detail
from quant_platform.report.builder import build_ticker_report, explain_tier
from quant_platform.report.export import export_json_report, export_markdown_report
from tests.helpers import make_uptrend_df


def test_eligibility_detail_passes(date_index):
    df = make_uptrend_df(date_index)
    detail = eligibility_detail(df)
    assert detail["passed"]
    assert detail["fail_reason"] is None
    assert len(detail["checks"]) >= 5


def test_eligibility_detail_fails_price(date_index):
    df = make_uptrend_df(date_index)
    df["Close"] = 5.0
    detail = eligibility_detail(df)
    assert not detail["passed"]
    assert detail["fail_reason"] == "price_below_minimum"


def test_explain_tier_filtered():
    reason = explain_tier({"eligible": False, "filter_reason": "price_below_minimum"})
    assert "below" in reason.lower()


def test_explain_tier2():
    reason = explain_tier(
        {
            "eligible": True,
            "tier": "Tier 2",
            "normalized_score": 70,
            "final_adjusted_score": 70,
            "compression_score": 5,
            "accumulation_score": 5,
            "relative_volume_score": 3,
        }
    )
    assert "65" in reason or "Watchlist" in reason


def test_build_ticker_report_excluded(date_index):
    df = make_uptrend_df(date_index)
    df["Close"] = 5.0
    report = build_ticker_report(
        ticker="TEST",
        row={"tier": "filtered", "filter_reason": "price_below_minimum", "eligible": False},
        stock_df=df,
        spy_df=df,
        sector_df=None,
        sector_etf=None,
        fund={},
        scores=None,
    )
    assert report["verdict"] == "excluded"
    assert report["scores"] is None
    assert not report["eligibility"]["passed"]


def test_export_reports(tmp_path: Path, date_index):
    df = make_uptrend_df(date_index)
    report = build_ticker_report(
        ticker="AAA",
        row={
            "tier": "Tier 3",
            "eligible": True,
            "normalized_score": 50,
            "final_adjusted_score": 50,
            "raw_score": 60,
            "regime_multiplier": 1.0,
            "rs_market_score": 10,
            "rs_sector_score": 5,
            "accumulation_score": 5,
            "relative_volume_score": 3,
            "compression_score": 5,
            "pattern_score": 2,
            "resistance_score": 3,
            "revenue_score": 8,
            "eps_score": 8,
        },
        stock_df=df,
        spy_df=df,
        sector_df=df,
        sector_etf="XLK",
        fund={"revenue_yoy": 0.25, "eps_combined": 0.35},
        scores={
            "rs_market_score": 10,
            "rs_sector_score": 5,
            "accumulation_score": 5,
            "relative_volume_score": 3,
            "compression_score": 5,
            "pattern_score": 2,
            "resistance_score": 3,
            "revenue_score": 8,
            "eps_score": 8,
        },
    )
    full = {
        "scan_summary": {
            "universe_size": 1,
            "eligible_count": 1,
            "excluded_count": 0,
            "tier_counts": {"Tier 1": 0, "Tier 2": 0, "Tier 3": 1, "filtered": 0},
            "filter_breakdown": {},
        },
        "market_regime": {
            "label": "strong",
            "multiplier": 1.0,
            "meaning": "test",
            "spy_price": 500,
            "sma50": 490,
            "sma200": 480,
            "return_63d_pct": 5.0,
            "pct_below_52w_high": 2.0,
            "high_52w": 510,
        },
        "tickers": [report],
    }

    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    export_json_report(full, json_path)
    export_markdown_report(full, md_path)

    assert json_path.exists()
    loaded = json.loads(json_path.read_text())
    assert loaded["tickers"][0]["ticker"] == "AAA"
    assert "scores" in loaded["tickers"][0]

    md_text = md_path.read_text()
    assert "# Breakout Scan Report" in md_text
    assert "AAA" in md_text
