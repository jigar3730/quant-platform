"""Streamlit dashboard for breakout scan reports."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from quant_platform.config import DEFAULT_OUTPUT_JSON, HISTORY_DB, HISTORY_DIR
from quant_platform.history.duckdb_store import backfill_from_archives
from quant_platform.viz.components import (
    get_ticker_by_name,
    render_compare_radar,
    render_exclusion_chart,
    render_heatmap,
    render_regime_panel,
    render_scan_header,
    render_scatter,
    render_score_histogram,
    render_ticker_detail,
    render_tier_chart,
    tier_badge_html,
)
from quant_platform.viz.data import (
    full_universe_dataframe,
    load_report,
    score_heatmap_dataframe,
    tickers_to_dataframe,
)
from quant_platform.viz.navigation import set_detail_ticker, sync_detail_ticker, ticker_link_html
from quant_platform.viz.styles import COMPONENT_HELP, CUSTOM_CSS

st.set_page_config(
    page_title="Breakout Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("Controls")

history_files = sorted(HISTORY_DIR.glob("*/breakout_scan_report.json"), reverse=True)
history_options = {str(DEFAULT_OUTPUT_JSON): "Latest (data/output)"}
for p in history_files:
    history_options[str(p)] = f"Archive {p.parent.name}"

default_path = str(DEFAULT_OUTPUT_JSON)
if default_path not in history_options:
    history_options[default_path] = "Latest (data/output)"

selected_label = st.sidebar.selectbox(
    "Scan to load",
    options=list(history_options.values()),
    index=0,
)
report_path = next(k for k, v in history_options.items() if v == selected_label)
report_path = st.sidebar.text_input("Report path", value=report_path)

st.sidebar.divider()
st.sidebar.header("Filters")
tier_filter = st.sidebar.selectbox("Tier", ["All", "Tier 1", "Tier 2", "Tier 3", "filtered"])
eligible_only = st.sidebar.checkbox("Eligible only", value=False)
actionable_only = st.sidebar.checkbox("Actionable only (Tier 1+2)", value=False)
min_score = st.sidebar.slider("Min final score", 0.0, 100.0, 0.0, 5.0)
search = st.sidebar.text_input("Search ticker", "").strip().upper()

with st.sidebar.expander("Score component guide"):
    for key, text in COMPONENT_HELP.items():
        label = key.replace("_", " ").title()
        st.markdown(f"**{label}** — {text}")

if st.sidebar.button("Sync archives to DuckDB"):
    synced = backfill_from_archives()
    st.sidebar.success(f"Synced {synced} archived scan(s).")
elif not HISTORY_DB.exists() and history_files:
    synced = backfill_from_archives()
    if synced:
        st.sidebar.caption(f"Loaded {synced} archived scan(s) into DuckDB.")

# --- Load report ---
try:
    report = load_report(report_path)
except FileNotFoundError:
    st.error(f"Report not found: `{report_path}`")
    st.info("Run `quant-scan --report both` first, or pick an archived scan from the sidebar.")
    st.stop()
except json.JSONDecodeError:
    st.error("Invalid JSON report file.")
    st.stop()

regime = report["market_regime"]
summary = report["scan_summary"]
tickers = report["tickers"]
df = tickers_to_dataframe(tickers)
all_symbols = sorted(df["ticker"].tolist())
detail_ticker = sync_detail_ticker()

st.sidebar.divider()
st.sidebar.header("Ticker Detail")
sidebar_pick = st.sidebar.selectbox(
    "Open ticker profile",
    options=[""] + all_symbols,
    index=(all_symbols.index(detail_ticker) + 1) if detail_ticker in all_symbols else 0,
    format_func=lambda x: "Select a ticker..." if x == "" else x,
)
if sidebar_pick and sidebar_pick != detail_ticker:
    set_detail_ticker(sidebar_pick)
    detail_ticker = sidebar_pick
if detail_ticker and st.sidebar.button("Clear ticker selection"):
    set_detail_ticker(None)
    detail_ticker = None

# Apply filters
filtered = df.copy()
if tier_filter != "All":
    filtered = filtered[filtered["tier"] == tier_filter]
if eligible_only:
    filtered = filtered[filtered["eligible"]]
if actionable_only:
    filtered = filtered[filtered["tier"].isin(["Tier 1", "Tier 2"])]
if min_score > 0:
    filtered = filtered[filtered["final_score"] >= min_score]
if search:
    filtered = filtered[filtered["ticker"].str.contains(search, na=False)]

render_scan_header(report_path, summary, regime)

if detail_ticker:
    link = ticker_link_html(detail_ticker)
    st.markdown(
        f'<div class="info-card">Viewing profile: <strong>{link}</strong> '
        f"— open the <em>Ticker Detail</em> tab or click any ticker link.</div>",
        unsafe_allow_html=True,
    )

tab_overview, tab_all, tab_detail, tab_watchlist, tab_compare = st.tabs(
    ["Overview", "All Tickers", "Ticker Detail", "Actionable Watchlist", "Compare"]
)

# === OVERVIEW TAB ===
with tab_overview:
    render_regime_panel(regime)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(render_tier_chart(summary["tier_counts"]), use_container_width=True)
    with c2:
        excl_fig = render_exclusion_chart(summary.get("filter_breakdown", {}))
        if excl_fig:
            st.plotly_chart(excl_fig, use_container_width=True)
        else:
            st.success("All tickers in universe were evaluated for scoring.")

    eligible_df = df[df["eligible"]]
    if not eligible_df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(render_score_histogram(eligible_df), use_container_width=True)
        with col_b:
            heat_df = score_heatmap_dataframe(tickers, eligible_only=True)
            if len(heat_df) > 1:
                st.plotly_chart(render_heatmap(heat_df), use_container_width=True)

        scatter_rows = []
        for t in tickers:
            if not t.get("eligible") or not t.get("scores"):
                continue
            scatter_rows.append(
                {
                    "ticker": t["ticker"],
                    "tier": t["tier"],
                    "compression": t["scores"]["compression"]["score"],
                    "rs_market": t["scores"]["rs_market"]["score"],
                    "final_score": t["summary"]["final_adjusted_score"],
                }
            )
        if scatter_rows:
            scatter_df = pd.DataFrame(scatter_rows)
            st.caption(
                "Ticker labels are clickable — opens fundamentals, technical scores, and news."
            )
            st.plotly_chart(render_scatter(scatter_df), use_container_width=True)
            links = " · ".join(ticker_link_html(t) for t in scatter_df["ticker"].head(20))
            st.markdown(links, unsafe_allow_html=True)

# === ALL TICKERS TAB ===
with tab_all:
    st.markdown("### Full Universe")
    st.caption(
        f"{len(tickers)} tickers with scan scores. "
        "Click a row to open its profile, or click any blue ticker link."
    )

    full_df = full_universe_dataframe(tickers)
    if tier_filter != "All":
        full_df = full_df[full_df["tier"] == tier_filter]
    if eligible_only:
        full_df = full_df[full_df["eligible"]]
    if actionable_only:
        full_df = full_df[full_df["tier"].isin(["Tier 1", "Tier 2"])]
    if min_score > 0:
        full_df = full_df[full_df["final_score"] >= min_score]
    if search:
        full_df = full_df[full_df["ticker"].str.contains(search, na=False)]

    display_cols = [
        "ticker",
        "tier",
        "eligible",
        "final_score",
        "normalized_score",
        "raw_score",
        "sector_etf",
        "RS vs Market",
        "RS vs Sector",
        "Accumulation",
        "Relative Volume",
        "Compression",
        "Pattern",
        "Resistance",
        "Revenue",
        "EPS",
        "revenue_yoy_pct",
        "eps_growth_pct",
        "filter_reason",
    ]
    table_df = full_df[[c for c in display_cols if c in full_df.columns]].copy()

    selection = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="all_tickers_select",
        column_config={
            "eligible": st.column_config.CheckboxColumn("Eligible"),
            "revenue_yoy_pct": st.column_config.NumberColumn("Rev YoY %", format="%.1f"),
            "eps_growth_pct": st.column_config.NumberColumn("EPS Gr %", format="%.1f"),
        },
    )

    if selection.selection.rows:
        picked = table_df.iloc[selection.selection.rows[0]]["ticker"]
        set_detail_ticker(picked)
        detail_ticker = picked

    link_cols = st.columns(10)
    for i, symbol in enumerate(table_df["ticker"].head(30)):
        with link_cols[i % 10]:
            st.markdown(ticker_link_html(symbol), unsafe_allow_html=True)

    st.download_button(
        "Download CSV",
        full_df.to_csv(index=False).encode(),
        file_name="breakout_scan_full.csv",
        mime="text/csv",
    )

# === TICKER DETAIL TAB ===
with tab_detail:
    st.markdown("### Ticker Profile")
    st.caption("Fundamentals, technical scores, eligibility checks, news, and score history.")

    pick_index = all_symbols.index(detail_ticker) if detail_ticker in all_symbols else 0
    active = st.selectbox(
        "Select ticker",
        all_symbols,
        index=pick_index,
        key="detail_tab_pick",
    )
    if active != detail_ticker:
        set_detail_ticker(active)
    ticker_data = get_ticker_by_name(tickers, active)
    if ticker_data:
        render_ticker_detail(active, ticker_data)
    else:
        st.warning(f"No data for {active}.")

# === ACTIONABLE WATCHLIST TAB ===
with tab_watchlist:
    st.markdown("### Tier 1 and Tier 2 — Actionable Candidates")
    actionable = df[df["tier"].isin(["Tier 1", "Tier 2"])].sort_values(
        "final_score", ascending=False
    )
    if actionable.empty:
        st.warning(
            "No actionable tickers in this scan. "
            "Try lowering thresholds or check market regime."
        )
    else:
        for _, row in actionable.iterrows():
            symbol = row["ticker"]
            t = get_ticker_by_name(tickers, symbol)
            if not t:
                continue
            with st.expander(
                f"{symbol} — {row['tier']} — Score {row['final_score']:.1f}",
                expanded=row["tier"] == "Tier 1",
            ):
                st.markdown(
                    f"Open full profile: {ticker_link_html(symbol)} {tier_badge_html(row['tier'])}",
                    unsafe_allow_html=True,
                )
                st.caption(t.get("tier_reason", ""))
                cols = st.columns(4)
                cols[0].metric("Final Score", f"{row['final_score']:.1f}")
                cols[1].metric("Normalized", f"{row['normalized_score']:.1f}")
                cols[2].metric("Sector ETF", row.get("sector_etf") or "—")
                scores = t.get("scores") or {}
                if scores:
                    top = sorted(
                        scores.items(),
                        key=lambda x: x[1].get("score", 0),
                        reverse=True,
                    )[:3]
                    top_str = ", ".join(
                        f"{k.replace('_', ' ').title()}: {v.get('score', 0):.0f}"
                        for k, v in top
                    )
                    top_display = top_str[:30] + "..." if len(top_str) > 30 else top_str
                    cols[3].metric("Top signals", top_display)
                st.caption("Click the ticker link above for fundamentals, technicals, and news.")

# === COMPARE TAB ===
with tab_compare:
    st.markdown("### Compare Tickers")
    eligible_names = (
        df[df["eligible"]]
        .sort_values("final_score", ascending=False)["ticker"]
        .tolist()
    )
    if len(eligible_names) < 2:
        st.warning("Need at least 2 eligible tickers to compare.")
    else:
        picked = st.multiselect(
            "Select 2–3 tickers",
            eligible_names,
            default=eligible_names[: min(3, len(eligible_names))],
            max_selections=3,
        )
        if len(picked) >= 2:
            compare_links = " · ".join(ticker_link_html(t) for t in picked)
            st.markdown(f"Profiles: {compare_links}", unsafe_allow_html=True)

            compare_data = [get_ticker_by_name(tickers, n) for n in picked]
            compare_data = [t for t in compare_data if t]
            fig = render_compare_radar(compare_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            compare_rows = []
            for t in compare_data:
                s = t.get("summary", {})
                row = {
                    "ticker": t["ticker"],
                    "tier": t["tier"],
                    "final_score": s.get("final_adjusted_score", 0),
                    "sector_etf": t.get("sector_etf"),
                }
                scores = t.get("scores") or {}
                for key, label in [
                    ("rs_market", "RS Mkt"),
                    ("rs_sector", "RS Sec"),
                    ("compression", "Compress"),
                    ("accumulation", "Accum"),
                    ("revenue", "Revenue"),
                    ("eps", "EPS"),
                ]:
                    row[label] = scores.get(key, {}).get("score", 0)
                compare_rows.append(row)
            compare_df = pd.DataFrame(compare_rows)
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
            st.markdown(
                " · ".join(ticker_link_html(t) for t in compare_df["ticker"]),
                unsafe_allow_html=True,
            )
