"""Finqube-style compare page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from quant_platform.viz.layout.cards import extract_scan_date
from quant_platform.viz.layout.universe import render_universe_filter_bar
from quant_platform.viz.shared.components import get_ticker_by_name, render_compare_radar
from quant_platform.viz.shared.navigation import render_breadcrumb, ticker_link_html
from quant_platform.viz.strategy.filters import ScanFilters, apply_filters
from quant_platform.viz.strategy.registry import VizStrategyConfig


def render_compare_page(
    *,
    config: VizStrategyConfig,
    df: pd.DataFrame,
    tickers: list[dict],
    filters: ScanFilters,
    report_path: str,
) -> None:
    scan_date = extract_scan_date(report_path)
    render_breadcrumb(scan_date=scan_date, on_universe=True)

    filters = render_universe_filter_bar(config, filters)

    st.markdown('<div class="layout-card">', unsafe_allow_html=True)
    st.markdown("#### Compare tickers")

    filtered = apply_filters(df, filters, config)
    eligible_names = (
        filtered[filtered["eligible"]]
        .sort_values("final_score", ascending=False)["ticker"]
        .tolist()
    )
    if len(eligible_names) < 2:
        st.warning("Need at least 2 eligible tickers to compare.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    picked = st.multiselect(
        "Select 2–3 tickers",
        eligible_names,
        default=eligible_names[: min(3, len(eligible_names))],
        max_selections=3,
        key="compare_pick",
    )
    if len(picked) < 2:
        st.markdown("</div>", unsafe_allow_html=True)
        return

    compare_links = " · ".join(ticker_link_html(symbol) for symbol in picked)
    st.markdown(f"Profiles: {compare_links}", unsafe_allow_html=True)

    compare_data = [get_ticker_by_name(tickers, name) for name in picked]
    compare_data = [item for item in compare_data if item]
    fig = render_compare_radar(compare_data, config)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    compare_rows = []
    for ticker_data in compare_data:
        summary = ticker_data.get("summary", {})
        row = {
            "ticker": ticker_data["ticker"],
            "tier": ticker_data["tier"],
            "final_score": summary.get("final_adjusted_score", 0),
            "sector_etf": ticker_data.get("sector_etf"),
        }
        scores = ticker_data.get("scores") or {}
        for key, label in config.score_labels.items():
            row[label] = scores.get(key, {}).get("score", 0)
        compare_rows.append(row)

    compare_df = pd.DataFrame(compare_rows)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
