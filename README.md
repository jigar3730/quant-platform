# quant-platform

A quantitative stock scanning pipeline that identifies high-quality breakout candidates from actively traded US equities. The scanner fetches market data via yfinance, applies eligibility filters, scores technical and fundamental signals, adjusts for SPY market regime, and exports ranked results.

## Features

- Scans the 100 most-active US stocks by default (or a custom ticker list)
- Hard filters for liquidity, trend alignment, price, and 52-week range
- Nine scoring components: relative strength, volume, compression, pattern, resistance, revenue, EPS
- SPY market regime multiplier (strong / neutral / weak)
- Tier assignment: Tier 1 (breakout ready), Tier 2 (watchlist), Tier 3, filtered
- CSV summary output for spreadsheets
- Optional JSON and Markdown reports with per-indicator explanations
- Interactive Streamlit dashboard with charts, full-universe table, and ticker profiles
- Live news and market snapshots per ticker (Yahoo Finance)
- Daily JSON archival (`data/history/YYYY-MM-DD/`) plus DuckDB score history
- Email alerts for actionable tickers (Tier 1 and Tier 2)
- Docker deployment with 5 PM scheduled scans

## Requirements

- Python 3.12+
- Network access for live yfinance data

## Installation

```bash
cd quant-platform

uv pip install -e .              # core scanner
uv pip install -e .[dev]           # + pytest, ruff
uv pip install -e .[viz]           # + Streamlit dashboard
uv pip install -e .[dev,viz]       # full setup
```

Devcontainer users: dependencies install automatically via `postCreateCommand`.

## Quick start

```bash
# 1. Run a full scan with detailed reports
quant-scan --report both

# 2. Review results
#    data/output/breakout_scan_results.csv
#    data/output/breakout_scan_summary.md

# 3. Open interactive dashboard (requires [viz])
quant-view
#    http://localhost:8501
```

Archive for history and score trends:

```bash
quant-scan --report both --archive
# or
quant-daily --no-email
```

## CLI reference

### `quant-scan`

| Flag | Description |
|------|-------------|
| `--tickers AAPL,MSFT` | Override universe with comma-separated tickers |
| `--output PATH` | CSV output path |
| `--report {json,md,both}` | Write detailed analysis reports |
| `--report-json PATH` | JSON report path |
| `--report-md PATH` | Markdown summary path |
| `--cache` | Use parquet cache for faster same-day re-runs |
| `--dry-run` | Offline mode with synthetic data |
| `--archive` | Archive to `data/history/YYYY-MM-DD/` and upsert DuckDB |
| `--email` | Email actionable Tier 1+2 tickers |

```bash
quant-scan --report both --archive    # scan + history + DuckDB
quant-scan --tickers NVDA,AMD --cache
```

### `quant-daily`

Runs scan, archives, and optionally emails actionable tickers.

```bash
quant-daily                 # scan + archive + email
quant-daily --no-email      # scan + archive only
```

Equivalent to `quant-scan --report both --archive --email`.

### `quant-view`

Requires `[viz]`. Reads `data/output/breakout_scan_report.json` by default; can load archived scans from the sidebar.

```bash
quant-scan --report both
quant-view
```

## Dashboard overview

Five tabs:

| Tab | Purpose |
|-----|---------|
| **Overview** | Market regime, tier chart, exclusion breakdown, score distribution, heatmap, scatter |
| **All Tickers** | Full universe table (all scores, fundamentals); click row or ticker link for profile |
| **Ticker Detail** | Fundamentals, technical scores, eligibility, live news, score history |
| **Actionable Watchlist** | Tier 1 and Tier 2 candidates with profile links |
| **Compare** | Side-by-side radar chart for 2–3 tickers |

Blue ticker links (`?ticker=MU`) open the unified profile from anywhere in the app. Sidebar picker and filters apply across tabs.

## Output files

| File | Description |
|------|-------------|
| `data/output/breakout_scan_results.csv` | Ranked summary table |
| `data/output/breakout_scan_report.json` | Full per-ticker analysis (dashboard input) |
| `data/output/breakout_scan_summary.md` | Human-readable summary |
| `data/history/YYYY-MM-DD/` | Daily archive (CSV, JSON, MD, log, summary) |
| `data/history/scan_index.csv` | Index of archived scans (day-level stats) |
| `data/scan_history.duckdb` | Per-ticker score history (upserted on `--archive`) |
| `logs/scan.log` | Runtime log |

**Note:** Without `--archive`, only `data/output/` is updated (latest scan overwrites previous). JSON per day is stored only when archiving is enabled.

## Docker (daily 5 PM scan + email)

```bash
cp .env.example .env
docker compose up -d
docker compose run --rm scanner scan   # optional: run now
```

## Interpreting results

| Tier | Meaning |
|------|---------|
| Tier 1 | Breakout ready — high score with compression and volume confirmation |
| Tier 2 | Watchlist — score 65–79, or high score missing Tier 1 criteria |
| Tier 3 | Below watchlist threshold (score under 65) |
| filtered | Failed eligibility (trend, liquidity, price, etc.) |

Sort by `final_adjusted_score` descending. See **[USER_MANUAL.md](USER_MANUAL.md)** for scoring formulas, dashboard usage, history, and troubleshooting.

## Project structure

```
quant-platform/
  src/quant_platform/
    cli.py, daily.py, view.py, dashboard.py
    config.py
    data/           # universe, fetch, cache, news
    filters/        # eligibility
    regime/         # SPY market regime
    scoring/        # components and aggregation
    report/         # JSON/Markdown builder
    history/        # JSON archive + DuckDB store
    notify/         # email alerts
    pipeline/       # orchestration
    viz/            # dashboard components, styles, navigation
  data/output/      # latest scan results
  data/history/     # archived scans
  tests/
  Agent.md          # strategy specification
  USER_MANUAL.md    # detailed user guide
```

## Development

```bash
pytest                  # unit tests (no network)
pytest -m integration   # live yfinance tests
ruff check src tests
```

## Documentation

- **[USER_MANUAL.md](USER_MANUAL.md)** — installation, CLI, outputs, scoring, dashboard, history, email, Docker
- **[Agent.md](Agent.md)** — complete strategy specification

## License

Internal / project use. See repository for license terms.
