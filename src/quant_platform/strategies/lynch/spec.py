"""Peter Lynch strategy registration for the engine registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from quant_platform.engine.protocols import StrategySpec
from quant_platform.lynch import config as lynch_cfg


@dataclass(frozen=True)
class LynchStrategySpec(StrategySpec):
    """Config holder; Lynch uses FundamentalStrategyRunner, not price-based engine."""

    preset: str = field(default="summary", kw_only=True)
    filters: list = field(default_factory=list, kw_only=True)
    factor_bindings: list = field(default_factory=list, kw_only=True)
    penalties: list = field(default_factory=list, kw_only=True)

    def aggregate(self, ticker, regime):
        raise NotImplementedError("Lynch uses FundamentalStrategyRunner")

    def assign_tier(self, ticker) -> str:
        raise NotImplementedError("Lynch uses FundamentalStrategyRunner")


def lynch_strategy(preset: str = "summary") -> LynchStrategySpec:
    if preset not in lynch_cfg.PRESETS:
        raise ValueError(f"Unknown preset: {preset}")
    return LynchStrategySpec(
        id="lynch",
        name="Peter Lynch Scanner",
        max_raw_score=100.0,
        regime_mode="none",
        preset=preset,
    )


LYNCH_STRATEGY = lynch_strategy()
