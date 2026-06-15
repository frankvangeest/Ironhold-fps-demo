#!/usr/bin/env python3
"""
Report the size of the assets/ directory and warn if it exceeds 70% of the 1 GB GitHub repo limit.

Used as a Claude UserPromptSubmit hook — outputs nothing when under threshold,
outputs a warning line when over so it surfaces in Claude's context.

Usage:
    python scripts/check_asset_size.py
"""
import os
from pathlib import Path

WARN_THRESHOLD_BYTES = 700 * 1024 * 1024   # 700 MB  (70% of 1 GB)
HARD_LIMIT_BYTES     = 1024 * 1024 * 1024  # 1 GB

ROOT = Path(__file__).parent.parent
ASSETS_DIR = ROOT / "assets"


def dir_size(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                pass
    return total


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    if not ASSETS_DIR.exists():
        return

    size = dir_size(ASSETS_DIR)
    pct = size / HARD_LIMIT_BYTES * 100

    if size >= WARN_THRESHOLD_BYTES:
        print(
            f"[!] ASSET SIZE WARNING: assets/ is {human(size)} "
            f"({pct:.0f}% of 1 GB GitHub limit). "
            f"Review before adding more files."
        )


if __name__ == "__main__":
    main()
