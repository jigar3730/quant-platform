"""Launch the Streamlit dashboard."""

import subprocess
import sys
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent / "dashboard.py"


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DASHBOARD),
        "--server.headless",
        "true",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
