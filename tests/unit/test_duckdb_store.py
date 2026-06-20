import json
from datetime import date, datetime

from quant_platform.history.archive import archive_scan_outputs
from quant_platform.history.duckdb_store import (
    backfill_from_archives,
    get_ticker_history,
    insert_scan_report,
    list_scan_dates,
    list_scans,
    upsert_scan_report,
)


def _sample_report(strategy_id: str = "breakout"):
    return {
        "strategy_id": strategy_id,
        "scan_summary": {
            "universe_size": 2,
            "eligible_count": 1,
            "excluded_count": 1,
            "tier_counts": {"Tier 1": 0, "Tier 2": 1, "Tier 3": 0, "filtered": 1},
            "filter_breakdown": {},
        },
        "market_regime": {"label": "strong", "multiplier": 1.0},
        "tickers": [
            {
                "ticker": "MU",
                "eligible": True,
                "tier": "Tier 2",
                "sector_etf": "SOXX",
                "eligibility": {"fail_reason": None},
                "summary": {
                    "raw_score": 72.0,
                    "normalized_score": 68.0,
                    "final_adjusted_score": 68.0,
                },
                "scores": {
                    "rs_market": {"score": 18.0, "max": 20},
                    "compression": {"score": 10.0, "max": 15},
                },
            },
            {
                "ticker": "XYZ",
                "eligible": False,
                "tier": "filtered",
                "eligibility": {"fail_reason": "trend_misaligned"},
                "summary": {
                    "raw_score": 0,
                    "normalized_score": 0,
                    "final_adjusted_score": 0,
                },
                "scores": None,
            },
        ],
    }


def _patch_paths(tmp_path, monkeypatch):
    history = tmp_path / "history"
    db = tmp_path / "scan_history.duckdb"
    monkeypatch.setattr("quant_platform.history.archive.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DB", db)
    monkeypatch.setattr("quant_platform.history.archive.INDEX_FILE", history / "scan_index.csv")
    monkeypatch.setattr("quant_platform.history.archive.LOG_DIR", tmp_path / "logs")
    return history, db


def test_insert_and_query_ticker_history(tmp_path, monkeypatch):
    _, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_report()

    insert_scan_report(
        report,
        scan_date=date(2026, 6, 6),
        scan_time=datetime(2026, 6, 6, 9, 0, 0),
    )
    assert db.exists()
    assert list_scan_dates() == ["2026-06-06"]
    assert len(list_scans()) == 1

    history = get_ticker_history("MU")
    assert len(history) == 1
    assert history[0]["final_score"] == 68.0
    assert history[0]["tier"] == "Tier 2"
    assert "scan_time" in history[0]

    report["tickers"][0]["summary"]["final_adjusted_score"] = 71.0
    insert_scan_report(
        report,
        scan_date=date(2026, 6, 6),
        scan_time=datetime(2026, 6, 6, 14, 0, 0),
    )
    history = get_ticker_history("MU")
    assert len(history) == 2
    assert history[0]["final_score"] == 71.0
    assert len(list_scans(strategy_id="breakout")) == 2


def test_multiple_strategies_same_day(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    day = date(2026, 6, 20)

    upsert_scan_report(
        _sample_report("breakout"),
        scan_date=day,
        scan_time=datetime(2026, 6, 20, 9, 0, 0),
    )
    upsert_scan_report(
        _sample_report("swing"),
        scan_date=day,
        scan_time=datetime(2026, 6, 20, 10, 0, 0),
    )

    assert len(list_scans()) == 2
    assert len(list_scans(strategy_id="breakout")) == 1
    assert len(list_scans(strategy_id="swing")) == 1


def test_archive_writes_json_and_duckdb(tmp_path, monkeypatch):
    history, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_report()
    csv_path = tmp_path / "results.csv"
    json_path = tmp_path / "report.json"
    csv_path.write_text("ticker,tier\nMU,Tier 2\n")
    json_path.write_text(json.dumps(report))

    archive_dir = archive_scan_outputs(
        csv_path=csv_path,
        json_path=json_path,
        scan_report=report,
        scan_date=date(2026, 6, 6),
    )

    assert (archive_dir / "breakout_scan_report.json").exists()
    assert db.exists()
    assert get_ticker_history("MU")[0]["final_score"] == 68.0


def test_insert_swing_tier_counts(tmp_path, monkeypatch):
    _, db = _patch_paths(tmp_path, monkeypatch)
    report = {
        "strategy_id": "swing",
        "scan_summary": {
            "universe_size": 3,
            "eligible_count": 2,
            "excluded_count": 1,
            "tier_counts": {"A": 1, "B": 1, "C": 0, "filtered": 1},
            "actionable_count": 2,
            "filter_breakdown": {},
        },
        "market_regime": {"label": "strong", "multiplier": 1.0},
        "tickers": [
            {
                "ticker": "AAA",
                "eligible": True,
                "tier": "A",
                "eligibility": {"fail_reason": None},
                "summary": {
                    "raw_score": 50.0,
                    "normalized_score": 83.0,
                    "final_adjusted_score": 83.0,
                },
                "scores": {"trend": {"score": 15.0, "max": 0}},
            }
        ],
    }

    insert_scan_report(
        report,
        scan_date=date(2026, 6, 20),
        scan_time=datetime(2026, 6, 20, 11, 0, 0),
    )
    assert db.exists()

    conn = __import__("duckdb").connect(str(db))
    try:
        row = conn.execute(
            """
            SELECT tier1_count, tier2_count, tier3_count, actionable_count, strategy_id
            FROM scans
            WHERE scan_date = ? AND strategy_id = ?
            """,
            ["2026-06-20", "swing"],
        ).fetchone()
    finally:
        conn.close()

    assert row == (1, 1, 0, 2, "swing")


def test_backfill_from_archives(tmp_path, monkeypatch):
    history, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_report()
    day1 = history / "2026-06-05"
    day2 = history / "2026-06-06"
    day1.mkdir(parents=True)
    day2.mkdir(parents=True)
    (day1 / "breakout_scan_report.json").write_text(json.dumps(report))
    report["tickers"][0]["summary"]["final_adjusted_score"] = 70.0
    (day2 / "breakout_scan_report.json").write_text(json.dumps(report))

    synced = backfill_from_archives()
    assert synced == 2
    assert db.exists()
    mu_history = get_ticker_history("MU", limit=10)
    assert len(mu_history) == 2
    scores = {row["scan_date"]: row["final_score"] for row in mu_history}
    assert scores["2026-06-05"] == 68.0
    assert scores["2026-06-06"] == 70.0
