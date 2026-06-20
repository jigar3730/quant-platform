"""Unified scan report loading for the dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quant_platform.config import HISTORY_DIR
from quant_platform.filters.eligibility import FILTER_LABELS
from quant_platform.viz.strategy.registry import VizStrategyConfig


def list_report_paths(config: VizStrategyConfig) -> dict[str, str]:
    """Map path string -> sidebar label (latest first)."""
    options: dict[str, str] = {}
    default = Path(config.default_report_path)
    if default.exists():
        options[str(default)] = "Latest (data/output)"
    for path in sorted(HISTORY_DIR.glob(config.archive_glob), reverse=True):
        options[str(path)] = f"Archive {path.parent.name}"
    if str(default) not in options:
        options[str(default)] = "Latest (data/output)"
    return options


def load_scan_report(path: Path | str) -> dict:
    path = Path(path)
    with path.open() as f:
        return json.load(f)


def validate_report_strategy(report: dict, config: VizStrategyConfig) -> str | None:
    """Return warning message if report strategy_id mismatches selection."""
    report_id = report.get("strategy_id")
    if report_id and report_id != config.id:
        return (
            f"Report strategy_id is '{report_id}' but '{config.label}' "
            f"({config.id}) is selected."
        )
    return None


def report_to_dataframe(report: dict, config: VizStrategyConfig) -> pd.DataFrame:
    return tickers_to_dataframe(report.get("tickers") or [], config)


def tickers_to_dataframe(tickers: list[dict], config: VizStrategyConfig) -> pd.DataFrame:
    rows = []
    for t in tickers:
        summary = t.get("summary") or {}
        elig = t.get("eligibility") or {}
        fail_reason = elig.get("fail_reason")
        rows.append(
            {
                "ticker": t["ticker"],
                "eligible": t.get("eligible", False),
                "tier": t.get("tier", "filtered"),
                "sector_etf": t.get("sector_etf"),
                "final_score": summary.get("final_adjusted_score", 0),
                "normalized_score": summary.get("normalized_score", 0),
                "raw_score": summary.get("raw_score", 0),
                "tier_reason": t.get("tier_reason", ""),
                "filter_reason": fail_reason,
            }
        )
    return pd.DataFrame(rows)


def scores_to_dataframe(ticker: dict, config: VizStrategyConfig) -> pd.DataFrame:
    scores = ticker.get("scores") or {}
    rows = []
    for key in config.score_component_keys:
        label = config.score_labels.get(key, key.replace("_", " ").title())
        comp = scores.get(key)
        if not comp:
            continue
        rows.append(
            {
                "component": label,
                "key": key,
                "score": comp.get("score", 0),
                "max": comp.get("max", 0),
                "pct": (comp.get("score", 0) / comp["max"] * 100) if comp.get("max") else 0,
                "meaning": comp.get("meaning", ""),
            }
        )
    return pd.DataFrame(rows)


def _top_signal(scores: dict, config: VizStrategyConfig) -> str:
    if not scores:
        return ""
    best_key = ""
    best_score = -1.0
    for key, comp in scores.items():
        if not comp:
            continue
        score = float(comp.get("score", 0))
        if score > best_score:
            best_score = score
            best_key = key
    if best_score < 0 or not best_key:
        return ""
    label = config.score_labels.get(best_key, best_key)
    return f"{label} ({best_score:.0f})"


def _component_total(scores: dict, keys: tuple[str, ...]) -> float | None:
    values = []
    for key in keys:
        comp = scores.get(key)
        if comp and comp.get("score") is not None:
            values.append(float(comp["score"]))
    return round(sum(values), 1) if values else None


def full_universe_dataframe(tickers: list[dict], config: VizStrategyConfig) -> pd.DataFrame:
    rows = []
    for t in tickers:
        summary = t.get("summary") or {}
        scores = t.get("scores") or {}
        elig = t.get("eligibility") or {}
        fail_reason = elig.get("fail_reason") or ""
        row: dict = {
            "ticker": t["ticker"],
            "eligible": t.get("eligible", False),
            "tier": t.get("tier", "filtered"),
            "sector_etf": t.get("sector_etf"),
            "final_score": round(summary.get("final_adjusted_score", 0), 1),
            "normalized_score": round(summary.get("normalized_score", 0), 1),
            "raw_score": round(summary.get("raw_score", 0), 1),
            "tier_reason": t.get("tier_reason", ""),
            "top_signal": _top_signal(scores, config),
            "tech_score": _component_total(scores, config.technical_keys),
            "fund_score": _component_total(scores, config.fundamental_keys),
            "filter_reason": fail_reason,
            "filter_label": FILTER_LABELS.get(fail_reason, fail_reason) if fail_reason else "",
        }
        for key, label in config.score_labels.items():
            comp = scores.get(key)
            row[label] = round(comp.get("score", 0), 1) if comp else None
        if config.id == "breakout":
            rev_raw = scores.get("revenue", {}).get("raw", {})
            eps_raw = scores.get("eps", {}).get("raw", {})
            row["revenue_yoy_pct"] = rev_raw.get("revenue_yoy_pct")
            row["eps_growth_pct"] = eps_raw.get("eps_combined_pct")
        rows.append(row)
    return pd.DataFrame(rows).sort_values("final_score", ascending=False)


def score_heatmap_dataframe(
    tickers: list[dict],
    config: VizStrategyConfig,
    *,
    eligible_only: bool = True,
) -> pd.DataFrame:
    subset = [t for t in tickers if t.get("eligible")] if eligible_only else tickers
    rows = []
    for t in subset:
        scores = t.get("scores") or {}
        row = {"ticker": t["ticker"]}
        for key, label in config.score_labels.items():
            comp = scores.get(key, {})
            row[label] = comp.get("score", 0)
        rows.append(row)
    return pd.DataFrame(rows)
