"""DuckDB store for scan history (additive to JSON archives)."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import duckdb

from quant_platform.config import HISTORY_DB, HISTORY_DIR

SCHEMA_VERSION = 2

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key VARCHAR PRIMARY KEY,
    value INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    scan_date DATE NOT NULL,
    strategy_id VARCHAR NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    universe_size INTEGER,
    eligible_count INTEGER,
    excluded_count INTEGER,
    tier1_count INTEGER,
    tier2_count INTEGER,
    tier3_count INTEGER,
    filtered_count INTEGER,
    actionable_count INTEGER,
    regime VARCHAR,
    regime_multiplier DOUBLE,
    archive_dir VARCHAR,
    json_path VARCHAR,
    PRIMARY KEY (scan_date, strategy_id, scan_time)
);

CREATE TABLE IF NOT EXISTS ticker_scores (
    scan_date DATE NOT NULL,
    strategy_id VARCHAR NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    ticker VARCHAR NOT NULL,
    eligible BOOLEAN,
    tier VARCHAR,
    sector_etf VARCHAR,
    raw_score DOUBLE,
    normalized_score DOUBLE,
    final_score DOUBLE,
    filter_reason VARCHAR,
    PRIMARY KEY (scan_date, strategy_id, scan_time, ticker)
);

CREATE TABLE IF NOT EXISTS component_scores (
    scan_date DATE NOT NULL,
    strategy_id VARCHAR NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    ticker VARCHAR NOT NULL,
    component VARCHAR NOT NULL,
    score DOUBLE,
    max_score DOUBLE,
    PRIMARY KEY (scan_date, strategy_id, scan_time, ticker, component)
);
"""

_LYNCH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS lynch_scans (
    scan_date DATE NOT NULL,
    preset VARCHAR NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    universe_size INTEGER,
    passed_count INTEGER,
    fast_grower_count INTEGER,
    stalwart_count INTEGER,
    asset_play_count INTEGER,
    archive_dir VARCHAR,
    json_path VARCHAR,
    PRIMARY KEY (scan_date, preset, scan_time)
);

CREATE TABLE IF NOT EXISTS lynch_ticker_scores (
    scan_date DATE NOT NULL,
    preset VARCHAR NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    ticker VARCHAR NOT NULL,
    passed BOOLEAN,
    lynch_score DOUBLE,
    categories VARCHAR,
    pe_ratio DOUBLE,
    peg_ratio DOUBLE,
    eps_growth_5y DOUBLE,
    debt_to_equity DOUBLE,
    institutional_pct DOUBLE,
    analyst_count INTEGER,
    PRIMARY KEY (scan_date, preset, scan_time, ticker)
);
"""

_DROP_TABLES_SQL = """
DROP TABLE IF EXISTS component_scores;
DROP TABLE IF EXISTS ticker_scores;
DROP TABLE IF EXISTS scans;
DROP TABLE IF EXISTS lynch_ticker_scores;
DROP TABLE IF EXISTS lynch_scans;
DROP TABLE IF EXISTS schema_meta;
"""


def _scan_timestamp(scan_time: datetime | None = None) -> datetime:
    return scan_time or datetime.now().replace(microsecond=0)


def _connect() -> duckdb.DuckDBPyConnection:
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(HISTORY_DB))
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    version = None
    try:
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        ).fetchone()
        if row:
            version = row[0]
    except duckdb.CatalogException:
        version = None

    if version != SCHEMA_VERSION:
        conn.execute(_DROP_TABLES_SQL)
        conn.execute(_SCHEMA_SQL)
        conn.execute(_LYNCH_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO schema_meta (key, value) VALUES ('version', ?)",
            [SCHEMA_VERSION],
        )


def _normalized_tier_counts(tiers: dict, strategy_id: str) -> tuple[int, int, int, int, int]:
    """Map strategy-specific tier labels into scans table columns."""
    filtered = tiers.get("filtered", 0)
    if strategy_id == "swing":
        tier1 = tiers.get("A", 0)
        tier2 = tiers.get("B", 0)
        tier3 = tiers.get("C", 0)
    else:
        tier1 = tiers.get("Tier 1", 0)
        tier2 = tiers.get("Tier 2", 0)
        tier3 = tiers.get("Tier 3", 0)
    actionable = tier1 + tier2
    return tier1, tier2, tier3, filtered, actionable


def insert_scan_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
    scan_time: datetime | None = None,
) -> datetime:
    """Append one scan run to DuckDB (multiple runs per day/strategy allowed)."""
    summary = report["scan_summary"]
    regime = report["market_regime"]
    tiers = summary["tier_counts"]
    strategy_id = report.get("strategy_id", "breakout")
    tier1, tier2, tier3, filtered, actionable = _normalized_tier_counts(tiers, strategy_id)
    actionable = summary.get("actionable_count", actionable)
    scan_key = scan_date.isoformat()
    run_time = _scan_timestamp(scan_time)

    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO scans (
                scan_date, strategy_id, scan_time, universe_size, eligible_count,
                excluded_count, tier1_count, tier2_count, tier3_count, filtered_count,
                actionable_count, regime, regime_multiplier, archive_dir, json_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_key,
                strategy_id,
                run_time.isoformat(sep=" ", timespec="seconds"),
                summary["universe_size"],
                summary["eligible_count"],
                summary.get("excluded_count", 0),
                tier1,
                tier2,
                tier3,
                filtered,
                actionable,
                regime["label"],
                regime["multiplier"],
                str(archive_dir) if archive_dir else None,
                str(json_path) if json_path else None,
            ],
        )

        for t in report["tickers"]:
            s = t.get("summary") or {}
            elig = t.get("eligibility") or {}
            conn.execute(
                """
                INSERT INTO ticker_scores (
                    scan_date, strategy_id, scan_time, ticker, eligible, tier, sector_etf,
                    raw_score, normalized_score, final_score, filter_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    scan_key,
                    strategy_id,
                    run_time.isoformat(sep=" ", timespec="seconds"),
                    t["ticker"],
                    bool(t.get("eligible")),
                    t.get("tier", "filtered"),
                    t.get("sector_etf"),
                    s.get("raw_score", 0),
                    s.get("normalized_score", 0),
                    s.get("final_adjusted_score", 0),
                    elig.get("fail_reason"),
                ],
            )
            scores = t.get("scores") or {}
            for component, comp in scores.items():
                conn.execute(
                    """
                    INSERT INTO component_scores (
                        scan_date, strategy_id, scan_time, ticker, component,
                        score, max_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        scan_key,
                        strategy_id,
                        run_time.isoformat(sep=" ", timespec="seconds"),
                        t["ticker"],
                        component,
                        comp.get("score", 0),
                        comp.get("max", 0),
                    ],
                )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    return run_time


def upsert_scan_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
    scan_time: datetime | None = None,
) -> datetime:
    """Backward-compatible alias for insert_scan_report."""
    return insert_scan_report(
        report,
        scan_date=scan_date,
        archive_dir=archive_dir,
        json_path=json_path,
        scan_time=scan_time,
    )


def get_ticker_history(
    ticker: str,
    *,
    strategy_id: str = "breakout",
    limit: int = 90,
) -> list[dict]:
    """Return score history for a ticker and strategy, newest first."""
    if not HISTORY_DB.exists():
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT scan_date, scan_time, tier, eligible, final_score, normalized_score,
                   raw_score, sector_etf
            FROM ticker_scores
            WHERE ticker = ? AND strategy_id = ?
            ORDER BY scan_date DESC, scan_time DESC
            LIMIT ?
            """,
            [ticker.upper(), strategy_id, limit],
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "scan_date": str(r[0]),
            "scan_time": str(r[1]),
            "tier": r[2],
            "eligible": r[3],
            "final_score": r[4],
            "normalized_score": r[5],
            "raw_score": r[6],
            "sector_etf": r[7],
        }
        for r in rows
    ]


def list_scans(*, strategy_id: str | None = None) -> list[dict]:
    """List scan runs newest first, optionally filtered by strategy."""
    if not HISTORY_DB.exists():
        return []

    conn = _connect()
    try:
        if strategy_id:
            rows = conn.execute(
                """
                SELECT scan_date, strategy_id, scan_time, json_path, archive_dir
                FROM scans
                WHERE strategy_id = ?
                ORDER BY scan_date DESC, scan_time DESC
                """,
                [strategy_id],
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT scan_date, strategy_id, scan_time, json_path, archive_dir
                FROM scans
                ORDER BY scan_date DESC, scan_time DESC
                """
            ).fetchall()
    finally:
        conn.close()

    return [
        {
            "scan_date": str(r[0]),
            "strategy_id": r[1],
            "scan_time": str(r[2]),
            "json_path": r[3],
            "archive_dir": r[4],
        }
        for r in rows
    ]


def list_scan_dates(*, strategy_id: str | None = None) -> list[str]:
    """Distinct scan dates from stored runs, newest first."""
    scans = list_scans(strategy_id=strategy_id)
    seen: set[str] = set()
    dates: list[str] = []
    for row in scans:
        day = row["scan_date"]
        if day not in seen:
            seen.add(day)
            dates.append(day)
    return dates


def insert_lynch_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
    scan_time: datetime | None = None,
) -> datetime:
    """Append one Lynch scan run to DuckDB."""
    summary = report["scan_summary"]
    cats = summary["category_counts"]
    preset = summary["preset"]
    scan_key = scan_date.isoformat()
    run_time = _scan_timestamp(scan_time)

    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO lynch_scans (
                scan_date, preset, scan_time, universe_size, passed_count,
                fast_grower_count, stalwart_count, asset_play_count,
                archive_dir, json_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_key,
                preset,
                run_time.isoformat(sep=" ", timespec="seconds"),
                summary["universe_size"],
                summary["passed_count"],
                cats["fast_grower"],
                cats["stalwart"],
                cats["asset_play"],
                str(archive_dir) if archive_dir else None,
                str(json_path) if json_path else None,
            ],
        )

        for t in report["tickers"]:
            m = t.get("metrics") or {}
            cats_list = ",".join(t.get("categories", []))
            conn.execute(
                """
                INSERT INTO lynch_ticker_scores (
                    scan_date, preset, scan_time, ticker, passed, lynch_score,
                    categories, pe_ratio, peg_ratio, eps_growth_5y, debt_to_equity,
                    institutional_pct, analyst_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    scan_key,
                    preset,
                    run_time.isoformat(sep=" ", timespec="seconds"),
                    t["ticker"],
                    bool(t.get("passed")),
                    t.get("lynch_score", 0),
                    cats_list,
                    t.get("pe_ratio"),
                    t.get("peg_ratio"),
                    m.get("eps_growth_5y"),
                    t.get("debt_to_equity"),
                    t.get("institutional_pct"),
                    t.get("analyst_count"),
                ],
            )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    return run_time


def upsert_lynch_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
    scan_time: datetime | None = None,
) -> datetime:
    """Backward-compatible alias for insert_lynch_report."""
    return insert_lynch_report(
        report,
        scan_date=scan_date,
        archive_dir=archive_dir,
        json_path=json_path,
        scan_time=scan_time,
    )


def get_lynch_ticker_history(
    ticker: str,
    *,
    preset: str | None = None,
    limit: int = 90,
) -> list[dict]:
    if not HISTORY_DB.exists():
        return []
    conn = _connect()
    try:
        if preset:
            rows = conn.execute(
                """
                SELECT scan_date, scan_time, passed, lynch_score, categories,
                       peg_ratio, pe_ratio
                FROM lynch_ticker_scores
                WHERE ticker = ? AND preset = ?
                ORDER BY scan_date DESC, scan_time DESC
                LIMIT ?
                """,
                [ticker.upper(), preset, limit],
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT scan_date, scan_time, passed, lynch_score, categories,
                       peg_ratio, pe_ratio
                FROM lynch_ticker_scores
                WHERE ticker = ?
                ORDER BY scan_date DESC, scan_time DESC
                LIMIT ?
                """,
                [ticker.upper(), limit],
            ).fetchall()
    finally:
        conn.close()
    return [
        {
            "scan_date": str(r[0]),
            "scan_time": str(r[1]),
            "passed": r[2],
            "lynch_score": r[3],
            "categories": r[4],
            "peg_ratio": r[5],
            "pe_ratio": r[6],
        }
        for r in rows
    ]


def _backfill_scan_time(scan_date: date, index: int) -> datetime:
    """Assign distinct timestamps when backfilling one row per archive folder."""
    base = datetime.combine(scan_date, time(12, 0, 0))
    return base + timedelta(seconds=index)


def backfill_from_archives() -> int:
    """Load archived price-scanner JSON reports into DuckDB."""
    patterns = ("breakout_scan_report.json", "swing_scan_report.json")
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(HISTORY_DIR.glob(f"*/{pattern}")))

    synced = 0
    for index, path in enumerate(paths):
        try:
            scan_date = date.fromisoformat(path.parent.name)
        except ValueError:
            continue
        report = json.loads(path.read_text())
        insert_scan_report(
            report,
            scan_date=scan_date,
            archive_dir=path.parent,
            json_path=path,
            scan_time=_backfill_scan_time(scan_date, index),
        )
        synced += 1
    return synced


def backfill_lynch_from_archives() -> int:
    """Load archived Lynch JSON reports into DuckDB."""
    paths = sorted(HISTORY_DIR.glob("*/lynch_scan_report.json"))
    synced = 0
    for index, path in enumerate(paths):
        try:
            scan_date = date.fromisoformat(path.parent.name)
        except ValueError:
            continue
        report = json.loads(path.read_text())
        insert_lynch_report(
            report,
            scan_date=scan_date,
            archive_dir=path.parent,
            json_path=path,
            scan_time=_backfill_scan_time(scan_date, index),
        )
        synced += 1
    return synced
