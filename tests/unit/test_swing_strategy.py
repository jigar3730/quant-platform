from quant_platform.engine.runner import StrategyEngine
from quant_platform.strategies.registry import get_strategy


def test_swing_strategy_dry_run():
    engine = StrategyEngine(
        get_strategy("swing"),
        tickers=["AAA", "BBB", "CCC"],
        dry_run=True,
    )
    result = engine.run()
    assert result.strategy_id == "swing"
    df = result.to_dataframe()
    assert "tier" in df.columns
    assert "trend_score" in df.columns
    assert len(df) == 3
