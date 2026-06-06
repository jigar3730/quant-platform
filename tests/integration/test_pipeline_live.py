from pathlib import Path

import pytest

from quant_platform.pipeline.runner import PipelineRunner

pytestmark = pytest.mark.integration


def test_pipeline_live_small(tmp_path: Path):
    output = tmp_path / "live.csv"
    runner = PipelineRunner(
        tickers=["AAPL", "MSFT"],
        output=output,
        use_cache=False,
    )
    results = runner.run()
    assert output.exists()
    assert len(results) == 2
