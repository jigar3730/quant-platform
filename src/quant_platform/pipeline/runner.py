import logging
from pathlib import Path

import pandas as pd

from quant_platform.config import (
    ALL_SECTOR_ETFS,
    BENCHMARK_TICKER,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
)
from quant_platform.data.fetch import download_fundamentals, download_prices
from quant_platform.data.sector import resolve_sector_etf
from quant_platform.data.tickers import resolve_universe
from quant_platform.filters.eligibility import check_eligibility
from quant_platform.history.archive import archive_scan_outputs
from quant_platform.notify.email import send_scan_email
from quant_platform.regime.market import compute_market_regime, regime_detail
from quant_platform.report.builder import build_scan_report
from quant_platform.report.export import export_json_report, export_markdown_report
from quant_platform.scoring.aggregate import build_results_table, export_results
from quant_platform.scoring.fundamentals import score_eps, score_revenue
from quant_platform.scoring.relative_strength import (
    compute_rs_market_ratio,
    compute_rs_sector_ratio,
    score_rs_market,
    score_rs_sector,
)
from quant_platform.scoring.resistance import score_resistance
from quant_platform.scoring.volatility import score_bollinger_compression, score_pattern_quality
from quant_platform.scoring.volume import (
    compute_accumulation_ratio,
    score_accumulation,
    score_relative_volume,
)

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(
        self,
        *,
        tickers: list[str] | None = None,
        tickers_file: Path | None = None,
        dynamic_universe: bool = False,
        output: Path = DEFAULT_OUTPUT_CSV,
        use_cache: bool = False,
        dry_run: bool = False,
        report: str | None = None,
        report_json: Path = DEFAULT_OUTPUT_JSON,
        report_md: Path = DEFAULT_OUTPUT_MD,
        archive: bool = False,
        send_email: bool = False,
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
        self.send_email = send_email

    def run(self) -> pd.DataFrame:
        universe = resolve_universe(
            self.tickers,
            tickers_file=self.tickers_file,
            dynamic=self.dynamic_universe,
        )
        logger.info("Scanning %d tickers", len(universe))

        download_tickers = sorted(
            set(universe) | set(ALL_SECTOR_ETFS) | {BENCHMARK_TICKER}
        )

        if self.dry_run:
            prices = _synthetic_prices(download_tickers)
            fundamentals = _synthetic_fundamentals(universe)
        else:
            prices = download_prices(download_tickers, use_cache=self.use_cache)
            fundamentals = download_fundamentals(universe, use_cache=self.use_cache)

        spy_df = _ticker_df(prices, BENCHMARK_TICKER)
        if spy_df is None or spy_df.empty:
            raise RuntimeError(f"Missing benchmark data for {BENCHMARK_TICKER}")

        regime = compute_market_regime(spy_df)
        regime_info = regime_detail(spy_df)
        logger.info("Market regime: %s (multiplier=%.2f)", regime.label, regime.multiplier)

        fund_map = fundamentals.set_index("ticker").to_dict(orient="index")

        sector_dfs = {etf: _ticker_df(prices, etf) for etf in ALL_SECTOR_ETFS}

        eligibility: dict[str, tuple[bool, str]] = {}
        sector_etfs: dict[str, str] = {}
        stock_dfs: dict[str, pd.DataFrame] = {}

        for ticker in universe:
            df = _ticker_df(prices, ticker)
            if df is None or df.empty:
                eligibility[ticker] = (False, "no_price_data")
                continue
            stock_dfs[ticker] = df
            eligible, reason = check_eligibility(df)
            eligibility[ticker] = (eligible, reason)
            if eligible:
                sector_etfs[ticker] = resolve_sector_etf(ticker)

        eligible_tickers = [t for t in universe if eligibility[t][0]]

        rs_market_ratios = pd.Series(
            {
                t: compute_rs_market_ratio(stock_dfs[t], spy_df)
                for t in eligible_tickers
            },
            dtype=float,
        )
        rs_sector_ratios = pd.Series(
            {
                t: compute_rs_sector_ratio(
                    stock_dfs[t],
                    sector_dfs.get(sector_etfs[t]),
                )
                for t in eligible_tickers
                if sector_dfs.get(sector_etfs[t]) is not None
            },
            dtype=float,
        )
        sector_etf_series = pd.Series(sector_etfs)
        accumulation_ratios = pd.Series(
            {t: compute_accumulation_ratio(stock_dfs[t]) for t in eligible_tickers},
            dtype=float,
        )

        rs_market_scores = score_rs_market(rs_market_ratios)
        rs_sector_scores = score_rs_sector(rs_sector_ratios, sector_etf_series)
        accumulation_scores = score_accumulation(accumulation_ratios)

        rows: list[dict] = []
        scores_by_ticker: dict[str, dict] = {}
        for ticker in universe:
            eligible, reason = eligibility[ticker]
            row: dict = {
                "ticker": ticker,
                "eligible": eligible,
                "filter_reason": reason,
                "sector_etf": sector_etfs.get(ticker),
            }

            if not eligible:
                rows.append(row)
                continue

            df = stock_dfs[ticker]
            fund = fund_map.get(ticker, {})
            scores = {
                "rs_market_score": float(rs_market_scores.get(ticker, 0)),
                "rs_sector_score": float(rs_sector_scores.get(ticker, 0)),
                "accumulation_score": float(accumulation_scores.get(ticker, 0)),
                "relative_volume_score": score_relative_volume(df),
                "compression_score": score_bollinger_compression(df),
                "pattern_score": score_pattern_quality(df),
                "resistance_score": score_resistance(df),
                "revenue_score": score_revenue(fund.get("revenue_yoy")),
                "eps_score": score_eps(fund.get("eps_combined")),
            }
            scores_by_ticker[ticker] = scores
            row.update(scores)
            rows.append(row)

        results = build_results_table(rows, regime)
        export_results(results, self.output)
        logger.info("Wrote %d rows to %s", len(results), self.output)

        if self.report:
            scan_report = build_scan_report(
                results_df=results,
                universe=universe,
                stock_dfs=stock_dfs,
                spy_df=spy_df,
                sector_dfs=sector_dfs,
                sector_etfs=sector_etfs,
                fund_map=fund_map,
                regime_detail=regime_info,
                scores_by_ticker=scores_by_ticker,
            )
            if self.report in ("json", "both"):
                export_json_report(scan_report, self.report_json)
                logger.info("Wrote detailed JSON report to %s", self.report_json)
            if self.report in ("md", "both"):
                export_markdown_report(scan_report, self.report_md)
                logger.info("Wrote markdown summary to %s", self.report_md)

            archive_dir = None
            if self.archive:
                archive_dir = archive_scan_outputs(
                    csv_path=self.output,
                    json_path=self.report_json if self.report in ("json", "both") else None,
                    md_path=self.report_md if self.report in ("md", "both") else None,
                    scan_report=scan_report,
                )
                logger.info("Archived scan to %s", archive_dir)

            if self.send_email:
                if send_scan_email(scan_report, archive_dir=archive_dir if self.archive else None):
                    logger.info("Actionable tickers email sent")
                else:
                    logger.warning(
                        "Email not sent — configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_TO"
                    )

        return results


def _ticker_df(prices: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    sub = prices[prices["ticker"] == ticker].copy()
    if sub.empty:
        return None
    return sub.sort_values("Date").reset_index(drop=True)


def _synthetic_prices(tickers: list[str]) -> pd.DataFrame:
    """Generate synthetic OHLCV for dry-run mode."""
    import numpy as np

    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=260)
    frames = []
    rng = np.random.default_rng(42)
    for i, ticker in enumerate(tickers):
        base = 50 + i * 5
        noise = rng.normal(0, 0.5, len(dates)).cumsum()
        close = base + noise + np.linspace(0, 20, len(dates))
        high = close + rng.uniform(0.5, 2, len(dates))
        low = close - rng.uniform(0.5, 2, len(dates))
        open_ = close + rng.uniform(-1, 1, len(dates))
        volume = rng.integers(1_000_000, 3_000_000, len(dates))
        frames.append(
            pd.DataFrame(
                {
                    "Date": dates,
                    "Open": open_,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": volume,
                    "ticker": ticker,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _synthetic_fundamentals(tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": tickers,
            "revenue_yoy": [0.25] * len(tickers),
            "eps_combined": [0.35] * len(tickers),
        }
    )
