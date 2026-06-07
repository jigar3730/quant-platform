"""Streamlit dashboard for breakout and Peter Lynch scan reports."""

from __future__ import annotations

import json

import streamlit as st

from quant_platform.viz.data import load_report, tickers_to_dataframe
from quant_platform.viz.lynch_components import render_lynch_tab
from quant_platform.viz.lynch_data import list_lynch_report_paths, load_lynch_report
from quant_platform.viz.navigation import sync_detail_ticker
from quant_platform.viz.pages.breakout import (
    render_all_tickers_tab,
    render_breakout_header,
    render_compare_tab,
    render_overview_tab,
    render_ticker_detail_tab,
    render_watchlist_tab,
)
from quant_platform.viz.sidebar import render_sidebar_controls, render_sidebar_ticker_picker
from quant_platform.viz.styles import CUSTOM_CSS

st.set_page_config(
    page_title="Quant Platform",
    page_icon="QP",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

report_path, lynch_report_path, filters = render_sidebar_controls()

report = None
df = None
tickers: list[dict] = []
all_symbols: list[str] = []
regime = None
summary = None

try:
    report = load_report(report_path)
    regime = report["market_regime"]
    summary = report["scan_summary"]
    tickers = report["tickers"]
    df = tickers_to_dataframe(tickers)
    all_symbols = sorted(df["ticker"].tolist())
except FileNotFoundError:
    st.sidebar.warning("Breakout report not found — breakout tabs will be empty.")
except json.JSONDecodeError:
    st.sidebar.error("Invalid breakout JSON report file.")

lynch_options = list_lynch_report_paths()
lynch_report = None
if lynch_report_path:
    try:
        lynch_report = load_lynch_report(lynch_report_path)
    except FileNotFoundError:
        st.sidebar.warning("Lynch report not found — Peter Lynch tab will be empty.")
    except json.JSONDecodeError:
        st.sidebar.error("Invalid Lynch JSON report file.")

if report is None and lynch_report is None:
    st.error("No scan reports found.")
    st.info(
        "Run `quant-scan --report both` and/or `quant-lynch --report both --archive`, "
        "then reload the dashboard."
    )
    st.stop()

detail_ticker = render_sidebar_ticker_picker(all_symbols) if all_symbols else sync_detail_ticker()

if report is not None:
    render_breakout_header(
        report_path=report_path,
        summary=summary,
        regime=regime,
        detail_ticker=detail_ticker,
    )

tab_names = ["Full Universe", "Overview", "Ticker Detail", "Actionable Watchlist", "Compare"]
if lynch_report is not None or lynch_options:
    tab_names.append("Peter Lynch")

tabs = st.tabs(tab_names)
tab_map = dict(zip(tab_names, tabs, strict=True))

with tab_map["Overview"]:
    if report is None:
        st.info("Load a breakout scan from the sidebar to view this tab.")
    else:
        render_overview_tab(
            report_path=report_path,
            summary=summary,
            regime=regime,
            df=df,
            tickers=tickers,
            filters=filters,
        )

with tab_map["Full Universe"]:
    if report is None:
        st.info("Load a breakout scan from the sidebar to view this tab.")
    else:
        detail_ticker = render_all_tickers_tab(
            tickers=tickers,
            filters=filters,
            detail_ticker=detail_ticker,
        )

with tab_map["Ticker Detail"]:
    if report is None:
        st.info("Load a breakout scan from the sidebar to view this tab.")
    else:
        render_ticker_detail_tab(
            tickers=tickers,
            all_symbols=all_symbols,
            detail_ticker=detail_ticker,
        )

with tab_map["Actionable Watchlist"]:
    if report is None:
        st.info("Load a breakout scan from the sidebar to view this tab.")
    else:
        render_watchlist_tab(df=df, tickers=tickers, filters=filters)

with tab_map["Compare"]:
    if report is None:
        st.info("Load a breakout scan from the sidebar to view this tab.")
    else:
        render_compare_tab(df=df, tickers=tickers, filters=filters)

if "Peter Lynch" in tab_map:
    with tab_map["Peter Lynch"]:
        if lynch_report is None:
            st.info(
                "No Lynch report loaded. Run `quant-lynch --report both --archive` "
                "or pick an archived scan in the sidebar."
            )
        else:
            render_lynch_tab(lynch_report, lynch_report_path)
