from datetime import date
from pathlib import Path

from quant_platform.config import HISTORY_DIR, LOG_DIR
from quant_platform.history.common import (
    append_csv_index,
    archive_timestamp,
    copy_if_exists,
    ensure_archive_dir,
)
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
    output_stem: str = "breakout_scan",
    log_name: str = "scan.log",
) -> Path:
    """Copy scan outputs into data/history/YYYY-MM-DD/ and update index."""
    scan_date = scan_date or date.today()
    archive_dir = ensure_archive_dir(HISTORY_DIR, scan_date)

    copy_if_exists(csv_path, archive_dir / f"{output_stem}_results.csv")
    archived_json = archive_dir / f"{output_stem}_report.json"
    if json_path:
        copy_if_exists(json_path, archived_json)
    if md_path:
        copy_if_exists(md_path, archive_dir / f"{output_stem}_summary.md")

    log_src = LOG_DIR / log_name
    copy_if_exists(log_src, archive_dir / log_name)

    if scan_report:
        summary_path = (
            archive_dir / "scan_summary.txt"
            if output_stem == "breakout_scan"
            else archive_dir / f"{output_stem}_summary.txt"
        )
        _write_text_summary(summary_path, scan_report)

    if scan_report:
        _append_index(scan_date, archive_dir, scan_report)
        upsert_scan_report(
            scan_report,
            scan_date=scan_date,
            archive_dir=archive_dir,
            json_path=archived_json if json_path else None,
        )

    return archive_dir


def _write_text_summary(path: Path, report: dict) -> None:
    summary = report["scan_summary"]
    regime = report["market_regime"]
    tiers = summary["tier_counts"]
    actionable = summary.get(
        "actionable_count",
        tiers.get("Tier 1", 0) + tiers.get("Tier 2", 0),
    )
    tier_line = " | ".join(f"{name}: {count}" for name, count in tiers.items())
    lines = [
        f"Scan date: {path.parent.name}",
        f"Strategy: {report.get('strategy_id', 'breakout')}",
        f"Regime: {regime['label']} (multiplier {regime['multiplier']})",
        f"Universe: {summary['universe_size']}",
        f"Eligible: {summary['eligible_count']}",
        f"Actionable: {actionable}",
        tier_line,
        "",
        "Actionable tickers:",
    ]
    actionable_tiers = {"Tier 1", "Tier 2", "A", "B"}
    for t in report["tickers"]:
        if t.get("tier") in actionable_tiers:
            score = t.get("summary", {}).get("final_adjusted_score", 0)
            reason = t.get("tier_reason", "")
            lines.append(f"  {t['ticker']}: {t['tier']} (score {score}) — {reason}")
    path.write_text("\n".join(lines) + "\n")


def _append_index(scan_date: date, archive_dir: Path, report: dict) -> None:
    summary = report["scan_summary"]
    tiers = summary["tier_counts"]
    strategy_id = report.get("strategy_id", "breakout")
    if strategy_id == "swing":
        tier1, tier2, tier3 = tiers.get("A", 0), tiers.get("B", 0), tiers.get("C", 0)
    else:
        tier1 = tiers.get("Tier 1", 0)
        tier2 = tiers.get("Tier 2", 0)
        tier3 = tiers.get("Tier 3", 0)
    actionable = summary.get("actionable_count", tier1 + tier2)
    append_csv_index(
        INDEX_FILE,
        INDEX_COLUMNS,
        {
            "scan_date": scan_date.isoformat(),
            "scan_time": archive_timestamp(),
            "universe_size": summary["universe_size"],
            "eligible_count": summary["eligible_count"],
            "tier1_count": tier1,
            "tier2_count": tier2,
            "tier3_count": tier3,
            "filtered_count": tiers.get("filtered", 0),
            "actionable_count": actionable,
            "regime": report["market_regime"]["label"],
            "archive_dir": str(archive_dir),
        },
    )
