from quant_platform.engine.runner import StrategyEngine
from quant_platform.strategies.registry import get_strategy


def test_fake_strategy_engine_dry_run():
    engine = StrategyEngine(
        get_strategy("fake"),
        tickers=["AAA", "BBB", "CCC"],
        dry_run=True,
    )
    result = engine.run()

    assert result.strategy_id == "fake"
    assert len(result.tickers) == 3
    eligible = [t for t in result.tickers if t.eligible]
    assert len(eligible) == 3
    assert all(t.raw_score > 0 for t in eligible)
    assert all(t.tier in ("Tier 1", "Tier 2", "Tier 3") for t in eligible)


def test_fake_strategy_factor_scores():
    engine = StrategyEngine(
        get_strategy("fake"),
        tickers=["AAA", "BBB"],
        dry_run=True,
    )
    result = engine.run()
    t = result.tickers[0]
    assert "fake_universe" in t.factors
    assert "fake_ticker" in t.factors
