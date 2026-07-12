#!/usr/bin/env python3
"""
Download the latest ironhold-lib pkg files, docs/, and engine CLAUDE references from GitHub,
then update ironhold-lib.json.
Stores the previous commit SHA so check_lib_version.py can list changes since last update.

Usage:
    python scripts/update_lib.py             # update to latest main
    python scripts/update_lib.py --dry-run   # show what would change, do not write
    python scripts/update_lib.py --no-docs   # skip docs/ and engine CLAUDE download
"""
import json
import shutil
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
DOCS_DIR = ROOT / "docs"
VERSION_FILE = ROOT / "ironhold-lib.json"


def get_latest_commit():
    req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["sha"], data["commit"]["message"].splitlines()[0]


def download_file(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def fetch_tree(sha):
    """Return flat list of blob entries for the repo at the given commit SHA."""
    url = f"https://api.github.com/repos/{REPO}/git/trees/{sha}?recursive=1"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [item for item in data["tree"] if item["type"] == "blob"]


# Engine CLAUDE.md files that are useful offline references
ENGINE_CLAUDE_FILES = {
    "assets/CLAUDE.md":          "docs/engine_assets_claude.md",
    "assets/projects/CLAUDE.md": "docs/engine_projects_claude.md",
}


def download_docs(sha):
    tree = fetch_tree(sha)
    doc_files = [item["path"] for item in tree if item["path"].startswith("docs/")]

    if not doc_files:
        print("  No docs/ files found in repo at this SHA.")
        return 0

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()

    for rel_path in doc_files:
        raw_url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{rel_path}"
        dest = ROOT / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = download_file(raw_url)
        dest.write_bytes(data)

    # Also fetch the engine CLAUDE.md references into docs/
    for src_path, dest_rel in ENGINE_CLAUDE_FILES.items():
        raw_url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{src_path}"
        dest = ROOT / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = download_file(raw_url)
            dest.write_bytes(data)
        except Exception as e:
            print(f"  Warning: could not fetch {src_path}: {e}")

    return len(doc_files) + len(ENGINE_CLAUDE_FILES)


def main():
    dry_run = "--dry-run" in sys.argv
    skip_docs = "--no-docs" in sys.argv

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
        if not skip_docs and not dry_run:
            print("Re-downloading docs/ to ensure they match pinned SHA...")
            n = download_docs(sha)
            print(f"  {n} docs files updated.")
        return

    if dry_run:
        print("[dry-run] Would download pkg/:")
        for f in PKG_FILES:
            print(f"  {f}")
        if not skip_docs:
            print("[dry-run] Would fetch repo tree and download docs/")
        print(f"[dry-run] Would set previous_commit = {pinned[:12] if pinned else 'none'}")
        print(f"[dry-run] Would set commit = {sha[:12]}")
        return

    PKG_DIR.mkdir(exist_ok=True)
    for filename in PKG_FILES:
        print(f"  Downloading pkg/{filename}...")
        data = download_file(f"{RAW_BASE}/{filename}")
        (PKG_DIR / filename).write_bytes(data)

    if not skip_docs:
        print("Fetching docs/ file tree...")
        n = download_docs(sha)
        print(f"  {n} docs files downloaded to docs/  (gitignored, not committed)")

    version["previous_commit"] = pinned
    version["commit"] = sha
    VERSION_FILE.write_text(json.dumps(version, indent=2) + "\n")

    print(f"\nDone. pkg/ updated to commit {sha[:12]}.")
    print("Commit pkg/ and ironhold-lib.json to lock this version.")


if __name__ == "__main__":
    main()
