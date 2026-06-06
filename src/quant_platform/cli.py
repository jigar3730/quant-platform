import argparse
import logging
import sys
from pathlib import Path

from quant_platform.config import (
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
    LOG_DIR,
)
from quant_platform.pipeline.runner import PipelineRunner


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "scan.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Breakout stock scanner")
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated tickers (overrides universe fetch)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help="Output CSV path",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Use optional parquet cache for price/fundamental data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with synthetic data (no network)",
    )
    parser.add_argument(
        "--report",
        choices=["json", "md", "both"],
        default=None,
        help="Write detailed analysis report (json, md, or both)",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Path for JSON report (with --report json or both)",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Path for markdown summary (with --report md or both)",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive outputs to data/history/YYYY-MM-DD/",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Email actionable tickers (Tier 1+2); requires SMTP env vars",
    )
    args = parser.parse_args(argv)

    if (args.archive or args.email) and not args.report:
        args.report = "both"

    _setup_logging()

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    runner = PipelineRunner(
        tickers=tickers,
        output=args.output,
        use_cache=args.cache,
        dry_run=args.dry_run,
        report=args.report,
        report_json=args.report_json,
        report_md=args.report_md,
        archive=args.archive,
        send_email=args.email,
    )
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
