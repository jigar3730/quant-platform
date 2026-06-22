"""Finqube-style app shell (Zone A)."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from quant_platform.history.duckdb_store import backfill_from_archives, backfill_lynch_from_archives
from quant_platform.viz.shared.navigation import resolve_view, set_detail_ticker, set_view
from quant_platform.viz.strategy.registry import VizStrategyConfig, list_viz_strategies
from quant_platform.viz.strategy.reports import list_report_paths


@dataclass
class ShellState:
    config: VizStrategyConfig
    report_path: str
    view: str


def render_app_shell() -> ShellState | None:
    strategies = list_viz_strategies()
    labels = [s.label for s in strategies]
    label_to_config = {s.label: s for s in strategies}

    view = resolve_view()

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    row1 = st.columns([2, 2, 1.5, 1.5, 1.2])
    with row1[0]:
        st.markdown('<p class="app-shell-brand">Quant Platform</p>', unsafe_allow_html=True)
        st.markdown('<p class="app-shell-sub">Multi-strategy research scanner</p>', unsafe_allow_html=True)

    with row1[1]:
        with st.form("shell_search_form", clear_on_submit=True):
            search = st.text_input(
                "Search ticker",
                placeholder="Search ticker…",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Go", use_container_width=True)
        if submitted and search.strip():
            set_detail_ticker(search.strip())
            st.rerun()

    with row1[2]:
        selected_label = st.selectbox(
            "Strategy",
            labels,
            key="shell_strategy",
            label_visibility="collapsed",
        )
        config = label_to_config[selected_label]
        if config.page_set != "price":
            st.markdown("</div>", unsafe_allow_html=True)
            return None

    with row1[3]:
        report_options = list_report_paths(config)
        if report_options:
            option_labels = list(report_options.values())
            selected_report_label = st.selectbox(
                "Report",
                option_labels,
                key="shell_report",
                label_visibility="collapsed",
            )
            report_path = next(
                key for key, label in report_options.items() if label == selected_report_label
            )
        else:
            report_path = config.default_report_path

    with row1[4]:
        nav_col1, nav_col2 = st.columns(2)
        if nav_col1.button("Universe", use_container_width=True, type="primary" if view == "universe" else "secondary"):
            set_view("universe")
            st.rerun()
        if nav_col2.button("Compare", use_container_width=True, type="primary" if view == "compare" else "secondary"):
            set_view("compare")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Settings"):
        report_path = st.text_input("Report path override", value=report_path, key="shell_report_path")
        if st.button("Sync archives to DuckDB"):
            breakout_synced = backfill_from_archives()
            lynch_synced = backfill_lynch_from_archives()
            st.success(
                f"Synced {breakout_synced} breakout + {lynch_synced} Lynch archived scan(s)."
            )
        if config.component_help:
            st.markdown("**Score component guide**")
            for key, text in config.component_help.items():
                label = config.score_labels.get(key, key.replace("_", " ").title())
                st.markdown(f"- **{label}** — {text}")

    return ShellState(
        config=config,
        report_path=report_path,
        view=view,
    )


def render_lynch_sidebar() -> tuple[VizStrategyConfig, str]:
    """Lynch page set keeps sidebar controls."""
    st.sidebar.title("Controls")
    config = next(s for s in list_viz_strategies() if s.id == "lynch")
    report_options = list_report_paths(config)
    if report_options:
        option_labels = list(report_options.values())
        selected_report_label = st.sidebar.selectbox("Report", option_labels, index=0)
        report_path = next(
            key for key, label in report_options.items() if label == selected_report_label
        )
    else:
        report_path = config.default_report_path
    report_path = st.sidebar.text_input("Report path", value=report_path)
    if st.sidebar.button("Sync archives to DuckDB"):
        breakout_synced = backfill_from_archives()
        lynch_synced = backfill_lynch_from_archives()
        st.sidebar.success(
            f"Synced {breakout_synced} breakout + {lynch_synced} Lynch archived scan(s)."
        )
    return config, report_path
