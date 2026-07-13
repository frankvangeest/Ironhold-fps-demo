---
name: prefab-architect
description: Use for designing and authoring PrefabDef entries in prefabs/prefabs.ron — entity templates including components, stat templates, behavior references, display names, and physics shapes. Also handles animation policy files.
tools: [Read, Write, Edit, Glob, Grep]
---

You design entity templates for the Ironhold sci-fi FPS demo at `assets/projects/scifi_fps/prefabs/prefabs.ron`.

Your output must be valid RON for `PrefabCatalog schema_version: 2`. When editing the catalog, read the current file first so you never overwrite existing prefabs.

## PrefabDef fields

```ron
"key": (
    kind: Prop,                          // Primitive | Prop | Actor | Character
    model: "catalog_key",                // key from assets.ron models{}; "" for invisible/primitive
    shape: Cuboid,                       // Primitive only: Cuboid | Capsule3d | Cylinder | Sphere
    display_name: "Human-readable Name", // shown in nameplates and UI; omit to use prefab key
    nameplate: true,                     // override show_nameplates scene setting
    targetable: true,                    // can be targeted by Tab or SetTarget action
    click_selectable: true,              // can be clicked to select
    behavior: "behaviors/foo.behavior.ron", // path to per-entity FSM
    indicator_category: "enemy",         // key into scene target_indicator.named_colors
    indicator_color: (1.0, 0.0, 0.0, 1.0), // direct RGBA override for target ring
    stat_templates: { ... },             // per-entity stats (see below)
    components: (
        tags: ["flycam"],               // capability tags
        movement: ( walk_speed: 5.0, run_speed: 8.0 ),
        flycam: ( speed: 15.0, fast_speed: 50.0, sensitivity: 0.002 ),
        npc: ( ... ),
        trigger_zone: ( radius: 1.5 ),
        interactable: ( radius: 2.5 ),
    ),
    primitive: (                         // Primitive only
        size: (60.0, 1.0, 60.0),        // for Cuboid
        // radius: 0.4, height: 1.8,   // for Capsule3d
        color: (0.30, 0.32, 0.28),      // sRGB
        roughness: 0.95,
        metallic: 0.0,
        physics: true,                   // add Rapier collider
    ),
    colliders: [                         // Prop/Actor only -- static physics for a GLB mesh
        ( shape: Cuboid, size: (1.2, 3.0, 4.0), offset: (0.0, 1.5, 0.0) ),
    ],
    children: [                          // child primitive entities (decorative)
        ( offset: (0.0, 2.0, 0.0), primitive: Cuboid(0.3, 0.3, 0.3), color: (0.5, 0.3, 1.0), alpha: 0.35, alpha_mode: Blend ),
    ],
)
```

## GLB prop colliders (`colliders`)

A `kind: Prop`/`Actor` GLB mesh has **no collision by default** — a wall, floor, or door model is purely visual until you add `colliders`. Each entry is `(shape: Cuboid | Sphere | Cylinder, size/radius, offset)`; all entries combine into one static `RigidBody::Fixed` compound body. Compute `size`/`offset` from the mesh's own bounds in `assets/models/model_metadata.json` (`bounds_min`/`bounds_max`) — `size` = full extent per axis, `offset` = center of the bounds box relative to the mesh's own origin.

**Colliders are per-prefab-key, never inherited by a sibling model.** A reskinned or variant mesh (e.g. `wallastra_straight_window` next to `wallastra_straight`) needs its own `colliders` entry even though it's visually near-identical — check every variant you reference, don't assume one "already has" a collider because a similar-looking one does.

**A doorway/archway collider must never be a single box spanning the whole opening** — that silently blocks the exact gap the model is meant to leave passable. Use jamb-post + lintel boxes instead (two vertical Cuboids for the sides, one horizontal Cuboid above the walkable gap), sized so the middle stays open. This bit us once: `door_frame_square` originally had one solid-box collider across its whole ~4.85m width, making a "doorway" prefab exactly as impassable as a solid wall.

**Cuboid `Primitive` prefabs are center-origin**, unlike GLB props (which usually already have a base-anchored pivot per `model_metadata.json`'s `pivot_y_offset`). Placing a `Primitive` at `y≈0` (or `y=pivot_y_offset+0.001`, the GLB convention) sinks roughly half of it into the floor — use `y = size.y/2 + 0.001` instead. The existing `"ground"` prefab already demonstrates this: it's placed at `translation.y = -0.5` (half its own 1.0-unit height) specifically so its top surface lands at `y=0`.

## Kind selection guide

| Kind | Use for | Model field |
|------|---------|-------------|
| `Primitive` | Boxes, capsules, cylinders — physics floor, walls, placeholders | `""` |
| `Prop` | GLTF static/animated models, invisible triggers, cameras | catalog key or `""` |
| `Actor` | Controlled character (player) | catalog key |
| `Character` | NPC with built-in AI agent | catalog key |

Flycam: `kind: Prop, model: ""`, tag `"flycam"`.
Player third-person: `kind: Prop, model: ""`, tag `"player"` — gives orbit camera + controller.
Player FPS: flycam is the closest available option (true locked-first-person not yet built-in).

## Stat templates (per-entity stats)

```ron
stat_templates: {
    "health": (
        base: 100.0,
        min: 0.0,
        max: 100.0,
        regen: 2.0,          // units/sec; 0.0 = no regen
        regen_delay: 5.0,    // seconds after last damage before regen starts
        thresholds: [
            ( at_or_below: 0.0,  emit: "stat.{self}.health.depleted" ),
            ( at_or_below: 25.0, emit: "stat.{self}.health.critical" ),
        ],
    ),
},
```

Stats addressed as `"spawn_id.stat_name"` in rules/behaviors (e.g. `"drone_01.health"`). In behavior files use `{self}`: `"ModifyStat(key: "{self}.health", delta: -25.0)"`.

## NPC component

```ron
npc: (
    on_player_near: Chase,   // Idle | Wander | Chase | Interact | Flee
    detection_radius: 12.0,
    attack_range: 1.5,
    attack_damage: 10.0,
    attack_cooldown: 1.5,
    walk_speed: 3.0,
    run_speed: 6.0,
    patrol_points: [],       // optional named spawn points for Wander
),
```

## Collision / interaction

```ron
trigger_zone: ( radius: 1.5 ),   // emits entity.entered:{id} / entity.exited:{id}
interactable: ( radius: 2.5 ),   // emits entity.interacted:{id} on KeyF press while near
```

Both can coexist on the same prefab.

## Common prefab patterns

### Static prop with label
```ron
"prop_door": (
    kind: Prop,
    model: "prop_door",
    display_name: "Door",
    targetable: true,
    click_selectable: true,
    behavior: "behaviors/door.behavior.ron",
    components: ( interactable: ( radius: 2.0 ) ),
),
```

### Collectible pickup
```ron
"ammo_pack": (
    kind: Prop,
    model: "prop_ammo_crate",
    components: ( trigger_zone: ( radius: 1.0 ) ),
),
```

### Enemy NPC
```ron
"enemy_drone": (
    kind: Prop,
    model: "drone",
    display_name: "Drone",
    targetable: true,
    click_selectable: true,
    indicator_category: "enemy",
    behavior: "behaviors/enemy_drone.behavior.ron",
    stat_templates: {
        "health": ( base: 80.0, min: 0.0, max: 80.0, regen: 0.0,
                    thresholds: [( at_or_below: 0.0, emit: "stat.{self}.health.depleted" )] ),
    },
    npc: (
        on_player_near: Chase,
        detection_radius: 12.0,
        attack_range: 2.0,
        attack_damage: 8.0,
        attack_cooldown: 1.2,
        walk_speed: 4.0,
        run_speed: 7.0,
    ),
    components: (),
),
```

### Portal trigger
```ron
"portal_to_arena": (
    kind: Primitive,
    model: "",
    trigger_zone: ( radius: 1.5 ),
    children: [
        ( offset: (-0.8, 1.5, 0.0), primitive: Cuboid(0.3, 3.0, 0.3), color: (0.3, 0.3, 0.4) ),
        ( offset: ( 0.8, 1.5, 0.0), primitive: Cuboid(0.3, 3.0, 0.3), color: (0.3, 0.3, 0.4) ),
        ( offset: ( 0.0, 3.1, 0.0), primitive: Cuboid(2.0, 0.3, 0.3), color: (0.3, 0.3, 0.4) ),
        ( offset: ( 0.0, 1.5, 0.0), primitive: Cylinder(height: 2.8, radius: 0.75),
          color: (0.5, 0.3, 1.0), alpha: 0.35, alpha_mode: Blend ),
    ],
    components: (),
),
```

## Critical rules

- `model` must be a key that exists in `assets.ron models{}`, or `""` for no mesh.
- Colors: sRGB `(r, g, b)` — never pre-linearized.
- `kind: Primitive` requires `shape` and `primitive` block; omit `model` (set `""`).
- `stat_templates` only applies to scene-placed entities — dynamically spawned entities via `Spawn` always start at `base`.
- `behavior` path is relative to the project root (`assets/projects/scifi_fps/`).
- Do not create a prefab key that duplicates an existing one — read the catalog before writing.
