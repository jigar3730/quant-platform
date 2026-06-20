# quant-platform

A quantitative stock scanning pipeline for US equities. It includes **breakout**, **swing pullback**, and **Peter Lynch** strategies that fetch market data via yfinance, apply eligibility filters, score technical and fundamental signals, adjust for SPY market regime, and export ranked results.

## Features

- **Breakout scanner** (`quant-scan`) — compression, relative strength, volume, and growth signals
- **Swing pullback scanner** (`quant-swing`) — weekly trend, pullback quality, and volume behavior
- **Peter Lynch scanner** (`quant-lynch`) — PEG, growth, debt, neglect, and category presets
- Scans the most-active US stocks by default (or a custom ticker list in `data/tickers.txt`)
- Hard filters for liquidity, trend alignment, price, and range; **all tickers with price data are scored** (filters label exclusions; tiers apply to eligible names only)
- SPY market regime multiplier (strong / neutral / weak)
- CSV summary output for spreadsheets; optional JSON and Markdown reports
- **Strategy-aware Streamlit dashboard** (`quant-view`) — Breakout, Swing, and Lynch via sidebar selector
- Live news and market snapshots per ticker (Yahoo Finance)
- Daily JSON archival (`data/history/YYYY-MM-DD/`) plus DuckDB score history (composite key per strategy)
- Email alerts for actionable breakout tickers (Tier 1 and Tier 2)
- Docker deployment with 5 PM scheduled scans

## Requirements

- Python 3.12+
- Network access for live yfinance data

## Installation

```bash
cd quant-platform

pip install -e .              # core scanner
pip install -e .[dev]           # + pytest, ruff
pip install -e .[viz]           # + Streamlit dashboard
pip install -e .[dev,viz]       # full setup
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

## Static ticker universe

Edit `data/tickers.txt` to define a shared watchlist for **all scanners** (`quant-scan`, `quant-swing`, `quant-lynch`, `quant-daily`). One symbol per line; lines starting with `#` are comments.

```text
# VSMAX small-cap holdings (update manually)
SMCI
FIX
...
```

Universe resolution order:

1. `--tickers` on the CLI (highest priority)
2. `data/tickers.txt` (or `--tickers-file PATH`) when the file exists and has symbols
3. Dynamic fetch — 100 most-active stocks from Yahoo (`--dynamic-universe` forces this)

JSON is also supported: `data/tickers.json` with `{"tickers": ["AAPL", "MSFT"]}`.

## CLI reference

### `quant-scan`

| Flag | Description |
|------|-------------|
| `--tickers AAPL,MSFT` | Override ticker config file and dynamic fetch |
| `--tickers-file PATH` | Static ticker list (default: `data/tickers.txt`) |
| `--dynamic-universe` | Ignore ticker config; use Yahoo most-actives |
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

### `quant-lynch` — Peter Lynch 10-bagger screen

| Flag | Description |
|------|-------------|
| `--preset {base,fast_grower,stalwart,asset_play,summary}` | Lynch screen preset (default: `summary`) |
| `--tickers AAPL,MSFT` | Override ticker config file and dynamic fetch |
| `--tickers-file PATH` | Static ticker list (default: `data/tickers.txt`) |
| `--dynamic-universe` | Ignore ticker config; use Yahoo most-actives |
| `--report {json,md,both}` | Detailed Lynch report |
| `--archive` | Archive to `data/history/YYYY-MM-DD/` and upsert DuckDB |

```bash
quant-lynch --report both                    # full Lynch scan (all categories)
quant-lynch --preset fast_grower --report both
quant-lynch --preset stalwart --tickers F,JNJ,KO
quant-lynch --report both --archive          # scan + history + DuckDB
```

Outputs: `data/output/lynch_scan_results.csv`, optional JSON/MD reports.

### `quant-swing` — Swing pullback scanner

| Flag | Description |
|------|-------------|
| `--tickers AAPL,MSFT` | Override ticker config file and dynamic fetch |
| `--tickers-file PATH` | Static ticker list (default: `data/tickers.txt`) |
| `--dynamic-universe` | Ignore ticker config; use Yahoo most-actives |
| `--report {json,md,both}` | Detailed swing report |
| `--archive` | Archive to `data/history/YYYY-MM-DD/` and upsert DuckDB |

```bash
quant-swing --report both
quant-swing --report both --archive    # scan + history + DuckDB
quant-swing --tickers NVDA,AMD --cache
```

Outputs: `data/output/swing_scan_results.csv`, optional JSON/MD reports. Tiers: **A** (≥80), **B** (65–79), **C** (below 65), **filtered** (failed eligibility).

### `quant-view`

Requires `[viz]`. Pick a **strategy** in the sidebar (Breakout, Swing Pullback, or Peter Lynch), then load the latest or an archived report.

```bash
quant-scan --report both --archive    # Breakout
quant-swing --report both --archive   # Swing pullback
quant-lynch --report both --archive   # Peter Lynch
quant-view
```

## Dashboard overview

Use the sidebar **Strategy** selector to switch between scan types. **Breakout** and **Swing Pullback** share the same tab layout; **Peter Lynch** has its own sub-tabs.

| Tab / view | Purpose |
|------------|---------|
| **Full Universe** | Interactive scan table, filters, sort, and live ticker preview panel |
| **Overview** | Market regime, tier chart, exclusion breakdown, score distribution, heatmap, scatter |
| **Ticker Detail** | Fundamentals, technical scores, eligibility, live news, score history |
| **Actionable Watchlist** | Top-tier candidates (Tier 1+2 for breakout; A+B for swing) |
| **Compare** | Side-by-side radar chart for 2–3 tickers |
| **Peter Lynch** | Overview, candidates, full universe, ticker detail (when Lynch strategy selected) |

Blue ticker links (`?ticker=MU`) open the unified profile from anywhere in the app. Sidebar picker and filters apply across tabs for price-scanner strategies.

## Output files

| File | Description |
|------|-------------|
| `data/tickers.txt` | Shared static universe for all scanners (edit manually) |
| `data/output/breakout_scan_results.csv` | Ranked summary table |
| `data/output/breakout_scan_report.json` | Full per-ticker breakout analysis (dashboard input) |
| `data/output/breakout_scan_summary.md` | Human-readable breakout summary |
| `data/output/swing_scan_results.csv` | Swing pullback ranked table |
| `data/output/swing_scan_report.json` | Full per-ticker swing analysis (dashboard input) |
| `data/output/swing_scan_summary.md` | Human-readable swing summary |
| `data/output/lynch_scan_results.csv` | Peter Lynch screen results |
| `data/output/lynch_scan_report.json` | Lynch scan detail (with `--report`) |
| `data/history/YYYY-MM-DD/` | Daily archive (breakout, swing, and/or Lynch CSV, JSON, MD, log, summary) |
| `data/history/scan_index.csv` | Index of archived breakout scans |
| `data/history/lynch_scan_index.csv` | Index of archived Lynch scans |
| `data/scan_history.duckdb` | Per-ticker score history for breakout, swing, and Lynch (`strategy_id` key) |
| `logs/scan.log` | Runtime log |

**Note:** Without `--archive`, only `data/output/` is updated (latest scan overwrites previous). JSON per day is stored only when archiving is enabled.

## Docker (daily 5 PM scan + email)

```bash
cp .env.example .env
docker compose up -d
docker compose run --rm scanner scan   # optional: run now
```

## Interpreting results

### Breakout tiers

| Tier | Meaning |
|------|---------|
| Tier 1 | Breakout ready — high score with compression and volume confirmation |
| Tier 2 | Watchlist — score 65–79, or high score missing Tier 1 criteria |
| Tier 3 | Below watchlist threshold (score under 65) |
| filtered | Failed eligibility (trend, liquidity, price, etc.) — may still show component scores in JSON/dashboard |

### Swing tiers

| Tier | Meaning |
|------|---------|
| A | Strong pullback setup (final score ≥ 80) |
| B | Watchlist (final score 65–79) |
| C | Eligible but lower score |
| filtered | Failed swing eligibility filters |

Sort by `final_adjusted_score` descending. See **[USER_MANUAL.md](USER_MANUAL.md)** for scoring formulas, dashboard usage, history, and troubleshooting.

## Project structure

```
quant-platform/
  src/quant_platform/   # Python package (scanners, dashboard, scoring)
  data/                 # tickers.txt (config) + output/ + history/ (generated)
  tests/                # unit + integration
  docker/               # scheduled scan container
  logs/                 # scan logs
```

See **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** for the full layout: every module, data lifecycle, entry points, and conventions.

## Development

```bash
pytest                  # unit tests (no network)
pytest -m integration   # live yfinance tests
ruff check src tests
```

## Documentation

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** — folder layout, modules, data flow, conventions
- **[USER_MANUAL.md](USER_MANUAL.md)** — installation, CLI, outputs, scoring, dashboard, history, email, Docker
- **[Agent.md](Agent.md)** — original strategy specification

## License

Internal / project use. See repository for license terms.
