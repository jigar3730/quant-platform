"""CLI for swing pullback scanner."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from quant_platform.config import DEFAULT_SWING_CSV, DEFAULT_TICKERS_FILE
from quant_platform.logging_setup import setup_logging
from quant_platform.swing.runner import SwingScannerRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Swing pullback stock scanner")
    parser.add_argument("--tickers", type=str, default=None)
    parser.add_argument("--tickers-file", type=Path, default=DEFAULT_TICKERS_FILE)
    parser.add_argument("--dynamic-universe", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_SWING_CSV)
    parser.add_argument("--cache", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    setup_logging("swing_scan.log")

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    SwingScannerRunner(
        tickers=tickers,
        tickers_file=args.tickers_file,
        dynamic_universe=args.dynamic_universe,
        output=args.output,
        use_cache=args.cache,
        dry_run=args.dry_run,
    ).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
