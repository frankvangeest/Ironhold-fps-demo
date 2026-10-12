#!/usr/bin/env python3
"""Keep opencode.json's "agent" block in step with .claude/agents/*.md.

The Claude agent files are the single source: each OpenCode agent loads the same file as its prompt and gets its
permissions from the file's `tools:` frontmatter (no Bash -> bash denied, no Write/Edit -> edit denied, no
WebFetch/WebSearch -> those denied). The global bash allow-list stays in opencode.json's top-level "permission".

    python scripts/sync_opencode_agents.py            # rewrite the "agent" block
    python scripts/sync_opencode_agents.py --check    # exit 1 if opencode.json is out of date (a new/edited Claude agent)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / ".claude" / "agents"
CONFIG = ROOT / "opencode.json"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        raise SystemExit(f"{path}: no frontmatter")
    out = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            out[k.strip()] = v.strip().strip('"')
    return out


def build() -> dict:
    agents = {}
    for path in sorted(AGENTS.glob("*.md")):
        fm = frontmatter(path)
        name = fm["name"]
        tools = {t.strip() for t in fm.get("tools", "").strip("[]").split(",") if t.strip()}
        perm = {"task": "deny"}
        if not tools & {"Write", "Edit"}:
            perm["edit"] = "deny"
        if "Bash" not in tools:
            perm["bash"] = "deny"
        if "WebFetch" not in tools:
            perm["webfetch"] = "deny"
        if "WebSearch" not in tools:
            perm["websearch"] = "deny"
        agents[name] = {
            "mode": "subagent",
            "description": re.split(r"\\+n", fm["description"])[0],  # drop the <example> blocks some files append
            "prompt": "{file:.claude/agents/%s}" % path.name,
            "permission": perm,
        }
    return agents


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    want = build()
    if "--check" in sys.argv:
        if cfg.get("agent") == want:
            print("opencode.json agents match .claude/agents")
            return 0
        have = set(cfg.get("agent", {}))
        print("opencode.json is out of date; run: python scripts/sync_opencode_agents.py")
        print("  missing:", sorted(set(want) - have), " stale:", sorted(have - set(want)))
        return 1
    cfg["agent"] = want
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(want)} agents to opencode.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
