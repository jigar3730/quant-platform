"""Shared helpers for scan archival."""

from __future__ import annotations

import csv
import shutil
from datetime import date, datetime
from pathlib import Path


def copy_if_exists(src: Path, dest: Path) -> None:
    if src.exists():
        shutil.copy2(src, dest)


def append_csv_index(index_file: Path, columns: list[str], row: dict) -> None:
    index_file.parent.mkdir(parents=True, exist_ok=True)
    write_header = not index_file.exists()
    with index_file.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def archive_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_archive_dir(history_dir: Path, scan_date: date) -> Path:
    archive_dir = history_dir / scan_date.isoformat()
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir
