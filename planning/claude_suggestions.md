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
