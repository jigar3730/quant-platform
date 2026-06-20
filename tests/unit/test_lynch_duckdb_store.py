import json
from datetime import date, datetime

from quant_platform.history.duckdb_store import (
    backfill_lynch_from_archives,
    get_lynch_ticker_history,
    insert_lynch_report,
    upsert_lynch_report,
)


def _sample_lynch_report() -> dict:
    return {
        "scan_summary": {
            "scanner": "peter_lynch",
            "preset": "summary",
            "preset_label": "Full Lynch Scan",
            "universe_size": 1,
            "passed_count": 1,
            "category_counts": {"fast_grower": 1, "stalwart": 0, "asset_play": 0},
        },
        "tickers": [
            {
                "ticker": "MU",
                "passed": True,
                "categories": ["fast_grower"],
                "lynch_score": 88.0,
                "pe_ratio": 15.0,
                "peg_ratio": 0.9,
                "debt_to_equity": 0.2,
                "institutional_pct": 30.0,
                "analyst_count": 3,
                "metrics": {"eps_growth_5y": 0.2},
            }
        ],
        "candidates": [],
    }


def _patch_paths(tmp_path, monkeypatch):
    history = tmp_path / "history"
    db = tmp_path / "scan_history.duckdb"
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DB", db)
    return history, db


def test_insert_and_query_lynch_ticker_history(tmp_path, monkeypatch):
    _, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_lynch_report()

    insert_lynch_report(
        report,
        scan_date=date(2026, 6, 6),
        scan_time=datetime(2026, 6, 6, 9, 0, 0),
    )
    assert db.exists()

    history = get_lynch_ticker_history("MU")
    assert len(history) == 1
    assert history[0]["lynch_score"] == 88.0
    assert history[0]["passed"] is True
    assert "scan_time" in history[0]

    report["tickers"][0]["lynch_score"] = 92.0
    upsert_lynch_report(
        report,
        scan_date=date(2026, 6, 6),
        scan_time=datetime(2026, 6, 6, 15, 0, 0),
    )
    history = get_lynch_ticker_history("MU")
    assert len(history) == 2
    assert history[0]["lynch_score"] == 92.0


def test_backfill_lynch_from_archives(tmp_path, monkeypatch):
    history, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_lynch_report()
    day1 = history / "2026-06-05"
    day2 = history / "2026-06-06"
    day1.mkdir(parents=True)
    day2.mkdir(parents=True)
    (day1 / "lynch_scan_report.json").write_text(json.dumps(report))
    report["tickers"][0]["lynch_score"] = 90.0
    (day2 / "lynch_scan_report.json").write_text(json.dumps(report))

    synced = backfill_lynch_from_archives()
    assert synced == 2
    assert db.exists()
    mu_history = get_lynch_ticker_history("MU", limit=10)
    assert len(mu_history) == 2
    scores = {row["scan_date"]: row["lynch_score"] for row in mu_history}
    assert scores["2026-06-05"] == 88.0
    assert scores["2026-06-06"] == 90.0
