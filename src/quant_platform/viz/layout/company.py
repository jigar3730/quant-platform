"""Finqube-style company profile page (Zones B–E)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from quant_platform.viz.layout.cards import (
    build_company_hero_html,
    build_key_insight_html,
    build_score_strip_html,
    build_universe_context_html,
    extract_scan_date,
    score_pills_from_ticker,
)
from quant_platform.viz.shared.components import (
    _load_ticker_news,
    _load_ticker_snapshot,
    _render_score_cards,
    render_radar,
    render_score_bars,
    tier_badge_html,
)
from quant_platform.viz.shared.navigation import render_breadcrumb
from quant_platform.viz.strategy.registry import VizStrategyConfig
from quant_platform.viz.strategy.reports import scores_to_dataframe


def _hero_insight(ticker_data: dict) -> str:
    if ticker_data.get("tier_reason"):
        return ticker_data["tier_reason"]
    if not ticker_data.get("eligible"):
        fail = ticker_data.get("eligibility", {}).get("fail_reason")
        if fail:
            from quant_platform.filters.eligibility import FILTER_LABELS

            return FILTER_LABELS.get(fail, fail.replace("_", " ").title())
    return ""


def render_company_page(
    *,
    ticker: str,
    ticker_data: dict,
    config: VizStrategyConfig,
    df: pd.DataFrame,
    report_path: str,
) -> None:
    scan_date = extract_scan_date(report_path)
    render_breadcrumb(scan_date=scan_date, on_universe=False)

    snapshot = _load_ticker_snapshot(ticker)
    company_name = snapshot.get("short_name") or snapshot.get("name") if snapshot else None
    summary = ticker_data.get("summary") or {}

    st.markdown(
        build_company_hero_html(
            ticker=ticker,
            company_name=company_name,
            tier_badge=tier_badge_html(ticker_data.get("tier", "filtered"), config),
            strategy_label=config.label,
            snapshot=snapshot,
            sector_etf=ticker_data.get("sector_etf"),
            scan_date=scan_date,
            insight=_hero_insight(ticker_data),
        ),
        unsafe_allow_html=True,
    )

    pills = score_pills_from_ticker(ticker_data, config)
    st.markdown(
        build_score_strip_html(
            final_score=float(summary.get("final_adjusted_score", 0)),
            regime_multiplier=summary.get("regime_multiplier"),
            pills=pills,
        ),
        unsafe_allow_html=True,
    )

    tab_summary, tab_technical, tab_news = st.tabs(["Summary", "Technical", "News"])

    with tab_summary:
        _render_summary_tab(ticker, ticker_data, config, df)

    with tab_technical:
        _render_technical_tab(ticker, ticker_data, config)

    with tab_news:
        _render_news_tab(ticker)


def _render_summary_tab(
    ticker: str,
    ticker_data: dict,
    config: VizStrategyConfig,
    df: pd.DataFrame,
) -> None:
    summary = ticker_data.get("summary") or {}
    col_left, col_right = st.columns(2)
    scores_df = scores_to_dataframe(ticker_data, config)

    with col_left:
        st.markdown('<div class="layout-card">', unsafe_allow_html=True)
        if not scores_df.empty:
            st.plotly_chart(render_radar(scores_df, ticker), use_container_width=True)
        else:
            st.info("No score components available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown(
            build_universe_context_html(
                ticker=ticker,
                final_score=float(summary.get("final_adjusted_score", 0)),
                tier=ticker_data.get("tier", "filtered"),
                df=df,
                config=config,
            ),
            unsafe_allow_html=True,
        )

    st.markdown(build_key_insight_html(ticker_data, config), unsafe_allow_html=True)


def _render_technical_tab(
    ticker: str,
    ticker_data: dict,
    config: VizStrategyConfig,
) -> None:
    technical_df = scores_to_dataframe(ticker_data, config)
    if not technical_df.empty:
        st.markdown('<div class="layout-card">', unsafe_allow_html=True)
        st.plotly_chart(render_score_bars(technical_df, ticker), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="layout-card">', unsafe_allow_html=True)
    _render_score_cards(ticker_data, config, config.technical_keys, "Factor detail")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_news_tab(ticker: str) -> None:
    snapshot = _load_ticker_snapshot(ticker)
    if snapshot:
        change = snapshot.get("change_pct")
        change_str = f"{change:+.2f}%" if change is not None else "—"
        from quant_platform.viz.layout.cards import format_market_cap

        st.markdown(
            f"""
            <div class="layout-card">
              <div class="layout-card-title">Live market</div>
              <p>
                <strong>${snapshot.get("price", 0):,.2f}</strong>
                &nbsp; {change_str} &nbsp;|&nbsp;
                MCap {format_market_cap(snapshot.get("market_cap"))}
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    news = _load_ticker_news(ticker, count=8)
    if not news:
        st.info("No recent news found for this ticker.")
        return

    import html

    for article in news:
        title = html.escape(article.get("title", ""))
        url = article.get("url")
        meta = " · ".join(
            html.escape(str(p)) for p in [article.get("publisher"), article.get("published")] if p
        )
        title_html = f'<a href="{html.escape(url)}" target="_blank">{title}</a>' if url else title
        summary = html.escape(article.get("summary", ""))
        st.markdown(
            f"""
            <div class="news-card">
              <strong>{title_html}</strong>
              <div class="news-card-meta">{meta}</div>
              <p>{summary[:280]}{"..." if len(summary) > 280 else ""}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
