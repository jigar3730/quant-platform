"""Daily scheduled scan: run, archive, and email."""

from __future__ import annotations

import argparse
import logging

from quant_platform.config import (
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
)
from quant_platform.logging_setup import setup_logging
from quant_platform.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


def run_daily_scan(*, send_email: bool = True, use_cache: bool = True) -> int:
    """Run full daily workflow: scan, archive, optional email."""
    setup_logging("scan.log")
    runner = PipelineRunner(
        output=DEFAULT_OUTPUT_CSV,
        use_cache=use_cache,
        report="both",
        report_json=DEFAULT_OUTPUT_JSON,
        report_md=DEFAULT_OUTPUT_MD,
        archive=True,
        send_email=send_email,
    )
    runner.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily breakout scan with archive and email")
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip actionable tickers email",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable parquet cache for price/fundamental data",
    )
    args = parser.parse_args(argv)
    return run_daily_scan(send_email=not args.no_email, use_cache=not args.no_cache)


if __name__ == "__main__":
    raise SystemExit(main())
