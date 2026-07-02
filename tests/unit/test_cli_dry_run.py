from quant_platform.cli import main
from quant_platform.config import (
    DEFAULT_DRY_RUN_CSV,
    DEFAULT_DRY_RUN_JSON,
    DEFAULT_DRY_RUN_MD,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
)


def test_dry_run_redirects_default_output_paths(tmp_path, monkeypatch):
    captured: dict = {}

    class FakeRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def run(self):
            return None

    monkeypatch.setattr("quant_platform.cli.PipelineRunner", FakeRunner)
    main(
        [
            "--dry-run",
            "--tickers",
            "AAA",
            "--report",
            "both",
        ]
    )

    assert captured["dry_run"] is True
    assert captured["output"] == DEFAULT_DRY_RUN_CSV
    assert captured["report_json"] == DEFAULT_DRY_RUN_JSON
    assert captured["report_md"] == DEFAULT_DRY_RUN_MD
    assert captured["output"] != DEFAULT_OUTPUT_CSV
    assert captured["report_json"] != DEFAULT_OUTPUT_JSON


def test_dry_run_rejects_archive():
    try:
        main(["--dry-run", "--archive"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("expected SystemExit")
