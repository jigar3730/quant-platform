from quant_platform.filters.eligibility import FILTER_LABELS, eligibility_detail
from quant_platform.report.diagnostics import score_components_detail


def explain_tier(row: dict) -> str:
    if not row.get("eligible"):
        reason = row.get("filter_reason", "unknown")
        return FILTER_LABELS.get(reason, reason)

    tier = row.get("tier", "")
    normalized = row.get("normalized_score", 0)
    final = row.get("final_adjusted_score", 0)
    compression = row.get("compression_score", 0)
    accumulation = row.get("accumulation_score", 0)
    rel_vol = row.get("relative_volume_score", 0)

    if tier == "Tier 1":
        return (
            f"Breakout ready: score {normalized:.1f} (>=80), adjusted {final:.1f} (>=70), "
            f"compression {compression:.1f} (>=8), volume signal met"
        )

    if tier == "Tier 2":
        if normalized >= 80:
            missing = []
            if final < 70:
                missing.append(f"adjusted score {final:.1f} < 70")
            if compression < 8:
                missing.append(f"compression {compression:.1f} < 8")
            if accumulation < 8 and rel_vol < 5:
                missing.append("accumulation and relative volume below Tier 1 thresholds")
            joined = "; ".join(missing)
            return f"High score ({normalized:.1f}) but missing Tier 1 criteria: {joined}"
        return f"Watchlist candidate: normalized score {normalized:.1f} (65-79 range)"

    return f"Below watchlist threshold: normalized score {normalized:.1f} (<65)"


def build_ticker_report(
    *,
    ticker: str,
    row: dict,
    stock_df,
    spy_df,
    sector_df,
    sector_etf: str | None,
    fund: dict,
    scores: dict | None,
) -> dict:
    if stock_df is None or stock_df.empty:
        eligibility = {
            "passed": False,
            "fail_reason": "no_price_data",
            "checks": [],
            "summary": FILTER_LABELS["no_price_data"],
        }
        return {
            "ticker": ticker,
            "verdict": "excluded",
            "eligible": False,
            "tier": "filtered",
            "tier_reason": FILTER_LABELS["no_price_data"],
            "eligibility": eligibility,
            "scores": None,
            "summary": {
                "raw_score": 0,
                "normalized_score": 0,
                "final_adjusted_score": 0,
            },
        }

    elig = eligibility_detail(stock_df)
    elig["summary"] = (
        "Passed all eligibility filters"
        if elig["passed"]
        else FILTER_LABELS.get(elig["fail_reason"], elig["fail_reason"])
    )

    if not elig["passed"]:
        return {
            "ticker": ticker,
            "verdict": "excluded",
            "eligible": False,
            "tier": "filtered",
            "tier_reason": elig["summary"],
            "eligibility": elig,
            "scores": None,
            "summary": {
                "raw_score": 0,
                "normalized_score": 0,
                "final_adjusted_score": 0,
            },
        }

    score_detail = score_components_detail(
        stock_df=stock_df,
        spy_df=spy_df,
        sector_df=sector_df,
        sector_etf=sector_etf,
        fund=fund,
        scores=scores or {},
    )

    return {
        "ticker": ticker,
        "verdict": "eligible",
        "eligible": True,
        "tier": row.get("tier"),
        "tier_reason": explain_tier(row),
        "sector_etf": sector_etf,
        "eligibility": elig,
        "scores": score_detail,
        "summary": {
            "raw_score": row.get("raw_score"),
            "normalized_score": round(row.get("normalized_score", 0), 2),
            "regime_multiplier": row.get("regime_multiplier"),
            "final_adjusted_score": round(row.get("final_adjusted_score", 0), 2),
        },
    }


def build_scan_report(
    *,
    results_df,
    universe: list[str],
    stock_dfs: dict,
    spy_df,
    sector_dfs: dict,
    sector_etfs: dict,
    fund_map: dict,
    regime_detail: dict,
    scores_by_ticker: dict,
) -> dict:
    tickers_report = []
    for ticker in universe:
        row = results_df[results_df["ticker"] == ticker].iloc[0].to_dict()
        sector_etf = sector_etfs.get(ticker)
        sector_df = sector_dfs.get(sector_etf)
        tickers_report.append(
            build_ticker_report(
                ticker=ticker,
                row=row,
                stock_df=stock_dfs.get(ticker),
                spy_df=spy_df,
                sector_df=sector_df,
                sector_etf=sector_etf,
                fund=fund_map.get(ticker, {}),
                scores=scores_by_ticker.get(ticker),
            )
        )

    eligible = [t for t in tickers_report if t["eligible"]]
    excluded = [t for t in tickers_report if not t["eligible"]]

    filter_counts: dict[str, int] = {}
    for t in excluded:
        reason = t["eligibility"].get("fail_reason", "unknown")
        filter_counts[reason] = filter_counts.get(reason, 0) + 1

    return {
        "scan_summary": {
            "universe_size": len(universe),
            "eligible_count": len(eligible),
            "excluded_count": len(excluded),
            "tier_counts": {
                "Tier 1": int((results_df["tier"] == "Tier 1").sum()),
                "Tier 2": int((results_df["tier"] == "Tier 2").sum()),
                "Tier 3": int((results_df["tier"] == "Tier 3").sum()),
                "filtered": int((results_df["tier"] == "filtered").sum()),
            },
            "filter_breakdown": filter_counts,
        },
        "market_regime": regime_detail,
        "tickers": tickers_report,
    }
