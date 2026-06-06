import json
from pathlib import Path

from quant_platform.pipeline.runner import PipelineRunner


def test_dry_run_with_report(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"

    runner = PipelineRunner(
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
    assert "scan_summary" in report
    assert "market_regime" in report
    assert len(report["tickers"]) == 2
    assert "eligibility" in report["tickers"][0]
