import csv
import shutil
from datetime import date, datetime
from pathlib import Path

from quant_platform.config import HISTORY_DIR, LOG_DIR
from quant_platform.history.duckdb_store import upsert_scan_report

INDEX_FILE = HISTORY_DIR / "scan_index.csv"
INDEX_COLUMNS = [
    "scan_date",
    "scan_time",
    "universe_size",
    "eligible_count",
    "tier1_count",
    "tier2_count",
    "tier3_count",
    "filtered_count",
    "actionable_count",
    "regime",
    "archive_dir",
]


def archive_scan_outputs(
    *,
    csv_path: Path,
    json_path: Path | None = None,
    md_path: Path | None = None,
    scan_report: dict | None = None,
    scan_date: date | None = None,
) -> Path:
    """Copy scan outputs into data/history/YYYY-MM-DD/ and update index."""
    scan_date = scan_date or date.today()
    archive_dir = HISTORY_DIR / scan_date.isoformat()
    archive_dir.mkdir(parents=True, exist_ok=True)

    _copy_if_exists(csv_path, archive_dir / "breakout_scan_results.csv")
    if json_path:
        _copy_if_exists(json_path, archive_dir / "breakout_scan_report.json")
    if md_path:
        _copy_if_exists(md_path, archive_dir / "breakout_scan_summary.md")

    log_src = LOG_DIR / "scan.log"
    if log_src.exists():
        shutil.copy2(log_src, archive_dir / "scan.log")

    if scan_report:
        summary_path = archive_dir / "scan_summary.txt"
        _write_text_summary(summary_path, scan_report)

    if scan_report:
        _append_index(scan_date, archive_dir, scan_report)
        upsert_scan_report(
            scan_report,
            scan_date=scan_date,
            archive_dir=archive_dir,
            json_path=archive_dir / "breakout_scan_report.json" if json_path else None,
        )

    return archive_dir


def _copy_if_exists(src: Path, dest: Path) -> None:
    if src.exists():
        shutil.copy2(src, dest)


def _write_text_summary(path: Path, report: dict) -> None:
    summary = report["scan_summary"]
    regime = report["market_regime"]
    tiers = summary["tier_counts"]
    actionable = tiers["Tier 1"] + tiers["Tier 2"]
    lines = [
        f"Scan date: {path.parent.name}",
        f"Regime: {regime['label']} (multiplier {regime['multiplier']})",
        f"Universe: {summary['universe_size']}",
        f"Eligible: {summary['eligible_count']}",
        f"Actionable (Tier 1+2): {actionable}",
        f"Tier 1: {tiers['Tier 1']} | Tier 2: {tiers['Tier 2']} | "
        f"Tier 3: {tiers['Tier 3']} | Filtered: {tiers['filtered']}",
        "",
        "Actionable tickers:",
    ]
    for t in report["tickers"]:
        if t.get("tier") in ("Tier 1", "Tier 2"):
            score = t.get("summary", {}).get("final_adjusted_score", 0)
            reason = t.get("tier_reason", "")
            lines.append(f"  {t['ticker']}: {t['tier']} (score {score}) — {reason}")
    path.write_text("\n".join(lines) + "\n")


def _append_index(scan_date: date, archive_dir: Path, report: dict) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    summary = report["scan_summary"]
    tiers = summary["tier_counts"]
    row = {
        "scan_date": scan_date.isoformat(),
        "scan_time": datetime.now().isoformat(timespec="seconds"),
        "universe_size": summary["universe_size"],
        "eligible_count": summary["eligible_count"],
        "tier1_count": tiers["Tier 1"],
        "tier2_count": tiers["Tier 2"],
        "tier3_count": tiers["Tier 3"],
        "filtered_count": tiers["filtered"],
        "actionable_count": tiers["Tier 1"] + tiers["Tier 2"],
        "regime": report["market_regime"]["label"],
        "archive_dir": str(archive_dir),
    }
    write_header = not INDEX_FILE.exists()
    with INDEX_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INDEX_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
