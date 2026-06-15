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
python scripts/update_lib.py          # download latest pkg/ and update the JSON
python scripts/update_lib.py --dry-run
```

After updating, commit both `pkg/` and `ironhold-lib.json` together.

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

### WASM-specific patterns

- Fire warmup `SpawnEffect` at `position: (0, -100, 0)` on `scene.ready` for each distinct particle variant (sphere, flame shader) to pre-compile WebGPU pipelines before player interaction.
- Use `PreloadPrefab(key)` on `scene.ready` to eliminate GLB-decode stalls on first spawn.
- Use `PreloadScene(path)` on `scene.ready` to warm next-scene assets before the player reaches a transition.
- Spawns are frame-paced (max 2/frame) by the engine to avoid pipeline-compile stalls.
- Dynamic point lights cap at 16 simultaneous fading lights; plan scene lighting accordingly.

## Planning

| File | Purpose |
|---|---|
| `planning/backlog.md` | Active task list — work top-to-bottom unless priority overrides |
| `planning/claude_suggestions.md` | Good ideas that would derail the current task — log here, Frank promotes to backlog |
| `planning/feature_request.md` | Desired features the engine does not yet support |

When you have a suggestion that is not directly part of the current task, add it to `claude_suggestions.md` (What / Why / While working on: X) instead of raising it in conversation.

## Docs reference

The `docs/` folder is a local copy from ironhold-lib for offline reference — it is gitignored and not committed. Always prefer the live docs in the engine repo if they diverge.
