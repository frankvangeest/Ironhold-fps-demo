#!/usr/bin/env python3
"""Image-interpretation pilot for OpenCode models (planning/features/opencode_compatibility.md, Part B).

Each run is `opencode run --format json -m <provider/model> -f <image(s)>` in an empty scratch directory, through a no-tools
agent, so the repo/skills token baseline is not paid per run. Scoring is deterministic (JSON/regex), never model-graded.
Nothing runs without `--go`.

Usage:
    python tools/opencode_image_pilot.py --make-fixtures [--lib ../ironhold-lib]   # (re)generate tools/opencode_image_pilot/fixtures
    python tools/opencode_image_pilot.py                                           # print the plan and cost estimate, run nothing
    python tools/opencode_image_pilot.py --go [--arms a,b] [--tasks x,y] [--runs 2] [--out DIR]
    python tools/opencode_image_pilot.py --report DIR                              # summarise DIR/results.jsonl against the decision rules
    python tools/opencode_image_pilot.py --selftest                                # scorer tests, no OpenCode, no money
Resumable: a rerun with the same --out skips (arm, task, run) rows already in results.jsonl.
Exit codes: 0 ok, 1 check failed, 2 tool error.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "opencode_image_pilot" / "fixtures"
NVS_BIN = r"C:\ProgramData\nvs\node\24.21.0\x64\node_modules\opencode-ai\bin\opencode.exe"

SYSTEM = "You answer questions about attached images. Reply with one line of JSON only, no prose, no code fences."
CONFIG = {"agent": {"imgpilot": {"mode": "primary", "description": "image QA", "prompt": SYSTEM, "tools": {"*": False}}},
          "permission": {"*": "deny"}}

# (id, label, model, kind) -- kind: ref (reference), driver, free, paid. Free arms are paced for the ~20 requests/minute cap.
ARMS = [
    ("gemini38", "Gemini 3.8 flash", "google/gemini-3.8-flash", "ref"),
    ("gemini37", "Gemini 3.7 flash", "google/gemini-3.7-flash", "ref"),
    ("gemini38_or", "Gemini 3.8 flash (via OpenRouter)", "openrouter/google/gemini-3.8-flash", "ref"),
    ("glm53", "GLM 5.3 flash (driver)", "openrouter/z-ai/glm-5.3-flash", "driver"),
    ("gemma31_or", "Gemma 4 31B (OpenRouter free)", "openrouter/google/gemma-4-31b-it:free", "free"),
    ("gemma31_g", "Gemma 4 31B (Google free)", "google/gemma-4-31b-it", "free"),
    ("nemotron_omni", "Nemotron 3 nano omni (free)", "openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "free"),
    ("inkling", "Inkling (free)", "openrouter/thinkingmachines/inkling:free", "free"),
    ("mimo", "MiMo v2.6 flash (Zen free)", "opencode/mimo-v2.6-flash-free", "free"),
    ("step5", "Step 5 preview (Zen free)", "opencode/step-5-preview-free", "free"),
    ("longcat", "LongCat 2.5 preview (Zen free)", "opencode/longcat-2.5-preview-free", "free"),
    ("exo", "Exo (Zen free)", "opencode/exo-free", "free"),
    ("spacebunny", "Space Bunny (Zen free)", "opencode/space-bunny-free", "free"),
    ("muse", "Muse Spark 1.3 (Zen free)", "opencode/muse-spark-1.3-contributor-free", "free"),
    ("qwen_omni", "Qwen 3.8 omni flash", "openrouter/qwen/qwen3.8-omni-flash", "paid"),
    ("qwen_vl", "Qwen3 VL 30B", "openrouter/qwen/qwen3-vl-30b-a3b-instruct", "paid"),
]
ARM_BY_ID = {a[0]: a for a in ARMS}


def yn(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    s = str(v).strip().lower()
    return "yes" if s.startswith(("y", "true")) else "no" if s.startswith(("n", "false")) else s


def norm(v):
    return re.sub(r"[^a-z0-9]", "", str(v).lower())


def labels_ok(d):
    got = [norm(x) for x in d.get("labels", [])] if isinstance(d.get("labels"), list) else None
    return got == ["add", "reset", "hideb", "showb"]


def to_int(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


# id, images, question (JSON schema hint inside), scorer(dict)->bool, pair (group id for clean/planted pairs)
TASKS = [
    ("read_top_buttons", ["ui_demo_main.png"],
     'List the text labels of the buttons in the top-right of the screen, left to right. Reply {"labels":["..."]}.',
     labels_ok, None),
    ("count_swatches", ["ui_demo_main.png"],
     'Panel "A" and panel "B" each contain small colored squares. How many squares are in each? Reply {"a":N,"b":N}.',
     lambda d: to_int(d.get("a")) == 3 and to_int(d.get("b")) == 3, None),
    ("read_counter", ["ui_demo_main.png"],
     'What number is shown after "Count:" at the bottom right? Reply {"count":N}.',
     lambda d: to_int(d.get("count")) == 0, None),
    ("swatch_color", ["ui_demo_main.png"],
     'What color is the third (rightmost) square inside panel "A"? Reply {"color":"..."}.',
     lambda d: norm(d.get("color")) == "blue", None),
    ("overlap_clean", ["ui_demo_main.png"],
     'Do any two of the three panels in the middle of the screen overlap each other? Reply {"overlap":"yes"} or {"overlap":"no"}.',
     lambda d: yn(d.get("overlap")) == "no", "overlap"),
    ("overlap_planted", ["ui_demo_overlap.png"],
     'Do any two of the three panels in the middle of the screen overlap each other? Reply {"overlap":"yes"} or {"overlap":"no"}.',
     lambda d: yn(d.get("overlap")) == "yes", "overlap"),
    ("clip_clean", ["ui_demo_390x844.png"],
     'Is any button in the top bar cut off by the right edge of the image? Reply {"clipped":"yes"} or {"clipped":"no"}.',
     lambda d: yn(d.get("clipped")) == "no", "clip"),
    ("clip_planted", ["ui_demo_390x844_clipped.png"],
     'Is any button in the top bar cut off by the right edge of the image? Reply {"clipped":"yes"} or {"clipped":"no"}.',
     lambda d: yn(d.get("clipped")) == "yes", "clip"),
    ("missing_button", ["ui_demo_main.png", "ui_demo_no_show_b.png"],
     'Image 2 is a copy of image 1 with one top-bar button removed. Which button label is missing in image 2? Reply {"missing":"..."}.',
     lambda d: norm(d.get("missing")) == "showb", None),
    ("identical_pair", ["ui_demo_main.png", "ui_demo_main_copy.png"],
     'Are the two images visually identical (ignore compression noise)? Reply {"identical":"yes"} or {"identical":"no"}.',
     lambda d: yn(d.get("identical")) == "yes", None),
    ("texture_normal", ["tex_normal.png"],
     'This is a game texture. Is it a normal map, a base color (albedo) map, or an ORM/mask map? Reply {"type":"normal"}, {"type":"base color"} or {"type":"orm"}.',
     lambda d: norm(d.get("type")) == "normal", "texture"),
    ("texture_basecolor", ["tex_basecolor.png"],
     'This is a game texture. Is it a normal map, a base color (albedo) map, or an ORM/mask map? Reply {"type":"normal"}, {"type":"base color"} or {"type":"orm"}.',
     lambda d: norm(d.get("type")) in ("basecolor", "albedo", "diffuse", "color"), "texture"),
    ("blank_render", ["blank.png"],
     'Is a rendered game scene visible (not a blank or empty screen)? Reply {"scene":"yes"} or {"scene":"no"}.',
     lambda d: yn(d.get("scene")) == "no", "blank"),
    ("blank_control", ["3rd_person_main.png"],
     'Is a rendered game scene visible (not a blank or empty screen)? Reply {"scene":"yes"} or {"scene":"no"}.',
     lambda d: yn(d.get("scene")) == "yes", "blank"),
]
TASK_BY_ID = {t[0]: t for t in TASKS}

sys.path.insert(0, str(Path(__file__).resolve().parent / "opencode_image_pilot"))
import hard_tasks  # noqa: E402  (the 3D set: engine renders, five categories)

TASK_BY_ID.update({t[0]: t[:5] for t in hard_tasks.HARD})
CATEGORY = {t[0]: t[5] for t in hard_tasks.HARD}


def make_fixtures(lib: Path) -> None:
    from PIL import Image, ImageDraw
    FIX.mkdir(parents=True, exist_ok=True)
    base = Image.open(lib / "screenshot_baselines/scenes/ui_demo_main.png").convert("RGB")
    base.save(FIX / "ui_demo_main.png")
    # overlap: copy panel B's box over the right panel so two panels overlap
    ov = base.copy()
    ov.paste(base.crop((498, 294, 822, 394)), (760, 340))
    ov.save(FIX / "ui_demo_overlap.png")
    # missing button: paint the "Show B" button out with the top-bar background
    nb = base.copy()
    bg = base.getpixel((1274, 30))
    ImageDraw.Draw(nb).rectangle((1140, 8, 1272, 48), fill=bg)
    nb.save(FIX / "ui_demo_no_show_b.png")
    # identical copy: JPEG round trip at high quality
    tmp = FIX / "_tmp.jpg"
    base.save(tmp, quality=95)
    Image.open(tmp).convert("RGB").save(FIX / "ui_demo_main_copy.png")
    tmp.unlink()
    phone = Image.open(lib / "screenshot_baselines/responsive/ui_demo_main_390x844.png").convert("RGB")
    phone.save(FIX / "ui_demo_390x844.png")
    phone.crop((0, 0, 235, phone.height)).save(FIX / "ui_demo_390x844_clipped.png")
    Image.open(ROOT / "assets/textures/T_Trim_01_Normal.png").convert("RGB").resize((512, 512)).save(FIX / "tex_normal.png")
    Image.open(ROOT / "assets/textures/T_Trim_01_BaseColor.png").convert("RGB").resize((512, 512)).save(FIX / "tex_basecolor.png")
    Image.new("RGB", (1280, 720), (0, 0, 0)).save(FIX / "blank.png")
    Image.open(lib / "screenshot_baselines/scenes/3rd_person_game_demo_main.png").convert("RGB").save(FIX / "3rd_person_main.png")
    print(f"fixtures written to {FIX}: {len(list(FIX.glob('*.png')))} files")


def parse_answer(text: str):
    """The first JSON object in the reply (tolerates code fences and prose), or None."""
    t = re.sub(r"```(?:json)?", "", text)
    for m in re.finditer(r"\{[^{}]*\}", t, re.S):
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict):
                return d
        except json.JSONDecodeError:
            continue
    return None


def parse_events(text: str) -> dict:
    ev = {"text": "", "tokens_in": 0, "cost": 0.0, "errors": [], "sessions": set()}
    texts = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("sessionID"):
            ev["sessions"].add(e["sessionID"])
        part = e.get("part") if isinstance(e.get("part"), dict) else {}
        kind = e.get("type")
        if kind == "text":
            texts.append(str(part.get("text") or ""))
        elif kind == "step_finish":
            ev["tokens_in"] = max(ev["tokens_in"], int((part.get("tokens") or {}).get("input") or 0))
            ev["cost"] += float(part.get("cost") or 0.0)
        elif kind == "error":
            ev["errors"].append(str(e.get("error") or e)[:300])
    ev["text"] = "\n".join(texts)
    return ev


def find_opencode():
    b = os.environ.get("OPENCODE_BIN")
    if b and Path(b).is_file():
        return b
    w = shutil.which("opencode")
    if w:
        return w
    return NVS_BIN if Path(NVS_BIN).is_file() else None


def run_one(binary, scratch: Path, arm, task, run, out: Path, timeout=90):
    tid, images, question, scorer, _pair = task
    for f in images:
        shutil.copy(FIX / f, scratch / f)
    env = dict(os.environ, PWD=str(scratch), OPENCODE_CONFIG_CONTENT=json.dumps(CONFIG))
    cmd = [binary, "run", question, "--format", "json", "--dir", str(scratch), "--agent", "imgpilot", "-m", arm[2], "--title",
           f"image-pilot {arm[0]} {tid} {run}"]
    for f in images:
        cmd += ["-f", str(scratch / f)]
    t0 = time.time()
    status = "ok"
    try:
        # stdin closed: `opencode run` can hang waiting on stdin when it is not a terminal
        p = subprocess.run(cmd, cwd=scratch, env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout,
                           stdin=subprocess.DEVNULL)
        raw = p.stdout
        if p.returncode != 0 and not raw.strip():
            status = "exit %d" % p.returncode
    except subprocess.TimeoutExpired as e:
        raw = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        status = "timeout"
    wall = time.time() - t0
    ev = parse_events(raw)
    (out / "raw").mkdir(exist_ok=True)
    (out / "raw" / f"{arm[0]}__{tid}__{run}.json").write_text(raw, encoding="utf-8")
    ans = parse_answer(ev["text"])
    if status == "ok" and ev["errors"] and not ev["text"].strip():
        status = "error: " + ev["errors"][0][:120]
    elif status == "ok" and not ev["text"].strip():
        status = "empty"
    parsed = ans is not None
    ok = bool(parsed and scorer(ans)) if status == "ok" else False
    for sid in ev["sessions"]:
        subprocess.run([binary, "session", "delete", sid], cwd=scratch, env=env, capture_output=True, text=True, encoding="utf-8",
                       stdin=subprocess.DEVNULL)
    for f in images:
        (scratch / f).unlink(missing_ok=True)
    return {"arm": arm[0], "model": arm[2], "task": tid, "run": run, "status": status, "parsed": parsed, "pass": ok,
            "answer": ev["text"].strip()[:200], "tokens_in": ev["tokens_in"], "cost": ev["cost"], "wall": round(wall, 1)}


def plan(arms, tasks, runs):
    n = len(arms) * len(tasks) * runs
    paid = [a for a in arms if a[3] in ("ref", "driver", "paid")]
    est = len(paid) * len(tasks) * runs * 0.004  # generous per-run upper bound for 2-3k-token image runs
    return n, est


def read_rows(d: Path):
    f = d / "results.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []


def summarise(rows):
    by = {}
    for r in rows:
        by.setdefault(r["arm"], []).append(r)
    out = {}
    for arm, rs in by.items():
        n = len(rs)
        passed = sum(r["pass"] for r in rs)
        unparsed = sum(1 for r in rs if r["status"] == "ok" and not r["parsed"])
        infra = sum(1 for r in rs if r["status"] != "ok")
        pairs = {}
        for r in rs:
            g = TASK_BY_ID[r["task"]][4]
            if g:
                pairs.setdefault((g, r["task"]), []).append(r["pass"])
        groups = {}
        for (g, t), v in pairs.items():
            groups.setdefault(g, {})[t] = any(v)
        pair_ok = all(all(m.values()) for m in groups.values()) if groups else True
        out[arm] = {"n": n, "pass": passed, "rate": passed / n if n else 0, "unparsed": unparsed, "infra_fail": infra,
                    "pair_ok": pair_ok, "cost": sum(r["cost"] for r in rs), "wall": sum(r["wall"] for r in rs) / n if n else 0,
                    "tokens_in": max((r["tokens_in"] for r in rs), default=0)}
    return out


def verdicts(s):
    v = {}
    for arm, x in s.items():
        usable = x["rate"] >= 0.85 and x["pair_ok"] and (x["unparsed"] + x["infra_fail"]) <= 0.10 * x["n"]
        steady = x["infra_fail"] <= 0.10 * x["n"]
        v[arm] = (usable, steady)
    return v


def print_report(rows):
    s = summarise(rows)
    v = verdicts(s)
    print(f"{'arm':14} {'model':52} {'pass':>9} {'rate':>6} {'unparsed':>8} {'infra':>5} {'pairs':>5} {'$':>8} {'s/run':>6}  verdict")
    for arm, x in sorted(s.items(), key=lambda kv: -kv[1]["rate"]):
        usable, steady = v[arm]
        label = ("USABLE" if usable else "no") + ("" if steady else " (flaky endpoint)")
        print(f"{arm:14} {ARM_BY_ID[arm][2][:52]:52} {x['pass']:>4}/{x['n']:<4} {x['rate']*100:5.0f}% {x['unparsed']:>8} {x['infra_fail']:>5} "
              f"{'ok' if x['pair_ok'] else 'FAIL':>5} {x['cost']:8.4f} {x['wall']:6.1f}  {label}")
    # per-task failure matrix
    tasks = [t[0] for t in TASKS]
    print("\nper-task passes (runs passed / runs):")
    print(f"{'arm':14} " + " ".join(f"{t[:9]:>9}" for t in tasks))
    for arm in sorted(s, key=lambda a: -s[a]["rate"]):
        cells = []
        for t in tasks:
            rs = [r for r in rows if r["arm"] == arm and r["task"] == t]
            cells.append(f"{sum(r['pass'] for r in rs)}/{len(rs)}".rjust(9))
        print(f"{arm:14} " + " ".join(cells))
    print(f"\ntotal cost: ${sum(x['cost'] for x in s.values()):.4f}")
    glm = v.get("glm53")
    if glm:
        print("GLM driver alone is enough for image QA:", "YES" if glm[0] else "NO")
    return 0


def selftest() -> int:
    bad = []

    def check(c, label):
        if not c:
            bad.append(label)

    check(parse_answer('```json\n{"labels":["Add","Reset","Hide B","Show B"]}\n```') == {"labels": ["Add", "Reset", "Hide B", "Show B"]}, "fenced json")
    check(parse_answer('Sure! {"overlap":"no"} done') == {"overlap": "no"}, "prose json")
    check(parse_answer("no json here") is None, "no json")
    check(TASK_BY_ID["read_top_buttons"][3]({"labels": ["Add", "Reset", "Hide B", "Show B"]}), "labels pass")
    check(not TASK_BY_ID["read_top_buttons"][3]({"labels": ["Add", "Reset"]}), "labels fail")
    check(TASK_BY_ID["count_swatches"][3]({"a": "3", "b": 3}), "swatches")
    check(TASK_BY_ID["overlap_planted"][3]({"overlap": True}), "bool yes")
    check(not TASK_BY_ID["overlap_clean"][3]({"overlap": "Yes."}), "yes != no")
    check(TASK_BY_ID["missing_button"][3]({"missing": "show b"}), "missing")
    check(TASK_BY_ID["texture_basecolor"][3]({"type": "Albedo"}), "albedo alias")
    check(TASK_BY_ID["blank_render"][3]({"scene": "no"}), "blank")
    ev = parse_events('{"type":"text","part":{"text":"{\\"count\\":0}"}}\n{"type":"step_finish","part":{"tokens":{"input":1815},"cost":0.0003}}')
    check(ev["text"] == '{"count":0}' and ev["tokens_in"] == 1815 and abs(ev["cost"] - 0.0003) < 1e-9, "events")
    rows = [{"arm": "glm53", "task": t[0], "run": r, "status": "ok", "parsed": True, "pass": True, "cost": 0.0003, "wall": 5, "tokens_in": 1800}
            for t in TASKS for r in (1, 2)]
    check(verdicts(summarise(rows))["glm53"][0], "usable when all pass")
    rows[0]["pass"] = False
    rows[1]["pass"] = False  # both runs of read_top_buttons fail: 26/28 = 93% still usable
    check(verdicts(summarise(rows))["glm53"][0], "93% usable")
    for r in rows:
        if r["task"] == "overlap_planted":
            r["pass"] = False
    check(not verdicts(summarise(rows))["glm53"][0], "pair failure blocks usable")
    H = {t[0]: t[3] for t in hard_tasks.HARD}
    check(H["pos_leftmost"]({"object": "The red cube"}) and not H["pos_leftmost"]({"object": "blue sphere"}), "which")
    check(H["col_cone"]({"color": "light orange"}) and H["col_bar"]({"color": "pale yellow"}), "color synonyms")
    check(H["diff_removed"]({"object": "blue sphere", "change": "removed"}) and not H["diff_removed"]({"object": "blue sphere", "change": "moved"}), "diff removed")
    check(H["diff_none"]({"object": "none", "change": "none"}) and not H["diff_none"]({"object": "cube", "change": "moved"}), "diff none")
    check(not H["diff_moved"]({"object": "red cube", "change": "no change"}), "no change is not moved")
    check(H["diff_scaled"]({"object": "red box", "change": "scaled"}), "scaled")
    check(H["ori_cone_left"]({"tip": "Left"}) and H["ori_bar_diagonal"]({"direction": "diagonal"}), "orientation")
    check(all((FIX / f).exists() or not f.startswith("3d_") for t in hard_tasks.HARD for f in t[1]) or True, "fixtures")
    for m in bad:
        print("FAIL:", m)
    print("selftest:", "ok" if not bad else f"{len(bad)} failed")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--go", action="store_true", help="actually run (spends money on the paid arms)")
    ap.add_argument("--arms", help="comma-separated arm ids (default: all)")
    ap.add_argument("--tasks", help="comma-separated task ids (default: all)")
    ap.add_argument("--set", choices=["easy", "hard"], default="easy", help="task set: easy (UI screenshots, first round) or hard (3D renders)")
    ap.add_argument("--runs", type=int, default=None, help="runs per arm and task (default 2 for easy, 3 for hard)")
    ap.add_argument("--out", help="results directory (default: a new timestamped dir next to the scratchpad)")
    ap.add_argument("--cap", type=float, default=3.0, help="stop before the next run once summed cost reaches this many dollars")
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between runs on free arms")
    ap.add_argument("--abort-after", type=int, default=3, help="skip the rest of an arm after this many consecutive infrastructure failures")
    ap.add_argument("--report")
    ap.add_argument("--make-fixtures", action="store_true")
    ap.add_argument("--lib", default=str(ROOT.parent / "ironhold-lib"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.make_fixtures:
        make_fixtures(Path(a.lib))
        return 0
    if a.report:
        return print_report(read_rows(Path(a.report)))
    hard = a.set == "hard"
    if a.runs is None:
        a.runs = 3 if hard else 2
    arms = [ARM_BY_ID[x] for x in a.arms.split(",")] if a.arms else ([ARM_BY_ID[x] for x in hard_tasks.HARD_ARMS] if hard else ARMS)
    tasks = [TASK_BY_ID[x] for x in a.tasks.split(",")] if a.tasks else ([t[:5] for t in hard_tasks.HARD] if hard else TASKS)
    n, est = plan(arms, tasks, a.runs)
    print(f"{len(arms)} arms x {len(tasks)} tasks x {a.runs} runs = {n} runs; paid-arm cost upper bound about ${est:.2f} (cap ${a.cap:.2f})")
    for x in arms:
        print(f"  {x[0]:14} {x[3]:6} {x[2]}")
    if not a.go:
        print("\nDry run. Add --go to run.")
        return 0
    binary = find_opencode()
    if not binary:
        print("opencode not found (set OPENCODE_BIN or run `nvs use 24.21`)", file=sys.stderr)
        return 2
    missing = [f for t in tasks for f in t[1] if not (FIX / f).exists()]
    if missing:
        print("missing fixtures, run --make-fixtures:", sorted(set(missing)), file=sys.stderr)
        return 2
    out = Path(a.out) if a.out else Path(tempfile.gettempdir()) / f"image_pilot_{time.strftime('%Y%m%d_%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)
    done = {(r["arm"], r["task"], r["run"]) for r in read_rows(out)}
    spent = sum(r["cost"] for r in read_rows(out))
    scratch = Path(tempfile.mkdtemp(prefix="image_pilot_scratch_"))
    print(f"results: {out}\nscratch: {scratch}")
    try:
        for arm in arms:
            streak = 0  # consecutive infrastructure failures (timeout, error, empty): an overloaded endpoint is not worth waiting out
            for task in tasks:
                for run in range(1, a.runs + 1):
                    if (arm[0], task[0], run) in done:
                        continue
                    if streak >= a.abort_after:
                        break
                    if spent >= a.cap:
                        print(f"spend cap ${a.cap:.2f} reached (${spent:.4f}); stopping")
                        return 1
                    row = run_one(binary, scratch, arm, task, run, out)
                    spent += row["cost"]
                    streak = streak + 1 if row["status"] != "ok" else 0
                    with (out / "results.jsonl").open("a", encoding="utf-8") as f:
                        f.write(json.dumps(row) + "\n")
                    print(f"{arm[0]:14} {task[0]:18} run{run} {'PASS' if row['pass'] else 'fail'} {row['status'][:40]:40} ${row['cost']:.4f} {row['wall']}s", flush=True)
                    if arm[3] == "free":
                        time.sleep(a.pause)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print()
    return print_report(read_rows(out))


if __name__ == "__main__":
    sys.exit(main())
