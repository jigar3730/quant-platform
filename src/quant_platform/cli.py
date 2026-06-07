import argparse
from pathlib import Path

from quant_platform.config import (
    DEFAULT_DRY_RUN_CSV,
    DEFAULT_DRY_RUN_JSON,
    DEFAULT_DRY_RUN_MD,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
    DEFAULT_TICKERS_FILE,
)
from quant_platform.logging_setup import setup_logging
from quant_platform.pipeline.runner import PipelineRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Breakout stock scanner")
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated tickers (overrides ticker config file and dynamic fetch)",
    )
    parser.add_argument(
        "--tickers-file",
        type=Path,
        default=DEFAULT_TICKERS_FILE,
        help="Static ticker list file (default: data/tickers.txt)",
    )
    parser.add_argument(
        "--dynamic-universe",
        action="store_true",
        help="Ignore ticker config file; fetch most-active stocks from Yahoo",
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

    if args.dry_run and (args.archive or args.email):
        parser.error("--dry-run cannot be combined with --archive or --email")

    if args.dry_run:
        if args.output == DEFAULT_OUTPUT_CSV:
            args.output = DEFAULT_DRY_RUN_CSV
        if args.report_json == DEFAULT_OUTPUT_JSON:
            args.report_json = DEFAULT_DRY_RUN_JSON
        if args.report_md == DEFAULT_OUTPUT_MD:
            args.report_md = DEFAULT_DRY_RUN_MD

    if (args.archive or args.email) and not args.report:
        args.report = "both"

    setup_logging("scan.log")

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    runner = PipelineRunner(
        tickers=tickers,
        tickers_file=args.tickers_file,
        dynamic_universe=args.dynamic_universe,
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
