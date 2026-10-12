#!/usr/bin/env python3
"""Validate the asset projects whose RON files have uncommitted changes, with the bundled ironhold.exe.

Silent and exit 0 when nothing under assets/projects/ changed (so it is cheap to run at the end of every session).
Prints the validator output and exits 1 on a validation error.

    python scripts/validate_changed_ron.py          # manual / OpenCode plugin
    python scripts/validate_changed_ron.py --hook   # Claude Code Stop hook: exit 2 (feeds stderr back to Claude) on failure,
                                                    # exit 0 if the hook already re-fired once (stop_hook_active) to avoid a loop
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "tools" / "ironhold_cli" / "ironhold.exe"


def changed_projects() -> list[Path]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "assets/projects"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    projects = set()
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        parts = Path(path).parts
        if path.endswith(".ron") and len(parts) > 3:
            projects.add(ROOT / "assets" / "projects" / parts[2])
    return sorted(p for p in projects if p.is_dir())


def main() -> int:
    hook = "--hook" in sys.argv
    if hook:
        try:
            if json.load(sys.stdin).get("stop_hook_active"):
                return 0
        except (ValueError, OSError):
            pass
    if not VALIDATOR.exists():
        return 0
    failures = []
    for project in changed_projects():
        r = subprocess.run([str(VALIDATOR), "validate", str(project)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"ironhold validate failed for {project.name}:\n{(r.stdout + r.stderr).strip()}")
    if not failures:
        return 0
    msg = "\n\n".join(failures) + "\nFix the RON errors above before finishing."
    print(msg, file=sys.stderr if hook else sys.stdout)
    return 2 if hook else 1


if __name__ == "__main__":
    sys.exit(main())
