"""Reusable dashboard UI components — strategy-aware via VizStrategyConfig."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from quant_platform.data.news import fetch_ticker_news, fetch_ticker_snapshot
from quant_platform.filters.eligibility import FILTER_LABELS
from quant_platform.viz.shared.navigation import ticker_link_html
from quant_platform.viz.shared.styles import DEFAULT_TIER_COLORS, PLOTLY_LAYOUT, tier_badge_styles
from quant_platform.viz.shared.validation import regime_looks_synthetic
from quant_platform.viz.strategy.registry import VizStrategyConfig
from quant_platform.viz.strategy.reports import scores_to_dataframe


def apply_chart_style(fig: go.Figure, *, height: int | None = None) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    if height:
        fig.update_layout(height=height)
    return fig


def tier_color_map(config: VizStrategyConfig) -> dict[str, str]:
    return {**DEFAULT_TIER_COLORS, **config.tier_colors}


def tier_badge_html(tier: str, config: VizStrategyConfig) -> str:
    styles = tier_badge_styles(config)
    style = styles.get(tier, styles.get("filtered", "background:#f1f5f9;color:#475569;"))
    return f"<span class='tier-badge' style='{style}'>{tier}</span>"


def render_scan_header(
    config: VizStrategyConfig,
    report_path: str,
    summary: dict,
    regime: dict,
) -> None:
    tiers = summary["tier_counts"]
    tier_parts = " &nbsp;|&nbsp; ".join(
        f"{tiers.get(label, 0)} {label}" for label in config.tiers
    )
    st.markdown(
        f"""
        <div class="scan-header">
            <h1>{config.label} Scanner</h1>
            <p>
              {summary['universe_size']} tickers scanned
              &nbsp;|&nbsp; {summary['eligible_count']} eligible
              &nbsp;|&nbsp; {tier_parts}
              &nbsp;|&nbsp; Regime: <strong>{regime['label'].title()}</strong>
              (×{regime['multiplier']})
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Report: `{report_path}`")


def render_regime_panel(regime: dict) -> None:
    if regime_looks_synthetic(regime):
        st.warning(
            "SPY price looks like **synthetic dry-run data**, not live market data. "
            "Reload the archived scan from the sidebar, or run "
            "`quant-scan --report both` without `--dry-run`."
        )
    st.markdown('<div class="info-card"><h4>Market Regime (SPY)</h4>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SPY Price", f"${regime['spy_price']}")
    c2.metric("SMA 50", f"${regime['sma50']}")
    c3.metric("SMA 200", f"${regime['sma200']}")
    c4.metric("63d Return", f"{regime['return_63d_pct']}%")
    st.markdown(
        f"**{regime['meaning']}**  \n"
        f"52-week high: ${regime.get('high_52w', '—')} "
        f"({regime['pct_below_52w_high']}% below high)"
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_tier_chart(tiers: dict, config: VizStrategyConfig) -> go.Figure:
    labels = [*config.tiers, "filtered"]
    values = [tiers.get(label, 0) for label in labels]
    colors = [tier_color_map(config).get(label, "#94a3b8") for label in labels]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.45, marker_colors=colors))
    fig.update_layout(title="Tier Distribution", showlegend=True, height=320)
    return apply_chart_style(fig)


def render_exclusion_chart(breakdown: dict) -> go.Figure | None:
    if not breakdown:
        return None
    labels = [FILTER_LABELS.get(k, k.replace("_", " ").title()) for k in breakdown]
    fig = px.bar(
        x=list(breakdown.values()),
        y=labels,
        orientation="h",
        labels={"x": "Tickers", "y": ""},
        color=list(breakdown.values()),
        color_continuous_scale="Reds",
    )
    fig.update_layout(title="Why Stocks Were Excluded", showlegend=False, coloraxis_showscale=False)
    return apply_chart_style(fig, height=max(220, len(breakdown) * 36))


def render_score_histogram(eligible_df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        eligible_df,
        x="final_score",
        nbins=12,
        color_discrete_sequence=["#3b82f6"],
        labels={"final_score": "Final Score"},
    )
    fig.update_layout(title="Score Distribution (Eligible)")
    return apply_chart_style(fig, height=280)


def render_heatmap(heat_df: pd.DataFrame) -> go.Figure:
    melt = heat_df.melt(id_vars="ticker", var_name="component", value_name="score")
    fig = px.density_heatmap(
        melt,
        x="component",
        y="ticker",
        z="score",
        histfunc="avg",
        color_continuous_scale="Blues",
        labels={"score": "Points"},
    )
    fig.update_layout(
        title="Component Scores by Ticker",
        height=max(320, len(heat_df) * 24),
    )
    return apply_chart_style(fig)


def render_scatter(scatter_df: pd.DataFrame, config: VizStrategyConfig) -> go.Figure:
    x_key, y_key = config.scatter_defaults
    x_label = config.score_labels.get(x_key, x_key.replace("_", " ").title())
    y_label = config.score_labels.get(y_key, y_key.replace("_", " ").title())
    fig = px.scatter(
        scatter_df,
        x=x_key,
        y=y_key,
        text="ticker",
        size="final_score",
        color="tier",
        color_discrete_map=tier_color_map(config),
        hover_data=["final_score", "tier"],
        labels={
            x_key: f"{x_label} Score",
            y_key: f"{y_label} Score",
            "final_score": "Final Score",
        },
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(title=f"{x_label} vs {y_label}")
    return apply_chart_style(fig, height=400)


def render_score_bars(scores_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = px.bar(
        scores_df,
        x="score",
        y="component",
        orientation="h",
        range_x=[0, max(scores_df["max"].max(), 1)],
        text=scores_df["score"].round(1),
        color="pct",
        color_continuous_scale="Blues",
        labels={"score": "Score", "component": "", "pct": "% of max"},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(title=f"{ticker} — Component Scores", showlegend=False)
    return apply_chart_style(fig, height=360)


def render_radar(scores_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=scores_df["pct"].tolist(),
            theta=scores_df["component"].tolist(),
            fill="toself",
            name=ticker,
            line_color="#3b82f6",
            fillcolor="rgba(59,130,246,0.25)",
        )
    )
    fig.update_layout(
        title=f"{ticker} — Score Profile",
        polar=dict(radialaxis=dict(range=[0, 100], tickformat=".0f")),
        height=360,
    )
    return apply_chart_style(fig)


def render_compare_radar(ticker_list: list[dict], config: VizStrategyConfig) -> go.Figure | None:
    fig = go.Figure()
    palette = ["#3b82f6", "#f59e0b", "#10b981"]
    for i, t in enumerate(ticker_list):
        comp_df = scores_to_dataframe(t, config)
        if comp_df.empty:
            continue
        fig.add_trace(
            go.Scatterpolar(
                r=comp_df["pct"].tolist(),
                theta=comp_df["component"].tolist(),
                fill="toself",
                name=t["ticker"],
                opacity=0.6,
                line_color=palette[i % len(palette)],
            )
        )
    if not fig.data:
        return None
    fig.update_layout(
        title="Ticker Comparison",
        polar=dict(radialaxis=dict(range=[0, 100])),
        height=420,
    )
    return apply_chart_style(fig)


def render_eligibility_panel(ticker_data: dict) -> None:
    st.markdown("#### Eligibility Checks")
    checks = ticker_data.get("eligibility", {}).get("checks", [])
    if not checks:
        st.info("No eligibility data.")
        return

    for check in checks:
        passed = check.get("passed")
        badge = "<span class='pass-badge'>PASS</span>" if passed else "<span class='fail-badge'>FAIL</span>"
        rule = check.get("rule", "").replace("_", " ").title()
        value = check.get("value")
        threshold = check.get("threshold", "")
        detail = check.get("detail")

        with st.container():
            cols = st.columns([1, 4])
            cols[0].markdown(badge, unsafe_allow_html=True)
            body = f"**{rule}** — threshold: {threshold}"
            if isinstance(value, dict):
                parts = [f"{k.replace('_', ' ')}: **{v}**" for k, v in value.items()]
                body += "  \n" + " · ".join(parts)
            elif value is not None:
                body += f"  \nValue: **{value}**"
            if detail and not passed:
                body += f"  \n_{detail}_"
            cols[1].markdown(body)


def _render_score_cards(
    ticker_data: dict,
    config: VizStrategyConfig,
    keys: tuple[str, ...],
    title: str,
) -> None:
    scores = ticker_data.get("scores") or {}
    subset = [(k, config.score_labels[k]) for k in keys if k in config.score_labels]
    if not subset:
        return

    st.markdown(f"#### {title}")
    for key, label in subset:
        comp = scores.get(key)
        if not comp:
            continue
        score = float(comp.get("score", 0))
        max_pts = comp.get("max", 0)
        pct = (score / max_pts * 100) if max_pts else 0
        help_text = config.component_help.get(key, "")
        st.markdown(
            f"""
            <div class="component-card">
              <strong>{label}</strong>
              <span style="float:right">{score:.1f} / {max_pts}</span>
              <div style="background:#e2e8f0;border-radius:4px;height:6px;margin:6px 0;">
                <div style="background:#3b82f6;width:{pct:.0f}%;
                     height:6px;border-radius:4px;"></div>
              </div>
              <small style="color:#64748b">{comp.get('meaning', '')}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if help_text:
            st.caption(help_text)
        raw = comp.get("raw", {})
        if raw:
            with st.expander(f"Raw data — {label}"):
                st.json(raw)


def render_fundamentals_panel(ticker_data: dict, config: VizStrategyConfig) -> None:
    scores = ticker_data.get("scores") or {}
    if not config.fundamental_keys:
        st.info("No fundamental score components for this strategy.")
        return
    if not any(scores.get(k) for k in config.fundamental_keys):
        st.info("Fundamental scores unavailable for this ticker.")
        return
    _render_score_cards(ticker_data, config, config.fundamental_keys, "Fundamentals")


def render_technical_panel(
    ticker_data: dict,
    ticker: str,
    config: VizStrategyConfig,
) -> None:
    scores = ticker_data.get("scores") or {}
    if not any(scores.get(k) for k in config.technical_keys):
        st.info("Technical scores unavailable for this ticker.")
        return

    technical_df = scores_to_dataframe(ticker_data, config)
    technical_df = technical_df[technical_df["key"].isin(config.technical_keys)]
    if not technical_df.empty:
        st.plotly_chart(render_score_bars(technical_df, ticker), use_container_width=True)
        st.plotly_chart(render_radar(technical_df, ticker), use_container_width=True)
    _render_score_cards(ticker_data, config, config.technical_keys, "Technical Scores")


@st.cache_data(ttl=600, show_spinner=False)
def _load_ticker_news(ticker: str, count: int) -> list[dict]:
    return fetch_ticker_news(ticker, count=count)


@st.cache_data(ttl=300, show_spinner=False)
def _load_ticker_snapshot(ticker: str) -> dict | None:
    return fetch_ticker_snapshot(ticker)


def _format_market_cap(value: float | None) -> str:
    if not value:
        return "—"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value:,.0f}"


def render_ticker_news_panel(ticker: str, *, compact: bool = False) -> None:
    st.markdown("#### Latest News & Market Update")

    snapshot = _load_ticker_snapshot(ticker)
    if snapshot:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Live Price", f"${snapshot['price']:,.2f}")
        change = snapshot.get("change_pct")
        c2.metric("Day Change", f"{change:+.2f}%" if change is not None else "—")
        c3.metric("Market Cap", _format_market_cap(snapshot.get("market_cap")))
        year_chg = snapshot.get("year_change_pct")
        c4.metric("1Y Change", f"{year_chg:+.1f}%" if year_chg is not None else "—")
        day_hi = snapshot.get("day_high")
        day_lo = snapshot.get("day_low")
        if day_hi and day_lo:
            currency = snapshot.get("currency", "USD")
            st.caption(f"Today's range: ${day_lo:,.2f} – ${day_hi:,.2f} ({currency})")
    else:
        st.caption("Live market data unavailable.")

    news = _load_ticker_news(ticker, count=3 if compact else 8)
    if not news:
        st.info("No recent news found for this ticker.")
        return

    for i, article in enumerate(news):
        title = article["title"]
        url = article.get("url")
        meta_parts = [article.get("publisher"), article.get("published")]
        meta = " · ".join(part for part in meta_parts if part)

        if url:
            st.markdown(f"**[{title}]({url})**")
        else:
            st.markdown(f"**{title}**")
        if meta:
            st.caption(meta)
        summary = article.get("summary", "")
        if summary:
            st.markdown(summary)
        if i < len(news) - 1:
            st.markdown("---")


def render_score_history(history: list[dict], ticker: str) -> go.Figure | None:
    if not history:
        return None
    df = pd.DataFrame(history)
    sort_cols = ["scan_date", "scan_time"] if "scan_time" in df.columns else ["scan_date"]
    df = df.sort_values(sort_cols)
    x_col = "scan_time" if "scan_time" in df.columns else "scan_date"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df["final_score"],
            mode="lines+markers",
            name="Final score",
            line=dict(color="#3b82f6", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df["normalized_score"],
            mode="lines+markers",
            name="Normalized",
            line=dict(color="#94a3b8", width=1, dash="dot"),
        )
    )
    fig.update_layout(
        title=f"{ticker} — Score History",
        xaxis_title="Scan date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return apply_chart_style(fig)


def render_ticker_detail(
    ticker: str,
    ticker_data: dict,
    config: VizStrategyConfig,
    *,
    compact_news: bool = False,
    show_history: bool = True,
) -> None:
    tier = ticker_data.get("tier", "filtered")
    eligible = ticker_data.get("eligible", False)
    st.markdown(
        f"## {ticker_link_html(ticker)} {tier_badge_html(tier, config)}",
        unsafe_allow_html=True,
    )
    if ticker_data.get("tier_reason"):
        st.info(ticker_data["tier_reason"])
    elif not eligible:
        fail = ticker_data.get("eligibility", {}).get("fail_reason")
        if fail:
            label = FILTER_LABELS.get(fail, fail.replace("_", " ").title())
            st.warning(f"Filtered: {label}")

    summary = ticker_data.get("summary", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Score", f"{summary.get('final_adjusted_score', 0):.1f}")
    m2.metric("Normalized", f"{summary.get('normalized_score', 0):.1f}")
    m3.metric("Raw Score", f"{summary.get('raw_score', 0):.1f}")
    m4.metric("Sector ETF", ticker_data.get("sector_etf") or "—")

    render_ticker_news_panel(ticker, compact=compact_news)

    if show_history and config.duckdb_strategy_id:
        from quant_platform.history.duckdb_store import get_ticker_history

        history = get_ticker_history(ticker, strategy_id=config.duckdb_strategy_id)
        if history:
            hist_fig = render_score_history(history, ticker)
            if hist_fig:
                st.plotly_chart(hist_fig, use_container_width=True)
            hist_cols = ["scan_date", "scan_time", "tier", "final_score", "normalized_score"]
            hist_cols = [c for c in hist_cols if c in history[0]]
            hist_df = pd.DataFrame(history)[hist_cols]
            with st.expander(f"Score history ({len(history)} scans)"):
                st.dataframe(hist_df, use_container_width=True, hide_index=True)

    tab_fund, tab_tech, tab_elig = st.tabs(["Fundamentals", "Technical", "Eligibility"])
    with tab_fund:
        render_fundamentals_panel(ticker_data, config)
    with tab_tech:
        render_technical_panel(ticker_data, ticker, config)
    with tab_elig:
        render_eligibility_panel(ticker_data)


def get_ticker_by_name(tickers: list[dict], name: str) -> dict | None:
    return next((t for t in tickers if t["ticker"] == name), None)


def filter_reason_label(code: str | None) -> str:
    if not code:
        return ""
    return FILTER_LABELS.get(code, code.replace("_", " ").title())
