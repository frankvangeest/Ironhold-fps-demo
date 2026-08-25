# Backlog

Tasks promoted from `claude_suggestions.md` or added directly. Work top-to-bottom unless priority overrides.

---

## In Progress

<!-- Move tasks here when actively working on them -->

## Up Next

## Backlog

- [ ] Forgejo support in lib scripts: add `forge_type` to `ironhold-lib.json` and branch API calls in `check_lib_version.py` / `update_lib.py` to support Forgejo's different endpoint format and raw URL structure. Do when migration is actually happening so it can be tested against a real instance.

## Done

- [x] Test `ironhold_cli` RON validation — 2026-08-26. Built from `ironhold-lib` (`cargo build --release -p ironhold_cli`, commit `593278467c6a42ad505af35090318cb576e9d37e`). Confirmed standalone (only needs a project directory) against `scifi_fps` (9 files, all valid) and three intentionally broken copies: caught a parse error with file/line, a missing prefab key referenced by a scene, and a missing effect key referenced by a rule. Found one gap: a `LoadScene(...)` in `rules.ron` pointing at a nonexistent scene file was NOT caught, despite being a documented cross-file check — likely only wired for `state_machine.ron` transitions, not `rules.ron` actions (this project uses `rules_path`). Binary committed to `tools/ironhold_cli/ironhold.exe`, usage documented in `CLAUDE.md` and `tools/ironhold_cli/README.md`.
