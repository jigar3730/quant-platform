from __future__ import annotations

from dataclasses import dataclass

from quant_platform.engine.context import ScanContext
from quant_platform.engine.types import TickerResult
from quant_platform.indicators import ema
from quant_platform.regime.market import MarketRegime

SWING_MAX_RAW_SCORE = 60.0

SWING_SCORE_COLUMNS = [
    "trend_score",
    "relative_strength_score",
    "pullback_score",
    "volume_score",
]


def aggregate_swing_ticker(ticker: TickerResult, regime: MarketRegime) -> TickerResult:
    raw = sum(fr.score for fr in ticker.factors.values())
    penalty = sum(ticker.penalties.values())
    raw = max(0.0, raw + penalty)
    ticker.raw_score = raw
    ticker.normalized_score = (raw / SWING_MAX_RAW_SCORE) * 100
    ticker.regime_multiplier = regime.multiplier
    ticker.final_score = ticker.normalized_score * regime.multiplier
    return ticker


def assign_swing_tier(ticker: TickerResult) -> str:
    if not ticker.eligible:
        return "filtered"
    if ticker.final_score >= 80:
        return "A"
    if ticker.final_score >= 65:
        return "B"
    return "C"


@dataclass
class OverextendedPenalty:
    name: str = "overextended"

    def apply(self, ctx: ScanContext, ticker: TickerResult) -> float:
        df = ctx.stock_df(ticker.ticker)
        if df is None:
            return 0.0
        close = df["Close"]
        ema50 = float(ema(close, 50).iloc[-1])
        price = float(close.iloc[-1])
        if ema50 <= 0:
            return 0.0
        pct_above = (price - ema50) / ema50
        if pct_above >= 0.15:
            return -20.0
        if pct_above >= 0.10:
            return -10.0
        return 0.0


@dataclass
class RsiClimaxPenalty:
    name: str = "rsi_climax"

    def apply(self, ctx: ScanContext, ticker: TickerResult) -> float:
        from quant_platform.indicators import rsi

        df = ctx.stock_df(ticker.ticker)
        if df is None:
            return 0.0
        rsi_val = float(rsi(df["Close"], 14).iloc[-1])
        if rsi_val > 70:
            return -10.0
        return 0.0
