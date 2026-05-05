#!/usr/bin/env python3
"""
Precheck script for Day 19 dataset readiness.

Checks:
- Supported file extensions
- Empty/very small files
- CSV readability and basic row counts
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".py",
    ".js",
    ".html",
    ".css",
    ".csv",
    ".pptx",
    ".xlsx",
    ".xls",
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".bmp",
}


@dataclass
class FileCheckResult:
    path: Path
    size_bytes: int
    supported: bool
    is_empty: bool
    is_tiny: bool
    csv_rows: int | None = None
    csv_columns: int | None = None
    csv_error: str | None = None


def iter_files(data_dir: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        yield from sorted(p for p in data_dir.rglob("*") if p.is_file())
    else:
        yield from sorted(p for p in data_dir.iterdir() if p.is_file())


def inspect_file(path: Path) -> FileCheckResult:
    size = path.stat().st_size
    ext = path.suffix.lower()
    supported = ext in SUPPORTED_EXTENSIONS
    is_empty = size == 0
    is_tiny = size < 64

    result = FileCheckResult(
        path=path,
        size_bytes=size,
        supported=supported,
        is_empty=is_empty,
        is_tiny=is_tiny,
    )

    if ext == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                row_count = sum(1 for _ in reader)
            result.csv_columns = len(header)
            result.csv_rows = row_count
        except Exception as exc:
            result.csv_error = str(exc)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 19 data precheck")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to input data directory",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan nested directories",
    )
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir.exists() or not data_dir.is_dir():
        print(f"ERROR: data directory not found: {data_dir}")
        return 1

    files = list(iter_files(data_dir, args.recursive))
    if not files:
        print(f"ERROR: no files found in {data_dir}")
        return 1

    results = [inspect_file(path) for path in files]

    unsupported = [r for r in results if not r.supported]
    empty = [r for r in results if r.is_empty]
    tiny = [r for r in results if r.is_tiny and not r.is_empty]
    csv_errors = [r for r in results if r.csv_error]

    print("\nDay 19 Data Precheck")
    print("=" * 40)
    print(f"Data dir: {data_dir}")
    print(f"Total files: {len(results)}")
    print(f"Supported: {len(results) - len(unsupported)}")
    print(f"Unsupported: {len(unsupported)}")
    print(f"Empty files: {len(empty)}")
    print(f"Tiny files (<64B): {len(tiny)}")
    print(f"CSV read errors: {len(csv_errors)}")
    print("=" * 40)

    if unsupported:
        print("\nUnsupported files:")
        for item in unsupported:
            print(f"- {item.path} ({item.path.suffix})")

    if empty:
        print("\nEmpty files:")
        for item in empty:
            print(f"- {item.path}")

    if csv_errors:
        print("\nCSV read errors:")
        for item in csv_errors:
            print(f"- {item.path}: {item.csv_error}")

    csv_ok = [r for r in results if r.path.suffix.lower() == ".csv" and not r.csv_error]
    if csv_ok:
        print("\nCSV summary:")
        for item in csv_ok:
            print(
                f"- {item.path.name}: rows={item.csv_rows or 0}, cols={item.csv_columns or 0}"
            )

    if unsupported or empty or csv_errors:
        print("\nPrecheck status: WARN")
        return 2

    print("\nPrecheck status: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

