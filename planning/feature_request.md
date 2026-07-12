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

## Scripted cutscene camera / sequencer

**What we need**: Directable cutscenes for dramatic/emotional beats — cuts between framed shots, camera moves along an authored path (dolly/pan/track), timed holds, letterbox bars, and the ability to temporarily take control away from the player during a sequence, driven entirely from RON (no engine recompile).

**Engine gap**: There is no cutscene/sequencer system. Camera options today are `player`-tagged orbit camera, `"flycam"` free-fly, and split/party multi-cameras (`docs/20_data_formats.md`) — all built for live player control, not authored playback. There's no keyframed camera path, no cut/shot list, no letterbox/aspect-ratio bars, and no "disable player input for scene X seconds" primitive. Not listed on `docs/50_roadmap_and_milestones.md`.

**Workaround**: Approximate dramatic moments with what exists today — fixed `CameraConfig` framing, `CameraShake`, lighting shifts via `ModifyStat`/scene transitions, `ShowFloatingText` for beat text, and hard scene cuts (`LoadScene`) standing in for a "cut". No true camera move, no letterboxing, no player-input lock. See the `cinematics-director` agent (`.claude/agents/cinematics-director.md`) for how to compose the best possible shot with current tools.
