# Financial Analyst Review

Review date: 2026-06-07. Scope: breakout scanner, Lynch scanner, dashboard, and underlying Yahoo Finance data pipeline.

## Executive summary

The platform implements a coherent Minervini-style breakout workflow (trend, liquidity, 52-week position, multi-factor scoring, market regime) plus a separate Peter Lynch fundamental screen. Architecture is usable for **idea generation and watchlist triage**, not for trade execution without independent verification.

**Critical functional issues addressed in this pass:**

1. Price feed anomalies (e.g. split-adjustment glitches showing MU ~$864) now fail eligibility with `price_data_anomaly`.
2. EPS/revenue YoY from negative or tiny prior periods no longer produce absurd percentages (756%+); values above 300% YoY are treated as unreliable.
3. Lynch debt/equity threshold labels corrected (ratio vs mistaken percent display).

## What works well (analyst perspective)

| Area | Assessment |
|------|------------|
| Eligibility stack | Sound Minervini-style gates: $10+ price, 750k liquidity, MA alignment, rising 200 SMA, 52w band |
| Scoring decomposition | RS vs SPY/sector, accumulation, compression, pattern, resistance, fundamentals — transparent in reports |
| Regime adjustment | SPY trend multiplier scales scores in weak markets — appropriate risk framing |
| Tier narrative | `explain_tier()` documents why high scorers land in Tier 2 vs Tier 1 |
| Lynch categories | Fast grower / stalwart / asset play presets align with Lynch framework |
| Dry-run isolation | Synthetic QA data no longer overwrites production scan output |

## Remaining limitations (non-blocking but important)

| Issue | Risk | Mitigation for users |
|-------|------|----------------------|
| Yahoo Finance single source | Stale splits, missing fundamentals, delayed quotes | Cross-check prices and EPS on broker/SEC filings before sizing |
| No survivorship / delisting handling | Universe is static file; delisted names may error | Refresh `data/tickers.txt`; review excluded tickers |
| Lynch vs breakout duplication | Two pipelines, overlapping tickers, different metrics | Treat as complementary screens, not one composite rank |
| Regime can demote Tier 1 | `final_adjusted_score` < 70 in weak markets blocks Tier 1 even with high raw score | Read `tier_reason`; do not ignore regime multiplier |
| No position sizing / risk | Scores are relative, not dollar risk | Apply your own stop-loss and position limits |
| News on dashboard | Headline snapshot only | Not a substitute for catalyst research |

## Tier logic (verified)

- **Tier 1:** normalized ≥ 80, adjusted ≥ 70, compression ≥ 8, and (accumulation ≥ 8 or relative volume ≥ 5).
- **Tier 2:** eligible but missing Tier 1 setup, or normalized 65–79.
- **Tier 3:** eligible, normalized < 65.
- **Filtered:** failed hard eligibility (including new price anomaly filter).

High normalized scores without compression/volume land in **Tier 2**, not Tier 1 — consistent with breakout readiness semantics.

## Data quality rules (new)

- **Price spike:** latest close must be within 3× of the 20-day median close.
- **Growth rates:** YoY/CAGR null if prior period ≤ 0 or if growth > 300% (likely bad base or feed error).

## Recommended workflow

1. Maintain `data/tickers.txt` as your investable universe.
2. Run `quant-scan --report both --archive` after the close; review Tier 1/2 in **Full Universe** tab.
3. Run `quant-lynch --report both --archive` for fundamental angle on the same universe.
4. For any name near resistance or with extreme fundamental display, verify price and EPS manually.
5. Do not trade on dashboard output alone — this is a screening assistant, not investment advice.

## Disclaimer

This tool does not provide investment advice. Past patterns and scores do not guarantee future performance. All data is third-party and may be incorrect.
