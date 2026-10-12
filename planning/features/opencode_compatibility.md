# Feature: OpenCode compatibility for ironhold-fps-demo (GLM driver, image-model pilot)

_Status: Draft (Part A awaiting review; Part B pilot done 2026-10-12, results at the bottom)_
_Planned at: `2d02e6e` (2026-10-12)_

## What
Make this repo work under OpenCode the same way `ironhold-lib` does, with `openrouter/z-ai/glm-5.3-flash` as the driver and a
vision-capable model for image interpretation. Claude Code stays fully supported. **Codex support is dropped** (Frank,
2026-10-12). Developer tooling only; nothing changes for the game.

Reference setup: `../ironhold-lib/.opencode/README.md` and `../ironhold-lib/planning/features/opencode_compatibility.md`.

## Where the repo is today (commit `6b75d34`, "Add opencode support")
- `.opencode/agents/*.md`: 7 hand-copied agents (same role text as `.claude/agents/*.md`, OpenCode frontmatter `mode: subagent`).
- `.opencode/plugins/hooks.ts` (39 lines): a hooks bridge.
- `opencode.json`: only `$schema`. No model, no permissions, no `instructions`.
- `AGENTS.md`: a full copy of `CLAUDE.md` with Codex wording ("Codex.ai/code", `.Codex/agents`), and it says agents are defined
  "three ways" including `.codex/agents/*.toml`.
- `.codex/`: committed (agents as TOML).

Problems: two copies of every instruction file that drift apart (the repo's own `CLAUDE.md` already warns agent examples go
stale after engine updates), no model routing, no permissions, Codex leftovers.

## Part A: alignment (not started)
1. **Delete `.codex/`.** Reword `AGENTS.md` and `CLAUDE.md`'s "defined three ways" sentence to two ways.
2. **One instruction source.** `CLAUDE.md` stays the source; `opencode.json` loads it with `"instructions": ["CLAUDE.md"]`.
   `AGENTS.md` becomes a short pointer or goes away. Do **not** use an `@CLAUDE.md` stub: OpenCode does not expand it and the
   stub would hide the real file (`../ironhold-lib/.opencode/README.md` fact V2).
3. **Agents built from the Claude originals.** Replace the 7 copies in `.opencode/agents/` by `opencode.json` agent entries
   whose `prompt` is `{file:.claude/agents/<name>.md}`, plus a small sync check so a new Claude agent cannot be forgotten.
   (Frontmatter differs: Claude uses `tools: [..]`, OpenCode uses `mode`/`permission`; the prompt body is shared.)
4. **`opencode.json` content:** `model` = `openrouter/z-ai/glm-5.3-flash`; `small_model`; a bash allow-list
   (`python scripts/*`, `tools/ironhold_cli/ironhold.exe *`, `git status*`, `git diff*`, `ls*`, `grep*`); `external_directory`
   `ask`; a per-agent model map (see Part B for the image model).
5. **Hooks.** Claude hooks today: `scripts/check_asset_size.py` on prompt submit and a Stop reminder. Compare `hooks.ts`
   with the lib's `claude_hooks_bridge.ts` and keep one bridge; verify the asset-size check actually fires under OpenCode.
6. **Docs:** `.opencode/README.md` (models, how to run on this Windows machine: `nvs use 24.21`), and a note in `CLAUDE.md`.
7. **Verify:** `opencode debug config` shows the intended driver and agents; run one agent from each category headless.

Open decisions for Frank (Part A):
- Is a committed `AGENTS.md` still wanted at all (OpenCode finds `CLAUDE.md` through `instructions`)?
- Keep the 7 agents' tool restrictions (`tools: [Read, Write, Edit, Glob, Grep, Bash]`) as OpenCode `permission` entries, or
  rely on the global allow-list?
- Do the image agents (below) need to exist as named subagents, or is the driver enough (see Part B finding on GLM)?

## Part B: image-interpretation pilot (run 2026-10-12)

### Question
Which models can reliably read the screenshots and texture images this project works with, and is the GLM driver good
enough that no separate vision agent is needed?

### Catalog facts (OpenCode 1.18.33 `opencode models --verbose`, 2026-10-12)
- `openrouter/z-ai/glm-5.3-flash` is listed with `input.image: true` and tool calls, at $0.15/$0.50 per million tokens. So
  the driver may read images itself. The pilot checks that against real runs instead of trusting the catalog.
- Free models with image input and tool calls: OpenRouter `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`,
  `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, `thinkingmachines/inkling:free`, `thinkingmachines/inkling-small:free`;
  Zen `mimo-v2.6-flash-free`, `step-5-preview-free`, `longcat-2.5-preview-free`, `exo-free`, `space-bunny-free`,
  `muse-spark-1.3-contributor-free`; Google API `gemma-4-31b-it`, `gemma-4-26b-a4b-it` (free).
- Gemini: `google/gemini-3.8-flash` is $0.75/$3.75 per million tokens. The lib README warns
  these are billed unless the key's project has no billing account; check in AI Studio.
- Free endpoints rate-limit (about 20 requests per minute) and Zen free models may use prompts for training; the fixtures
  here are the project's own screenshots and CC0 textures, so that is acceptable.

### Method
`tools/opencode_image_pilot.py` (this repo). Same safety rules as the lib's `opencode_pilot.py`:
- nothing spends money without `--go`; without it, it prints the plan and a cost estimate;
- every run is `opencode run --format json -m <provider/model> -f <image(s)>` in an **empty scratch directory** (not this repo),
  using a dedicated no-tools agent whose prompt only says "answer about the attached image(s), JSON only", so the 25-30k-token
  repo/skills baseline is not paid per run (the pilot measures `tokens_in` to confirm);
- sequential runs, a script spend cap (default $3) on summed `step_finish` cost, pauses between free-endpoint runs, and each
  run's session is deleted afterwards;
- **deterministic scoring**: each task asks for a one-line JSON object; a regex/JSON check decides pass or fail. No model
  grades another model.

### Fixtures (`tools/opencode_image_pilot/fixtures/`, generated by `--make-fixtures`, committed)
Derived from `../ironhold-lib/screenshot_baselines/` (ground truth known by construction) and this repo's textures
(downscaled to 512 px):

| Task id | Image(s) | Question | Expected |
|---|---|---|---|
| `read_top_buttons` | `ui_demo_main` | top-right button labels, left to right | `["Add","Reset","Hide B","Show B"]` |
| `count_swatches` | `ui_demo_main` | colored squares in panel A and in panel B | `{"a":3,"b":3}` |
| `read_counter` | `ui_demo_main` | number after "Count:" | `0` |
| `swatch_color` | `ui_demo_main` | color of the third square in panel A | `blue` |
| `overlap_clean` | `ui_demo_main` | do two panels overlap? | `no` |
| `overlap_planted` | panel B pasted over panel C | do two panels overlap? | `yes` |
| `clip_clean` | `ui_demo_main_390x844` | any top-bar button cut off by the screen edge? | `no` |
| `clip_planted` | same, cropped to 235 px wide so `Show B` is cut off | same | `yes` |
| `missing_button` | clean + a copy with `Show B` painted out | which button is missing in image 2? | `Show B` |
| `identical_pair` | clean + a re-encoded copy | are the two images identical? | `yes` |
| `texture_normal` | `T_Trim_01_Normal` | normal map, base color, or ORM/mask? | `normal` |
| `texture_basecolor` | `T_Trim_01_BaseColor` | same | `base color` |
| `blank_render` | all-black 1280x720 | does it show a rendered scene? | `no` |
| `blank_control` | `3rd_person_game_demo_main` | same | `yes` |

Two runs per model per task (28 runs per model); the planted/clean pairs catch models that always answer the same way.

### Models (arms)
Reference: `google/gemini-3.8-flash` (Google API and via OpenRouter) and `google/gemini-3.7-flash` (`gemini-2.5-flash` was dropped: Google no
longer offers it to new users). Driver candidate: `openrouter/z-ai/glm-5.3-flash`.
Open-weight or free: Gemma 4 31B (OpenRouter free and Google free), Nemotron 3 nano omni (free), Inkling (free), Zen
`mimo-v2.6-flash-free`, `step-5-preview-free`, `longcat-2.5-preview-free`, `exo-free`, `space-bunny-free`,
`muse-spark-1.3-contributor-free`; cheap paid open: `qwen/qwen3.8-omni-flash`, `qwen/qwen3-vl-30b-a3b-instruct`.

### Decision rules (set before running)
- **Usable for image QA:** passes at least 85% of runs overall **and** both members of every clean/planted pair in at least
  one of its two runs (so it is not answering by default), with at most 10% malformed/unparseable replies.
- **GLM is enough as the only model** if it is usable by that rule. Otherwise the image agent gets the cheapest *usable* model,
  free preferred, Gemini as the fallback.
- A free model is recommended as primary only if it also finished without a rate-limit or empty-reply failure in more than
  90% of runs.

### Results (run 2026-10-12, OpenCode 1.18.33, 16 models x 14 tasks x 2 runs, total cost $0.11)

| Model | Passed | Cost for its runs | s/run | Verdict |
|---|---|---|---|---|
| Gemini 3.8 flash via OpenRouter | 28/28 | $0.060 | 6.0 | usable (reference) |
| **GLM 5.3 flash (the driver)** | **28/28** | **$0.016** | 8.1 | **usable** |
| Qwen 3.8 omni flash | 28/28 | $0.011 | 8.5 | usable |
| Qwen3 VL 30B A3B | 28/28 | $0.006 | 3.4 | usable, fastest |
| Inkling (OpenRouter free) | 27/28 | $0 | 6.2 | usable, free (missed one `overlap_planted` run) |
| Gemma 4 31B (Google free) | 25/28 | $0 | 48 | capable but flaky: 3 of 28 runs timed out or errored |
| Nemotron 3 nano omni (free) | 23/28 | $0 | 24 | not usable: 0/2 on `texture_normal` and `clip_planted`, 2 timeouts |
| Gemini 3.8 / 3.7 flash via the Google API | 6/9, 5/11 | $0.02 | 40-68 | not measurable: "exceeded your current quota" and timeouts |
| Gemma 4 31B (OpenRouter free) | 1/6 | $0 | 74 | not measurable: rate-limited upstream |
| Zen free models (mimo, step-5, longcat, space-bunny, muse) | 0 | $0 | - | not measurable: HTTP 403 "OpenCode's free tier can only be used from within OpenCode" |
| `opencode/exo-free` | 0 | $0 | - | HTTP 410: model deprecated |

Per-task detail is in `python tools/opencode_image_pilot.py --report <results dir>` (the results were written to the session
scratchpad; the figures above are copied here). Every "not measurable" row is an availability failure, not a capability
result; the script aborts an arm after 3 consecutive infrastructure failures.

### Conclusions against the decision rules
- **GLM 5.3 flash alone is enough for image QA** (28/28, both members of every clean/planted pair, $0.0006 per run, 1.8k input
  tokens with the no-tools agent). **No separate vision agent is needed**; Part A's open question about image agents resolves
  to "driver reads images directly".
- **Fallback chain if GLM misbehaves:** `openrouter/qwen/qwen3-vl-30b-a3b-instruct` (cheapest and fastest of the 100% group),
  then `openrouter/google/gemini-3.8-flash`. Free fallback: `openrouter/thinkingmachines/inkling:free` (96%).
- **Gemini on the Google API is not a reliable image route today**: quota exceeded (so the key's project is on the free tier, with
  no billing, which also means it is not spending money) and timeouts under load. Gemini 3.8 flash through OpenRouter worked.
- **The Zen free models cannot be called from a headless `opencode run`** in this setup (HTTP 403, also from a git-initialised
  directory). Likely cause: `opencode auth list` has no OpenCode/Zen credential, so only the interactive client may use the
  free tier. **Unverified**; if confirmed it also affects any Zen free agent in `ironhold-lib`'s `.opencode/opencode.json`
  when run headless (for example the lib's pilot scripts). Worth a separate check there.

### Limits of this pilot
- The tasks are small, synthetic and easy for the top models: four models scored 100%, so the pilot separates "usable" from
  "not usable" but not the usable ones from each other. A harder second round (subtle pixel diffs, small text at 390x844,
  judging a 3D scene's lighting, reading a glTF preview) is needed before choosing between them for quality-critical work.
- Two runs per task, one machine, one day: free endpoints change by the hour.
- Only the `imgpilot` no-tools agent was tested; a real driver session also carries the repo's instruction baseline.

### Decision (Frank, 2026-10-12)
`openrouter/qwen/qwen3-vl-30b-a3b-instruct` is the **image-interpretation model** (cheapest at $0.006 per 28 runs, fastest at
3.4 s, 28/28). It is provisional: the pilot cannot separate it from GLM 5.3 flash, Qwen 3.8 omni flash and Gemini 3.8 flash
(all 28/28), so a harder second round (see "Limits") decides whether it stays. The saving over GLM is about $0.0003 per
image run, so the reason to use it is speed and keeping the driver's context small, not cost.
Untested and needed for Part A: whether an image reaches a subagent. The driver delegates with text through the `task` tool,
so the image agent would have to open the file itself with the `read` tool (which attaches images for vision models); the
pilot attached images directly with `-f` and did not cover that path.

## Part B, round 2: 3D scene interpretation (registered 2026-10-12, before the run)

### Why
Image interpretation here will be used to build and debug 3D scenes, so round 2 tests that: position, object recognition,
colors, orientation, and differences between two scene edits.

### Delegation test (done first, 2026-10-12)
Driver `glm53` (agent `driver`, only the `task` tool) delegated to a subagent `imgreader` on `qwen3-vl-30b-a3b-instruct` (only the
`read` tool) with a file path and a question. **It works end to end:** the subagent opened the PNG with `read` and the driver
relayed the correct labels. Caveats seen in the one run: the subagent first wrote its `read` call as plain text instead of making a
tool call, so the driver had to resume the session (3 driver steps, about $0.001 in total); and `opencode run` hung twice until
stdin was closed (`< /dev/null`; `tools/opencode_image_pilot.py` now passes `stdin=DEVNULL`). Image delegation therefore costs
more steps and one retry versus the driver reading the image itself.

### Fixtures
Real engine renders (`tools/opencode_image_pilot/render_scenes.py`: a throwaway project, a Fixed camera, visible WebGPU
Chromium via ironhold-lib's `test_web` helpers). One base scene with five objects at known places (red cube left, blue sphere
far, green cylinder right, orange cone far right, yellow bar on the ground pointing at the camera) and single-edit variants:
bar rotated 90 and 45 degrees, cone lying left and right, cube moved, cube nudged 0.6 units, cylinder recolored, sphere removed,
white cube added, cube scaled 1.8x, plus a re-render of the unchanged scene as the "no change" control.

### Tasks (28, `tools/opencode_image_pilot/hard_tasks.py`)
position (5), recognition (6: three shapes, three object counts), color (3), orientation (6: bar toward/across/diagonal, cone tip
up/left/right), diff (8: moved, nudged, recolored, removed, added, rotated, scaled, none). Scoring is by synonym lists on a
one-line JSON answer. Every task of a group (counts, bar direction, cone tip, diff) must pass in at least one run, so a model that
always gives the same answer cannot pass.

### Models and runs
`glm53`, `qwen_vl`, `qwen_omni`, `gemini38_or`, `inkling` (the five that were usable in round 1), 3 runs each = 420 runs, cap $3.

### Decision rule
A model is **eligible** as image model for scene work if it passes at least 85% of all runs and at least 75% in every category.
Among eligible models: lowest cost per run, then lowest latency. If none is eligible, the best overall rate per category decides
which categories get a human check.

### Follow-ups
- Part A (alignment) is not started; it needs Frank's answers to the open decisions above.
- Check whether the Zen free tier works headless in `ironhold-lib` (finding above).
- Optional harder image round (above).


### Part B, round 2 results (2026-10-12)

420 runs, 5 models x 28 tasks x 3 runs, total cost $0.34. Two defects in my own test were found after the run, so the
numbers below exclude `diff_recolored` (the "purple" fixture still renders a green cylinder: the colour is defined on the shared
prefab, so the per-variant override never reached the render; models answering "none" were right) and rescore `pos_closest`
(answers "yellow box/cuboid/prism" were correct; the synonym list for "bar" lacked them, now fixed). This is a post-hoc change to the
registered scoring; it only touches those two tasks.

| model | position | recognition | color | orientation | diff | overall | verdict |
|---|---|---|---|---|---|---|---|
| glm53 | 15/15 | 18/18 | 9/9 | 18/18 | 21/21 | 100% | eligible |
| gemini38_or | 15/15 | 18/18 | 9/9 | 18/18 | 21/21 | 100% | eligible (costliest) |
| qwen_omni | 15/15 | 18/18 | 9/9 | 18/18 | 20/21 | 99% | eligible |
| inkling:free | 12/15 | 18/18 | 9/9 | 15/18 | 19/21 | 90% | eligible, weakest margin |
| qwen_vl | 15/15 | 15/18 | 9/9 | 15/18 | 14/21 | 84% | NOT eligible (<85%, 67% in two categories) |

Conclusions: Qwen3 VL 30B A3B fails the registered rule (cone pointing left, 5-object count, rotation and no-change diffs), so it
is no longer the provisional image model. GLM 5.3 flash reads the 3D renders itself with no misses, so the driver needs no image
subagent; delegation also costs extra steps (see delegation test). Follow-up: fix the `cylinder_purple` fixture (per-variant prefab)
and re-run `diff_recolored` before treating colour-change detection as measured.

#### Recolour re-run (2026-10-12)

Fixture fixed (prefab id now includes the colour, `render_scenes.py --only cylinder_purple`; the base render is byte-identical).
Only `diff_recolored` was re-run, 3 runs per model, $0.01: qwen_vl 3/3, qwen_omni 3/3, gemini38_or 3/3, inkling 3/3,
glm53 2/3 (one run said "green cone"). Colour-change detection is now measured; the diff column becomes glm53 23/24 (the full
24 with this task), qwen_vl 17/24, qwen_omni 23/24, gemini38_or 24/24, inkling 22/24. No eligibility verdict changes; glm53 still
passes every category above 75% and overall above 85%.
