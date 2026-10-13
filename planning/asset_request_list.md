# Asset Request List

Assets needed for the scifi_fps project, derived from `storyline/00-05_*.md` (the narrative
bible) against what the game actually contains today. Current inventory (from `assets.ron`):
190 models (all environment kit: walls/platforms/columns/decals/props + 3 alien creatures),
21 textures (trim/padded-wall PBR sets), **0 audio, 0 effects, 0 decals, 0 custom materials**.
The player is a primitive capsule and all hub furniture is placeholder cuboids explicitly
marked "real models not modeled yet".

Priority legend:
- **P0** — blocks the first playable mission loop (weapons → enemies → Mission 1)
- **P1** — needed for Mission 1 "Survey" to feel like the story beat it is
- **P2** — polish; improves what already works

---

## Global requirements (apply to every entry)

- **Art style**: stylized hand-painted — chunky silhouettes, partially baked lighting in
  albedo, controlled saturation, readable at half scale. No photorealistic scanned textures.
  Cooler/metallic palette acceptable for this sci-fi theme. Storyline tone: worn working
  military-scientific (Accord), not glossy chrome.
- **Textures**: 512x512 preferred, 1024x1024 for hero assets. PNG. PBR sets follow the
  engine convention: `{Name}_BaseColor`, `{Name}_Normal`, `{Name}_ORM` (roughness in G
  channel, metallic in B, AO in R), optional `{Name}_Emissive`.
- **Models**: GLTF/GLB with separate `.bin` + textures, or fully embedded — either is fine,
  but **every referenced dependency file must ship with the model** (see the existing
  `Decal_Line_90.gltf` 404 bug: it references a `.bin` that was never committed).
- **Animated characters**: the GLB **must contain at least one embedded animation clip**
  (engine requirement — without one, animation retargeting silently does nothing). Clip
  naming: `Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop` minimum for player characters.
- **Audio**: `.wav` (PCM) for short SFX; `.ogg` for music/ambient loops. `.mp3` avoided,
  `.aiff`/`.flac` unsupported by the engine. Trim leading silence from all SFX. Mono for
  positional SFX, stereo acceptable for music/UI.
- **Effects**: particle effects are defined in `assets.ron` `effects:` and are *not* files —
  but any effect that should not render as a plain sphere mesh needs **sprite billboard
  textures** registered in `textures:` (see Effect entries below).
- **All in-game text** (labels, dialogue): ASCII only — the engine font has no glyphs
  outside `U+0020..U+007E`.
- **File placement**: models under `assets/models/{Category}/`, textures under
  `assets/textures/{subfolder}/` (particles / decals / ui / terrain per engine convention),
  audio under `assets/audio/`. After landing any asset, register it in `assets.ron` with a
  catalog key (suggested keys are given per entry) and re-run the metadata scan
  (`scripts/scan_gltf_metadata.py`) for new models.

---

## 1. Characters (animated GLB) — P0/P1

### 1.1 Team character models — Kael, Yun, Rook, Mira — **P0**

- **Catalog keys**: `char_kael`, `char_yun`, `char_rook`, `char_mira`
- **Used for**: The four Integration Program soldiers — the playable cast
  (`storyline/01_characters.md`: the game supports 1–4 players in local co-op, each player
  takes one character; in single-player the others are "present in the story"). They are
  also the hub's population (briefing room, suit bay) until NPC dialogue exists. Replaces
  the primitive-capsule player visual identity with actual characters.
- **Requirements**:
  - Humanoid, adult proportions, ~1.8 m tall at authored scale, base-anchored pivot
    (matching `pivot_y_offset ≈ height/2` convention the existing alien models use).
  - Distinct silhouettes between the four (Kael: controlled/steady bearing; Yun: wiry,
    scavenger-culture layers; Rook: bulky frame, talkative energy; Mira: slightly built,
    clinical posture). Same Core suit language across all four — a shared "Integration
    Program" design system with per-character variation — since all four wear the Core kit.
  - Embedded clips required: `Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop`
    (AnimationPolicy `base:`). One clip minimum is an engine hard requirement; the four
    above are what a moving player needs.
  - Face/hair detail budget can stay low (third-person co-op framing); silhouette and
    palette must read at 20 m.
  - 1024x1024 texture atlas per character is justified (hero assets).

### 1.2 Survey lead — **P1**

- **Catalog key**: `char_survey_lead`
- **Used for**: Mission 1 "Survey" — the nephew of a Compact general, "the situational
  awareness of a filing cabinet", makes three bad decisions in a row (`storyline/03_act1.md`).
  He is Mission 1's minor antagonist and the story's first example of the gap between the
  Accord's ideals and the people those ideals protect.
- **Requirements**: humanoid, corporate/official wardrobe that reads as "connected, not
  competent" — clean, brand-new, visibly unsuited to the field. Clips: `Idle_Loop`,
  `Walk_Loop` (he wanders into the wrong location per the beat list).

### 1.3 Survey crew civilians x3 — **P1**

- **Catalog keys**: `char_survey_crew_a/b/c`
- **Used for**: Mission 1 escort objective — the people the team escorts to the survey
  zone. They must read as fragile/valuable next to the Integrates.
- **Requirements**: humanoid, light work-suit variants, can share one base mesh with three
  albedo/color variants to keep cost down. Clips: `Idle_Loop`, `Walk_Loop`.

### 1.4 Petra Solander — **P2**

- **Catalog key**: `char_petra`
- **Used for**: Commander of the Integration Program; comms presence in Act 1, physically
  present in debrief scenes. In the hub she can anchor the command office; even before
  dialogue exists she can stand in the briefing room as scene dressing.
- **Requirements**: humanoid, civilian-authority dress (not field kit), calm/imposing
  bearing. Clips: `Idle_Loop` minimum.

### 1.5 Settlement coordinator — **P2**

- **Catalog key**: `char_coordinator`
- **Used for**: Mission 2 "Home Fires" (Drevet) recurring minor character — competent,
  direct, quietly grateful.
- **Requirements**: humanoid, fringe-settlement civilian wear (not Accord-styled). Clips:
  `Idle_Loop`, `Walk_Loop`. Can share the survey-crew base mesh with a different palette.

---

## 2. Weapons (GLB) — P0

### 2.1 Player rifle — **P0**

- **Catalog keys**: `weapon_rifle` (world/pickup), `weapon_rifle_firstperson` (optional
  low-poly view variant)
- **Used for**: The entire weapons + shooting task — there is no attack system, no weapon
  prefab, and `prop_weapon_rack` is a colored box. This is the Armory pickup and the thing
  the player carries through every mission. Nothing else in the game can be built until a
  weapon exists to fire.
- **Requirements**:
  - Sci-fi carbine/rifle, ~0.8–1.0 m, chunky readable silhouette (stylized, not milspec-
    photoreal). Muzzle reference point clear at the barrel tip (needed for muzzle-flash
    effect offset and projectile/hitscan origin tuning).
  - No animation clips required (weapon is a prop); a simple 2–3 frame recoil/charge clip
    (`Fire_Loop` optional) is a bonus.
  - Clean separation of grip/muzzle/ejection marks in the UV layout so the muzzle-flash
    effect can be anchored at the right spot.
  - First-person variant (lower poly, no stock details that clip the camera) is a separate
    optional deliverable — decide after the first in-browser test with the world model.

### 2.2 Weapon rack contents (secondary) — **P2**

- **Catalog keys**: `weapon_ammo_box`, `weapon_case_closed`
- **Used for**: dressing the Armory weapon rack and ammo pickups (`prop_itemholder` already
  exists as a display base). Ammo box doubles as the world model for ammo pickups in
  missions.
- **Requirements**: small props, ~0.3–0.6 m, one texture each, no clips.

---

## 3. Environment — Maren's Moon, Mission 1 "Survey" — P1

Mission 1 (`storyline/03_act1.md`) is an **outdoor** escort mission on a semi-charted moon:
resource survey zone, territorial herd predators migrated into it, a swarm event running
three days early. The current kit is 100% interior (walls/platforms); nothing outdoor exists.

### 3.1 Terrain layer textures — **P1**

- **Catalog keys**: `terrain_maren_rock`, `terrain_maren_dirt`, `terrain_maren_moss`
- **Used for**: The Mission 1 ground surface via the engine's splatmap terrain system
  (`TerrainMaterialDef`: RGBA splatmap, one layer per RGB channel, tiling layer textures).
- **Requirements**: seamless tiling, 512x512 each, full PBR set per layer (BaseColor,
  Normal, ORM). Palette: cold regolith greys/browns with a restrained mossy teal for the
  "biologically interesting" zone the survey is assessing — the moss zone is the story
  objective, so it must read as distinct at a glance. Painted stylization (visible brush
  value structure), not photo scans.

### 3.2 Skybox — **P1**

- **Catalog key**: `skybox_maren_dusk`
- **Used for**: `global_environment` / scene environment for Mission 1 (and possibly the
  Observation Deck window view). Maren's Moon should feel exposed and marginal — dusk sky,
  large foreign planet or star on the horizon reads "fringe" instantly.
- **Requirements**: cubemap or 2:1 equirect panorama PNG; no HDR (engine is non-HDR).
  Low-frequency shapes only; terrain silhouettes sell the mood, not the sky detail.

### 3.3 Landscape rocks x3 — **P1**

- **Catalog keys**: `prop_rock_small`, `prop_rock_medium`, `prop_rock_large`
- **Used for**: scatter dressing + combat cover in the survey zone; also usable in later
  cave/ridge scenes (Mission 2's northern ridge).
- **Requirements**: base-anchored pivots, collision-friendly low-poly silhouettes, one
  shared 512 rock texture set, no clips. Sizes ~0.5 / 1.5 / 3–4 m.

### 3.4 Alien flora x2 — **P1**

- **Catalog keys**: `prop_flora_sporepod`, `prop_flora_gnarltree`
- **Used for**: Selling "resource-flagged moon with biological interest" and giving the
  moss zone visual identity. Spore pods can later double as early-swarm-event trigger
  dressing (the swarm runs three days early — pods agitating is a readable warning sign).
- **Requirements**: spore pod ~0.5 m (emissive inner glow acceptable — baked emissive in
  albedo/ORM-Emissive, not a dynamic light); gnarled tree 3–5 m with a silhouette that
  reads wrong/alien, not just "dead tree". No clips.

### 3.5 Survey camp kit — **P1**

- **Catalog keys**: `prop_survey_tent`, `prop_sensor_array`, `prop_drill_rig`,
  `prop_generator`
- **Used for**: The survey crew's camp the team escorts to/defends. Also the "survey
  equipment failure" beat needs at least one damaged-equipment moment (a tipped sensor
  array + sparks effect covers it).
- **Requirements**: 1–4 m props, Accord-industrial styling consistent with the existing
  wallastra/prop palette, base-anchored pivots, colliders authored per prefab when
  registered (cuboid approximations fine). Generator should have a baked emissive status
  strip. No clips.

### 3.6 Territorial herd predator — **P1 (reuses existing assets if scoped down)**

- **Catalog key**: `alien_herd_predator` (new) — fallback: reuse `alien_scolitex`
- **Used for**: Mission 1's primary threat — the territorial predators whose migration the
  survey crew ignores. Distinct from the Act 1 Mission 5 "wrong creatures" (enhanced-failure
  victims); these are natural fauna, dangerous but *of* the ecosystem.
- **Requirements**: quadruped herd animal, ~2–2.5 m long, herd-posture silhouette (low
  head, broad shoulders), Territory displays (plates/frills) that read as warning color.
  Clips: `Idle_Loop`, `Walk_Loop`, `Run_Loop`, `Attack_Loop`. If budget forces reuse,
  `alien_scolitex` (3.4x3.4x3.2 m) is oversized but acceptable for a first playable pass —
  note this in the Mission 1 design pass.

---

## 4. Hub furniture replacements — P2

Existing placeholder cuboids to replace (all explicitly commented "placeholder" in
`prefabs.ron`), in room-use order from the backlog's "hub rooms earn their keep" task:

- **`prop_suit_rack`** (replaces `placeholder_suit_rack`, Suit Bay) — rack frame with 2–3
  hanging **Core suit** silhouettes (`prop_core_suit` as a separate pickup/display model —
  the Suit Bay "gear up" gate needs an actual suit to pick up). Suit is the hero prop of
  the whole fiction ("Not soldiers, but people who can go where others cannot") — 1024
  texture justified, distinctive but chunky-readable design.
- **`prop_locker_set`** (replaces `placeholder_locker`) — 3-locker bank, Accord livery
  decals friendly.
- **`prop_briefing_table`** (replaces `placeholder_briefing_table`) — holo-table with
  baked emissive map surface; pairs with a briefing hologram effect (see 6.4).
- **`prop_weapon_rack`** (replaces `placeholder_weapon_rack`, Armory) — wall rack holding
  the rifle from 2.1.
- **`prop_cot`**, **`prop_locker_tall`** (optional, P2) — barracks dressing if the hub gets
  a crew quarters corner.

Requirements for all: same scale language as existing `prop_*` GLBs (base-anchored,
`model_metadata.json` scan after import), 512 textures, no clips.

---

## 5. Audio — P0/P1 (backlog "Audio baseline" depends on this)

Registered as `assets.ron` `audio:` entries with `path` + per-entry `volume`. Music via
`PlayMusicLoop`, SFX via `PlaySound`.

### 5.1 Music / ambient loops (OGG) — **P0**

| Key | Length | Used for |
|---|---|---|
| `music_menu` | 60–90 s, seamless loop | Start menu. Quiet, spacious, slightly hopeful — "the Accord at its best" tone. |
| `music_hub` | 90–120 s, seamless loop | Integration Wing hub. Low ambient hum + distant mechanical rhythm; working-station mood. |
| `music_survey_explore` | 2–3 min, seamless loop | Mission 1 exploration phase. Open-air tension, thin and airy. |
| `music_survey_action` | 60–90 s, seamless loop | Mission 1 encounter phase. Percussive escalation of the explore track (same key/tempo family for a clean crossfade). |

Requirements: 44.1 kHz, loop-safe (no silence at loop point, no tail cut), -14 LUFS-ish
mastering, all tracks avoid busy mids (they sit under dialogue/floating text).

### 5.2 UI SFX (WAV) — **P0**

| Key | Used for |
|---|---|
| `sfx_ui_click` | Every menu/button press |
| `sfx_ui_hover` | Optional hover tick |
| `sfx_briefing_sting` | Briefing trigger pop-up (currently silent) |
| `sfx_mission_complete` | Mission-end return-to-hub moment |

Requirements: < 0.5 s each, mono, no leading silence.

### 5.3 Player SFX (WAV) — **P0**

| Key | Used for |
|---|---|
| `sfx_weapon_fire` | Rifle shot (pairs with muzzle-flash effect) |
| `sfx_weapon_reload` | Reload/ammo pickup |
| `sfx_hit_impact` | Player shot connecting (generic) |
| `sfx_player_hurt` | Damage taken feedback |
| `sfx_footstep_metal` | Hub/interior footsteps (4-6 variants, or one authored-to-loop file) |
| `sfx_footstep_dirt` | Maren's Moon surface footsteps (4-6 variants) |
| `sfx_pickup` | Ammo/suit/item pickups |
| `sfx_jump` / `sfx_land` | Jump takeoff/landing (pairs with the engine's `jump_enter`/`jump_exit` overrides) |

Requirements: mono, dry but not anechoic (engine has no reverb bus — bake a touch of room
into the file where appropriate), fire/hurt must punch through the music mix.

### 5.4 World/creature SFX (WAV) — **P1**

| Key | Used for |
|---|---|
| `sfx_alien_roar` | Herd predator aggression trigger; swarm event stinger |
| `sfx_alien_death` | Death flow (pairs with ichor-burst effect) |
| `sfx_alien_movement` | Loopable movement/scuttle layer for nearby-predator tension |
| `sfx_swarm_pass` | The early swarm event flyover beat |
| `sfx_camp_generator` | Loopable survey-camp ambience layer |
| `sfx_comms_chirp` | Petra/comms line punctuation (used before real VO exists) |

---

## 6. Particle sprite textures + effect definitions — P0/P1

Every effect below is authored in `assets.ron` `effects:` (EffectDef) and needs its sprite
textures registered in `textures:` first. **Without sprites, particles render as plain
sphere meshes** — the sprite set is the actual asset request.

### 6.1 Particle sprite set (PNG, alpha) — **P0**

- **Catalog keys**: `particle_spark`, `particle_glow_soft`, `particle_smoke_puff`,
  `particle_ember`
- **Used for**: all effects below; also the WASM warmup pass (spawn each variant once at
  `position: Some((0,-100,0))` on `scene.ready` to pre-compile WebGPU pipelines).
- **Requirements**: 256x256 RGBA PNG, soft-edged, white/greyscale luminance (color is
  tinted by EffectDef `color_start/color_end`), readable at both small (sparks) and large
  (smoke) scale. Additive-friendly (bright core) for spark/glow; plain alpha for smoke.

### 6.2 Combat effects — **P0** (ship with the weapons task)

| Effect key | Composition | Used for |
|---|---|---|
| `fx_muzzle_flash` | 1-2 frame glow sprite burst, additive, at muzzle offset | Every shot |
| `fx_hit_spark` | Spark sprite burst, `EaseOut`, brief | Shot impacts (walls/targets) |
| `fx_alien_hit` | Same family, tinted cooler/darker | Hitting fauna |
| `fx_alien_death` | Ichor burst + smoke puff, `EaseOut`, gravity | Death flow, pairs with `sfx_alien_death` |
| `fx_dust_puff` | Smoke puff, low speed, falls slowly | Landing, sprint starts, predator footfalls |

### 6.3 Ambient/environment effects — **P1**

| Effect key | Composition | Used for |
|---|---|---|
| `fx_spore_drift` | Slow rising motes, large `emitter: Disc`, `Ambient` priority | Moss zone mood on Maren's Moon |
| `fx_camp_generator_smoke` | Thin smoke column from the generator stack | Survey camp dressing |
| `fx_swarm_streaks` | Fast line-ish sprites overhead, `Npc` priority | The early swarm event flyover |

### 6.4 UI/story effects — **P1/P2**

| Effect key | Composition | Used for |
|---|---|---|
| `fx_briefing_hologram` | Slow cyan glow motes above the briefing table, `Ambient` | Briefing Room centerpiece (pairs with holo-table) |
| `fx_suit_up_flash` | Short white-glow burst | Suit Bay "gear up" gate confirmation |
| `fx_pickup_sparkle` | Small upward EaseIn glints | Ammo/suit/item pickups |

---

## 7. Decal textures — P1

- **Catalog keys**: `decal_target_ring`, `decal_aoe_warning`, `decal_splat_dark`
- **Used for**: `target_indicator` (enemy selection ring — P1 with combat), predator
  territory warning circles in Mission 1 (`ProjectDecal`), permanent dark splats where
  something bad happened.
- **Requirements**: 256-512x512 RGBA PNG, white-on-alpha (engine tints via `color`),
  hard-edge ring for targeting, soft-edge splat for marks. These live in the `decals:`
  map (not `textures:`) — `target_indicator.texture` reads from `decals:` specifically.

---

## 8. UI icon atlas — P1 (needed when items/inventory/HUD land)

- **Catalog key**: `icons_items`
- **Used for**: `items.ron` `ItemDef.icon_sheet` — the InventoryPanel/ContainerPanel/shop
  icon grid: ammo, medkit/stim, Core suit, sample vial (Mira's Mission 4 seed!), currency
  chip, keycard. Also reusable for HUD status icons.
- **Requirements**: one PNG atlas, grid of square cells (suggest 8 cols x 8 rows, 64 px
  cells, transparent background), consistent stroke weight/reading distance with the
  engine's pixel UI. Row-major indexing (`col + row * cols`). Empty cells fine. Keep each
  icon silhouette readable at 32 px display size.

---

## 9. Explicitly NOT requested yet (avoid scope creep)

- **Compact faction models** (General Voss, liaison) — Act 1 Mission 3 at the earliest;
  tone there is dialogue-led.
- **Void/Thermal/Cryo/Haz suit variants** — the fiction loves them but no script beat
  needs them yet; Core only.
- **Alien "wrong creatures"** (the enhanced-failure victims of Mission 5 / Act 2) — these
  need to read *wrong*, not just alien; defer until Act 1 Missions 4-5 are being built,
  and reuse `alien_cyclop`/`alien_oculichrysalis` as stand-ins in the interim.
- **Vehicle/transport models** — missions reference transports but none needs to be seen
  on screen yet; fade-out text + sound covers departures.

---

## Suggested build order

1. 6.1 particle sprites + 5.2/5.3 audio (unblocks the "Up Next" backlog items and every
   feedback moment)
2. 2.1 rifle + 6.2 combat effects (weapons + shooting task)
3. 1.1 team characters (player identity + hub population)
4. 3.x Mission 1 environment set + 5.4 creature SFX + 3.6 predator (Mission 1)
5. 4. hub furniture replacements + 6.3/6.4 ambient effects (polish pass)
6. 8. icon atlas + 7. decals as the inventory/HUD tasks need them
