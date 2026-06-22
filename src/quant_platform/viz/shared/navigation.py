"""Ticker deep-link navigation via query params and session state."""

from __future__ import annotations

import streamlit as st

DETAIL_TICKER_KEY = "detail_ticker"
VIEW_KEY = "app_view"


def ticker_link_html(ticker: str) -> str:
    return (
        f'<a class="ticker-link" href="?ticker={ticker}" '
        f'target="_self">{ticker}</a>'
    )


def sync_detail_ticker() -> str | None:
    if DETAIL_TICKER_KEY not in st.session_state:
        st.session_state[DETAIL_TICKER_KEY] = None

    query_ticker = st.query_params.get("ticker")
    if query_ticker:
        st.session_state[DETAIL_TICKER_KEY] = query_ticker.strip().upper()

    return st.session_state.get(DETAIL_TICKER_KEY)


def set_detail_ticker(ticker: str | None) -> None:
    if ticker:
        symbol = ticker.strip().upper()
        st.session_state[DETAIL_TICKER_KEY] = symbol
        st.query_params["ticker"] = symbol
        if "view" in st.query_params:
            del st.query_params["view"]
    else:
        st.session_state[DETAIL_TICKER_KEY] = None
        if "ticker" in st.query_params:
            del st.query_params["ticker"]


def set_view(view: str) -> None:
    if view == "compare":
        st.query_params["view"] = "compare"
        set_detail_ticker(None)
    elif view == "universe":
        if "view" in st.query_params:
            del st.query_params["view"]
        set_detail_ticker(None)
    else:
        st.query_params["view"] = view


def resolve_view() -> str:
    sync_detail_ticker()
    if st.query_params.get("view") == "compare":
        return "compare"
    if st.session_state.get(DETAIL_TICKER_KEY) or st.query_params.get("ticker"):
        return "company"
    return "universe"


def render_breadcrumb(*, scan_date: str, on_universe: bool = False) -> None:
    if on_universe:
        st.markdown(
            f'<div class="breadcrumb">Universe · Scan {_escape(scan_date)}</div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f'<div class="breadcrumb">'
        f'<a href="?" target="_self">← Back to Universe</a>'
        f" · Scan {_escape(scan_date)}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _escape(text: str) -> str:
    import html

    return html.escape(str(text))
