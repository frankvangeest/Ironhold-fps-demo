# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A sci-fi first-person shooter demo built on the **Ironhold** game engine (WASM/WebGPU). No Rust compilation happens here — the engine is consumed as a pre-built WASM binary from `pkg/`. The game is published on GitHub Pages. Assets live in this repo (not in the engine repo) because they are heavy.

## Local development

Serve locally with Python — WASM requires HTTP, not `file://`:

```
python -m http.server 8080
# Open: http://localhost:8080/?project=scifi_fps
```

## Library management

The engine WASM comes from [frankvangeest/ironhold-lib](https://github.com/frankvangeest/ironhold-lib). The pinned commit SHA is tracked in `ironhold-lib.json`.

```
python scripts/check_lib_version.py   # compare pinned vs. latest on main
python scripts/update_lib.py          # download latest pkg/ + docs/ and update the JSON
python scripts/update_lib.py --dry-run
python scripts/update_lib.py --no-docs  # skip docs/ download (slow connection)
```

`update_lib.py` also downloads `docs/` (offline reference) and `docs/engine_assets_claude.md` / `docs/engine_projects_claude.md` from the engine repo at the same pinned SHA. These are gitignored — regenerate with `update_lib.py` at any time.

After updating the engine, commit `pkg/` and `ironhold-lib.json` together (not `docs/`).

## Branching

- **`main`** — live (GitHub Pages). Never commit work-in-progress directly here.
- **`dev`** — the working branch. All development (including by agents) happens on `dev`. Merge `dev → main` after testing in browser.

```
git checkout dev                      # always work here
git merge dev && git push origin main # promote after a successful browser test
```

Agents commit to `dev` by default. Push to `main` only after you have confirmed the scene/feature works at `http://localhost:8080/?project=scifi_fps`.

## Deployment (GitHub Pages)

Push to `main`. GitHub Pages serves the repo root directly — no build step needed.
Game URL: `https://frankvangeest.github.io/Ironhold-fps-demo/?project=scifi_fps`

`index.html` redirects to `?project=scifi_fps` if no `project` param is present.

## Engine API

The WASM module (`pkg/ironhold_web.js`) exposes one function:

```js
import init, { start } from './pkg/ironhold_web.js';
await init();   // loads the .wasm file
start();        // starts the Bevy event loop — does not return
```

The runtime reads `?project=<name>` from the URL and loads `assets/projects/<name>/` from the same origin.

On WASM, `DebugState` is serialised as JSON into `<div id="debug-state">` every frame (used by automated tests):
```json
{"frame": 42, "app_state": "InGame", "last_action": "...", "scene": "...", "logic_state": "...", "score": 0}
```

## Game project structure

All game content lives under `assets/projects/scifi_fps/`:

```
assets/projects/scifi_fps/
  scifi_fps.project.ron         ← entry point (ProjectConfig schema v3)
  assets.ron                    ← models / textures / audio / effects / materials
  prefabs/prefabs.ron           ← named entity templates
  prefabs/animation/            ← AnimationPolicy per character type
  behaviors/                    ← per-entity FSM behavior files (.behavior.ron)
  scenes/                       ← one .scene.ron per scene
  logic/state_machine.ron       ← global FSM (use v3 project config)
  overrides/model_fixes.ron     ← per-asset transform corrections
  stats/stats.ron               ← global named stat definitions
```

Use `schema_version: 3` with `state_machine_path` in the project config (needed for multi-scene flow with menus/pause).

## Ironhold architecture (data-driven, no recompile)

All game behaviour is declared in **RON files** — no code changes needed for content iteration. The engine pipeline is:

**Events → Interpreter → Actions → Executor**

- **Events** are emitted by UI buttons, physics triggers, scene lifecycle, NPC AI, input, etc.
- **Rules / FSM** (`logic/state_machine.ron`) map events to actions.
- **Actions** are executed by capability systems (LoadScene, Spawn, PlaySound, ModifyStat, SpawnEffect, …).

### Key concepts

- **Project config** (`.project.ron`) is the entry point. It references all other files.
- **Scenes** (`.scene.ron`) declare entities, UI, lighting, terrain, and spawn points declaratively.
- **Prefabs** (`prefabs/prefabs.ron`) are named entity templates. Scenes place prefab instances by key.
- **Asset catalog** (`assets.ron`) is the named registry for models, textures, audio, effects, and materials.
- **Entity FSM** (`.behavior.ron`) — each entity can run its own state machine. `{self}` is substituted with the entity's spawn ID, making behavior files reusable across instances.
- **Stats** (`stats.ron`) define global named stats (health, mana, etc.) with min/max/regen/thresholds. Per-entity stats use `stat_templates` on the prefab; addressed as `"spawn_id.stat_name"`.

### Scene lifecycle event order

`scene.requested:<stem>` → `scene.loaded:<stem>` → `scene.ready:<stem>`

Wire `scene.ready:<name>` in `state_machine.ron` to start music, spawn effects, set initial state, and preload assets.

### Player setup

A prefab with `components.tags: ["player"]` spawns a third-person character controller + orbit camera. For FPS, use a `"flycam"` tagged prefab — it gives a free-flying camera driven by mouse + WASD. True FPS (locked first-person with weapon) is not yet a built-in capability; the flycam is the closest available option.

### Rendering constraints (web baseline)

No HDR, no bloom, no LUT-based tonemappers. Available: `AcesFitted`, `Reinhard`, `ReinhardLuminance`, `None`, `SomewhatBoringDisplayTransform`. All rendering must work in WebGPU WASM. Use WGSL for any custom shaders.

### Art style

**Stylized hand-painted** — chunky silhouettes, partially baked lighting in albedo, controlled saturation, readable at half scale. Textures: 512×512 preferred, 1024×1024 for hero assets. Photorealistic scanned textures do not belong in shared assets. This project targets a sci-fi theme, which may warrant a cooler, more metallic palette while staying within these constraints.

### Action RON syntax — the most common parse error

Actions are either **tuple variants** (positional args, no field names) or **struct variants** (named fields). Mixing them causes a parse error with no obvious diagnostic.

**Tuple variants — positional, no field names:**
```ron
LoadScene("scenes/game.scene.ron")
LoadSceneOverlay("scenes/pause.scene.ron")
UnloadOverlay
Despawn("enemy_01")
EnterState("playing")
EmitEvent("player.died")
SetVariable("score", "0")        // two positional strings
IncrementVariable("score", 1)    // string key, then i32 delta
SetVolume(80)
ToggleMute
PreloadScene("scenes/arena.scene.ron")
PreloadPrefab("enemy_orc")
PlayAnimation("run")
Log("debug message")
Quit
StopMusic
OpenInventory  CloseInventory  ToggleInventory
OpenShop("merchant_01")  CloseShop
```

**Struct variants — named fields:**
```ron
Spawn(prefab: "enemy_orc", id: "orc_01", position: (5.0, 0.5, 0.0))
PlaySound(key: "pickup_coin", volume: 0.8)
PlayMusicLoop(key: "bg_forest")
PlayAnimationOn(target: "{self}", clip: "attack")
EmitEventAfterDelay(event: "enemy.respawn:{self}", delay_secs: 5.0)
SpawnEffect(key: "hit_spark", entity: "{self}")
SpawnEffect(key: "explosion", position: Some((0.0, 0.5, 0.0)))
ModifyStat(key: "health", delta: -25.0)
SetStat(key: "{self}.health", value: 100.0)
ShowDamagePopup(entity: "{self}", amount: -25.0)
ShowFloatingText(entity: "{self}", text: "Critical hit!")
SetEntityVisible(entity: "{self}", visible: false)
CameraShake(duration_secs: 0.4, intensity: 0.15)
```

### WASM-specific patterns

- Fire warmup `SpawnEffect` at `position: Some((0.0, -100.0, 0.0))` on `scene.ready` for each distinct particle variant (sphere, flame shader) to pre-compile WebGPU pipelines before player interaction.
- Use `PreloadPrefab(key)` on `scene.ready` to eliminate GLB-decode stalls on first spawn.
- Use `PreloadScene(path)` on `scene.ready` to warm next-scene assets before the player reaches a transition.
- Spawns are frame-paced (max 2/frame) by the engine to avoid pipeline-compile stalls.
- Dynamic point lights cap at 16 simultaneous fading lights; plan scene lighting accordingly.

## Agents

Specialized agents live in `.claude/agents/`. In some Claude Code environments these are directly selectable via the Agent tool's `subagent_type`; in others (confirmed in at least one session on this repo) the Agent tool only lists built-ins (`claude`, `general-purpose`, `Explore`, `Plan`, etc.) and a custom `subagent_type` like `prefab-architect` errors with "Agent type not found." If that happens, don't fall back to an undirected `general-purpose` call — open the relevant `.claude/agents/<name>.md` file yourself (or tell the delegated agent to read it first) and follow its conventions explicitly in the prompt.

| Agent | `subagent_type` | Use for |
|---|---|---|
| `ironhold-ron` | `ironhold-ron` | Validating or authoring any RON file; all schema versions and field lists |
| `prefab-architect` | `prefab-architect` | Designing `PrefabDef` entries — components, stat templates, behavior references |
| `level-designer` | `level-designer` | Laying out scenes — entity placement, lighting, cover, spawn points, UI |
| `fsm-author` | `fsm-author` | Writing `state_machine.ron`, `rules.ron`, `.behavior.ron` — event → action logic |
| `asset-pipeline` | `asset-pipeline` | Running Python scripts, adding model batches, fixing texture paths, updating engine |
| `cinematics-director` | `cinematics-director` | Dramatic camera framing, lighting, and beat pacing for story moments (within current engine limits — no cutscene sequencer yet) |

## Debugging & verification tips

Learned the hard way while building the corridor kit and Integration Program Wing — save future sessions the rediscovery:

- **Cuboid `Primitive` prefabs are center-origin.** Unlike GLB `Prop` models (whose pivot is usually already base-anchored, per `pivot_y_offset` in `model_metadata.json`), a raw `Primitive` Cuboid's origin is its geometric center — same as the `"ground"` prefab, which needs `translation.y = -size.y/2` to put its top surface at `y=0`. Placing furniture/placeholder primitives at `y≈0` sinks half of them into the floor; use `y = height/2 + 0.001`.
- **Colliders are per-prefab-key, never inherited by a sibling model.** A reskinned/variant mesh (e.g. `wallastra_straight_window` next to `wallastra_straight`) does not automatically get the same `colliders` list — each prefab key needs its own, even when the meshes are near-identical.
- **A door frame's collider must not be one solid box.** `door_frame_square` originally had a single Cuboid spanning the whole opening, silently blocking the doorway it was meant to leave passable. Use jamb-post + lintel colliders (see the `archway` pattern in `docs/20_data_formats.md`) so the actual gap stays walkable.
- **Camera/flycam pitch sign**: `rotation_euler_deg`'s X-axis is **negative = look down, positive = look up** — confirmed empirically (not the first guess). Useful for `cinematics-director` framing and for building a debug top-down view: spawn a temporary `flycam` entity high up with `rotation_euler_deg: (-90, 0, 0)`. Temporarily setting the scene's `shadows_enabled: false` makes a top-down shot far easier to read — long raking shadows from the directional light otherwise look like extra geometry.
- **Testing in a real browser via Playwright on Windows**: headless Chromium's software renderer can't run this engine's WebGPU build, and Playwright's bundled Chromium is missing `dxil.dll` (needed for WebGPU-over-D3D12). Launch via an installed browser channel instead — `p.chromium.launch(channel="msedge", headless=False)` — which pops a real, visible window using the system GPU.
- **If a headed-browser screenshot comes back black/empty and nothing else explains it**: the user's PC may simply be locked (screen off) — a `headless=False` window still renders, but there's nothing to capture, or capture can fail outright. Don't assume it's a scene/rendering bug before ruling this out; ask the user to check, or wait until the machine is unlocked.
- **Modular kit wall convention** (WallAstra corridor kit, `prefabs.ron`): everything is a 4m×4m tile. A wall triplet (`bottommetal_straight` + `wallastra_straight` + `topastra_straight`) placed at a tile's own origin closes that tile's **west** edge at `rotation_euler_deg: (0,0,0)`, **south** at `(0,90,0)`, **east** at `(0,180,0)`, **north** at `(0,270,0)` — reuse these exact values for any new room/corridor shell rather than re-deriving rotation math. When attaching a multi-tile room to a corridor, design the room's entrance to exactly match the width of what it connects to (a `corridor_doorway` opening is one tile/4m wide — an 8m-wide room mouth overhangs into the corridor's solid wall) and put the entrance on whichever edge lets the whole room be placed at **identity rotation** — translation-only attachment avoids a fresh rotation-direction guess entirely.

## Planning

| File | Purpose |
|---|---|
| `planning/backlog.md` | Active task list — work top-to-bottom unless priority overrides |
| `planning/claude_suggestions.md` | Good ideas that would derail the current task — log here, Frank promotes to backlog |
| `planning/feature_request.md` | Desired features the engine does not yet support |

When you have a suggestion that is not directly part of the current task, add it to `claude_suggestions.md` (What / Why / While working on: X) instead of raising it in conversation.

## Docs reference

The `docs/` folder is a local copy from ironhold-lib for offline reference — gitignored, never committed. Regenerate with `python scripts/update_lib.py`. Also contains `engine_assets_claude.md` and `engine_projects_claude.md` (fetched from the engine repo at the same pinned SHA). Always prefer the live docs in the engine repo if they diverge.
