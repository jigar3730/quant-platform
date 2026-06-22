"""Streamlit dashboard for breakout, swing, and Peter Lynch scan reports."""

from __future__ import annotations

import json

import streamlit as st

from quant_platform.viz.layout.shell import render_app_shell, render_lynch_sidebar
from quant_platform.viz.pages.lynch import render_lynch_pages
from quant_platform.viz.pages.price_scanner import render_price_scanner
from quant_platform.viz.shared.styles import CUSTOM_CSS, PRICE_LAYOUT_CSS
from quant_platform.viz.strategy.reports import load_scan_report, validate_report_strategy

st.set_page_config(
    page_title="Quant Platform",
    page_icon="QP",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

shell = render_app_shell()
if shell is None:
    config, report_path = render_lynch_sidebar()
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
    render_lynch_pages(report, report_path)
    st.stop()

st.markdown(PRICE_LAYOUT_CSS, unsafe_allow_html=True)

try:
    report = load_scan_report(shell.report_path)
except FileNotFoundError:
    st.error(f"No {shell.config.label} report found.")
    st.info(shell.config.cli_hint)
    st.stop()
except json.JSONDecodeError:
    st.error("Invalid JSON report file.")
    st.stop()

mismatch = validate_report_strategy(report, shell.config)
if mismatch:
    st.warning(mismatch)

render_price_scanner(report=report, report_path=shell.report_path, shell=shell)
