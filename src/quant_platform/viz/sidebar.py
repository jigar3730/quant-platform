"""Dashboard sidebar controls."""

from __future__ import annotations

import streamlit as st

from quant_platform.history.duckdb_store import backfill_from_archives, backfill_lynch_from_archives
from quant_platform.viz.shared.navigation import set_detail_ticker, sync_detail_ticker
from quant_platform.viz.strategy.filters import ScanFilters, tier_filter_options
from quant_platform.viz.strategy.registry import VizStrategyConfig, list_viz_strategies
from quant_platform.viz.strategy.reports import list_report_paths


def render_strategy_sidebar() -> tuple[VizStrategyConfig, str, ScanFilters | None]:
    st.sidebar.title("Controls")

    strategies = list_viz_strategies()
    labels = [s.label for s in strategies]
    selected_label = st.sidebar.selectbox("Strategy", labels, index=0)
    config = next(s for s in strategies if s.label == selected_label)

    report_options = list_report_paths(config)
    if not report_options:
        report_path = config.default_report_path
    else:
        option_labels = list(report_options.values())
        selected_report_label = st.sidebar.selectbox("Report", option_labels, index=0)
        report_path = next(
            key for key, label in report_options.items() if label == selected_report_label
        )
    report_path = st.sidebar.text_input("Report path", value=report_path)

    filters: ScanFilters | None = None
    if config.page_set == "price":
        st.sidebar.divider()
        st.sidebar.header(f"{config.label} filters")
        actionable_label = " + ".join(config.actionable_tiers)
        filters = ScanFilters(
            tier=st.sidebar.selectbox("Tier", tier_filter_options(config)),
            eligible_only=st.sidebar.checkbox("Eligible only", value=False),
            actionable_only=st.sidebar.checkbox(
                f"Actionable only ({actionable_label})",
                value=False,
            ),
            min_score=st.sidebar.slider("Min final score", 0.0, 100.0, 0.0, 5.0),
            search=st.sidebar.text_input("Search ticker", "").strip().upper(),
        )

        if config.component_help:
            with st.sidebar.expander("Score component guide"):
                for key, text in config.component_help.items():
                    label = config.score_labels.get(key, key.replace("_", " ").title())
                    st.markdown(f"**{label}** — {text}")

    if st.sidebar.button("Sync archives to DuckDB"):
        breakout_synced = backfill_from_archives()
        lynch_synced = backfill_lynch_from_archives()
        st.sidebar.success(
            f"Synced {breakout_synced} breakout + {lynch_synced} Lynch archived scan(s)."
        )

    return config, report_path, filters


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
