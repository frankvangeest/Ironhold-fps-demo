#!/usr/bin/env python3
"""
Check whether the pinned ironhold-lib commit is behind the latest on main.

Usage:
    python scripts/check_lib_version.py
"""
import json
import urllib.request
import urllib.error
from pathlib import Path

REPO = "frankvangeest/ironhold-lib"
API_URL = f"https://api.github.com/repos/{REPO}/commits/main"
VERSION_FILE = Path(__file__).parent.parent / "ironhold-lib.json"


def get_latest_commit():
    req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["sha"], data["commit"]["message"].splitlines()[0]


def main():
    version = json.loads(VERSION_FILE.read_text())
    pinned = version.get("commit")

    print(f"Repo   : {REPO}")
    print(f"Pinned : {pinned or '(not set — run update_lib.py)'}")

    try:
        latest_sha, latest_msg = get_latest_commit()
    except urllib.error.URLError as e:
        print(f"Error  : Could not reach GitHub API — {e}")
        return

    print(f"Latest : {latest_sha[:12]}  {latest_msg}")

    if pinned is None:
        print("\n[!] No pinned commit recorded. Run 'python scripts/update_lib.py' to initialise.")
    elif pinned == latest_sha:
        print("\n[✓] Up to date.")
    else:
        print("\n[!] Update available. Run 'python scripts/update_lib.py' to update pkg/.")


if __name__ == "__main__":
    main()
