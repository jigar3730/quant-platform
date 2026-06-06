# Breakout Scanner — User Manual

This guide explains how to install, run, and interpret results from the quant-platform breakout stock scanner.

**Recent capabilities:** interactive dashboard (five tabs), full-universe table, ticker profile pages with live news, JSON daily archival, DuckDB score history, email alerts, and Docker scheduling.

## What this tool does

The scanner identifies high-quality breakout candidates from a universe of actively traded US stocks. For each ticker it:

1. Downloads price, volume, and fundamental data from yfinance
2. Applies hard eligibility filters (liquidity, trend, price, 52-week range)
3. Scores passing stocks across nine technical and fundamental components
4. Adjusts scores for the current SPY market regime
5. Assigns a tier (Tier 1, Tier 2, Tier 3, or filtered)
6. Exports ranked results to CSV and optional detailed reports

The default universe is the **100 most-active US stocks** from Yahoo Finance (`UNIVERSE_SIZE` in `config.py`). You can override this with `--tickers` or by changing `UNIVERSE_SIZE` before running a scan.

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
--tickers TICKERS     Comma-separated tickers (overrides universe fetch)
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

1. **Universe** — Fetches most-active tickers via `yf.screen("most_actives")`, or uses your `--tickers` list
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

A stock must pass **all** of these to be scored. Filtered stocks appear in output with `tier=filtered` and zero scores.

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
quant-scan --report both --archive   # generate JSON + optional history
quant-view                           # http://localhost:8501
```

### Layout

**Header** — universe size, eligible count, tier breakdown, SPY regime multiplier.

**Sidebar**
- **Scan to load** — latest output or any archived day (`data/history/YYYY-MM-DD/`)
- **Filters** — tier, eligible only, actionable only (Tier 1+2), min score, ticker search
- **Open ticker profile** — jump to any symbol's detail view
- **Sync archives to DuckDB** — backfill `scan_history.duckdb` from JSON archives
- **Score component guide** — plain-language explanation of each indicator

**Ticker links** — blue links (`?ticker=MU`) appear throughout the app. Clicking one opens that ticker's profile (sets URL query param and sidebar selection).

### Tabs

#### Overview
- SPY market regime panel (price, SMAs, 63d return, 52w high distance)
- Tier distribution donut chart
- Exclusion breakdown (why stocks failed filters)
- Score histogram, component heatmap, compression vs RS scatter plot
- Clickable ticker links under the scatter chart

#### All Tickers
Full universe table for every scanned symbol:
- Tier, eligibility, final/normalized/raw scores, sector ETF
- All nine component scores (RS, volume, compression, pattern, resistance, revenue, EPS)
- Revenue YoY % and EPS growth % (when available)
- Filter reason for excluded stocks

**Interactions:**
- Click any table row to open that ticker's profile
- Click blue ticker links (first 30 shown below table)
- **Download CSV** — export the full filtered table

Sidebar filters apply to this tab.

#### Ticker Detail
Unified profile for one symbol:
- **Live news and market update** — current price, day change, market cap, 1Y change, today's range, recent headlines with links (fetched live from Yahoo Finance; cached 5–10 minutes)
- **Score history chart** — final and normalized scores over archived scan dates (requires `--archive` on multiple days)
- **Fundamentals tab** — revenue and EPS scores with raw growth metrics
- **Technical tab** — RS, volume, compression, pattern, resistance with bar and radar charts
- **Eligibility tab** — pass/fail checks with actual values and thresholds

Use the sidebar picker, All Tickers row click, or any `?ticker=` link to navigate here.

#### Actionable Watchlist
Tier 1 and Tier 2 candidates only. Each expander shows key metrics and a link to the full Ticker Detail profile.

#### Compare
Select 2–3 eligible tickers for an overlay radar chart and side-by-side score table. Profile links above and below the table.

### Dashboard tips

- Run `quant-scan --report both` to refresh; press **R** in the browser or reload to pick up new data
- Load archived scans from the sidebar to review past days (JSON is preserved per day under `data/history/`)
- Use **All Tickers** + **Download CSV** for spreadsheet work outside the dashboard
- Live news requires network access when viewing a ticker profile
- Score history needs multiple archived scans (`quant-daily` or `--archive` each day)

---

## Score history (DuckDB)

Archiving writes **both** JSON and a queryable DuckDB database. Nothing replaces the JSON files.

| Storage | Path | Best for |
|---------|------|----------|
| JSON archive | `data/history/YYYY-MM-DD/breakout_scan_report.json` | Full detail, audit trail, dashboard drill-down |
| DuckDB | `data/scan_history.duckdb` | Score trends, tier changes over time |

DuckDB tables:
- `scans` — day-level metadata (universe size, tier counts, regime)
- `ticker_scores` — per-ticker tier and scores per scan date
- `component_scores` — per-component points per ticker per date

**Enable history:**

```bash
quant-scan --report both --archive
# or
quant-daily --no-email
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

Select **Archive YYYY-MM-DD** in the dashboard sidebar, or set the report path manually.

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
| `Report not found` in dashboard | Run `quant-scan --report both` first |
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

```
quant-platform/
  quant-scan              # CLI: run scanner
  quant-daily             # CLI: scan + archive + email
  quant-view              # CLI: launch dashboard
  data/
    output/               # latest CSV, JSON, MD
    history/              # archived scans (with --archive)
    cache/                # optional parquet cache
    scan_history.duckdb   # DuckDB score history
  logs/
    scan.log
    cron.log              # Docker scheduler
  docker/                 # Dockerfile, crontab, compose
  src/quant_platform/
    cli.py, daily.py, view.py, dashboard.py
    config.py
    data/                 # universe, fetch, cache, news
    filters/              # eligibility
    regime/               # SPY regime
    scoring/              # score components
    report/               # JSON/Markdown reports
    history/              # archive.py, duckdb_store.py
    notify/               # email
    pipeline/             # runner
    viz/                  # dashboard UI (components, styles, navigation, data)
  tests/
  USER_MANUAL.md
  Agent.md
```

---

## Further reading

- [Agent.md](Agent.md) — complete strategy specification with scoring formulas
- [README.md](README.md) — minimal install and run reference
