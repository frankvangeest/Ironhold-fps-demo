# Feature Requests (Engine)

Features this game needs that the Ironhold engine does not yet support. When the engine gains a capability, move the entry to the backlog and implement it.

Reference engine status: `docs/STATUS.md` and `docs/50_roadmap_and_milestones.md`.

---

<!-- Format:
## Feature name
**What we need**: description of the desired behaviour in-game
**Engine gap**: what is currently missing or planned (link to docs section if relevant)
**Workaround**: any partial workaround possible today, or "none"
-->

## FirstPerson movement model (strafe + single rotation axis)

**What we need**: Genre-correct FPS controls. A/D must strafe unconditionally (no modifier key), and the character body's yaw must be slaved to the camera yaw as one unit — in FirstPerson there should be no separate "rotate the body without turning the camera" axis at all.

**Engine gap** — empirically isolated 2026-10-14 to the **Actor (GLB) player path**. Test matrix across engine versions (pinned `222e446` vs `integration` @ `e3914a1`), capsule vs GLB Actor, scratch projects served from temp (`fp_check`/`fp_check2`), orbit and FirstPerson:

| Test | Pinned (222e446) | Integration |
|---|---|---|
| Capsule FP + A (`left` rotate) | camera + body rotate as one unit (world swivels) | same |
| **Actor FP + A (`left` rotate)** | **desync: body turns, camera keeps its own world yaw + world-space-positioned eye offset -> the model's head/shoulder sweeps into view** | **same desync** |
| Capsule + Q (`strafe_left`) | **dead** (pixel-identical before/after) | **works** (fixed between pin and integration, unmerged to main as of ebc338c) |
| **Actor + Q (`strafe_left`)** | dead (orbit + FP) | **still dead** |

So three distinct findings:
1. **FirstPerson rotate desync is Actor-only** — Primitive capsule players rotate camera+body as one unit on every engine version tested; GLB Actor players desync on both the pinned and the integration engine. The engine's own `camera_modes` demo never shows this because its FP player is a capsule. Root cause guess: on the Actor path, `left`/`right` rotate turns the entity while the FP camera's eye-offset/yaw composition does not follow the body rotation the way the Primitive path's does.
2. **`strafe_left`/`strafe_right` were dead for everyone on the pinned engine** (docs promise unconditional camera-relative strafe) — fixed for Primitive players somewhere between `222e446` and integration, **still dead for Actor players** on integration.
3. `strafe_mouse_button` toggle (hold LMB: `left`/`right` become strafe) works on both engines for both player kinds — the only working strafe path today.

**Workaround**: Partial, all data-side (already applied to `player_character` in `prefabs.ron`): A/D rebound to `strafe_left`/`strafe_right` (inert until the engine fixes the Actor strafe path — forward-compatible), rotate moved to arrow keys (removes the face-swing from casual play; W/S + mouse-look fully work). No data-only path to unconditional A/D strafe exists. An engine fix should cover both the Actor rotate desync and Actor strafe keys; mouse-yaw already rotates body+camera in sync, so "slave body yaw to camera yaw and strafe A/D" is the target behavior.

## Scripted cutscene camera / sequencer

**What we need**: Directable cutscenes for dramatic/emotional beats — cuts between framed shots, camera moves along an authored path (dolly/pan/track), timed holds, letterbox bars, and the ability to temporarily take control away from the player during a sequence, driven entirely from RON (no engine recompile).

**Engine gap**: There is no cutscene/sequencer system. Camera options today are `player`-tagged orbit camera, `"flycam"` free-fly, and split/party multi-cameras (`docs/20_data_formats.md`) — all built for live player control, not authored playback. There's no keyframed camera path, no cut/shot list, no letterbox/aspect-ratio bars, and no "disable player input for scene X seconds" primitive. Not listed on `docs/50_roadmap_and_milestones.md`.

**Workaround**: Approximate dramatic moments with what exists today — fixed `CameraConfig` framing, `CameraShake`, lighting shifts via `ModifyStat`/scene transitions, `ShowFloatingText` for beat text, and hard scene cuts (`LoadScene`) standing in for a "cut". No true camera move, no letterboxing, no player-input lock. See the `cinematics-director` agent (`.claude/agents/cinematics-director.md`) for how to compose the best possible shot with current tools.
