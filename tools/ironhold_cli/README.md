# ironhold CLI

A prebuilt native binary (`ironhold.exe`, Windows x64) for offline RON validation and
project introspection. Built from `ironhold-lib`'s `crates/ironhold_cli` — see
`ironhold-lib`'s own `planning/features/ironhold_cli.md` for the full command surface.

Rebuilt from ironhold-lib commit `222e446b1a96` (the commit pinned in `ironhold-lib.json`,
via `cargo build --release -p ironhold_cli` into a detached worktree, then copied here).
This matches the WASM commit currently pinned in `ironhold-lib.json`. Rebuild after a
`scripts/update_lib.py` run if a future engine update changes the RON schema (new/renamed
fields, new Action variants).

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

## Known gap — resolved upstream

The documented cross-file check "scene paths referenced in rules exist on disk" originally
did not fire for `LoadScene(...)` inside `logic/rules.ron`'s `do_actions` (tested against a
`LoadScene` pointing at a nonexistent scene file — no error reported). Prefab-key and
effect-key checks were unaffected.

**Root cause**: `cross_file_checks`'s per-action `match` had no arm for
`Action::LoadScene`, `Action::LoadSceneOverlay`, or `Action::PreloadScene` — all three
fell through the `_ => {}` catch-all (unimplemented, not a regression).

**Status**: fixed upstream in ironhold-lib `7acd354` (`feat(cli): validate scene-path
existence and merchant cross-references`). The `ironhold.exe` committed here is rebuilt
from pin `222e446b1a96` and re-verified (2026-09-17): a broken `LoadScene`/`PreloadScene`/
`LoadSceneOverlay` path and a missing `initial_scene` each report
`scene path "..." not found on disk` and exit `1`. Run `ironhold validate` before a
browser test as a fast first-pass check, not as a replacement for one.

## Rebuilding

```
cd <path to ironhold-lib checkout>
cargo build --release -p ironhold_cli
# binary lands at target/release/ironhold.exe (or $CARGO_TARGET_DIR/release/ironhold.exe)
```
