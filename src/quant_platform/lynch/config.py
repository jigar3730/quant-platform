"""Peter Lynch scanner thresholds and presets."""

from __future__ import annotations

from dataclasses import dataclass

# Part 1 — base quantitative screen
PEG_MAX = 1.0
PEG_BARGAIN = 0.5
EPS_GROWTH_MIN = 0.15
EPS_GROWTH_MAX = 0.30
PE_MAX = 20.0
DEBT_TO_EQUITY_MAX = 0.35
INSTITUTIONAL_OWNERSHIP_MAX = 0.50
ANALYST_COVERAGE_MAX = 5
ROE_MIN_ANTI = 0.10  # proxy when ROIC unavailable
REVENUE_CV_MAX = 0.60  # anti-filter: highly volatile revenue

# Preset A — Fast Growers
FAST_GROWER_MCAP_MAX = 5_000_000_000
FAST_GROWER_EPS_GROWTH_MIN = 0.20
FAST_GROWER_PEG_MAX = 1.0
FAST_GROWER_DE_MAX = 0.25

# Preset B — Stalwarts
STALWART_MCAP_MIN = 10_000_000_000
STALWART_PE_MAX = 15.0
STALWART_EPS_GROWTH_MIN = 0.10
STALWART_EPS_GROWTH_MAX = 0.15
STALWART_DIVIDEND_YIELD_MIN = 0.015

# Preset C — Asset Plays
ASSET_PLAY_PB_MAX = 1.0
ASSET_PLAY_NET_CASH_PRICE_MIN = 0.30

PRESETS = ("base", "fast_grower", "stalwart", "asset_play", "summary")


@dataclass(frozen=True)
class LynchPreset:
    name: str
    label: str


PRESET_LABELS = {
    "base": "Lynch Base Screen",
    "fast_grower": "Fast Growers (10-Bagger Hunt)",
    "stalwart": "Stalwarts (Portfolio Anchors)",
    "asset_play": "Asset Plays (Deep Value)",
    "summary": "Full Lynch Scan (all categories)",
}
