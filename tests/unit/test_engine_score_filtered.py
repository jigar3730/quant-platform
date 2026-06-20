"""Engine scores filtered tickers but keeps tier assignment for eligible only."""

from quant_platform.engine.runner import StrategyEngine
from quant_platform.strategies.registry import get_strategy


def test_swing_filtered_ticker_still_has_factor_scores():
    engine = StrategyEngine(
        get_strategy("swing"),
        tickers=["AAA", "BBB", "CCC"],
        dry_run=True,
    )
    result = engine.run()

    assert len(result.tickers) == 3
    for t in result.tickers:
        assert t.factors, f"{t.ticker} should have computed factors"
        assert t.raw_score >= 0
        assert t.normalized_score >= 0
        assert t.tier == "filtered"


def test_breakout_filtered_ticker_still_has_factor_scores(monkeypatch):
    monkeypatch.setattr("quant_platform.filters.eligibility.MIN_PRICE", 500.0)

    engine = StrategyEngine(
        get_strategy("breakout"),
        tickers=["AAA", "BBB", "CCC"],
        dry_run=True,
    )
    result = engine.run()
    filtered = [t for t in result.tickers if not t.eligible]
    assert len(filtered) == 3

    for t in filtered:
        assert t.tier == "filtered"
        assert t.factors
        assert t.final_score >= 0
        assert t.raw_score > 0


def test_filtered_rows_in_csv_have_component_scores():
    engine = StrategyEngine(
        get_strategy("swing"),
        tickers=["AAA", "BBB", "CCC"],
        dry_run=True,
    )
    df = engine.run().to_dataframe()
    assert len(df) == 3
    assert not df["eligible"].any()

    for col in ("trend_score", "pullback_score", "relative_strength_score", "volume_score"):
        assert col in df.columns
        assert (df[col].fillna(0) >= 0).all()
        assert df[col].sum() > 0


def test_no_price_data_ticker_has_empty_filter_checks():
    from quant_platform.engine.types import TickerResult
    from quant_platform.engine.export import ticker_results_filter_checks

    tr = TickerResult(
        ticker="MISSING",
        eligible=False,
        filter_reason="no_price_data",
        metadata={"filter_checks": []},
    )
    assert ticker_results_filter_checks([tr]) == {"MISSING": []}

    tr_none_meta = TickerResult(
        ticker="BAD",
        eligible=False,
        filter_reason="no_price_data",
        metadata=None,  # type: ignore[arg-type]
    )
    assert ticker_results_filter_checks([tr_none_meta]) == {"BAD": []}
