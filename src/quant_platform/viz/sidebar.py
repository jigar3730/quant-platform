"""Dashboard sidebar controls."""

from __future__ import annotations

import streamlit as st

from quant_platform.config import DEFAULT_OUTPUT_JSON, HISTORY_DIR
from quant_platform.history.duckdb_store import backfill_from_archives, backfill_lynch_from_archives
from quant_platform.viz.breakout_filters import BreakoutFilters
from quant_platform.viz.lynch_data import list_lynch_report_paths
from quant_platform.viz.navigation import set_detail_ticker, sync_detail_ticker
from quant_platform.viz.styles import COMPONENT_HELP


def _breakout_report_options() -> dict[str, str]:
    history_files = sorted(HISTORY_DIR.glob("*/breakout_scan_report.json"), reverse=True)
    options = {str(DEFAULT_OUTPUT_JSON): "Latest (data/output)"}
    for path in history_files:
        options[str(path)] = f"Archive {path.parent.name}"
    default_path = str(DEFAULT_OUTPUT_JSON)
    if default_path not in options:
        options[default_path] = "Latest (data/output)"
    return options


def render_sidebar_controls() -> tuple[str, str, BreakoutFilters, dict[str, str]]:
    st.sidebar.title("Controls")

    history_options = _breakout_report_options()
    selected_label = st.sidebar.selectbox(
        "Breakout scan to load",
        options=list(history_options.values()),
        index=0,
    )
    report_path = next(key for key, label in history_options.items() if label == selected_label)
    report_path = st.sidebar.text_input("Breakout report path", value=report_path)

    lynch_options = list_lynch_report_paths()
    lynch_labels = list(lynch_options.values()) if lynch_options else ["No Lynch reports"]
    lynch_selected_label = st.sidebar.selectbox(
        "Lynch scan to load",
        options=lynch_labels,
        index=0,
    )
    lynch_report_path = (
        next(key for key, label in lynch_options.items() if label == lynch_selected_label)
        if lynch_options
        else ""
    )
    if lynch_options:
        lynch_report_path = st.sidebar.text_input("Lynch report path", value=lynch_report_path)

    st.sidebar.divider()
    st.sidebar.header("Breakout filters")
    filters = BreakoutFilters(
        tier=st.sidebar.selectbox("Tier", ["All", "Tier 1", "Tier 2", "Tier 3", "filtered"]),
        eligible_only=st.sidebar.checkbox("Eligible only", value=False),
        actionable_only=st.sidebar.checkbox("Actionable only (Tier 1+2)", value=False),
        min_score=st.sidebar.slider("Min final score", 0.0, 100.0, 0.0, 5.0),
        search=st.sidebar.text_input("Search ticker", "").strip().upper(),
    )

    with st.sidebar.expander("Score component guide"):
        for key, text in COMPONENT_HELP.items():
            label = key.replace("_", " ").title()
            st.markdown(f"**{label}** — {text}")

    if st.sidebar.button("Sync archives to DuckDB"):
        breakout_synced = backfill_from_archives()
        lynch_synced = backfill_lynch_from_archives()
        st.sidebar.success(
            f"Synced {breakout_synced} breakout + {lynch_synced} Lynch archived scan(s)."
        )

    return report_path, lynch_report_path, filters, lynch_options


def render_sidebar_ticker_picker(all_symbols: list[str]) -> str | None:
    detail_ticker = sync_detail_ticker()
    st.sidebar.divider()
    st.sidebar.header("Ticker Detail")
    sidebar_pick = st.sidebar.selectbox(
        "Open ticker profile",
        options=[""] + all_symbols,
        index=(all_symbols.index(detail_ticker) + 1) if detail_ticker in all_symbols else 0,
        format_func=lambda value: "Select a ticker..." if value == "" else value,
    )
    if sidebar_pick and sidebar_pick != detail_ticker:
        set_detail_ticker(sidebar_pick)
        detail_ticker = sidebar_pick
    if detail_ticker and st.sidebar.button("Clear ticker selection"):
        set_detail_ticker(None)
        detail_ticker = None
    return detail_ticker
