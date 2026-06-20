from __future__ import annotations

from quant_platform.engine.protocols import StrategySpec

STRATEGY_IDS = ("breakout", "swing", "lynch", "fake")


def get_strategy(strategy_id: str) -> StrategySpec:
    if strategy_id == "fake":
        from quant_platform.strategies.fake.spec import FAKE_STRATEGY

        return FAKE_STRATEGY
    if strategy_id == "breakout":
        from quant_platform.strategies.breakout.spec import BREAKOUT_STRATEGY

        return BREAKOUT_STRATEGY
    if strategy_id == "swing":
        from quant_platform.strategies.swing.spec import SWING_STRATEGY

        return SWING_STRATEGY
    if strategy_id == "lynch":
        from quant_platform.strategies.lynch.spec import LYNCH_STRATEGY

        return LYNCH_STRATEGY
    raise ValueError(f"Unknown strategy: {strategy_id}")
