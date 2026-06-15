#!/usr/bin/env python3
"""
Download the latest ironhold-lib pkg files from GitHub and update ironhold-lib.json.

Usage:
    python scripts/update_lib.py           # update to latest main
    python scripts/update_lib.py --dry-run # show what would change, do not write
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO = "frankvangeest/ironhold-lib"
API_URL = f"https://api.github.com/repos/{REPO}/commits/main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main/pkg"

PKG_FILES = [
    "ironhold_web.js",
    "ironhold_web_bg.wasm",
    "ironhold_web.d.ts",
    "ironhold_web_bg.wasm.d.ts",
    "package.json",
]

ROOT = Path(__file__).parent.parent
PKG_DIR = ROOT / "pkg"
VERSION_FILE = ROOT / "ironhold-lib.json"


def get_latest_commit():
    req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["sha"], data["commit"]["message"].splitlines()[0]


def download_file(filename):
    url = f"{RAW_BASE}/{filename}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Fetching latest commit from {REPO}...")
    try:
        sha, msg = get_latest_commit()
    except urllib.error.URLError as e:
        print(f"Error: Could not reach GitHub — {e}")
        sys.exit(1)

    print(f"Latest : {sha[:12]}  {msg}")

    version = json.loads(VERSION_FILE.read_text())
    pinned = version.get("commit")
    if pinned == sha:
        print("Already up to date.")
        return

    if dry_run:
        print("[dry-run] Would download:")
        for f in PKG_FILES:
            print(f"  {f}")
        print(f"[dry-run] Would update ironhold-lib.json commit to {sha[:12]}")
        return

    PKG_DIR.mkdir(exist_ok=True)
    for filename in PKG_FILES:
        print(f"  Downloading {filename}...")
        data = download_file(filename)
        (PKG_DIR / filename).write_bytes(data)

    version["commit"] = sha
    VERSION_FILE.write_text(json.dumps(version, indent=2) + "\n")

    print(f"\nDone. pkg/ updated to commit {sha[:12]}.")
    print("Commit pkg/ and ironhold-lib.json to lock this version.")


if __name__ == "__main__":
    main()
