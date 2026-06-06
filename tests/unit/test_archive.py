import json
from datetime import date
from pathlib import Path

from quant_platform.history.archive import archive_scan_outputs


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
                "tier": "Tier 2",
                "tier_reason": "watchlist",
                "summary": {"final_adjusted_score": 68.0},
            }
        ],
    }


def test_archive_creates_dated_folder(tmp_path: Path, monkeypatch):
    history = tmp_path / "history"
    monkeypatch.setattr("quant_platform.history.archive.HISTORY_DIR", history)
    monkeypatch.setattr("quant_platform.history.duckdb_store.HISTORY_DIR", history)
    monkeypatch.setattr(
        "quant_platform.history.duckdb_store.HISTORY_DB",
        tmp_path / "scan_history.duckdb",
    )
    index = history / "scan_index.csv"
    monkeypatch.setattr("quant_platform.history.archive.INDEX_FILE", index)
    monkeypatch.setattr("quant_platform.history.archive.LOG_DIR", tmp_path / "logs")

    csv_path = tmp_path / "results.csv"
    json_path = tmp_path / "report.json"
    csv_path.write_text("ticker,tier\nMU,Tier 2\n")
    json_path.write_text(json.dumps(_sample_report()))

    archive_dir = archive_scan_outputs(
        csv_path=csv_path,
        json_path=json_path,
        scan_report=_sample_report(),
        scan_date=date(2026, 6, 6),
    )

    assert archive_dir.name == "2026-06-06"
    assert (archive_dir / "breakout_scan_results.csv").exists()
    assert (archive_dir / "breakout_scan_report.json").exists()
    assert (archive_dir / "scan_summary.txt").exists()
    assert (tmp_path / "history" / "scan_index.csv").exists()
    assert "MU" in (archive_dir / "scan_summary.txt").read_text()
