"""Dashboard strategy registry — UI config aligned with engine StrategySpec."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from quant_platform.config import (
    DEFAULT_LYNCH_JSON,
    DEFAULT_SWING_JSON,
    DEFAULT_OUTPUT_JSON,
)
from quant_platform.strategies.registry import get_strategy

PageSet = Literal["price", "lynch"]


@dataclass(frozen=True)
class VizStrategyConfig:
    id: str
    label: str
    page_set: PageSet
    default_report_path: str
    archive_glob: str
    tiers: tuple[str, ...]
    actionable_tiers: tuple[str, ...]
    score_columns: tuple[str, ...]
    score_component_keys: tuple[str, ...]
    score_labels: dict[str, str]
    fundamental_keys: tuple[str, ...]
    technical_keys: tuple[str, ...]
    scatter_defaults: tuple[str, str]
    duckdb_strategy_id: str | None
    cli_hint: str
    tier_colors: dict[str, str] = field(default_factory=dict)
    component_help: dict[str, str] = field(default_factory=dict)


_BREAKOUT_TIER_COLORS = {
    "Tier 1": "#22c55e",
    "Tier 2": "#eab308",
    "Tier 3": "#94a3b8",
    "filtered": "#ef4444",
}

_SWING_TIER_COLORS = {
    "A": "#22c55e",
    "B": "#eab308",
    "C": "#94a3b8",
    "filtered": "#ef4444",
}

_BREAKOUT_LABELS = {
    "rs_market": "RS vs Market",
    "rs_sector": "RS vs Sector",
    "accumulation": "Accumulation",
    "relative_volume": "Relative Volume",
    "compression": "Compression",
    "pattern": "Pattern",
    "resistance": "Resistance",
    "revenue": "Revenue",
    "eps": "EPS",
}

_SWING_LABELS = {
    "trend": "Weekly Trend",
    "relative_strength": "Relative Strength",
    "pullback": "Pullback Quality",
    "volume": "Pullback Volume",
}

_BREAKOUT_HELP = {
    "rs_market": "Relative strength vs SPY over 63d and 126d. Higher = outperforming the market.",
    "rs_sector": "Relative strength vs sector ETF peers. Ranked within sector group.",
    "accumulation": "Up-day volume divided by down-day volume (20d). Above 1 = buying pressure.",
    "relative_volume": "Today's or 3-day avg volume vs 20-day average. Surges signal demand.",
    "compression": (
        "Bollinger Band width percentile (120d). Low = volatility squeeze before breakout."
    ),
    "pattern": "Five-point base quality checklist near 52-week highs.",
    "resistance": "Distance to 50/65-day high resistance. Closer = nearer breakout.",
    "revenue": "Year-over-year quarterly revenue growth.",
    "eps": "Blended recent EPS growth and 3-year CAGR.",
}

_SWING_HELP = {
    "trend": "Weekly EMA trend alignment (20 vs 50) and price above support.",
    "relative_strength": "Relative strength vs SPY over recent windows.",
    "pullback": "Pullback depth, structure, and proximity to moving averages.",
    "volume": "Volume behavior during the pullback vs rally legs.",
}


def _breakout_config() -> VizStrategyConfig:
    spec = get_strategy("breakout")
    keys = tuple(k.replace("_score", "") for k in spec.score_columns)
    return VizStrategyConfig(
        id="breakout",
        label="Breakout",
        page_set="price",
        default_report_path=str(DEFAULT_OUTPUT_JSON),
        archive_glob="*/breakout_scan_report.json",
        tiers=("Tier 1", "Tier 2", "Tier 3"),
        actionable_tiers=("Tier 1", "Tier 2"),
        score_columns=tuple(spec.score_columns),
        score_component_keys=keys,
        score_labels=_BREAKOUT_LABELS,
        fundamental_keys=("revenue", "eps"),
        technical_keys=tuple(k for k in keys if k not in ("revenue", "eps")),
        scatter_defaults=("compression", "rs_market"),
        duckdb_strategy_id="breakout",
        cli_hint="Run `quant-scan --report both --archive`, then reload the dashboard.",
        tier_colors=_BREAKOUT_TIER_COLORS,
        component_help=_BREAKOUT_HELP,
    )


def _swing_config() -> VizStrategyConfig:
    spec = get_strategy("swing")
    keys = tuple(k.replace("_score", "") for k in spec.score_columns)
    return VizStrategyConfig(
        id="swing",
        label="Swing Pullback",
        page_set="price",
        default_report_path=str(DEFAULT_SWING_JSON),
        archive_glob="*/swing_scan_report.json",
        tiers=("A", "B", "C"),
        actionable_tiers=("A", "B"),
        score_columns=tuple(spec.score_columns),
        score_component_keys=keys,
        score_labels=_SWING_LABELS,
        fundamental_keys=(),
        technical_keys=keys,
        scatter_defaults=("pullback", "relative_strength"),
        duckdb_strategy_id="swing",
        cli_hint="Run `quant-swing --report both --archive`, then reload the dashboard.",
        tier_colors=_SWING_TIER_COLORS,
        component_help=_SWING_HELP,
    )


def _lynch_config() -> VizStrategyConfig:
    return VizStrategyConfig(
        id="lynch",
        label="Peter Lynch",
        page_set="lynch",
        default_report_path=str(DEFAULT_LYNCH_JSON),
        archive_glob="*/lynch_scan_report.json",
        tiers=(),
        actionable_tiers=(),
        score_columns=(),
        score_component_keys=(),
        score_labels={},
        fundamental_keys=(),
        technical_keys=(),
        scatter_defaults=("", ""),
        duckdb_strategy_id=None,
        cli_hint="Run `quant-lynch --report both --archive`, then reload the dashboard.",
    )


_CONFIGS: dict[str, VizStrategyConfig] = {
    "breakout": _breakout_config(),
    "swing": _swing_config(),
    "lynch": _lynch_config(),
}


def get_viz_strategy(strategy_id: str) -> VizStrategyConfig:
    if strategy_id not in _CONFIGS:
        raise ValueError(f"Unknown viz strategy: {strategy_id}")
    return _CONFIGS[strategy_id]


def list_viz_strategies() -> list[VizStrategyConfig]:
    return [_CONFIGS["breakout"], _CONFIGS["swing"], _CONFIGS["lynch"]]
