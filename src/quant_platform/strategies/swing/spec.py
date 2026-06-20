from __future__ import annotations

from dataclasses import dataclass

from quant_platform.engine.protocols import FactorBinding, StrategySpec
from quant_platform.factors.swing import (
    PullbackQualityFactor,
    PullbackVolumeFactor,
    SwingRelativeStrengthFactor,
    WeeklyTrendFactor,
)
from quant_platform.regime.market import MarketRegime
from quant_platform.strategies.swing.aggregate import (
    SWING_MAX_RAW_SCORE,
    SWING_SCORE_COLUMNS,
    OverextendedPenalty,
    RsiClimaxPenalty,
    aggregate_swing_ticker,
    assign_swing_tier,
)
from quant_platform.strategies.swing.filters import SwingEligibilityFilter


@dataclass
class SwingStrategySpec(StrategySpec):
    def aggregate(self, ticker, regime: MarketRegime):
        return aggregate_swing_ticker(ticker, regime)

    def assign_tier(self, ticker) -> str:
        return assign_swing_tier(ticker)


SWING_STRATEGY = SwingStrategySpec(
    id="swing",
    name="Swing Pullback Scanner",
    max_raw_score=SWING_MAX_RAW_SCORE,
    filters=[SwingEligibilityFilter()],
    factor_bindings=[
        FactorBinding(WeeklyTrendFactor()),
        FactorBinding(SwingRelativeStrengthFactor()),
        FactorBinding(PullbackQualityFactor()),
        FactorBinding(PullbackVolumeFactor()),
    ],
    regime_mode="multiplier",
    penalties=[OverextendedPenalty(), RsiClimaxPenalty()],
    sort_keys=["final_adjusted_score", "relative_strength_score", "pullback_score"],
    score_columns=SWING_SCORE_COLUMNS,
)
