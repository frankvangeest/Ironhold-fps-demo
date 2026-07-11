#!/usr/bin/env python3
"""
Check whether the pinned ironhold-lib commit is behind the latest on main.
When behind, lists all commits since the pinned version using the GitHub compare API.

Usage:
    python scripts/check_lib_version.py
"""
import json
import urllib.request
import urllib.error
from pathlib import Path

REPO = "frankvangeest/ironhold-lib"
VERSION_FILE = Path(__file__).parent.parent / "ironhold-lib.json"


def gh_get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def get_latest_commit():
    data = gh_get(f"https://api.github.com/repos/{REPO}/commits/main")
    return data["sha"], data["commit"]["message"].splitlines()[0]


def get_commits_since(base_sha):
    """Return commits between base_sha (exclusive) and main (inclusive), newest first."""
    data = gh_get(f"https://api.github.com/repos/{REPO}/compare/{base_sha}...main")
    return list(reversed(data["commits"]))


def main():
    version = json.loads(VERSION_FILE.read_text())
    pinned = version.get("commit")

    print(f"Repo   : {REPO}")
    print(f"Pinned : {pinned[:12] if pinned else '(not set)'}")

    try:
        latest_sha, latest_msg = get_latest_commit()
    except urllib.error.URLError as e:
        print(f"Error  : Could not reach GitHub API — {e}")
        return

    print(f"Latest : {latest_sha[:12]}  {latest_msg}")

    if pinned is None:
        print("\n[!] No pinned commit recorded. Run 'python scripts/update_lib.py' to initialise.")
        return

    if pinned == latest_sha:
        print("\n[OK] Up to date.")
        return

    print("\n[!] Update available. Commits since pinned (newest first):\n")
    try:
        commits = get_commits_since(pinned)
        for c in commits:
            sha = c["sha"][:12]
            msg = c["commit"]["message"].splitlines()[0]
            print(f"  {sha}  {msg}")
    except urllib.error.URLError as e:
        print(f"  (could not fetch commit list — {e})")

    print("\nRun 'python scripts/update_lib.py' to update pkg/.")


if __name__ == "__main__":
    main()
