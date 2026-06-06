from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd

from quant_platform.config import CACHE_DIR, CACHE_TTL_HOURS


def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.parquet"


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(tz=UTC) - mtime < timedelta(hours=CACHE_TTL_HOURS)


def read_prices_cache(tickers: list[str], use_cache: bool) -> pd.DataFrame | None:
    path = _cache_path("prices")
    if not use_cache or not _is_fresh(path):
        return None
    conn = duckdb.connect()
    try:
        df = conn.execute(
            "SELECT * FROM read_parquet(?) WHERE ticker IN ?",
            [str(path), tickers],
        ).df()
        if df.empty:
            return None
        return df
    finally:
        conn.close()


def write_prices_cache(df: pd.DataFrame) -> None:
    path = _cache_path("prices")
    df.to_parquet(path, index=False)


def read_fundamentals_cache(tickers: list[str], use_cache: bool) -> pd.DataFrame | None:
    path = _cache_path("fundamentals")
    if not use_cache or not _is_fresh(path):
        return None
    conn = duckdb.connect()
    try:
        df = conn.execute(
            "SELECT * FROM read_parquet(?) WHERE ticker IN ?",
            [str(path), tickers],
        ).df()
        if df.empty:
            return None
        return df
    finally:
        conn.close()


def write_fundamentals_cache(df: pd.DataFrame) -> None:
    path = _cache_path("fundamentals")
    df.to_parquet(path, index=False)
