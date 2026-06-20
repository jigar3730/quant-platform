import pandas as pd

from quant_platform.engine.runner import StrategyEngine
from quant_platform.pipeline.runner import PipelineRunner
from quant_platform.strategies.registry import get_strategy


def test_engine_breakout_parity_dry_run(tmp_path):
    tickers = ["AAA", "BBB", "CCC"]
    legacy_output = tmp_path / "legacy.csv"
    legacy = PipelineRunner(tickers=tickers, output=legacy_output, dry_run=True).run()

    engine = StrategyEngine(get_strategy("breakout"), tickers=tickers, dry_run=True)
    engine_df = engine.run().to_dataframe()

    assert list(legacy.columns) == list(engine_df.columns)
    assert len(legacy) == len(engine_df)

    compare_cols = [
        "ticker",
        "eligible",
        "tier",
        "raw_score",
        "normalized_score",
        "final_adjusted_score",
        "rs_market_score",
        "accumulation_score",
    ]
    legacy_sorted = legacy.sort_values("ticker").reset_index(drop=True)
    engine_sorted = engine_df.sort_values("ticker").reset_index(drop=True)

    for col in compare_cols:
        if col in ("tier", "ticker", "eligible"):
            assert legacy_sorted[col].tolist() == engine_sorted[col].tolist(), col
        else:
            assert legacy_sorted[col].equals(engine_sorted[col]) or pd.allclose(
                legacy_sorted[col].astype(float),
                engine_sorted[col].astype(float),
                equal_nan=True,
            ), col
