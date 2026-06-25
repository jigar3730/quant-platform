"""DuckDB store for scan history (additive to JSON archives)."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import duckdb

from quant_platform.config import HISTORY_DB, HISTORY_DIR

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    scan_date DATE PRIMARY KEY,
    scan_time TIMESTAMP,
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
    json_path VARCHAR
);

CREATE TABLE IF NOT EXISTS ticker_scores (
    scan_date DATE,
    ticker VARCHAR,
    eligible BOOLEAN,
    tier VARCHAR,
    sector_etf VARCHAR,
    raw_score DOUBLE,
    normalized_score DOUBLE,
    final_score DOUBLE,
    filter_reason VARCHAR,
    PRIMARY KEY (scan_date, ticker)
);

CREATE TABLE IF NOT EXISTS component_scores (
    scan_date DATE,
    ticker VARCHAR,
    component VARCHAR,
    score DOUBLE,
    max_score DOUBLE,
    PRIMARY KEY (scan_date, ticker, component)
);
"""

_LYNCH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS lynch_scans (
    scan_date DATE PRIMARY KEY,
    scan_time TIMESTAMP,
    preset VARCHAR,
    universe_size INTEGER,
    passed_count INTEGER,
    fast_grower_count INTEGER,
    stalwart_count INTEGER,
    asset_play_count INTEGER,
    archive_dir VARCHAR,
    json_path VARCHAR
);

CREATE TABLE IF NOT EXISTS lynch_ticker_scores (
    scan_date DATE,
    ticker VARCHAR,
    passed BOOLEAN,
    lynch_score DOUBLE,
    categories VARCHAR,
    pe_ratio DOUBLE,
    peg_ratio DOUBLE,
    eps_growth_5y DOUBLE,
    debt_to_equity DOUBLE,
    institutional_pct DOUBLE,
    analyst_count INTEGER,
    PRIMARY KEY (scan_date, ticker)
);
"""


def _connect() -> duckdb.DuckDBPyConnection:
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(HISTORY_DB))
    conn.execute(_SCHEMA_SQL)
    conn.execute(_LYNCH_SCHEMA_SQL)
    _ensure_strategy_id_columns(conn)
    return conn


def _ensure_strategy_id_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Add strategy_id to existing tables (nullable, default breakout)."""
    for table in ("scans", "ticker_scores", "component_scores"):
        cols = {row[0] for row in conn.execute(f"DESCRIBE {table}").fetchall()}
        if "strategy_id" not in cols:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN strategy_id VARCHAR DEFAULT 'breakout'"
            )


def upsert_scan_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
) -> None:
    """Insert or replace one day's scan into DuckDB."""
    summary = report["scan_summary"]
    regime = report["market_regime"]
    tiers = summary["tier_counts"]
    strategy_id = report.get("strategy_id", "breakout")
    scan_key = scan_date.isoformat()

    if strategy_id == "swing":
        tier1 = tiers.get("A", 0)
        tier2 = tiers.get("B", 0)
        tier3 = tiers.get("C", 0)
    else:
        tier1 = tiers.get("Tier 1", 0)
        tier2 = tiers.get("Tier 2", 0)
        tier3 = tiers.get("Tier 3", 0)
    actionable = summary.get("actionable_count", tier1 + tier2)

    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute(
            "DELETE FROM component_scores WHERE scan_date = ? AND strategy_id = ?",
            [scan_key, strategy_id],
        )
        conn.execute(
            "DELETE FROM ticker_scores WHERE scan_date = ? AND strategy_id = ?",
            [scan_key, strategy_id],
        )
        conn.execute(
            "DELETE FROM scans WHERE scan_date = ? AND strategy_id = ?",
            [scan_key, strategy_id],
        )

        conn.execute(
            """
            INSERT INTO scans (
                scan_date, scan_time, universe_size, eligible_count, excluded_count,
                tier1_count, tier2_count, tier3_count, filtered_count, actionable_count,
                regime, regime_multiplier, archive_dir, json_path, strategy_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_key,
                datetime.now().isoformat(timespec="seconds"),
                summary["universe_size"],
                summary["eligible_count"],
                summary.get("excluded_count", 0),
                tier1,
                tier2,
                tier3,
                tiers.get("filtered", 0),
                actionable,
                regime["label"],
                regime["multiplier"],
                str(archive_dir) if archive_dir else None,
                str(json_path) if json_path else None,
                strategy_id,
            ],
        )

        for t in report["tickers"]:
            s = t.get("summary") or {}
            elig = t.get("eligibility") or {}
            conn.execute(
                """
                INSERT INTO ticker_scores (
                    scan_date, ticker, eligible, tier, sector_etf,
                    raw_score, normalized_score, final_score, filter_reason, strategy_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    scan_key,
                    t["ticker"],
                    bool(t.get("eligible")),
                    t.get("tier", "filtered"),
                    t.get("sector_etf"),
                    s.get("raw_score", 0),
                    s.get("normalized_score", 0),
                    s.get("final_adjusted_score", 0),
                    elig.get("fail_reason"),
                    strategy_id,
                ],
            )
            scores = t.get("scores") or {}
            for component, comp in scores.items():
                conn.execute(
                    """
                    INSERT INTO component_scores (
                        scan_date, ticker, component, score, max_score, strategy_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        scan_key,
                        t["ticker"],
                        component,
                        comp.get("score", 0),
                        comp.get("max", 0),
                        strategy_id,
                    ],
                )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def get_ticker_history(ticker: str, *, limit: int = 90) -> list[dict]:
    """Return score history for a ticker, newest first."""
    if not HISTORY_DB.exists():
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT scan_date, tier, eligible, final_score, normalized_score,
                   raw_score, sector_etf
            FROM ticker_scores
            WHERE ticker = ?
            ORDER BY scan_date DESC
            LIMIT ?
            """,
            [ticker.upper(), limit],
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "scan_date": str(r[0]),
            "tier": r[1],
            "eligible": r[2],
            "final_score": r[3],
            "normalized_score": r[4],
            "raw_score": r[5],
            "sector_etf": r[6],
        }
        for r in rows
    ]


def list_scan_dates() -> list[str]:
    if not HISTORY_DB.exists():
        return []
    conn = _connect()
    try:
        rows = conn.execute("SELECT scan_date FROM scans ORDER BY scan_date DESC").fetchall()
    finally:
        conn.close()
    return [str(r[0]) for r in rows]


def upsert_lynch_report(
    report: dict,
    *,
    scan_date: date,
    archive_dir: Path | None = None,
    json_path: Path | None = None,
) -> None:
    """Insert or replace one day's Lynch scan into DuckDB."""
    summary = report["scan_summary"]
    cats = summary["category_counts"]
    scan_key = scan_date.isoformat()

    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM lynch_ticker_scores WHERE scan_date = ?", [scan_key])
        conn.execute("DELETE FROM lynch_scans WHERE scan_date = ?", [scan_key])

        conn.execute(
            """
            INSERT INTO lynch_scans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_key,
                datetime.now().isoformat(timespec="seconds"),
                summary["preset"],
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
                INSERT INTO lynch_ticker_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    scan_key,
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


def get_lynch_ticker_history(ticker: str, *, limit: int = 90) -> list[dict]:
    if not HISTORY_DB.exists():
        return []
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT scan_date, passed, lynch_score, categories, peg_ratio, pe_ratio
            FROM lynch_ticker_scores
            WHERE ticker = ?
            ORDER BY scan_date DESC
            LIMIT ?
            """,
            [ticker.upper(), limit],
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "scan_date": str(r[0]),
            "passed": r[1],
            "lynch_score": r[2],
            "categories": r[3],
            "peg_ratio": r[4],
            "pe_ratio": r[5],
        }
        for r in rows
    ]


def backfill_from_archives() -> int:
    """Load archived breakout JSON reports into DuckDB."""
    paths = sorted(HISTORY_DIR.glob("*/breakout_scan_report.json"))
    synced = 0
    for path in paths:
        try:
            scan_date = date.fromisoformat(path.parent.name)
        except ValueError:
            continue
        report = json.loads(path.read_text())
        upsert_scan_report(
            report,
            scan_date=scan_date,
            archive_dir=path.parent,
            json_path=path,
        )
        synced += 1
    return synced


def backfill_lynch_from_archives() -> int:
    """Load archived Lynch JSON reports into DuckDB."""
    paths = sorted(HISTORY_DIR.glob("*/lynch_scan_report.json"))
    synced = 0
    for path in paths:
        try:
            scan_date = date.fromisoformat(path.parent.name)
        except ValueError:
            continue
        report = json.loads(path.read_text())
        upsert_lynch_report(
            report,
            scan_date=scan_date,
            archive_dir=path.parent,
            json_path=path,
        )
        synced += 1
    return synced
