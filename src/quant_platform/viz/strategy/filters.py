"""Strategy-aware dashboard filters."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant_platform.viz.strategy.registry import VizStrategyConfig


@dataclass(frozen=True)
class ScanFilters:
    tier: str = "All"
    eligible_only: bool = False
    actionable_only: bool = False
    min_score: float = 0.0
    search: str = ""


def tier_filter_options(config: VizStrategyConfig) -> list[str]:
    return ["All", *config.tiers, "filtered"]


def apply_filters(
    df: pd.DataFrame,
    filters: ScanFilters,
    config: VizStrategyConfig,
) -> pd.DataFrame:
    result = df.copy()
    if filters.tier != "All":
        result = result[result["tier"] == filters.tier]
    if filters.eligible_only:
        result = result[result["eligible"]]
    if filters.actionable_only:
        result = result[result["tier"].isin(config.actionable_tiers)]
    if filters.min_score > 0:
        result = result[result["final_score"] >= filters.min_score]
    if filters.search:
        result = result[result["ticker"].str.contains(filters.search, na=False)]
    return result


def scatter_dataframe(tickers: list[dict], config: VizStrategyConfig) -> pd.DataFrame:
    x_key, y_key = config.scatter_defaults
    if not x_key or not y_key:
        return pd.DataFrame()

    rows = []
    for ticker in tickers:
        scores = ticker.get("scores") or {}
        summary = ticker.get("summary") or {}
        if x_key not in scores or y_key not in scores:
            continue
        rows.append(
            {
                "ticker": ticker["ticker"],
                "tier": ticker.get("tier", "filtered"),
                "eligible": ticker.get("eligible", False),
                x_key: scores[x_key]["score"],
                y_key: scores[y_key]["score"],
                "final_score": summary.get("final_adjusted_score", 0),
            }
        )
    return pd.DataFrame(rows)
