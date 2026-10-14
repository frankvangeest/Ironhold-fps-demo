# Player character model (primary player)

## Goal

Replace the placeholder capsule player with the skinned character model
(`character-male-01.glb`) so the player has a real body: shadow-casting,
animatable (idle/walk/run/jump), and ready for third-person framing later
(cutscenes, mirrors, mission scenes with visible companions).

Status: **implemented and browser-verified** (2026-10-14). Hub
(`integration_wing`) spawns `player_character`; orbit-camera test scene
`scenes/char_test.scene.ron` verifies the clips visually.

## What exists already

- `assets/models/Characters/character-male-01.glb` - skinned mannequin,
  1 embedded clip (`Idle_Loop`, satisfies the engine's "at least one embedded
  clip" requirement for animation retargeting).
- `assets/models/Characters/character-animations/*.glb` - animation-only packs
  (0 meshes). Clip names verified with `ironhold.exe inspect glb`:
  - `locomotion.glb`: Idle_Loop, Walk_Loop, Jog_Fwd_Loop, Sprint_Loop,
    Jump_Start (1.67s), Jump_Loop, Jump_Land, crouch/slide/roll variants.
  - `ranged.glb`: Pistol_Aim_Neutral/Shoot/Reload, OverhandThrow (weapons task).
  - `melee.glb`: Sword_*/Punch_*/Melee_* (weapons task).
  - `hit_death.glb`: Death01, Hit_Chest/Head/Knockback (enemy/death task).
- Engine: player prefab can be `kind: Actor` + `animation_policy` (GLB players
  are first-class: collider comes from `movement.collider_radius/height`).
  `jump_enter`/`jump_exit` are reserved override IDs the movement system fires
  automatically; a policy without them logs a WARN on every jump.

## Implementation (what was done)

1. `assets.ron` - registered `character_male_01` (model) and `anim_locomotion`
   (animation source). Other packs stay unregistered until their tasks land
   (unused catalog keys are `--strict` noise).
2. `prefabs/animation/player_male.ron` - AnimationPolicy:
   - `animation_sources: ["anim_locomotion"]`
   - base: idle=Idle_Loop, walk=Walk_Loop, run=Sprint_Loop, jump_loop=Jump_Loop
   - overrides: `jump_enter` -> Jump_Start, `jump_exit` -> Jump_Land
     (`looping: false`, short `duration` so the one-shot releases back to base
     locomotion).
3. `prefabs.ron` - new `"player_character"` prefab (Actor + policy), same
   movement tuning and FirstPerson camera as the old capsule `"player"` prefab
   (which stays as fallback/test fixture).
4. `integration_wing.scene.ron` - `player_01` now spawns `player_character`.

## Verification results (2026-10-14, headed msedge via Playwright)

- `ironhold.exe validate`: all 10 files valid.
- **Locomotion clips verified via orbit test scene** (`char_test.scene.ron` +
  `player_character_orbit` prefab): console DIAG log shows the full resolver
  chain firing on input - `Idle_Loop -> Walk_Loop -> Sprint_Loop ->
  Jump_Start` - and screenshots confirm the sprint pose mid-stride. Model
  scale is correct against a door frame + barrel reference; pivot is at the
  feet; shadow casts cleanly.
- **FirstPerson + body**: the engine does NOT hide the player's own mesh -
  with `eye_offset (0.0, 1.7, 0.0)` the camera sat inside the head mesh
  (looking down showed the inside of the skull). Fixed by pushing the eye
  forward: `eye_offset: (0.0, 1.6, -0.30)` (0.3m < 0.4m collider radius, so
  the camera stays within the capsule footprint). Neutral pitch is clean;
  looking down now shows the body from outside (dark when backlit - normal
  PBR, reads fine in lit areas). The black wedge at the bottom of some views
  is the body's own cast shadow on the floor, not the mesh.
- Console noise (benign): `animation_sources: clip 'Idle_Loop' overrides an
  earlier definition` - expected "last source wins" since Idle_Loop exists
  both in the model GLB and the locomotion pack. A transient
  `remove<NoFrustumCulling>` bevy command error storm appeared once and not
  on a repeat run - a race, present regardless of this change; worth
  remembering if it recurs.

## Movement model findings (2026-10-14, empirical)

The full input matrix was tested in the orbit scene to diagnose Frank's
"camera looks at the character's face on A/D" report:

| Input | Behavior |
|---|---|
| `forward`/`backward` (W/S) | works, character-relative |
| mouse-look yaw | rotates the character WITH the camera (in sync) |
| `left`/`right` (default A/D) | rotates the BODY only on the Actor path; FirstPerson camera keeps its own world yaw -> the body spins under a stationary camera and the face swings into view |
| `strafe_mouse_button` toggle (hold LMB + left/right) | strafes correctly (verified: real lateral movement + Walk_Loop) |
| `strafe_left`/`strafe_right` (Q/E defaults) | dead on the Actor path in every configuration tested |

Engine-version cross-check (scratch projects in temp, 2026-10-14): the rotate
desync is **Actor-path-specific, not a version issue** - a capsule
(`kind: Primitive`) FP player rotates camera+body as ONE UNIT on both our
pinned engine (`222e446`) and the engine repo's `integration` branch, while a
GLB Actor FP player desyncs on both. `strafe_left`/`strafe_right` are dead for
everyone on the pin; integration fixed them for primitives but they remain
dead for Actors. So updating our pin would fix nothing for the character
player. Full matrix + repro details in `planning/feature_request.md`.

Conclusion: unconditional A/D strafe is **not** achievable in data. The
`strafe_left`/`strafe_right` keys are unwired on the Actor path despite being
documented as unconditional strafe (filed in `planning/feature_request.md` together with
the FirstPerson rotate-desync issue). Interim binding on `player_character`:
A/D -> `strafe_left`/`strafe_right` (forward-compatible: they start working
the moment the engine honors them), rotate moved to arrow keys. Side effect:
A/D are currently inert; W/S + mouse-look fully work.

## Out of scope (tracked in backlog)

- Female variant + NPC crew prefabs (Mission 1 needs them).
- melee/ranged/hit_death packs (weapons + enemy-death tasks register those).
- Third-person cutscene framing (camera_modes registry exists engine-side if
  needed later).
