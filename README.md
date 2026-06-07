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
- **Peter Lynch scanner** (`quant-lynch`) — PEG, growth, debt, neglect, and category presets
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

## Static ticker universe

Edit `data/tickers.txt` to define a shared watchlist for **all scanners** (`quant-scan`, `quant-lynch`, `quant-daily`). One symbol per line; lines starting with `#` are comments.

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

### `quant-view`

Requires `[viz]`. Loads breakout and Lynch reports from `data/output/` or archived days in the sidebar.

```bash
quant-scan --report both
quant-view
```

## Dashboard overview

| Tab | Purpose |
|-----|---------|
| **Full Universe** | Interactive scan table, filters, sort, and live ticker preview panel |
| **Overview** | Market regime, tier chart, exclusion breakdown, score distribution, heatmap, scatter |
| **Ticker Detail** | Fundamentals, technical scores, eligibility, live news, score history |
| **Actionable Watchlist** | Tier 1 and Tier 2 candidates with profile links |
| **Compare** | Side-by-side radar chart for 2–3 tickers |
| **Peter Lynch** | Lynch scan overview, candidates, checks, metrics, and archived history |

Blue ticker links (`?ticker=MU`) open the unified profile from anywhere in the app. Sidebar picker and filters apply across tabs.

## Output files

| File | Description |
|------|-------------|
| `data/tickers.txt` | Shared static universe for all scanners (edit manually) |
| `data/output/breakout_scan_results.csv` | Ranked summary table |
| `data/output/breakout_scan_report.json` | Full per-ticker analysis (dashboard input) |
| `data/output/breakout_scan_summary.md` | Human-readable summary |
| `data/output/lynch_scan_results.csv` | Peter Lynch screen results |
| `data/output/lynch_scan_report.json` | Lynch scan detail (with `--report`) |
| `data/history/YYYY-MM-DD/` | Daily archive (breakout and/or Lynch CSV, JSON, MD, log, summary) |
| `data/history/scan_index.csv` | Index of archived breakout scans |
| `data/history/lynch_scan_index.csv` | Index of archived Lynch scans |
| `data/scan_history.duckdb` | Per-ticker score history for breakout and Lynch (upserted on `--archive`) |
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
