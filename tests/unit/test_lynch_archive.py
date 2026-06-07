import json
from datetime import date

from quant_platform.history.lynch_archive import archive_lynch_outputs


def _sample_report() -> dict:
    return {
        "scan_summary": {
            "scanner": "peter_lynch",
            "preset": "summary",
            "preset_label": "Summary (all categories)",
            "universe_size": 2,
            "passed_count": 1,
            "category_counts": {"fast_grower": 1, "stalwart": 0, "asset_play": 0},
        },
        "qualitative_overlay": ["Know what you own"],
        "tickers": [
            {
                "ticker": "LYNCH",
                "passed": True,
                "categories": ["fast_grower"],
                "lynch_score": 95.0,
                "pe_ratio": 15.0,
                "peg_ratio": 0.8,
                "debt_to_equity": 0.2,
                "institutional_pct": 30.0,
                "analyst_count": 3,
                "tier_reason": "Lynch match: Fast Grower",
                "metrics": {"eps_growth_5y": 0.2},
                "checks": [{"label": "PEG", "passed": True}],
            },
            {
                "ticker": "FAIL",
                "passed": False,
                "categories": [],
                "lynch_score": 20.0,
                "pe_ratio": 50.0,
                "peg_ratio": 3.0,
                "debt_to_equity": 1.5,
                "institutional_pct": 80.0,
                "analyst_count": 20,
                "tier_reason": "",
                "metrics": {},
                "checks": [],
            },
        ],
        "candidates": [],
    }


def test_archive_lynch_outputs(tmp_path, monkeypatch):
    history_dir = tmp_path / "history"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    csv_path = output_dir / "lynch_scan_results.csv"
    json_path = output_dir / "lynch_scan_report.json"
    csv_path.write_text("ticker,passed\nLYNCH,True\n")
    report = _sample_report()
    json_path.write_text(json.dumps(report))

    monkeypatch.setattr("quant_platform.history.lynch_archive.HISTORY_DIR", history_dir)
    monkeypatch.setattr(
        "quant_platform.history.lynch_archive.LYNCH_INDEX_FILE",
        history_dir / "lynch_scan_index.csv",
    )
    monkeypatch.setattr(
        "quant_platform.history.lynch_archive.upsert_lynch_report",
        lambda *a, **k: None,
    )

    scan_date = date(2026, 6, 6)
    archive_dir = archive_lynch_outputs(
        csv_path=csv_path,
        json_path=json_path,
        scan_report=report,
        scan_date=scan_date,
    )

    assert archive_dir == history_dir / "2026-06-06"
    assert (archive_dir / "lynch_scan_results.csv").exists()
    assert (archive_dir / "lynch_scan_report.json").exists()
    assert (archive_dir / "lynch_scan_summary.txt").exists()
    index = (history_dir / "lynch_scan_index.csv").read_text()
    assert "2026-06-06" in index
    assert "summary" in index
