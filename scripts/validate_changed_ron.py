#!/usr/bin/env python3
"""Validate the asset projects whose RON files have uncommitted changes, with the bundled ironhold.exe.

Silent and exit 0 when nothing under assets/projects/ changed (so it is cheap to run at the end of every session).
Prints the validator output and exits 1 on a validation error.

Also enforces the project's strict-ASCII convention: every changed .ron file under assets/projects/
must contain only ASCII bytes. The engine's embedded UI font has no glyphs beyond U+0020..U+007E,
so non-ASCII in any text field renders as a tofu box; comments are included so the rule stays
simple enough to lint blindly. (ironhold validate --strict does the field-aware version of this
check with a nicer message, but does not cover comments or ShowFloatingText strings.)

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


def changed_ron_files() -> list[Path]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "assets/projects"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    files = set()
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path.endswith(".ron") and len(Path(path).parts) > 3:
            files.add(ROOT / path)
    return sorted(f for f in files if f.is_file())


def ascii_violations(path: Path) -> list[str]:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as e:
        return [f"{path}: not valid UTF-8 ({e})"]
    found = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 127:
                found.append(f"{path}:{lineno}:{col}: non-ASCII U+{ord(ch):04X} {ch!r} "
                             f"— RON files must be pure ASCII (embedded UI font has no glyph for it)")
    return found


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
    files = changed_ron_files()
    projects = sorted({f.parent for f in files} if files else set())
    failures = []
    for project in projects:
        r = subprocess.run([str(VALIDATOR), "validate", str(project)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"ironhold validate failed for {project.name}:\n{(r.stdout + r.stderr).strip()}")
    for f in files:
        failures.extend(ascii_violations(f))
    if not failures:
        return 0
    msg = "\n".join(failures) + "\nFix the RON errors above before finishing."
    print(msg, file=sys.stderr if hook else sys.stdout)
    return 2 if hook else 1


if __name__ == "__main__":
    sys.exit(main())
