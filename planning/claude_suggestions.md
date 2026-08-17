# Claude Suggestions

Ideas raised by Claude during work sessions that are worth considering but would distract from the current task. Frank reviews these periodically and promotes desirable ones to `backlog.md`.

Format per entry:
- **What**: brief description
- **Why**: the value it would add
- **While**: what task was in progress when this came up

---

<!-- Suggestions go here -->

- **What**: `models/Decals/Decal_Line_90.gltf` 404s on load — it references `Decal_Line_90_001.bin`, which doesn't exist on disk (pre-existing, not caused by any recent change).
- **Why**: Currently a silent-ish console error in `showcase.scene.ron`; worth a pass with `asset-pipeline` to check for other decals with the same mismatched `.bin` reference.
- **While**: Verifying `showcase.scene.ron` still loads cleanly after adding colliders to the corridor kit prefabs.

- **What**: Every page load logs a console panic — `panicked at bevy_winit-0.18.0/src/lib.rs:128: Failed to build event loop: RecreationAttempt` (plus a preceding `bevy_log` "Could not set global logger and tracing subscriber as they are already set" error) — right after the initial `Project Config Path` log line. Reproduced identically on both `showcase.scene.ron` and `main.scene.ron`, before and after the `camera_modes v2` engine update, so it's not caused by the engine bump or the FirstPerson camera change. The game still reaches `app_state: "InGame"` fine afterward (pipeline warmup completes, scene loads) — so far cosmetic, not blocking.
- **Why**: A panic + duplicate-logger-init error on every single load is a smell worth root-causing (possibly a wasm-bindgen/browser re-init path, or an artifact specific to Playwright-driven page loads vs. a normal manual page load) before it masks a real problem later. Worth checking whether it reproduces on a normal (non-automated) browser load, and if so, filing upstream against `ironhold-lib`.
- **While**: Playwright-based in-browser smoke testing of the `camera_modes v2` engine update and the new `FirstPerson` player camera.

- **What**: `scenes/integration_wing.scene.ron` (the hub) has no in-game entry point yet — `scifi_fps.project.ron`'s `initial_scene` is `scenes/showcase.scene.ron`, there's no portal/`LoadScene` rule anywhere pointing at `integration_wing`, and the engine only supports `?project=<name>` in the URL, not a scene-level query param (confirmed in `docs/browser_tests.md`). To browser-test the new hub logic (`logic/rules.ron`'s `scene.ready:integration_wing` and `entity.entered:briefing_trigger` rules) right now, `initial_scene` has to be hand-edited temporarily.
- **Why**: A real playthrough needs either a main-menu "New Game"/"Continue" button that `LoadScene`s into `integration_wing`, or a portal from an existing scene. Worth a `level-designer` / `fsm-author` pass once the hub's first slice is validated, so the scene stops being reachable only by editing the project config.
- **While**: Authoring the first FSM slice for `integration_wing.scene.ron` (baseline hub state + Mission 1 briefing trigger).

- **What**: `assets.ron`'s `audio: {}` map is completely empty for `scifi_fps` — no music or SFX keys defined at all, so no `PlayMusicLoop`/`PlaySound` action can reference anything without inventing an asset key that doesn't resolve to a file.
- **Why**: The hub scene (and presumably others) would benefit from at least a low ambient hum/music loop on `scene.ready`. Worth an `asset-pipeline` pass to source/register a placeholder ambient track before more scenes get wired up expecting audio.
- **While**: Wiring `logic/rules.ron`'s `scene.ready:integration_wing` baseline setup — skipped `PlayMusicLoop` because no catalog key exists yet.

- **What**: `.claude/agents/prefab-architect.md`'s `PrefabDef` field listing nests `trigger_zone` / `interactable` under a `components: ( trigger_zone: (...), interactable: (...) )` block, and its own "Collectible pickup" example (`ammo_pack`) does the same. But its "Portal trigger" example (`portal_to_arena`) places `trigger_zone` top-level as a sibling of `kind`/`model`, and the authoritative engine docs (`docs/20_data_formats.md`'s `PrefabDef` field table, `docs/30_runtime_events_and_logic.md`'s `collectible_box` example) confirm top-level is correct — `trigger_zone`/`interactable` are not nested under `components`. I followed the top-level form (verified working here) but the agent doc's inconsistency could mislead future authoring.
- **Why**: A stale/self-contradictory field listing in a frequently-used agent doc risks silent parse errors for whoever authors the next trigger-zone or interactable prefab.
- **While**: Adding the `trigger_briefing_intel` trigger-zone prefab for the Briefing Room proximity trigger.
