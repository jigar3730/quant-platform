"""Streamlit dashboard for breakout, swing, and Peter Lynch scan reports."""

from __future__ import annotations

import json

import streamlit as st

from quant_platform.viz.pages.lynch import render_lynch_pages
from quant_platform.viz.pages.price_scanner import (
    render_all_tickers_tab,
    render_compare_tab,
    render_overview_tab,
    render_price_header,
    render_ticker_detail_tab,
    render_watchlist_tab,
)
from quant_platform.viz.shared.navigation import sync_detail_ticker
from quant_platform.viz.shared.styles import CUSTOM_CSS
from quant_platform.viz.sidebar import render_sidebar_ticker_picker, render_strategy_sidebar
from quant_platform.viz.strategy.reports import (
    load_scan_report,
    report_to_dataframe,
    validate_report_strategy,
)

st.set_page_config(
    page_title="Quant Platform",
    page_icon="QP",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

config, report_path, filters = render_strategy_sidebar()

try:
    report = load_scan_report(report_path)
except FileNotFoundError:
    st.error(f"No {config.label} report found.")
    st.info(config.cli_hint)
    st.stop()
except json.JSONDecodeError:
    st.error("Invalid JSON report file.")
    st.stop()

mismatch = validate_report_strategy(report, config)
if mismatch:
    st.warning(mismatch)

if config.page_set == "price":
    regime = report["market_regime"]
    summary = report["scan_summary"]
    tickers = report["tickers"]
    df = report_to_dataframe(report, config)
    all_symbols = sorted(df["ticker"].tolist())

    detail_ticker = render_sidebar_ticker_picker(all_symbols) if all_symbols else sync_detail_ticker()

    render_price_header(
        config=config,
        report_path=report_path,
        summary=summary,
        regime=regime,
        detail_ticker=detail_ticker,
    )

    tab_names = [
        "Full Universe",
        "Overview",
        "Ticker Detail",
        "Actionable Watchlist",
        "Compare",
    ]
    tabs = st.tabs(tab_names)
    tab_map = dict(zip(tab_names, tabs, strict=True))

    with tab_map["Overview"]:
        render_overview_tab(
            config=config,
            summary=summary,
            regime=regime,
            df=df,
            tickers=tickers,
            filters=filters,
        )

    with tab_map["Full Universe"]:
        detail_ticker = render_all_tickers_tab(
            config=config,
            tickers=tickers,
            filters=filters,
            detail_ticker=detail_ticker,
        )

    with tab_map["Ticker Detail"]:
        render_ticker_detail_tab(
            config=config,
            tickers=tickers,
            all_symbols=all_symbols,
            detail_ticker=detail_ticker,
        )

    with tab_map["Actionable Watchlist"]:
        render_watchlist_tab(config=config, df=df, tickers=tickers, filters=filters)

    with tab_map["Compare"]:
        render_compare_tab(config=config, df=df, tickers=tickers, filters=filters)

else:
    render_lynch_pages(report, report_path)
