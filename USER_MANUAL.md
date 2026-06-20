# quant-platform — User Manual

This guide explains how to install, run, and interpret results from the quant-platform stock scanners (breakout, swing pullback, and Peter Lynch).

**Recent capabilities:** strategy-aware dashboard (Breakout / Swing / Lynch selector), full-universe table with filtered-but-scored tickers, ticker profile pages with live news, JSON daily archival, DuckDB score history per strategy, email alerts, and Docker scheduling.

## What this tool does

The platform runs one or more scanners against a shared ticker universe. Each scanner:

1. Downloads price, volume, and (where applicable) fundamental data from yfinance
2. Applies hard eligibility filters (liquidity, trend, price, range — strategy-specific)
3. **Scores every ticker with price data**, even if it fails eligibility (filters become labels; tiers apply only to eligible names)
4. Adjusts scores for the current SPY market regime (breakout and swing)
5. Assigns a tier and exports ranked results to CSV and optional detailed reports

### Scanners at a glance

| Command | Strategy | Tiers | Dashboard |
|---------|----------|-------|-----------|
| `quant-scan` | Breakout | Tier 1 / 2 / 3 / filtered | Strategy → **Breakout** |
| `quant-swing` | Swing pullback | A / B / C / filtered | Strategy → **Swing Pullback** |
| `quant-lynch` | Peter Lynch | passed / failed + categories | Strategy → **Peter Lynch** |

### Scanner universe

All scanners share the same universe resolution:

| Priority | Source |
|----------|--------|
| 1 | `--tickers AAPL,MSFT` on the CLI |
| 2 | Static file `data/tickers.txt` (edit manually; one symbol per line) |
| 3 | Dynamic fetch — 100 most-active US stocks from Yahoo (`UNIVERSE_SIZE` in `config.py`) |

Use `data/tickers.txt` for a fixed list you maintain (e.g. Vanguard Small Cap Index VSMAX holdings). Lines starting with `#` are comments. You can also use `data/tickers.json`:

```json
{"tickers": ["AAPL", "MSFT", "NVDA"]}
```

Pass `--dynamic-universe` to skip the static file and use Yahoo's most-actives. Pass `--tickers-file PATH` to use a different config path.

---

## Prerequisites

- Python 3.12+
- Network access (for live yfinance data)
- Recommended: [uv](https://github.com/astral-sh/uv) or pip for package management

If you use the provided devcontainer, dependencies are installed automatically on create.

---

## Installation

From the project root:

```bash
# Core scanner only
uv pip install -e .

# Scanner + development tools (pytest, ruff)
uv pip install -e .[dev]

# Scanner + interactive dashboard
uv pip install -e .[viz]

# Everything
uv pip install -e .[dev,viz]
```

Verify installation:

```bash
quant-scan --help
quant-swing --help
quant-lynch --help
quant-view --help    # requires [viz] extra
```

---

## Quick start (recommended workflow)

```bash
# 1. Run a full scan with detailed reports
quant-scan --report both

# 2. Review the ranked CSV (spreadsheet-friendly)
#    data/output/breakout_scan_results.csv

# 3. Read the human-readable summary
#    data/output/breakout_scan_summary.md

# 4. (Recommended) Archive for history and score trends
quant-scan --report both --archive

# 5. Open the interactive dashboard (requires [viz])
quant-view
#    Browser opens at http://localhost:8501
```

For a faster test on a handful of tickers:

```bash
quant-scan --tickers AAPL,MSFT,NVDA,AMD,MU --report both
quant-view
```

---

## Swing pullback scanner (`quant-swing`)

Identifies stocks in a weekly uptrend experiencing a constructive pullback — useful for swing-entry timing rather than breakout compression setups.

### Scoring components (max 60 raw points)

| Component | What it measures |
|-----------|------------------|
| Weekly trend | EMA alignment and price above support on weekly bars |
| Relative strength | Outperformance vs SPY over recent windows |
| Pullback quality | Depth, structure, proximity to moving averages |
| Pullback volume | Volume behavior during pullback vs rally legs |

Penalties may apply for overextension or RSI climax conditions.

### Tiers

| Tier | Meaning |
|------|---------|
| **A** | Final score ≥ 80 |
| **B** | Final score 65–79 |
| **C** | Eligible, score below 65 |
| **filtered** | Failed swing eligibility (liquidity, weekly trend, etc.) |

### Usage

```bash
quant-swing --report both
quant-swing --report both --archive    # archive + DuckDB history
quant-swing --tickers NVDA,AMD,MU --cache
```

### CLI options

Same pattern as `quant-scan`: `--tickers`, `--tickers-file`, `--dynamic-universe`, `--output`, `--cache`, `--dry-run`, `--report {json,md,both}`, `--report-json`, `--report-md`, `--archive`.

### Outputs

| File | Description |
|------|-------------|
| `data/output/swing_scan_results.csv` | Ranked summary |
| `data/output/swing_scan_report.json` | Per-ticker detail (dashboard input) |
| `data/output/swing_scan_summary.md` | Human-readable summary |
| `data/history/YYYY-MM-DD/swing_scan_report.json` | Archived JSON (with `--archive`) |

View results in the dashboard: select **Swing Pullback** in the sidebar Strategy dropdown.

---

## Peter Lynch scanner (`quant-lynch`)

A second scanner implements Peter Lynch's quantitative framework from *One Up on Wall Street*.

### Presets

| Preset | Purpose |
|--------|---------|
| `summary` | Base screen + Fast Grower / Stalwart / Asset Play tags (default) |
| `base` | Core Lynch screen only (PEG, growth, debt, neglect, insiders) |
| `fast_grower` | Small/mid cap 10-bagger hunt (MCap < $5B, EPS growth >= 20%) |
| `stalwart` | Large-cap anchors (MCap > $10B, P/E < 15, dividend > 1.5%) |
| `asset_play` | Deep value (P/B < 1, net cash >= 30% of price) |

### Base screen criteria

- PEG <= 1.0
- EPS growth 5Y between 15% and 30%
- P/E < 20
- Debt/Equity < 35%
- Net cash positive (cash > debt)
- Institutional ownership < 50% **or** analyst coverage <= 5
- Insider buying (6m) **or** declining share count

### Anti-filters

- Negative trailing EPS (pre-profit speculative names)
- ROE below 10% (ROIC proxy when unavailable)
- Highly volatile quarterly revenue (customer concentration risk proxy)

### Usage

```bash
quant-lynch --report both
quant-lynch --preset fast_grower --report both
quant-lynch --tickers CASH,MU,PLUG --preset summary
quant-lynch --report both --archive    # archive + DuckDB history
```

### Outputs

| File | Description |
|------|-------------|
| `data/output/lynch_scan_results.csv` | Ranked Lynch candidates |
| `data/output/lynch_scan_report.json` | Per-ticker checks and metrics |
| `data/output/lynch_scan_summary.md` | Human-readable summary |
| `data/history/YYYY-MM-DD/lynch_scan_report.json` | Archived Lynch JSON (with `--archive`) |
| `data/history/lynch_scan_index.csv` | Day-level Lynch scan index |

### Qualitative overlay (manual)

The JSON/MD reports include Lynch's qualitative reminders — boring business, niche monopoly, recurring demand. **Your job after the scan:** run the "two-minute drill" on the top 10–20 names.

---

## Running scans (`quant-scan`)

### Basic commands

| Command | Description |
|---------|-------------|
| `quant-scan` | Full scan of ~100 most-active stocks |
| `quant-scan --report both` | Full scan + JSON and Markdown reports |
| `quant-scan --tickers AAPL,MSFT` | Scan only specified tickers |
| `quant-scan --cache` | Use parquet cache for faster re-runs (24h TTL) |
| `quant-scan --dry-run` | Offline test with synthetic data (no network) |

### All CLI options

```
--tickers TICKERS     Comma-separated tickers (overrides ticker config + dynamic fetch)
--tickers-file PATH   Static ticker list (default: data/tickers.txt)
--dynamic-universe    Ignore ticker config; fetch most-active stocks from Yahoo
--output PATH         CSV output path (default: data/output/breakout_scan_results.csv)
--cache               Read/write cached price and fundamental data
--dry-run             Run with synthetic data, no network calls
--report {json,md,both}
                      Write detailed analysis report
--report-json PATH    JSON report path (default: data/output/breakout_scan_report.json)
--report-md PATH      Markdown summary path (default: data/output/breakout_scan_summary.md)
--archive             Archive to data/history/YYYY-MM-DD/ and upsert DuckDB
--email               Email actionable Tier 1+2 tickers (requires SMTP env vars)
```

### Example sessions

**Daily scan after market close:**

```bash
quant-scan --report both --archive
# or
quant-daily --no-email
```

**Re-run within the same day (faster with cache):**

```bash
quant-scan --report both --cache
```

**Custom watchlist:**

```bash
quant-scan --tickers MU,AMD,NVDA,AVGO,MRVL --output data/output/semis_scan.csv --report both
```

**Offline development / CI:**

```bash
quant-scan --dry-run --tickers AAA,BBB,CCC --report json
```

### What happens during a scan

1. **Universe** — Uses `data/tickers.txt` when present, else fetches most-active tickers via `yf.screen("most_actives")`, unless you pass `--tickers`
2. **Download** — Pulls 252+ days of OHLCV for all tickers, SPY, and sector ETFs; downloads quarterly revenue/EPS
3. **Filter** — Each stock must pass all eligibility checks (see below)
4. **Score** — Eligible stocks are scored and percentile-ranked within the universe
5. **Regime** — SPY conditions produce a multiplier (1.0, 0.85, or 0.6) applied to all scores
6. **Export** — Results written to CSV and optional report files
7. **Log** — Progress logged to console and `logs/scan.log`

A full 100-ticker scan typically takes 30–60 seconds depending on network speed.

---

## Output files

| File | When created | Best for |
|------|--------------|----------|
| `data/output/breakout_scan_results.csv` | Every scan | Sorting, filtering in Excel/Sheets |
| `data/output/breakout_scan_report.json` | With `--report json` or `both` | Programmatic use, dashboard input |
| `data/output/breakout_scan_summary.md` | With `--report md` or `both` | Quick human-readable review |
| `logs/scan.log` | Every scan | Debugging, audit trail |
| `data/cache/*.parquet` | With `--cache` | Faster repeat downloads |
| `data/history/YYYY-MM-DD/` | With `--archive` or `quant-daily` | Full daily snapshot (CSV, JSON, MD) |
| `data/history/scan_index.csv` | With `--archive` | Day-level scan index |
| `data/scan_history.duckdb` | With `--archive` | Per-ticker score history for trends |

---

## Understanding the CSV

Each row is one ticker. Eligible stocks appear first (sorted by score), then filtered stocks (alphabetical).

### Key columns

| Column | Meaning |
|--------|---------|
| `ticker` | Stock symbol |
| `eligible` | `True` if all hard filters passed |
| `filter_reason` | Why excluded, or `eligible` if passed |
| `sector_etf` | Sector benchmark used for relative strength (e.g. SOXX, XLK) |
| `final_adjusted_score` | **Primary ranking column** (0–100, regime-adjusted) |
| `normalized_score` | Raw score scaled to 0–100 before regime adjustment |
| `tier` | `Tier 1`, `Tier 2`, `Tier 3`, or `filtered` |

### Score component columns (0 to max shown)

| Column | Max points | What it measures |
|--------|------------|------------------|
| `rs_market_score` | 20 | Relative strength vs SPY (63d + 126d) |
| `rs_sector_score` | 15 | Relative strength vs sector ETF |
| `accumulation_score` | 12 | Up-day vs down-day volume ratio |
| `relative_volume_score` | 8 | Short-term volume surge vs 20-day average |
| `compression_score` | 15 | Bollinger Band width squeeze |
| `pattern_score` | 5 | Base quality checklist (5 signals) |
| `resistance_score` | 5 | Proximity to near-term resistance |
| `revenue_score` | 15 | Year-over-year revenue growth |
| `eps_score` | 15 | Blended EPS growth (recent + 3yr CAGR) |

`raw_score` is the sum of all components. `normalized_score = raw_score / 120 * 100`.

---

## Eligibility filters (why stocks are excluded)

A stock must pass **all** strategy-specific hard filters to receive a tier (Tier 1–3, A–C, or Lynch pass). Filtered stocks remain in output with `tier=filtered`.

**Important:** Tickers with price data are still **scored** when filtered. The JSON report and dashboard show component scores and `filter_reason` / eligibility checks so you can see *why* a name failed and how strong its signals were anyway.

### Breakout filter codes

| Filter code | Rule |
|-------------|------|
| `insufficient_history` | Fewer than 200 trading days of data |
| `price_below_minimum` | Latest close below $10 |
| `low_liquidity` | 20-day average volume below 750,000 shares |
| `trend_misaligned` | Price not above SMA50 > SMA150 > SMA200 |
| `sma200_not_rising` | 200-day MA not higher than 30 trading days ago |
| `too_close_to_52w_low` | Price less than 30% above 52-week low |
| `too_far_from_52w_high` | Price more than 25% below 52-week high |
| `no_price_data` | yfinance returned no price history |

In the JSON report and dashboard, each filter shows the **actual values** that were checked (e.g. price vs each moving average).

---

## Scoring and tiers

### Market regime multiplier

Based on SPY conditions at scan time:

| Regime | Multiplier | Conditions |
|--------|------------|------------|
| **Strong** | 1.0 | SPY above SMA50, SMA50 above SMA200, 63-day return positive |
| **Neutral** | 0.85 | Neither strong nor weak |
| **Weak** | 0.6 | SPY below SMA200, or more than 10% below 52-week high |

`final_adjusted_score = normalized_score × regime_multiplier`

### Tier definitions

| Tier | Meaning | Criteria |
|------|---------|----------|
| **Tier 1** | Breakout ready | Score ≥ 80, adjusted ≥ 70, compression ≥ 8, and volume signal met |
| **Tier 2** | Watchlist | Score 65–79, or score ≥ 80 but missing Tier 1 volume/compression |
| **Tier 3** | Low priority | Eligible but score below 65 |
| **filtered** | Excluded | Failed one or more eligibility filters |

### How to read a candidate

**Strong Tier 2 example (MU):**
- Passed all trend and liquidity filters
- High RS vs market and sector
- Strong revenue/EPS growth
- Missing: Bollinger compression (not coiling yet) — hence Tier 2, not Tier 1

**Filtered example (MSFT):**
- Failed trend alignment: SMA50 below SMA150 below SMA200 (downtrend structure)
- Never scored; appears at bottom of CSV with `filter_reason=trend_misaligned`

---

## Detailed reports (`--report`)

### JSON report (`breakout_scan_report.json`)

Structured data for each ticker:

```json
{
  "ticker": "MU",
  "verdict": "eligible",
  "tier": "Tier 2",
  "tier_reason": "Watchlist candidate: normalized score 68.3 (65-79 range)",
  "eligibility": {
    "checks": [
      { "rule": "trend_alignment", "passed": true, "value": { "price": 864.01, "sma50": 617.35, ... } }
    ]
  },
  "scores": {
    "rs_market": {
      "score": 20, "max": 20,
      "raw": { "ratio_63d": 13.35, "avg_ratio": 22.59 },
      "meaning": "Strong outperformance vs SPY over 3-6 months"
    }
  }
}
```

Use this file for:
- The interactive dashboard (`quant-view`)
- Custom analysis scripts
- Archiving scan snapshots over time

### Markdown summary (`breakout_scan_summary.md`)

A readable report with:
- Market regime block
- Top eligible candidates with component explanations
- Excluded tickers with failure reasons

Good for a quick daily review without opening the dashboard.

---

## Interactive dashboard (`quant-view`)

Requires the `[viz]` install extra (Streamlit + Plotly).

```bash
quant-scan --report both --archive    # Breakout JSON + history
quant-swing --report both --archive   # Swing JSON + history
quant-lynch --report both --archive   # Lynch JSON + history
quant-view                            # http://localhost:8501
```

### Strategy selector

The sidebar **Strategy** dropdown switches the entire UI:

| Strategy | Report file | Tab layout |
|----------|-------------|------------|
| **Breakout** | `breakout_scan_report.json` | Five price-scanner tabs (below) |
| **Swing Pullback** | `swing_scan_report.json` | Same five tabs, swing tiers/scores |
| **Peter Lynch** | `lynch_scan_report.json` | Lynch sub-tabs (Overview, Candidates, All Tickers, Ticker Detail) |

Only one strategy is active at a time. Pick **Report** to load latest output or an archived day (`data/history/YYYY-MM-DD/`).

### Sidebar (price scanners: Breakout & Swing)

- **Strategy** — Breakout, Swing Pullback, or Peter Lynch
- **Report** — latest `data/output/` or archived JSON for the selected strategy
- **Report path** — override path manually if needed
- **Filters** — tier (strategy-specific labels), eligible only, actionable only (Tier 1+2 or A+B), min score, ticker search
- **Score component guide** — plain-language explanation of each indicator (breakout/swing)
- **Open ticker profile** — jump to any symbol (price scanners only)
- **Sync archives to DuckDB** — backfill breakout, swing, and Lynch history from JSON archives

**Ticker links** — blue links (`?ticker=MU`) appear throughout price-scanner views. Clicking one opens that ticker's profile (URL query param + sidebar selection).

### Price-scanner tabs (Breakout & Swing)

Shared layout; charts and columns adapt to the selected strategy (tiers, score labels, scatter axes).

#### Full Universe
Interactive table for every scanned symbol:
- Tier, eligibility, final/normalized scores, sector ETF, component scores
- `filter_reason` / exclusion label for filtered rows (scores still shown when present)
- Sort, sector filter, view mode (All / Eligible / Actionable)
- Click a row for an inline preview panel; **Open full profile** jumps to Ticker Detail
- **Download CSV** — export the filtered table

#### Overview
- SPY market regime panel
- Tier distribution chart (Tier 1/2/3 or A/B/C + filtered)
- Exclusion breakdown (why stocks failed filters)
- Score histogram, component heatmap, strategy-specific scatter (e.g. compression vs RS for breakout; pullback vs RS for swing)

#### Ticker Detail
Unified profile for one symbol:
- Live news and market snapshot (Yahoo Finance; cached 5–10 minutes)
- **Score history chart** from DuckDB (`strategy_id` = breakout or swing; requires archived scans)
- Fundamentals tab (breakout revenue/EPS; empty for swing)
- Technical tab — component bar/radar charts from strategy config
- Eligibility tab — pass/fail checks with actual values

#### Actionable Watchlist
Top-tier candidates only: Tier 1+2 (breakout) or A+B (swing). Expanders link to full profiles.

#### Compare
Select 2–3 eligible tickers for overlay radar chart and side-by-side score table.

### Peter Lynch views

When **Peter Lynch** is selected, the main tab bar is replaced by Lynch sub-tabs:

- **Overview** — category breakdown, score histogram, qualitative overlay
- **Candidates** — ranked passers with expandable checks
- **All Tickers** — full universe with passed/category filters and CSV download
- **Ticker Detail** — Lynch score, P/E, PEG, quantitative checks, DuckDB history

### Dashboard tips

- Run the matching CLI with `--report both` to refresh JSON; press **R** in the browser or reload
- Load archived scans from the **Report** dropdown to review past days
- Filtered tickers may show non-zero component scores — use **Full Universe** and **Ticker Detail** to inspect
- Live news requires network access; score history needs multiple archived scans and **Sync archives to DuckDB**
- If report `strategy_id` does not match the selected strategy, the dashboard shows a warning

---

## Score history (DuckDB)

Archiving writes **both** JSON and a queryable DuckDB database. Nothing replaces the JSON files.

| Storage | Path | Best for |
|---------|------|----------|
| JSON archive | `data/history/YYYY-MM-DD/breakout_scan_report.json` | Full detail, audit trail, dashboard drill-down |
| DuckDB | `data/scan_history.duckdb` | Score trends, tier changes over time |

DuckDB tables (schema v2 — composite primary key includes `strategy_id` and `scan_time`):

- `scans` — day-level metadata per strategy (universe size, tier counts, regime)
- `ticker_scores` — per-ticker tier and scores per scan
- `component_scores` — per-component points per ticker per scan

Breakout and swing share `ticker_scores` / `component_scores` with `strategy_id` of `breakout` or `swing`. Lynch uses separate `lynch_*` tables.

**Enable history:**

```bash
quant-scan --report both --archive
quant-swing --report both --archive
quant-lynch --report both --archive
# or
quant-daily --no-email   # breakout only
```

**Backfill** existing JSON archives into DuckDB: click **Sync archives to DuckDB** in the dashboard sidebar (or archives auto-sync on first load if the DB is missing).

Without `--archive`, only `data/output/` is updated and previous days are not kept.

---

## Typical workflows

### Daily breakout watchlist

```bash
quant-scan --report both
```

1. Open `breakout_scan_summary.md` for a quick read
2. Focus on Tier 1 and Tier 2 in the CSV
3. Use `quant-view` to drill into top candidates

### Sector-focused scan

```bash
quant-scan --tickers MU,AMD,NVDA,AVGO,MRVL,INTC,QCOM,ON --report both
```

### Spreadsheet analysis

```bash
quant-scan --output data/output/today.csv
```

Open the CSV in Excel/Google Sheets. Sort by `final_adjusted_score` descending. Filter `eligible=True`.

### Building score trends over time

```bash
# Run daily (manually or via Docker cron)
quant-daily --no-email
```

After several days:
- Dashboard **Ticker Detail** shows a score history chart per ticker
- DuckDB stores queryable history in `data/scan_history.duckdb`
- JSON archives remain the full source of truth under `data/history/YYYY-MM-DD/`

### Reviewing a past scan

Select **Report → Archive YYYY-MM-DD** in the dashboard sidebar for the chosen strategy, or edit the report path manually.

### Automated daily scan (Docker)

For hands-off daily operation with history and email:

```bash
cp .env.example .env          # configure SMTP + timezone
docker compose up -d          # starts scheduler (5 PM daily)
docker compose run --rm scanner scan   # run once now
```

Each run archives to `data/history/YYYY-MM-DD/` and emails Tier 1 + Tier 2 tickers.

---

## Historical data

**By default, scans overwrite the latest output** in `data/output/` only. Per-day JSON is **not** kept unless you archive.

| Mode | What is saved |
|------|----------------|
| `quant-scan --report both` | Latest CSV, JSON, MD in `data/output/` |
| `quant-scan --report both --archive` | Above + copy to `data/history/YYYY-MM-DD/` + DuckDB upsert |
| `quant-daily` | Same as archive mode (always archives; email optional) |

```
data/history/
  scan_index.csv              # day-level stats (tiers, regime, counts)
  2026-06-06/
    breakout_scan_results.csv
    breakout_scan_report.json   # full per-ticker detail
    breakout_scan_summary.md
    scan.log
    scan_summary.txt          # actionable tickers text summary
  2026-06-07/
    ...

data/scan_history.duckdb      # queryable ticker score history
```

Two scans on the same calendar day overwrite that day's folder. JSON and DuckDB are updated together on archive.

---

## Email notifications

Actionable tickers are **Tier 1 and Tier 2**. Configure via environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | Usually `587` |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP password or app password |
| `EMAIL_FROM` | Sender address |
| `EMAIL_TO` | Recipient(s), comma-separated |
| `TZ` | Timezone for Docker scheduler (default `America/New_York`) |

```bash
# One-off scan with email
quant-scan --report both --archive --email

# Daily workflow (archive + email)
quant-daily
```

The email includes an HTML table of actionable tickers with scores, sector, key components, and tier reasons.

---

## Docker deployment

### Setup

```bash
cp .env.example .env
# Edit .env with SMTP credentials and recipients

docker compose build
docker compose up -d
```

### Commands

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start scheduler (5 PM weekdays) |
| `docker compose run --rm scanner scan` | Run one scan immediately |
| `docker compose logs -f scanner` | Follow container logs |
| `tail -f logs/cron.log` | Follow cron execution log |

### Schedule

Default: **5:00 PM Monday–Friday** in the container timezone (`TZ` in `.env`, default `America/New_York`).

Edit `docker/crontab` to change the schedule.

### Data persistence

Docker volumes map `./data` and `./logs` to the host. Historical archives survive container restarts.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `yfinance screener unavailable; using fallback universe` | Network or API issue; retry later or use `--tickers` with your own list |
| Only 10 tickers scanned instead of 100 | Fallback universe was used; check network, update yfinance |
| `Report not found` in dashboard | Run the matching scanner with `--report both` (e.g. `quant-swing --report both` for Swing) |
| Wrong tiers/scores in dashboard | Confirm **Strategy** matches the JSON (`strategy_id` field); reload correct report |
| `quant-view` not found | Install viz extra: `uv pip install -e .[viz]` |
| Missing fundamentals (0 revenue/EPS score) | yfinance had no quarterly data; stock still scored on technicals |
| Scan is slow | Use `--cache` for same-day re-runs; use `--tickers` for smaller universe |
| All stocks filtered | Market may be in broad downtrend; check `filter_breakdown` in JSON or dashboard |
| No score history chart | Run `--archive` on multiple days; use **Sync archives to DuckDB** |
| No news in dashboard | Network required; yfinance may rate-limit — retry after a minute |
| Live price differs from scan | Dashboard news uses live Yahoo data; scan uses data at run time |
| Email not sent | Set `SMTP_HOST` and `EMAIL_TO` in `.env`; check `logs/scan.log` |
| Docker cron not running | Check `docker compose ps` and `logs/cron.log` |
| ImportError in dashboard | Restart `quant-view` after code changes; clear browser cache |

### Logs

Check `logs/scan.log` for warnings about individual tickers, screener fallbacks, and sector mapping gaps.

### Tests

```bash
pytest                    # unit tests (no network)
pytest -m integration     # includes live yfinance tests
```

---

## Project layout (reference)

| Path | Role |
|------|------|
| `src/quant_platform/` | Python package — scanners, scoring, dashboard |
| `data/tickers.txt` | Shared static universe (edit manually) |
| `data/output/` | Latest scan results (gitignored) |
| `data/history/` | Archived daily snapshots (gitignored) |
| `data/scan_history.duckdb` | Score trend database (gitignored) |
| `tests/` | Unit and integration tests |
| `docker/` | Scheduled scan container |

Full module-by-module documentation: **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**

---

## Further reading

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) — folder layout, modules, data flow
- [Agent.md](Agent.md) — original strategy specification with scoring formulas
- [README.md](README.md) — install and quick start
