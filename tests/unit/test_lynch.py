from quant_platform.lynch.categories import (
    assign_categories,
    classify_asset_play,
    classify_fast_grower,
    classify_stalwart,
)
from quant_platform.lynch.filters import apply_anti_filters, apply_base_screen, lynch_score
from quant_platform.lynch.metrics import compute_peg, normalize_debt_to_equity
from quant_platform.lynch.runner import LynchScannerRunner


def _ideal_metrics(**overrides) -> dict:
    base = {
        "ticker": "TEST",
        "trailing_eps": 2.5,
        "pe_ratio": 15.0,
        "peg_ratio": 0.8,
        "eps_growth_5y": 0.20,
        "debt_to_equity": 0.20,
        "net_cash": 500_000_000,
        "institutional_ownership": 0.30,
        "analyst_count": 3,
        "insider_purchases_6m": 10000.0,
        "shares_outstanding_change_yoy": -0.02,
        "market_cap": 2_000_000_000,
        "dividend_yield": 0.02,
        "price_to_book": 0.8,
        "net_cash_price_ratio": 0.35,
        "return_on_equity": 0.18,
        "revenue_cv": 0.15,
    }
    base.update(overrides)
    return base


def test_normalize_debt_to_equity_percent():
    assert normalize_debt_to_equity(35.0) == 0.35
    assert normalize_debt_to_equity(0.25) == 0.25


def test_compute_peg():
    assert compute_peg(15, 0.20) == 0.75  # 15 / 20%
    assert compute_peg(9, 0.15) == 0.6  # 9 / 15%


def test_base_screen_passes_ideal_candidate():
    passed, checks, fail = apply_base_screen(_ideal_metrics())
    assert passed is True
    assert fail is None
    assert lynch_score(checks) == 100.0


def test_anti_filter_rejects_negative_earnings():
    passed, _, fail = apply_anti_filters(_ideal_metrics(trailing_eps=-1.0, pe_ratio=None))
    assert passed is False
    assert fail == "no_earnings"


def test_fast_grower_classification():
    ok, _ = classify_fast_grower(_ideal_metrics())
    assert ok is True


def test_stalwart_classification():
    ok, _ = classify_stalwart(
        _ideal_metrics(
            market_cap=50_000_000_000,
            pe_ratio=12.0,
            eps_growth_5y=0.12,
            dividend_yield=0.02,
        )
    )
    assert ok is True


def test_asset_play_classification():
    ok, _ = classify_asset_play(_ideal_metrics(price_to_book=0.7, net_cash_price_ratio=0.4))
    assert ok is True


def test_assign_categories_multiple():
    metrics = _ideal_metrics(
        market_cap=2_000_000_000,
        eps_growth_5y=0.22,
        price_to_book=0.7,
        net_cash_price_ratio=0.4,
    )
    cats = assign_categories(metrics)
    assert "fast_grower" in cats
    assert "asset_play" in cats


def test_runner_evaluate_summary_preset(monkeypatch):
    metrics = _ideal_metrics(ticker="LYNCH")
    runner = LynchScannerRunner(tickers=["LYNCH"], preset="summary")
    monkeypatch.setattr(
        "quant_platform.lynch.runner.fetch_lynch_metrics_batch",
        lambda _: [metrics],
    )
    df = runner.run()
    assert len(df) == 1
    assert bool(df.iloc[0]["passed"]) is True
    assert df.iloc[0]["lynch_score"] > 0
