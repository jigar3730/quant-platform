from __future__ import annotations

from dataclasses import dataclass

from quant_platform.engine.context import ScanContext
from quant_platform.factors.base import make_factor_result
from quant_platform.scoring.fundamentals import score_eps, score_revenue


@dataclass
class RevenueFactor:
    name: str = "revenue"
    pass_kind: str = "ticker"

    def compute(self, ctx: ScanContext, ticker: str):
        fund = ctx.fundamentals(ticker)
        score = score_revenue(fund.get("revenue_yoy"))
        return make_factor_result(self.name, score, 15.0)


@dataclass
class EpsFactor:
    name: str = "eps"
    pass_kind: str = "ticker"

    def compute(self, ctx: ScanContext, ticker: str):
        fund = ctx.fundamentals(ticker)
        score = score_eps(fund.get("eps_combined"))
        return make_factor_result(self.name, score, 15.0)
