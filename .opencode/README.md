# OpenCode in ironhold-fps-demo

Claude Code and OpenCode are the two supported tools. `CLAUDE.md` and `.claude/agents/*.md` are the single source for both.

- **Driver:** `openrouter/z-ai/glm-5.3-flash` (`opencode.json`). It reads screenshots and renders itself; a pilot
  (`planning/features/opencode_compatibility.md`, Part B) found no need for a separate image agent.
- **Instructions:** `opencode.json` loads `CLAUDE.md`. There is no `AGENTS.md` (OpenCode does not expand an `@CLAUDE.md` stub).
- **Agents:** the 7 subagents in `opencode.json` load `.claude/agents/<name>.md` as their prompt; their permissions come from the
  `tools:` frontmatter (no Bash -> bash denied, and so on). After adding or editing a Claude agent run
  `python scripts/sync_opencode_agents.py` (`--check` exits 1 when `opencode.json` is stale). Don't hand-edit the `agent` block.
  Subagents are reached through the driver's `task` tool; `opencode run --agent <subagent>` is not possible.
- **Bash allow-list:** global, in `opencode.json`; anything else asks.
- **Validation:** `scripts/validate_changed_ron.py` runs `ironhold.exe validate` on every `assets/projects/<name>` with uncommitted
  RON changes (silent if none), and enforces the strict-ASCII convention on changed `.ron` files (the engine's UI font has no glyphs
  beyond `U+0020..U+007E`; non-ASCII text renders as a tofu box). It runs at the end of each session in both tools: Claude's Stop hook (exit 2 feeds the errors back
  so Claude fixes them; it does not loop) and the OpenCode plugin (warning only, the driver is not forced to continue).
- **End reminder:** the same plugin logs Claude's Stop-hook reminder ("did any good ideas belong in planning/claude_suggestions.md?") at
  every session end, at info level.
- **Hook:** `.opencode/plugins/hooks.ts` runs `scripts/check_asset_size.py` when a session goes idle (Claude runs it on prompt submit).
  It prints nothing under 700 MB of assets. Verified (2026-10-12) in a long-lived `opencode serve`/attach session; a one-shot
  `opencode run` exits before the async check finishes, so it never warns there. The bash tool runs Git Bash: use forward slashes
  (`tools/ironhold_cli/ironhold.exe`), backslash paths from `CLAUDE.md` get eaten.

Run on this machine: `nvs use 24.21`, then `opencode` (or `opencode run "<message>" --dir <repo> < /dev/null` headless: stdin must
be closed or it hangs).
