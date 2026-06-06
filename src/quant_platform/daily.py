"""Daily scheduled scan: run, archive, and email."""

import logging
import sys

from quant_platform.cli import _setup_logging
from quant_platform.config import (
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
)
from quant_platform.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


def run_daily_scan(*, send_email: bool = True, use_cache: bool = True) -> int:
    """Run full daily workflow: scan, archive, optional email."""
    _setup_logging()
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


def main() -> int:
    send = "--no-email" not in sys.argv
    return run_daily_scan(send_email=send)


if __name__ == "__main__":
    raise SystemExit(main())
