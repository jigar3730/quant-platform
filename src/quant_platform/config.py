from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = DATA_DIR / "output"
HISTORY_DIR = DATA_DIR / "history"
HISTORY_DB = DATA_DIR / "scan_history.duckdb"
DEFAULT_OUTPUT_CSV = OUTPUT_DIR / "breakout_scan_results.csv"
DEFAULT_OUTPUT_JSON = OUTPUT_DIR / "breakout_scan_report.json"
DEFAULT_OUTPUT_MD = OUTPUT_DIR / "breakout_scan_summary.md"
DRY_RUN_OUTPUT_DIR = OUTPUT_DIR / "dry_run"
DEFAULT_DRY_RUN_CSV = DRY_RUN_OUTPUT_DIR / "breakout_scan_results.csv"
DEFAULT_DRY_RUN_JSON = DRY_RUN_OUTPUT_DIR / "breakout_scan_report.json"
DEFAULT_DRY_RUN_MD = DRY_RUN_OUTPUT_DIR / "breakout_scan_summary.md"
DEFAULT_LYNCH_CSV = OUTPUT_DIR / "lynch_scan_results.csv"
DEFAULT_LYNCH_JSON = OUTPUT_DIR / "lynch_scan_report.json"
DEFAULT_LYNCH_MD = OUTPUT_DIR / "lynch_scan_summary.md"
DEFAULT_SWING_CSV = OUTPUT_DIR / "swing_scan_results.csv"
DEFAULT_SWING_JSON = OUTPUT_DIR / "swing_scan_report.json"
DEFAULT_SWING_MD = OUTPUT_DIR / "swing_scan_summary.md"
DEFAULT_TICKERS_FILE = DATA_DIR / "tickers.txt"

UNIVERSE_SIZE = 15
LYNCH_FETCH_WORKERS = 8
MIN_TRADING_DAYS = 200
MIN_AVG_VOLUME = 750_000
MIN_PRICE = 10.0
MAX_REASONABLE_GROWTH = 3.0
PRICE_SPIKE_RATIO = 3.0
LOOKBACK_DAYS = 252
CACHE_TTL_HOURS = 24

BENCHMARK_TICKER = "SPY"
FALLBACK_SECTOR_ETF = "SPY"

# Industry takes precedence over sector when both match.
INDUSTRY_TO_ETF: dict[str, str] = {
    "Semiconductors": "SOXX",
    "Software - Infrastructure": "IGV",
    "Software - Application": "IGV",
    "Software": "IGV",
    "Internet Content & Information": "IGV",
    "Biotechnology": "XBI",
    "Banks - Regional": "KRE",
    "Banks - Diversified": "XLF",
    "Oil & Gas E&P": "XLE",
    "Oil & Gas Integrated": "XLE",
    "Aerospace & Defense": "ITA",
    "Utilities - Regulated Electric": "XLU",
    "REIT - Residential": "VNQ",
    "REIT - Industrial": "VNQ",
}

SECTOR_TO_ETF: dict[str, str] = {
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Real Estate": "VNQ",
    "Utilities": "XLU",
}

ALL_SECTOR_ETFS = sorted(set(SECTOR_TO_ETF.values()) | set(INDUSTRY_TO_ETF.values()))

# Fallback when yfinance screener is unavailable
FALLBACK_UNIVERSE = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "AVGO",
    "NFLX",
]

RAW_SCORE_MAX = 120
