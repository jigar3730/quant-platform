"""CLI for Peter Lynch 10-bagger scanner."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from quant_platform.config import (
    DEFAULT_LYNCH_CSV,
    DEFAULT_LYNCH_JSON,
    DEFAULT_LYNCH_MD,
    DEFAULT_TICKERS_FILE,
)
from quant_platform.logging_setup import setup_logging
from quant_platform.lynch.config import PRESET_LABELS, PRESETS
from quant_platform.lynch.runner import LynchScannerRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Peter Lynch style 10-bagger stock scanner",
    )
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
        "--preset",
        choices=PRESETS,
        default="summary",
        help="Screen preset (default: summary = base + all categories)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_LYNCH_CSV)
    parser.add_argument(
        "--report",
        choices=["json", "md", "both"],
        default=None,
        help="Write detailed Lynch analysis report",
    )
    parser.add_argument("--report-json", type=Path, default=DEFAULT_LYNCH_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_LYNCH_MD)
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive to data/history/YYYY-MM-DD/ and upsert DuckDB",
    )
    args = parser.parse_args(argv)

    if args.archive and not args.report:
        args.report = "both"

    setup_logging("lynch_scan.log")
    logging.getLogger(__name__).info(
        "Preset: %s", PRESET_LABELS.get(args.preset, args.preset)
    )

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    runner = LynchScannerRunner(
        tickers=tickers,
        tickers_file=args.tickers_file,
        dynamic_universe=args.dynamic_universe,
        preset=args.preset,
        output=args.output,
        report=args.report,
        report_json=args.report_json,
        report_md=args.report_md,
        archive=args.archive,
    )
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
