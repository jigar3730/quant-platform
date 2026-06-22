"""Finqube-style universe list page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from quant_platform.viz.layout.cards import build_scan_summary_html, extract_scan_date
from quant_platform.viz.shared.components import (
    render_exclusion_chart,
    render_heatmap,
    render_regime_panel,
    render_score_histogram,
    render_scatter,
    render_tier_chart,
)
from quant_platform.viz.shared.navigation import render_breadcrumb, set_detail_ticker
from quant_platform.viz.shared.universe_panel import (
    apply_universe_controls,
    universe_display_columns,
    universe_table_column_config,
)
from quant_platform.viz.strategy.filters import ScanFilters, apply_filters, scatter_dataframe
from quant_platform.viz.strategy.registry import VizStrategyConfig
from quant_platform.viz.strategy.reports import full_universe_dataframe, score_heatmap_dataframe


def render_universe_filter_bar(
    config: VizStrategyConfig,
    filters: ScanFilters,
) -> ScanFilters:
    from quant_platform.viz.strategy.filters import tier_filter_options

    st.markdown('<p class="filter-bar-label">Filters</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1.5])
    tier = c1.selectbox(
        "Tier",
        tier_filter_options(config),
        index=tier_filter_options(config).index(filters.tier)
        if filters.tier in tier_filter_options(config)
        else 0,
        key="universe_filter_tier",
        label_visibility="collapsed",
    )
    min_score = c2.slider(
        "Min score",
        0.0,
        100.0,
        filters.min_score,
        5.0,
        key="universe_filter_min_score",
        label_visibility="collapsed",
    )
    eligible_only = c3.checkbox("Eligible", value=filters.eligible_only, key="universe_filter_eligible")
    actionable_label = " + ".join(config.actionable_tiers)
    actionable_only = c4.checkbox(
        f"Actionable ({actionable_label})",
        value=filters.actionable_only,
        key="universe_filter_actionable",
    )
    search = c5.text_input(
        "Search",
        value=filters.search,
        placeholder="Search ticker",
        key="universe_filter_search",
        label_visibility="collapsed",
    ).strip().upper()
    return ScanFilters(
        tier=tier,
        eligible_only=eligible_only,
        actionable_only=actionable_only,
        min_score=min_score,
        search=search,
    )


def render_universe_page(
    *,
    config: VizStrategyConfig,
    df: pd.DataFrame,
    tickers: list[dict],
    filters: ScanFilters,
    summary: dict,
    regime: dict,
    report_path: str,
) -> None:
    scan_date = extract_scan_date(report_path)
    render_breadcrumb(scan_date=scan_date, on_universe=True)

    st.markdown(
        build_scan_summary_html(
            strategy_label=config.label,
            summary=summary,
            regime=regime,
            config=config,
        ),
        unsafe_allow_html=True,
    )

    filters = render_universe_filter_bar(config, filters)

    full_df = apply_filters(full_universe_dataframe(tickers, config), filters, config)
    if full_df.empty:
        st.warning("No tickers match the current filters.")
        return

    table_df = apply_universe_controls(full_df, config)
    if table_df.empty:
        st.warning("No tickers match the selected view.")
        return

    display_cols = universe_display_columns(table_df, config)
    shown_df = table_df[display_cols].copy()

    st.markdown('<div class="layout-card">', unsafe_allow_html=True)
    st.markdown("#### Universe")
    selection = st.dataframe(
        shown_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="universe_table_select",
        column_config=universe_table_column_config(),
    )
    st.download_button(
        "Download filtered CSV",
        table_df.to_csv(index=False).encode(),
        file_name=f"{config.id}_scan_full.csv",
        mime="text/csv",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if selection.selection.rows:
        symbol = shown_df.iloc[selection.selection.rows[0]]["ticker"]
        set_detail_ticker(symbol)
        st.rerun()

    with st.expander("Scan insights", expanded=False):
        _render_scan_insights(config, summary, regime, df, tickers, filters)


def _render_scan_insights(
    config: VizStrategyConfig,
    summary: dict,
    regime: dict,
    df: pd.DataFrame,
    tickers: list[dict],
    filters: ScanFilters,
) -> None:
    render_regime_panel(regime)
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(render_tier_chart(summary["tier_counts"], config), use_container_width=True)
    with col_right:
        exclusion_fig = render_exclusion_chart(summary.get("filter_breakdown", {}))
        if exclusion_fig:
            st.plotly_chart(exclusion_fig, use_container_width=True)

    filtered_df = apply_filters(df, filters, config)
    eligible_df = filtered_df[filtered_df["eligible"]]
    if eligible_df.empty:
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(render_score_histogram(eligible_df), use_container_width=True)
    with col_b:
        eligible_symbols = {row["ticker"] for _, row in eligible_df.iterrows()}
        heat_df = score_heatmap_dataframe(
            [t for t in tickers if t["ticker"] in eligible_symbols],
            config,
            eligible_only=False,
        )
        if len(heat_df) > 1:
            st.plotly_chart(render_heatmap(heat_df), use_container_width=True)

    scatter_df = scatter_dataframe(
        [t for t in tickers if t["ticker"] in set(eligible_df["ticker"])],
        config,
    )
    if not scatter_df.empty:
        st.plotly_chart(render_scatter(scatter_df, config), use_container_width=True)
