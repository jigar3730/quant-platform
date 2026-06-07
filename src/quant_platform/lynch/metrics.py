"""Fetch Peter Lynch screening metrics from yfinance."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf

from quant_platform.config import LYNCH_FETCH_WORKERS
from quant_platform.data.fundamentals_helpers import cagr, quarterly_series
from quant_platform.data.quality import sanitize_growth_rate

logger = logging.getLogger(__name__)


def normalize_debt_to_equity(value: float | None) -> float | None:
    """yfinance often reports D/E as a percentage (e.g. 35 = 35%)."""
    if value is None or pd.isna(value):
        return None
    ratio = float(value)
    if ratio > 1.0:
        ratio /= 100.0
    return ratio


def compute_peg(pe: float | None, growth: float | None) -> float | None:
    """PEG = P/E divided by earnings growth percent (e.g. 15 for 15%)."""
    if pe is None or growth is None or pd.isna(pe) or pd.isna(growth):
        return None
    growth_pct = float(growth) * 100 if abs(float(growth)) <= 1.5 else float(growth)
    if growth_pct <= 0:
        return None
    return float(pe) / growth_pct


def _insider_purchases_6m(ticker: yf.Ticker) -> float | None:
    try:
        df = ticker.insider_purchases
        if df is None or df.empty:
            return None
        purchases = df.loc[df["Insider Purchases Last 6m"] == "Purchases", "Shares"]
        if purchases.empty:
            return None
        return float(purchases.iloc[0])
    except Exception:
        return None


def _shares_outstanding_change_yoy(ticker: yf.Ticker) -> float | None:
    try:
        start = (datetime.now(tz=UTC) - timedelta(days=400)).strftime("%Y-%m-%d")
        series = ticker.get_shares_full(start=start)
        if series is None or len(series) < 2:
            return None
        first = float(series.iloc[0])
        last = float(series.iloc[-1])
        if first <= 0:
            return None
        return (last - first) / first
    except Exception:
        return None


def _revenue_coefficient_of_variation(ticker: yf.Ticker) -> float | None:
    try:
        income = ticker.quarterly_income_stmt
        revenue = quarterly_series(income, "Total Revenue")
        if revenue.empty:
            revenue = quarterly_series(income, "Revenue")
        if len(revenue) < 4:
            return None
        recent = revenue.head(8).astype(float)
        mean = recent.mean()
        if mean <= 0:
            return None
        return float(recent.std() / mean)
    except Exception:
        return None


def _eps_growth_5y(ticker: yf.Ticker, info: dict) -> float | None:
    try:
        income = ticker.quarterly_income_stmt
        eps = quarterly_series(income, "Diluted EPS")
        if eps.empty:
            eps = quarterly_series(income, "Basic EPS")
        eps_cagr = sanitize_growth_rate(cagr(eps, years=5.0))
        if eps_cagr is not None:
            return eps_cagr
    except Exception:
        pass
    growth = info.get("earningsGrowth")
    if growth is not None and not pd.isna(growth):
        return sanitize_growth_rate(float(growth))
    return None


def fetch_lynch_metrics(ticker: str) -> dict:
    """Return normalized Lynch metrics for one ticker."""
    try:
        yt = yf.Ticker(ticker)
        info = yt.info or {}
    except Exception:
        logger.warning("Could not fetch Lynch metrics for %s", ticker)
        return {"ticker": ticker, "error": "fetch_failed"}

    pe = info.get("trailingPE") or info.get("forwardPE")
    eps_growth = _eps_growth_5y(yt, info)
    peg = info.get("pegRatio")
    if peg is None or pd.isna(peg):
        peg = compute_peg(pe, eps_growth)
    else:
        peg = float(peg)

    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    net_cash = None
    if total_cash is not None and total_debt is not None:
        net_cash = float(total_cash) - float(total_debt)

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    shares = info.get("sharesOutstanding")
    net_cash_per_share = None
    net_cash_price_ratio = None
    if net_cash is not None and shares and float(shares) > 0 and price:
        net_cash_per_share = net_cash / float(shares)
        net_cash_price_ratio = net_cash_per_share / float(price)

    de = normalize_debt_to_equity(info.get("debtToEquity"))
    inst = info.get("heldPercentInstitutions")
    analysts = info.get("numberOfAnalystOpinions")
    insider_purchases = _insider_purchases_6m(yt)
    shares_change = _shares_outstanding_change_yoy(yt)
    revenue_cv = _revenue_coefficient_of_variation(yt)
    roe = info.get("returnOnEquity")

    return {
        "ticker": ticker,
        "company_name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "price": price,
        "pe_ratio": float(pe) if pe is not None and not pd.isna(pe) else None,
        "peg_ratio": float(peg) if peg is not None and not pd.isna(peg) else None,
        "eps_growth_5y": eps_growth,
        "debt_to_equity": de,
        "total_cash": total_cash,
        "total_debt": total_debt,
        "net_cash": net_cash,
        "net_cash_per_share": net_cash_per_share,
        "net_cash_price_ratio": net_cash_price_ratio,
        "institutional_ownership": float(inst) if inst is not None else None,
        "analyst_count": int(analysts) if analysts is not None else None,
        "insider_purchases_6m": insider_purchases,
        "shares_outstanding_change_yoy": shares_change,
        "dividend_yield": info.get("dividendYield"),
        "price_to_book": info.get("priceToBook"),
        "trailing_eps": info.get("trailingEps"),
        "return_on_equity": float(roe) if roe is not None and not pd.isna(roe) else None,
        "revenue_cv": revenue_cv,
        "revenue_growth": info.get("revenueGrowth"),
    }


def fetch_lynch_metrics_batch(
    tickers: list[str],
    *,
    max_workers: int = LYNCH_FETCH_WORKERS,
) -> list[dict]:
    if not tickers:
        return []
    if len(tickers) == 1:
        return [fetch_lynch_metrics(tickers[0])]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    workers = min(max_workers, len(tickers))
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_lynch_metrics, symbol): symbol for symbol in tickers}
        for future in as_completed(futures):
            symbol = futures[future]
            results[symbol] = future.result()
    return [results[symbol] for symbol in tickers]
