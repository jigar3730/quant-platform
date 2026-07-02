"""Daily scheduled scan: run, archive, and email."""

from __future__ import annotations

import argparse
import logging

from quant_platform.config import (
    DEFAULT_DRY_RUN_CSV,
    DEFAULT_DRY_RUN_JSON,
    DEFAULT_DRY_RUN_MD,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
)
from quant_platform.logging_setup import setup_logging
from quant_platform.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


def run_daily_scan(
    *,
    send_email: bool = True,
    use_cache: bool = True,
    dry_run: bool = False,
) -> int:
    """Run full daily workflow: scan, archive, optional email."""
    setup_logging("scan.log")
    output = DEFAULT_DRY_RUN_CSV if dry_run else DEFAULT_OUTPUT_CSV
    report_json = DEFAULT_DRY_RUN_JSON if dry_run else DEFAULT_OUTPUT_JSON
    report_md = DEFAULT_DRY_RUN_MD if dry_run else DEFAULT_OUTPUT_MD
    runner = PipelineRunner(
        output=output,
        use_cache=use_cache,
        dry_run=dry_run,
        report="both",
        report_json=report_json,
        report_md=report_md,
        archive=not dry_run,
        send_email=send_email and not dry_run,
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Synthetic data; skip archive and email",
    )
    args = parser.parse_args(argv)
    if args.dry_run and not args.no_email:
        logger.info("Dry run: skipping email and archive")
    return run_daily_scan(
        send_email=not args.no_email,
        use_cache=not args.no_cache,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
