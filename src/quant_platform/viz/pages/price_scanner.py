"""Price-scanner dashboard router (breakout and swing)."""

from __future__ import annotations

import streamlit as st

from quant_platform.viz.layout.company import render_company_page
from quant_platform.viz.layout.compare import render_compare_page
from quant_platform.viz.layout.shell import ShellState
from quant_platform.viz.layout.universe import render_universe_page
from quant_platform.viz.shared.components import get_ticker_by_name
from quant_platform.viz.shared.navigation import sync_detail_ticker
from quant_platform.viz.strategy.filters import ScanFilters
from quant_platform.viz.strategy.reports import report_to_dataframe


def render_price_scanner(
    *,
    report: dict,
    report_path: str,
    shell: ShellState,
    filters: ScanFilters | None = None,
) -> None:
    config = shell.config
    regime = report["market_regime"]
    summary = report["scan_summary"]
    tickers = report["tickers"]
    df = report_to_dataframe(report, config)
    active_filters = filters or ScanFilters()
    detail_ticker = sync_detail_ticker()

    if shell.view == "company" and detail_ticker:
        ticker_data = get_ticker_by_name(tickers, detail_ticker)
        if ticker_data:
            render_company_page(
                ticker=detail_ticker,
                ticker_data=ticker_data,
                config=config,
                df=df,
                report_path=report_path,
            )
        else:
            st.warning(f"No scan data for {detail_ticker}.")
        return

    if shell.view == "compare":
        render_compare_page(
            config=config,
            df=df,
            tickers=tickers,
            filters=active_filters,
            report_path=report_path,
        )
        return

    render_universe_page(
        config=config,
        df=df,
        tickers=tickers,
        filters=active_filters,
        summary=summary,
        regime=regime,
        report_path=report_path,
    )
