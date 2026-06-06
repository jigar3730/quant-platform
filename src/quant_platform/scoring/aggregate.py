from pathlib import Path

import pandas as pd

from quant_platform.config import RAW_SCORE_MAX
from quant_platform.regime.market import MarketRegime


def assign_tier(row: pd.Series) -> str:
    if not row.get("eligible", False):
        return "filtered"

    normalized = row["normalized_score"]
    final = row["final_adjusted_score"]
    compression = row["compression_score"]
    accumulation = row["accumulation_score"]
    rel_vol = row["relative_volume_score"]

    tier1 = (
        normalized >= 80
        and final >= 70
        and compression >= 8
        and (accumulation >= 8 or rel_vol >= 5)
    )
    if tier1:
        return "Tier 1"

    if normalized >= 65:
        return "Tier 2"
    if normalized >= 80:
        return "Tier 2"
    return "Tier 3"


def build_results_table(
    rows: list[dict],
    regime: MarketRegime,
) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    score_cols = [
        "rs_market_score",
        "rs_sector_score",
        "accumulation_score",
        "relative_volume_score",
        "compression_score",
        "pattern_score",
        "resistance_score",
        "revenue_score",
        "eps_score",
    ]

    for col in score_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    df["raw_score"] = df[score_cols].sum(axis=1)
    df["normalized_score"] = (df["raw_score"] / RAW_SCORE_MAX) * 100
    df["regime_multiplier"] = regime.multiplier
    df["final_adjusted_score"] = df["normalized_score"] * regime.multiplier
    df["tier"] = df.apply(assign_tier, axis=1)

    eligible = df[df["eligible"]].copy()
    filtered = df[~df["eligible"]].copy()

    eligible = eligible.sort_values(
        by=["final_adjusted_score", "rs_market_score", "accumulation_score"],
        ascending=[False, False, False],
    )
    filtered = filtered.sort_values(by="ticker")

    return pd.concat([eligible, filtered], ignore_index=True)


def export_results(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
