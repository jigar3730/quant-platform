"""Dispatch strategy runs to the appropriate engine implementation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_platform.engine.runner import StrategyEngine
from quant_platform.lynch.runner import LynchScannerRunner
from quant_platform.strategies.registry import get_strategy


def run_price_strategy(
    strategy_id: str,
    *,
    tickers: list[str] | None = None,
    tickers_file: Path | None = None,
    dynamic_universe: bool = False,
    use_cache: bool = False,
    dry_run: bool = False,
) -> pd.DataFrame:
    engine = StrategyEngine(
        get_strategy(strategy_id),
        tickers=tickers,
        tickers_file=tickers_file,
        dynamic_universe=dynamic_universe,
        use_cache=use_cache,
        dry_run=dry_run,
    )
    return engine.run().to_dataframe()


def run_lynch_strategy(
    *,
    preset: str = "summary",
    tickers: list[str] | None = None,
    tickers_file: Path | None = None,
    dynamic_universe: bool = False,
    **kwargs,
) -> pd.DataFrame:
    """Lynch uses fundamental metrics; delegates to LynchScannerRunner."""
    runner = LynchScannerRunner(
        tickers=tickers,
        tickers_file=tickers_file,
        dynamic_universe=dynamic_universe,
        preset=preset,
        **kwargs,
    )
    return runner.run()
