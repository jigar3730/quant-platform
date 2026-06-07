# Project Structure

This document describes how **quant-platform** is organized: what lives where, what is source code vs generated data, and how the pieces connect.

## At a glance

```
quant-platform/
├── src/quant_platform/     # Application source (Python package)
├── data/                   # Runtime data (config + generated outputs)
├── tests/                  # Unit and integration tests
├── docker/                 # Scheduled scanner container
├── scripts/                # Repo maintenance helpers
├── .github/workflows/      # CI (pytest + ruff)
├── .devcontainer/          # VS Code / Cursor dev environment
├── README.md               # Quick start
├── USER_MANUAL.md          # Full user guide
├── Agent.md                # Original strategy specification (historical)
└── pyproject.toml          # Package metadata and CLI entry points
```

## Entry points

| Command | Module | Purpose |
|---------|--------|---------|
| `quant-scan` | `cli.py` | Breakout scanner |
| `quant-lynch` | `lynch/cli.py` | Peter Lynch scanner |
| `quant-daily` | `daily.py` | Scheduled breakout scan + archive + email |
| `quant-view` | `view.py` | Launches Streamlit dashboard |

All scanners share universe resolution via `data/tickers.py` (CLI → `data/tickers.txt` → Yahoo most-actives).

---

## Source package (`src/quant_platform/`)

### Root modules

| File | Role |
|------|------|
| `config.py` | Paths (`data/`, `logs/`), thresholds, sector maps, ticker file location |
| `cli.py` | `quant-scan` argument parsing and runner invocation |
| `daily.py` | `quant-daily` scheduled workflow |
| `view.py` | Subprocess launcher for Streamlit |
| `dashboard.py` | Streamlit app shell (tabs, report loading) |
| `logging_setup.py` | Shared logging config for all CLIs |
| `indicators.py` | SMA, returns, swing lows, 52-week range helpers |

### `data/` — market data layer

| File | Role |
|------|------|
| `fetch.py` | Download OHLCV and quarterly fundamentals (yfinance) |
| `cache.py` | Optional parquet cache for prices and fundamentals |
| `universe.py` | Dynamic universe (Yahoo most-actives screener) |
| `tickers.py` | Static ticker file loader + universe resolution |
| `sector.py` | Map ticker → sector ETF benchmark |
| `news.py` | Live news and price snapshot for dashboard |
| `fundamentals_helpers.py` | Shared quarterly series / CAGR helpers |

### `filters/` — pre-score eligibility

| File | Role |
|------|------|
| `eligibility.py` | Hard filters (liquidity, trend, 52-week range); `FILTER_LABELS` |

### `scoring/` — breakout signal components

| File | Role |
|------|------|
| `relative_strength.py` | RS vs SPY and vs sector |
| `volume.py` | Accumulation and relative volume |
| `volatility.py` | Bollinger compression and pattern quality |
| `resistance.py` | Proximity to resistance |
| `fundamentals.py` | Revenue and EPS growth scores |
| `aggregate.py` | Normalization, regime multiplier, tier assignment |

### `regime/` — market context

| File | Role |
|------|------|
| `market.py` | SPY regime (strong / neutral / weak) and multiplier |

### `report/` — breakout report builder

| File | Role |
|------|------|
| `builder.py` | Assemble per-ticker JSON report structure |
| `diagnostics.py` | Human-readable score explanations |
| `export.py` | Write JSON and Markdown files |

### `pipeline/` — breakout orchestration

| File | Role |
|------|------|
| `runner.py` | End-to-end breakout scan: fetch → filter → score → export → archive |

### `lynch/` — Peter Lynch scanner (parallel stack)

| File | Role |
|------|------|
| `cli.py` | `quant-lynch` CLI |
| `config.py` | Lynch thresholds and preset definitions |
| `metrics.py` | Fetch Lynch fundamentals (parallel yfinance) |
| `filters.py` | Base screen and anti-filters |
| `categories.py` | Fast grower / stalwart / asset play classification |
| `runner.py` | Lynch scan pipeline |
| `report.py` | Lynch JSON / Markdown export |

### `history/` — persistence

| File | Role |
|------|------|
| `common.py` | Shared archive helpers (copy files, CSV index) |
| `archive.py` | Breakout daily archive → `data/history/YYYY-MM-DD/` |
| `lynch_archive.py` | Lynch daily archive |
| `duckdb_store.py` | Score history DB (`scans`, `ticker_scores`, `lynch_*` tables) |

### `notify/` — alerts

| File | Role |
|------|------|
| `email.py` | SMTP email for Tier 1 + Tier 2 tickers |

### `viz/` — Streamlit dashboard

| File / dir | Role |
|------------|------|
| `dashboard.py` | *(parent)* Tab routing and report loading |
| `sidebar.py` | Report pickers, filters, ticker picker |
| `pages/breakout.py` | Breakout tab renderers (overview, universe, watchlist, compare) |
| `universe_panel.py` | Interactive Full Universe table + detail panel |
| `components.py` | Charts, ticker detail, news panel |
| `data.py` | Load JSON reports → DataFrames |
| `breakout_filters.py` | Sidebar filter application |
| `lynch_data.py` | Lynch report loaders |
| `lynch_components.py` | Peter Lynch tab UI |
| `navigation.py` | `?ticker=` URL query param bridge |
| `styles.py` | CSS and chart layout defaults |
| `display.py` | Arrow-safe value formatting for tables |
| `validation.py` | Detect synthetic / dry-run SPY data |

---

## Data directory (`data/`)

### Source-controlled (you edit these)

| Path | Purpose |
|------|---------|
| `data/tickers.txt` | **Shared static universe** for all scanners (one symbol per line) |
| `data/tickers.json` | Optional JSON alternative: `{"tickers": ["AAPL", ...]}` |
| `data/.gitkeep` | Keeps directory in git |

### Generated (gitignored — recreated by scans)

| Path | Purpose |
|------|---------|
| `data/output/` | **Latest** scan results (overwritten each run) |
| `data/output/dry_run/` | Isolated output from `--dry-run` (does not clobber latest) |
| `data/history/YYYY-MM-DD/` | **Archived** daily snapshots (with `--archive`) |
| `data/history/scan_index.csv` | Breakout archive index |
| `data/history/lynch_scan_index.csv` | Lynch archive index |
| `data/scan_history.duckdb` | Per-ticker score trends |
| `data/cache/` | Optional parquet price/fundamental cache |

### Output file naming

| Scanner | Latest (`data/output/`) | Archive (`data/history/YYYY-MM-DD/`) |
|---------|-------------------------|--------------------------------------|
| Breakout | `breakout_scan_results.csv`, `breakout_scan_report.json`, `breakout_scan_summary.md` | Same filenames + `scan.log`, `scan_summary.txt` |
| Lynch | `lynch_scan_results.csv`, `lynch_scan_report.json`, `lynch_scan_summary.md` | Same filenames + `lynch_scan.log`, `lynch_scan_summary.txt` |

**Flow:**

```
quant-scan / quant-lynch
        │
        ▼
  data/output/          ← always updated (latest only)
        │
        │  --archive
        ▼
  data/history/YYYY-MM-DD/  +  scan_history.duckdb
```

---

## Logs (`logs/`)

| File | Written by |
|------|------------|
| `scan.log` | `quant-scan`, `quant-daily` |
| `lynch_scan.log` | `quant-lynch` |

Archived copies land in `data/history/YYYY-MM-DD/` when using `--archive`.

---

## Tests (`tests/`)

| Directory | Contents |
|-----------|----------|
| `tests/unit/` | Fast tests, no network (scoring, filters, archive, viz helpers, Lynch logic) |
| `tests/integration/` | Live yfinance tests (`-m integration`) |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/helpers.py` | Test utilities |

Run: `pytest` (unit only by default) · `pytest -m integration` (network)

---

## Infrastructure

| Path | Purpose |
|------|---------|
| `docker/` | Scanner image, cron (5 PM ET), entrypoint |
| `docker-compose.yml` | Compose service for scheduled scans |
| `.env.example` | SMTP and email template variables |
| `.devcontainer/` | Dev container with `[dev,viz]` extras |
| `.github/workflows/ci.yml` | Ruff + pytest on push/PR |
| `scripts/push-to-github.sh` | One-time remote push helper |

---

## Dependency layers

```
                    ┌─────────────┐
                    │  quant-view │  Streamlit dashboard
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌──────────┐
   │ quant-scan  │  │ quant-lynch │  │quant-daily│
   └──────┬──────┘  └──────┬──────┘  └────┬─────┘
          │                │               │
          ▼                ▼               ▼
   pipeline/runner   lynch/runner    pipeline/runner
          │                │               │
          └────────┬───────┴───────────────┘
                   ▼
            data/ + scoring/ + filters/
                   │
                   ▼
            history/ + notify/
```

**Shared:** `config.py`, `data/tickers.py`, `data/fetch.py`, `logging_setup.py`, `history/duckdb_store.py`

**Separate:** Lynch and breakout each have their own runner, CLI, archive module, and viz tab — same patterns, not yet unified into one framework.

---

## Documentation map

| Document | Audience | Contents |
|----------|----------|----------|
| [README.md](README.md) | New users | Install, quick start, CLI flags |
| [USER_MANUAL.md](USER_MANUAL.md) | Operators | Scoring formulas, dashboard, Docker, troubleshooting |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Developers | This file — layout and module roles |
| [Agent.md](Agent.md) | Reference | Original MVP strategy spec (predates dashboard/history) |

---

## Conventions

- **Package layout:** `src/quant_platform/` (Hatch wheel in `pyproject.toml`)
- **Config:** Central paths in `config.py`; scanner-specific thresholds in `lynch/config.py`
- **No secrets in repo:** `.env` gitignored; use `.env.example` as template
- **Generated data never committed:** see `.gitignore` under `data/` and `logs/`
