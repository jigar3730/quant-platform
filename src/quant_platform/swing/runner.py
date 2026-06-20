"""Swing scanner pipeline via StrategyEngine."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from quant_platform.config import DEFAULT_SWING_CSV
from quant_platform.engine.runner import StrategyEngine
from quant_platform.scoring.aggregate import export_results
from quant_platform.strategies.registry import get_strategy

logger = logging.getLogger(__name__)


class SwingScannerRunner:
    def __init__(
        self,
        *,
        tickers: list[str] | None = None,
        tickers_file: Path | None = None,
        dynamic_universe: bool = False,
        output: Path = DEFAULT_SWING_CSV,
        use_cache: bool = False,
        dry_run: bool = False,
    ) -> None:
        self.tickers = tickers
        self.tickers_file = tickers_file
        self.dynamic_universe = dynamic_universe
        self.output = output
        self.use_cache = use_cache
        self.dry_run = dry_run

    def run(self) -> pd.DataFrame:
        engine = StrategyEngine(
            get_strategy("swing"),
            tickers=self.tickers,
            tickers_file=self.tickers_file,
            dynamic_universe=self.dynamic_universe,
            use_cache=self.use_cache,
            dry_run=self.dry_run,
        )
        result = engine.run()
        df = result.to_dataframe()
        export_results(df, self.output)
        logger.info("Wrote %d swing rows to %s", len(df), self.output)
        return df
