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


def _connect() -> duckdb.DuckDBPyConnection:
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(HISTORY_DB))
    conn.execute(_SCHEMA_SQL)
    return conn


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
    scan_key = scan_date.isoformat()

    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM component_scores WHERE scan_date = ?", [scan_key])
        conn.execute("DELETE FROM ticker_scores WHERE scan_date = ?", [scan_key])
        conn.execute("DELETE FROM scans WHERE scan_date = ?", [scan_key])

        conn.execute(
            """
            INSERT INTO scans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_key,
                datetime.now().isoformat(timespec="seconds"),
                summary["universe_size"],
                summary["eligible_count"],
                summary.get("excluded_count", 0),
                tiers["Tier 1"],
                tiers["Tier 2"],
                tiers["Tier 3"],
                tiers["filtered"],
                tiers["Tier 1"] + tiers["Tier 2"],
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
                INSERT INTO ticker_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ],
            )
            scores = t.get("scores") or {}
            for component, comp in scores.items():
                conn.execute(
                    """
                    INSERT INTO component_scores VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        scan_key,
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


def backfill_from_archives() -> int:
    """Load all archived JSON reports into DuckDB. Returns count synced."""
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
