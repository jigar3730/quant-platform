"""Interactive Full Universe detail panel and table helpers."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from quant_platform.filters.eligibility import FILTER_LABELS
from quant_platform.viz.shared.components import (
    apply_chart_style,
    render_ticker_news_panel,
    tier_badge_html,
)
from quant_platform.viz.shared.navigation import set_detail_ticker, ticker_link_html
from quant_platform.viz.strategy.registry import VizStrategyConfig
from quant_platform.viz.strategy.reports import scores_to_dataframe


def _sort_options(config: VizStrategyConfig) -> dict[str, str]:
    options = {"Final Score": "final_score", "Normalized": "normalized_score"}
    for key, label in config.score_labels.items():
        options[label] = label
    if config.id == "breakout":
        options["Revenue YoY %"] = "revenue_yoy_pct"
        options["EPS Growth %"] = "eps_growth_pct"
        options["Technical Score"] = "tech_score"
        options["Fundamental Score"] = "fund_score"
    return options


def render_universe_summary(full_df: pd.DataFrame, config: VizStrategyConfig) -> None:
    tiers = full_df["tier"].value_counts()
    eligible = int(full_df["eligible"].sum())
    cols = st.columns(min(5, 2 + len(config.tiers)))
    cols[0].metric("Universe", len(full_df))
    cols[1].metric("Eligible", eligible)
    for i, tier in enumerate(config.tiers):
        cols[2 + i].metric(tier, int(tiers.get(tier, 0)))
    avg_col = cols[-1]
    avg = full_df.loc[full_df["eligible"], "final_score"].mean()
    avg_col.metric("Avg Score (eligible)", f"{avg:.1f}" if eligible else "—")


def apply_universe_controls(full_df: pd.DataFrame, config: VizStrategyConfig) -> pd.DataFrame:
    st.markdown("##### Explore the universe")
    sort_options = _sort_options(config)
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    sort_label = c1.selectbox("Sort by", list(sort_options.keys()), key="universe_sort")
    sort_col = sort_options[sort_label]
    ascending = c2.toggle("Ascending", value=False, key="universe_sort_asc")

    sectors = sorted(full_df["sector_etf"].dropna().unique().tolist())
    sector_pick = c3.multiselect("Sector ETF", sectors, key="universe_sector_filter")

    view_mode = c4.selectbox("View", ["All", "Eligible", "Actionable"], key="universe_view")

    result = full_df.copy()
    if sector_pick:
        result = result[result["sector_etf"].isin(sector_pick)]
    if view_mode == "Eligible":
        result = result[result["eligible"]]
    elif view_mode == "Actionable":
        result = result[result["tier"].isin(config.actionable_tiers)]

    if sort_col in result.columns:
        result = result.sort_values(sort_col, ascending=ascending, na_position="last")
    return result


def _mini_score_chart(ticker_data: dict, ticker: str, config: VizStrategyConfig) -> go.Figure | None:
    score_df = scores_to_dataframe(ticker_data, config)
    if score_df.empty:
        return None
    top = score_df.nlargest(6, "score")
    fig = go.Figure(
        go.Bar(
            x=top["score"],
            y=top["component"],
            orientation="h",
            marker_color="#3b82f6",
            text=[f"{s:.0f}/{m:.0f}" for s, m in zip(top["score"], top["max"], strict=True)],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"{ticker} — top signals",
        height=260,
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis_title="Points",
    )
    return apply_chart_style(fig)


def render_universe_detail_panel(
    ticker: str,
    ticker_data: dict,
    config: VizStrategyConfig,
) -> None:
    summary = ticker_data.get("summary") or {}
    st.markdown(
        f"### {ticker_link_html(ticker)} "
        f"{tier_badge_html(ticker_data.get('tier', 'filtered'), config)}",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    cols[0].metric("Final Score", f"{summary.get('final_adjusted_score', 0):.1f}")
    cols[1].metric("Normalized", f"{summary.get('normalized_score', 0):.1f}")
    cols[2].metric("Sector ETF", ticker_data.get("sector_etf") or "—")
    cols[3].metric("Eligible", "Yes" if ticker_data.get("eligible") else "No")

    fail_reason = ticker_data.get("eligibility", {}).get("fail_reason")
    if ticker_data.get("eligible") and ticker_data.get("tier_reason"):
        st.success(ticker_data["tier_reason"])
    elif fail_reason:
        st.warning(FILTER_LABELS.get(fail_reason, fail_reason))

    fig = _mini_score_chart(ticker_data, ticker, config)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Open full profile", key=f"open_profile_{ticker}", use_container_width=True):
        set_detail_ticker(ticker)
        st.rerun()

    with st.expander("Live market snapshot", expanded=False):
        render_ticker_news_panel(ticker, compact=True)


def universe_table_column_config() -> dict:
    return {
        "eligible": st.column_config.CheckboxColumn("Eligible"),
        "final_score": st.column_config.ProgressColumn(
            "Final Score",
            format="%.1f",
            min_value=0,
            max_value=100,
        ),
        "normalized_score": st.column_config.NumberColumn("Normalized", format="%.1f"),
        "tech_score": st.column_config.NumberColumn("Technical", format="%.0f"),
        "fund_score": st.column_config.NumberColumn("Fundamental", format="%.0f"),
        "revenue_yoy_pct": st.column_config.NumberColumn("Rev YoY %", format="%.1f"),
        "eps_growth_pct": st.column_config.NumberColumn("EPS Gr %", format="%.1f"),
        "top_signal": st.column_config.TextColumn("Top Signal", width="medium"),
        "tier_reason": st.column_config.TextColumn("Tier Note", width="large"),
        "filter_label": st.column_config.TextColumn("Exclusion", width="medium"),
        "filter_reason": st.column_config.TextColumn("Filter", width="medium"),
    }


def universe_display_columns(table_df: pd.DataFrame, config: VizStrategyConfig) -> list[str]:
    preferred = [
        "ticker",
        "tier",
        "eligible",
        "final_score",
        "normalized_score",
        "top_signal",
        "tech_score",
        "fund_score",
        "sector_etf",
        *config.score_labels.values(),
        "revenue_yoy_pct",
        "eps_growth_pct",
        "tier_reason",
        "filter_label",
        "filter_reason",
    ]
    return [column for column in preferred if column in table_df.columns]
