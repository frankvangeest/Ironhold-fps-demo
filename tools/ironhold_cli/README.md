# ironhold CLI

A prebuilt native binary (`ironhold.exe`, Windows x64) for offline RON validation and
project introspection. Built from `ironhold-lib`'s `crates/ironhold_cli` — see
`ironhold-lib`'s own `planning/features/ironhold_cli.md` for the full command surface.

Built from ironhold-lib commit `593278467c6a42ad505af35090318cb576e9d37e` (`cargo build
--release -p ironhold_cli`). This is newer than the WASM commit currently pinned in
`ironhold-lib.json` (`452e2e20f54b...`) — the CLI validates RON schema/structure, which
has stayed compatible across that gap. Rebuild after a `scripts/update_lib.py` run if a
future engine update changes the RON schema (new/renamed fields, new Action variants).

`ironhold-lib` is used strictly as a reference/build source here — nothing in that repo
is modified. Only this prebuilt binary is committed to this repo.

## Usage

```
tools\ironhold_cli\ironhold.exe validate assets\projects\scifi_fps\
tools\ironhold_cli\ironhold.exe query prefabs assets\projects\scifi_fps\ --keys-only
tools\ironhold_cli\ironhold.exe stats assets\projects\scifi_fps\
tools\ironhold_cli\ironhold.exe schema show PrefabDef
```

`--json` must come before the subcommand: `ironhold.exe --json validate <dir>`.

Exit codes: `0` = valid, `1` = validation errors, `2` = tool/IO error.

## Known gap (tested 2026-08-26)

The documented cross-file check "scene paths referenced in rules exist on disk" does not
fire for `LoadScene(...)` inside `logic/rules.ron`'s `do_actions` (tested against a
`LoadScene` pointing at a nonexistent scene file — no error reported). It correctly
catches missing prefab keys (scene → `prefabs.ron`) and missing effect keys (rules →
`assets.ron`). Don't rely on `ironhold validate` alone to catch a typo'd `LoadScene`
path — this project uses `rules_path`, not `state_machine_path`, and the check may only
be wired for state-machine transitions.

## Rebuilding

```
cd <path to ironhold-lib checkout>
cargo build --release -p ironhold_cli
# binary lands at target/release/ironhold.exe (or $CARGO_TARGET_DIR/release/ironhold.exe)
```
