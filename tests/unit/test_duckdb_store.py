import json
from datetime import date
from pathlib import Path

from quant_platform.history.archive import archive_scan_outputs
from quant_platform.history.duckdb_store import (
    backfill_from_archives,
    get_ticker_history,
    list_scan_dates,
    upsert_scan_report,
)


def _sample_report():
    return {
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


def _patch_paths(tmp_path: Path, monkeypatch):
    history = tmp_path / "history"
    db = tmp_path / "scan_history.duckdb"
    monkeypatch.setattr("quant_platform.history.archive.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DB", db)
    monkeypatch.setattr("quant_platform.history.archive.INDEX_FILE", history / "scan_index.csv")
    monkeypatch.setattr("quant_platform.history.archive.LOG_DIR", tmp_path / "logs")
    return history, db


def test_upsert_and_query_ticker_history(tmp_path: Path, monkeypatch):
    _, db = _patch_paths(tmp_path, monkeypatch)
    report = _sample_report()

    upsert_scan_report(report, scan_date=date(2026, 6, 6))
    assert db.exists()
    assert list_scan_dates() == ["2026-06-06"]

    history = get_ticker_history("MU")
    assert len(history) == 1
    assert history[0]["final_score"] == 68.0
    assert history[0]["tier"] == "Tier 2"

    report["tickers"][0]["summary"]["final_adjusted_score"] = 71.0
    upsert_scan_report(report, scan_date=date(2026, 6, 6))
    history = get_ticker_history("MU")
    assert history[0]["final_score"] == 71.0
    assert list_scan_dates() == ["2026-06-06"]


def test_upsert_scan_report_handles_swing_tiers(tmp_path: Path, monkeypatch):
    _, db = _patch_paths(tmp_path, monkeypatch)
    report = {
        "strategy_id": "swing",
        "scan_summary": {
            "universe_size": 2,
            "eligible_count": 1,
            "excluded_count": 1,
            "tier_counts": {"A": 1, "B": 0, "C": 0, "filtered": 1},
            "filter_breakdown": {},
            "actionable_count": 1,
        },
        "market_regime": {"label": "strong", "multiplier": 1.0},
        "tickers": [
            {
                "ticker": "MU",
                "eligible": True,
                "tier": "A",
                "sector_etf": "SOXX",
                "eligibility": {"fail_reason": None},
                "summary": {
                    "raw_score": 82.0,
                    "normalized_score": 78.0,
                    "final_adjusted_score": 82.0,
                },
                "scores": None,
            },
            {
                "ticker": "XYZ",
                "eligible": False,
                "tier": "filtered",
                "sector_etf": None,
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

    upsert_scan_report(report, scan_date=date(2026, 6, 6))
    assert db.exists()
    assert list_scan_dates() == ["2026-06-06"]
    swing_history = get_ticker_history("MU")
    assert len(swing_history) == 1
    assert swing_history[0]["tier"] == "A"


def test_archive_writes_json_and_duckdb(tmp_path: Path, monkeypatch):
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


def test_backfill_from_archives(tmp_path: Path, monkeypatch):
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
