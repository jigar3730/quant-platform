import json
from pathlib import Path

from quant_platform.swing.cli import main
from quant_platform.swing.runner import SwingScannerRunner


def test_swing_dry_run_with_report(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"

    runner = SwingScannerRunner(
        tickers=["AAA", "BBB"],
        output=csv_path,
        dry_run=True,
        report="both",
        report_json=json_path,
        report_md=md_path,
    )
    runner.run()

    assert csv_path.exists()
    assert json_path.exists()
    assert md_path.exists()

    report = json.loads(json_path.read_text())
    assert report.get("strategy_id") == "swing"
    assert "scan_summary" in report
    assert len(report["tickers"]) == 2


def test_swing_cli_accepts_report_and_archive(monkeypatch):
    captured: dict = {}

    class FakeRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def run(self):
            return None

    monkeypatch.setattr("quant_platform.swing.cli.SwingScannerRunner", FakeRunner)
    main(["--report", "both", "--archive"])

    assert captured["report"] == "both"
    assert captured["archive"] is True


def test_swing_dry_run_rejects_archive():
    try:
        main(["--dry-run", "--archive"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("expected SystemExit")
