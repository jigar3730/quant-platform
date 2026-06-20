"""Minimal fake strategy for engine unit tests."""

from __future__ import annotations

from dataclasses import dataclass

from quant_platform.engine.protocols import FactorBinding, StrategySpec
from quant_platform.engine.types import FactorResult, FilterResult, TickerResult
from quant_platform.regime.market import MarketRegime

from quant_platform.engine.context import ScanContext


@dataclass
class AlwaysPassFilter:
    name: str = "always_pass"

    def evaluate(self, ctx: ScanContext, ticker: str) -> FilterResult:
        return FilterResult(passed=True, reason="eligible", checks=[])


@dataclass
class FakeUniverseFactor:
    name: str = "fake_universe"
    pass_kind: str = "universe"

    def compute_universe(
        self,
        ctx: ScanContext,
        tickers: list[str],
    ) -> dict[str, FactorResult]:
        return {
            t: FactorResult(
                name=self.name,
                score=float(i + 1) * 5,
                max_score=10.0,
                details={"rank": i},
            )
            for i, t in enumerate(tickers)
        }


@dataclass
class FakeTickerFactor:
    name: str = "fake_ticker"
    pass_kind: str = "ticker"

    def compute(self, ctx: ScanContext, ticker: str) -> FactorResult:
        df = ctx.stock_df(ticker)
        price = float(df["Close"].iloc[-1]) if df is not None else 0.0
        return FactorResult(
            name=self.name,
            score=min(price / 10.0, 10.0),
            max_score=10.0,
            details={"price": price},
        )


@dataclass
class FakeStrategySpec(StrategySpec):
    def aggregate(self, ticker: TickerResult, regime: MarketRegime) -> TickerResult:
        raw = sum(fr.score for fr in ticker.factors.values())
        penalty = sum(ticker.penalties.values())
        raw = max(0.0, raw + penalty)
        ticker.raw_score = raw
        ticker.normalized_score = (raw / self.max_raw_score) * 100
        ticker.regime_multiplier = regime.multiplier
        if self.regime_mode == "multiplier":
            ticker.final_score = ticker.normalized_score * regime.multiplier
        else:
            ticker.final_score = ticker.normalized_score
        return ticker

    def assign_tier(self, ticker: TickerResult) -> str:
        if not ticker.eligible:
            return "filtered"
        if ticker.normalized_score >= 80:
            return "Tier 1"
        if ticker.normalized_score >= 50:
            return "Tier 2"
        return "Tier 3"


FAKE_STRATEGY = FakeStrategySpec(
    id="fake",
    name="Fake Test Strategy",
    max_raw_score=20.0,
    filters=[AlwaysPassFilter()],
    factor_bindings=[
        FactorBinding(FakeUniverseFactor()),
        FactorBinding(FakeTickerFactor()),
    ],
    regime_mode="multiplier",
    sort_keys=["final_score"],
)
