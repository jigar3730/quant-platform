"""Archive Peter Lynch scan outputs to data/history/YYYY-MM-DD/."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from quant_platform.config import HISTORY_DIR, LOG_DIR
from quant_platform.history.common import (
    append_csv_index,
    archive_timestamp,
    copy_if_exists,
    ensure_archive_dir,
)
from quant_platform.history.duckdb_store import upsert_lynch_report

LYNCH_INDEX_FILE = HISTORY_DIR / "lynch_scan_index.csv"
LYNCH_INDEX_COLUMNS = [
    "scan_date",
    "scan_time",
    "preset",
    "universe_size",
    "passed_count",
    "fast_grower_count",
    "stalwart_count",
    "asset_play_count",
    "archive_dir",
]


def archive_lynch_outputs(
    *,
    csv_path: Path,
    json_path: Path | None = None,
    md_path: Path | None = None,
    scan_report: dict | None = None,
    scan_date: date | None = None,
) -> Path:
    """Copy Lynch outputs into data/history/YYYY-MM-DD/ and update index + DuckDB."""
    scan_date = scan_date or date.today()
    archive_dir = ensure_archive_dir(HISTORY_DIR, scan_date)

    copy_if_exists(csv_path, archive_dir / "lynch_scan_results.csv")
    if json_path:
        copy_if_exists(json_path, archive_dir / "lynch_scan_report.json")
    if md_path:
        copy_if_exists(md_path, archive_dir / "lynch_scan_summary.md")

    log_src = LOG_DIR / "lynch_scan.log"
    copy_if_exists(log_src, archive_dir / "lynch_scan.log")

    if scan_report:
        summary_path = archive_dir / "lynch_scan_summary.txt"
        _write_text_summary(summary_path, scan_report)
        _append_index(scan_date, archive_dir, scan_report)
        upsert_lynch_report(
            scan_report,
            scan_date=scan_date,
            archive_dir=archive_dir,
            json_path=archive_dir / "lynch_scan_report.json" if json_path else None,
        )

    return archive_dir


def _write_text_summary(path: Path, report: dict) -> None:
    summary = report["scan_summary"]
    cats = summary["category_counts"]
    lines = [
        f"Lynch scan date: {path.parent.name}",
        f"Preset: {summary['preset_label']}",
        f"Universe: {summary['universe_size']}",
        f"Passed: {summary['passed_count']}",
        f"Fast growers: {cats['fast_grower']} | Stalwarts: {cats['stalwart']} | "
        f"Asset plays: {cats['asset_play']}",
        "",
        "Top candidates:",
    ]
    for t in report.get("candidates", [])[:20]:
        cats_str = ", ".join(t.get("categories", [])) or "base"
        lines.append(
            f"  {t['ticker']}: score {t.get('lynch_score', 0)} ({cats_str}) — "
            f"{t.get('tier_reason', '')}"
        )
    path.write_text("\n".join(lines) + "\n")


def _append_index(scan_date: date, archive_dir: Path, report: dict) -> None:
    summary = report["scan_summary"]
    cats = summary["category_counts"]
    append_csv_index(
        LYNCH_INDEX_FILE,
        LYNCH_INDEX_COLUMNS,
        {
            "scan_date": scan_date.isoformat(),
            "scan_time": archive_timestamp(),
            "preset": summary["preset"],
            "universe_size": summary["universe_size"],
            "passed_count": summary["passed_count"],
            "fast_grower_count": cats["fast_grower"],
            "stalwart_count": cats["stalwart"],
            "asset_play_count": cats["asset_play"],
            "archive_dir": str(archive_dir),
        },
    )
