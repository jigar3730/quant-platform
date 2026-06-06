from pathlib import Path

from quant_platform.pipeline.runner import PipelineRunner


def test_dry_run_pipeline(tmp_path: Path):
    output = tmp_path / "out.csv"
    runner = PipelineRunner(
        tickers=["AAA", "BBB", "CCC"],
        output=output,
        dry_run=True,
    )
    results = runner.run()
    assert output.exists()
    assert "tier" in results.columns
    assert len(results) == 3
