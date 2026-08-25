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

## Known gap (tested 2026-08-26, root-caused 2026-08-26 — not yet fixed upstream)

The documented cross-file check "scene paths referenced in rules exist on disk" does not
fire for `LoadScene(...)` inside `logic/rules.ron`'s `do_actions` (tested against a
`LoadScene` pointing at a nonexistent scene file — no error reported). It correctly
catches missing prefab keys (scene → `prefabs.ron`) and missing effect keys (rules →
`assets.ron`). Don't rely on `ironhold validate` alone to catch a typo'd `LoadScene`
path.

**Root cause** (confirmed by reading `ironhold-lib/crates/ironhold_cli/src/commands/validate.rs`,
not a guess): `cross_file_checks`'s per-action `match` (lines ~168–252) has no arm for
`Action::LoadScene`, `Action::LoadSceneOverlay`, or `Action::PreloadScene` — all three
fall through the `_ => {}` catch-all. It's not a state-machine-vs-rules gap as originally
suspected; it's simply unimplemented. `ironhold-lib`'s own `planning/features/ironhold_cli.md`
(line 75) lists "scene paths referenced in rules / state machine exist on disk" as a
planned v1 check, but no code was ever written for it — every other listed check (prefab
keys, effect keys) has a matching arm; this one doesn't.

**Fix** (mirrors the existing `behavior_path` exists-on-disk check already in the same
file at lines ~670–683 — same `project_dir.join(path).exists()` pattern). Since
`ironhold-lib` is reference-only for this repo (not modified here), apply this to
`ironhold-lib/crates/ironhold_cli/src/commands/validate.rs` directly, then
`cargo build --release -p ironhold_cli` and re-copy the binary here:

```rust
            Action::PreloadGlb(key) => {
                if let Some(c) = asset_catalog {
                    if !c.models.contains_key(key) {
                        errors.push(CrossFileError {
                            source_file: source.clone(),
                            message: format!("model key {:?} not found in assets.ron", key),
                            error_type: "missing_reference",
                        });
                    }
                }
            }
            // NEW — add this arm right after PreloadGlb:
            Action::LoadScene(path) | Action::LoadSceneOverlay(path) | Action::PreloadScene(path) => {
                if !project_dir.join(path).exists() {
                    errors.push(CrossFileError {
                        source_file: source.clone(),
                        message: format!("scene path {:?} not found on disk", path),
                        error_type: "missing_file",
                    });
                }
            }
```

Verification once applied: re-run the three-broken-copy test from this project's
`ironhold_cli` backlog entry (`planning/backlog.md`, Done section) — specifically the
`LoadScene("scenes/does_not_exist.scene.ron")` case in `logic/rules.ron`, which should
now report `logic/rules.ron: scene path "scenes/does_not_exist.scene.ron" not found on
disk` and exit `1` instead of silently passing.

## Rebuilding

```
cd <path to ironhold-lib checkout>
cargo build --release -p ironhold_cli
# binary lands at target/release/ironhold.exe (or $CARGO_TARGET_DIR/release/ironhold.exe)
```
