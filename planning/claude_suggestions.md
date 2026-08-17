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
