from __future__ import annotations

from dataclasses import dataclass

from quant_platform.config import MIN_AVG_VOLUME, MIN_PRICE
from quant_platform.data.quality import has_price_spike
from quant_platform.engine.context import ScanContext
from quant_platform.engine.types import FilterResult
from quant_platform.indicators import ema, resample_weekly


@dataclass
class SwingEligibilityFilter:
    name: str = "swing_eligibility"

    def evaluate(self, ctx: ScanContext, ticker: str) -> FilterResult:
        df = ctx.stock_df(ticker)
        if df is None or df.empty:
            return FilterResult(passed=False, reason="no_price_data", checks=[])

        checks: list[dict] = []
        close = df["Close"]
        price = float(close.iloc[-1])

        if price < MIN_PRICE:
            return FilterResult(
                passed=False,
                reason="price_below_minimum",
                checks=[{"rule": "price", "passed": False, "value": price}],
            )

        if has_price_spike(df):
            return FilterResult(
                passed=False,
                reason="price_data_anomaly",
                checks=[{"rule": "price_stability", "passed": False}],
            )

        avg_vol = float(df["Volume"].tail(20).mean())
        checks.append({"rule": "liquidity", "passed": avg_vol >= MIN_AVG_VOLUME, "value": avg_vol})
        if avg_vol < MIN_AVG_VOLUME:
            return FilterResult(passed=False, reason="low_liquidity", checks=checks)

        weekly = resample_weekly(df)
        if len(weekly) < 55:
            return FilterResult(passed=False, reason="insufficient_history", checks=checks)

        w_close = weekly["Close"]
        ema20 = float(ema(w_close, 20).iloc[-1])
        ema50 = float(ema(w_close, 50).iloc[-1])
        w_price = float(w_close.iloc[-1])
        trend_ok = ema20 > ema50 and w_price > ema50
        checks.append(
            {
                "rule": "weekly_uptrend",
                "passed": trend_ok,
                "value": {"ema20": ema20, "ema50": ema50, "price": w_price},
            }
        )
        if not trend_ok:
            return FilterResult(passed=False, reason="trend_misaligned", checks=checks)

        return FilterResult(passed=True, reason="eligible", checks=checks)
