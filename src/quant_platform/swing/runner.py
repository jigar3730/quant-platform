"""Swing scanner pipeline via StrategyEngine."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from quant_platform.config import (
    DEFAULT_SWING_CSV,
    DEFAULT_SWING_JSON,
    DEFAULT_SWING_MD,
)
from quant_platform.engine.export import ticker_results_to_legacy_scores
from quant_platform.engine.runner import StrategyEngine
from quant_platform.history.archive import archive_scan_outputs
from quant_platform.report.builder import build_scan_report
from quant_platform.report.export import export_json_report, export_markdown_report
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
        report: str | None = None,
        report_json: Path = DEFAULT_SWING_JSON,
        report_md: Path = DEFAULT_SWING_MD,
        archive: bool = False,
    ) -> None:
        self.tickers = tickers
        self.tickers_file = tickers_file
        self.dynamic_universe = dynamic_universe
        self.output = output
        self.use_cache = use_cache
        self.dry_run = dry_run
        self.report = report
        self.report_json = report_json
        self.report_md = report_md
        self.archive = archive

    def run(self) -> pd.DataFrame:
        engine = StrategyEngine(
            get_strategy("swing"),
            tickers=self.tickers,
            tickers_file=self.tickers_file,
            dynamic_universe=self.dynamic_universe,
            use_cache=self.use_cache,
            dry_run=self.dry_run,
        )
        scan_result = engine.run()
        df = scan_result.to_dataframe()
        export_results(df, self.output)
        logger.info("Wrote %d swing rows to %s", len(df), self.output)

        if self.report:
            ctx = engine._context
            assert ctx is not None
            scores_by_ticker = ticker_results_to_legacy_scores(scan_result.tickers)
            scan_report = build_scan_report(
                results_df=df,
                universe=scan_result.universe,
                stock_dfs=ctx.stock_dfs,
                spy_df=ctx.spy_df,
                sector_dfs=ctx.sector_dfs,
                sector_etfs=ctx.sector_etfs,
                fund_map=ctx.fund_map,
                regime_detail=scan_result.regime_detail,
                scores_by_ticker=scores_by_ticker,
                strategy_id=scan_result.strategy_id,
            )
            if self.report in ("json", "both"):
                export_json_report(scan_report, self.report_json)
                logger.info("Wrote detailed JSON report to %s", self.report_json)
            if self.report in ("md", "both"):
                export_markdown_report(scan_report, self.report_md)
                logger.info("Wrote markdown summary to %s", self.report_md)

            if self.archive:
                archive_dir = archive_scan_outputs(
                    csv_path=self.output,
                    json_path=self.report_json if self.report in ("json", "both") else None,
                    md_path=self.report_md if self.report in ("md", "both") else None,
                    scan_report=scan_report,
                    output_stem="swing_scan",
                    log_name="swing_scan.log",
                )
                logger.info("Archived swing scan to %s", archive_dir)

        return df
