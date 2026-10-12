#!/usr/bin/env python3
"""Render the 3D fixtures for the hard image-interpretation round (planning/features/opencode_compatibility.md).

Writes a throwaway project `image_pilot_scenes` into the ironhold-lib checkout (assets/projects/, untracked, deleted afterwards),
serves it with lib's serve.py and screenshots every scene variant in a visible WebGPU Chromium (the lib's real-GPU path).
The ground truth is the scene definition below: one base scene with five objects at known places seen by a fixed camera,
plus single-edit variants. Same camera, light and ground in every variant, so the differences are exactly the edits.

    python tools/opencode_image_pilot/render_scenes.py [--lib ../ironhold-lib] [--port 8002] [--keep]
Needs the lib's `pkg/` (any recent build) and Playwright. Output: tools/opencode_image_pilot/fixtures/3d_<variant>.png
"""

import argparse
import asyncio
import copy
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
PROJECT = "image_pilot_scenes"

# name -> (shape, primitive params, color). Positions are in the scene; rotation is euler degrees (x, y, z).
BASE = {
    "red_cube":      dict(shape="Cuboid", prim="size: (1.2, 1.2, 1.2)", color=(0.55, 0.0, 0.02), pos=(-3.0, 0.6, 0.0), rot=(0, 0, 0), scale=1.0),
    "blue_sphere":   dict(shape="Sphere", prim="radius: 0.9", color=(0.10, 0.25, 0.90), pos=(0.0, 0.9, -4.0), rot=(0, 0, 0), scale=1.0),
    "green_cylinder": dict(shape="Cylinder", prim="radius: 0.6, height: 1.6", color=(0.10, 0.65, 0.15), pos=(3.0, 0.8, 0.0), rot=(0, 0, 0), scale=1.0),
    "orange_cone":   dict(shape="Cone", prim="radius: 0.7, height: 1.6", color=(0.95, 0.45, 0.05), pos=(5.5, 0.8, -3.0), rot=(0, 0, 0), scale=1.0),
    "yellow_bar":    dict(shape="Cuboid", prim="size: (0.5, 0.5, 3.0)", color=(0.95, 0.85, 0.10), pos=(0.0, 0.25, 3.0), rot=(0, 0, 0), scale=1.0),
}


def edit(**changes):
    """A variant: {object: {field: value}}; a None object value removes it; a new name adds it."""
    def apply(objs):
        o = copy.deepcopy(objs)
        for name, ch in changes.items():
            if ch is None:
                o.pop(name)
            elif name in o:
                o[name].update(ch)
            else:
                o[name] = ch
        return o
    return apply


VARIANTS = {
    "base": edit(),
    "base_again": edit(),  # re-render of the unchanged scene (control for "no change")
    "bar_across": edit(yellow_bar=dict(rot=(0, 90, 0))),
    "bar_diagonal": edit(yellow_bar=dict(rot=(0, 45, 0))),
    "cone_left": edit(orange_cone=dict(rot=(0, 0, 90), pos=(5.5, 0.7, -3.0))),
    "cone_right": edit(orange_cone=dict(rot=(0, 0, -90), pos=(5.5, 0.7, -3.0))),
    "cube_moved": edit(red_cube=dict(pos=(1.4, 0.6, -1.0))),
    "cube_nudged": edit(red_cube=dict(pos=(-2.4, 0.6, 0.0))),
    "cylinder_purple": edit(green_cylinder=dict(color=(0.60, 0.15, 0.80))),
    "sphere_removed": edit(blue_sphere=None),
    "white_cube_added": edit(white_cube=dict(shape="Cuboid", prim="size: (0.9, 0.9, 0.9)", color=(0.95, 0.95, 0.95), pos=(1.8, 0.45, 2.0), rot=(0, 0, 0), scale=1.0)),
    "cube_scaled": edit(red_cube=dict(scale=1.8, pos=(-3.0, 1.08, 0.0))),
}


def prefab_ron(name, o):
    r, g, b = o["color"]
    return (f'    "{name}": (\n      kind: Primitive, model: "", shape: {o["shape"]}, components: (),\n'
            f'      primitive: ( {o["prim"]}, color: ({r}, {g}, {b}), roughness: 0.55 ),\n    ),\n')


def scene_ron(variant, objs):
    ents = ""
    for name, o in objs.items():
        x, y, z = o["pos"]
        rx, ry, rz = o["rot"]
        s = o["scale"]
        ents += (f'    ( id: "{name}", prefab: "{name}",\n      transform: ( translation: ({x}, {y}, {z}), '
                 f'rotation_euler_deg: ({rx}, {ry}, {rz}), scale: ({s}, {s}, {s}) ) ),\n')
    return f'''(
  schema_version: 2,
  name: "{variant}",
  tonemapping: AcesFitted,
  lighting: (
    ambient: (0.25, 0.28, 0.35),
    ambient_brightness: 300.0,
    directional: ( color: (1.0, 0.96, 0.85), intensity: 30000.0, rotation_euler_deg: (-50.0, 30.0, 0.0), shadows_enabled: true ),
  ),
  spawn_points: {{ "player_start": (0.0, 0.5, 30.0) }},
  entities: [
    ( id: "ground", prefab: "ground", transform: ( translation: (0.0, -0.5, 0.0), rotation_euler_deg: (0.0, 0.0, 0.0), scale: (1.0, 1.0, 1.0) ) ),
    // The camera owner stands far behind the fixed camera, out of frame.
    ( id: "player_01", prefab: "camera_owner", transform: ( translation: (0.0, 0.5, 30.0), rotation_euler_deg: (0.0, 0.0, 0.0), scale: (1.0, 1.0, 1.0) ) ),
{ents}  ],
  ui: [],
)
'''


def write_project(root: Path):
    if root.exists():
        shutil.rmtree(root)
    (root / "scenes").mkdir(parents=True)
    (root / "logic").mkdir()
    (root / "prefabs").mkdir()
    (root / f"{PROJECT}.project.ron").write_text(f'''(
    schema_version: 3,
    project_id: "{PROJECT}",
    display_name: "Image pilot scenes",
    initial_scene: "scenes/base.scene.ron",
    asset_catalog: "assets.ron",
    prefab_catalog: "prefabs/prefabs.ron",
    state_machine_path: "logic/state_machine.ron",
    global_environment: ( intensity: 400.0, fallback: ( top_color: (0.30, 0.45, 0.70), bottom_color: (0.20, 0.22, 0.25) ) ),
)
''', encoding="utf-8")
    (root / "assets.ron").write_text("(\n    schema_version: 1,\n    models: {},\n    textures: {},\n    audio: {},\n    effects: {},\n    materials: {},\n)\n", encoding="utf-8")
    (root / "logic" / "state_machine.ron").write_text("(\n    schema_version: 1,\n    global_on: [],\n)\n", encoding="utf-8")
    all_objs = {}
    for fn in VARIANTS.values():
        all_objs.update(fn(BASE))
    prefabs = "".join(prefab_ron(n, o) for n, o in all_objs.items())
    (root / "prefabs" / "prefabs.ron").write_text(f'''(
    schema_version: 2,
    prefabs: {{
    "ground": (
      kind: Primitive, model: "", shape: Cuboid, components: (),
      primitive: ( size: (60.0, 1.0, 60.0), color: (0.38, 0.40, 0.34), roughness: 0.95, physics: true ),
    ),
    "camera_owner": (
      kind: Primitive, model: "", shape: Capsule3d,
      components: (
        tags: ["player"],
        camera_mode: Fixed(( position: (0.0, 5.0, 10.0), look_at: (0.0, 0.8, -1.0) )),
      ),
      primitive: ( radius: 0.4, height: 1.8, color: (0.5, 0.5, 0.5) ),
    ),
{prefabs}    }}
)
''', encoding="utf-8")
    for v, fn in VARIANTS.items():
        (root / "scenes" / f"{v}.scene.ron").write_text(scene_ron(v, fn(BASE)), encoding="utf-8")


async def render(lib: Path, port: int):
    sys.path.insert(0, str(lib))
    import os
    os.chdir(lib)
    import test_web as tw
    from playwright.async_api import async_playwright
    tw.PORT = port
    tw.BASE_URL = f"http://localhost:{port}"
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=tw.CHROMIUM_ARGS_REAL_GPU)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        for v in VARIANTS:
            page, errors = await tw.open_project(context, PROJECT, f"scenes/{v}.scene.ron")
            try:
                await tw.wait_for_scene_ready(page, settle_frames=60)
                await asyncio.sleep(0.8)
                await page.screenshot(path=str(FIX / f"3d_{v}.png"))
                print(f"rendered {v}" + (f"  (browser errors: {errors[:2]})" if errors else ""), flush=True)
            finally:
                await page.close()
        await browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default=str(HERE.parent.parent.parent / "ironhold-lib"))
    ap.add_argument("--port", type=int, default=8002)
    ap.add_argument("--keep", action="store_true", help="keep the throwaway project in the lib afterwards")
    a = ap.parse_args()
    lib = Path(a.lib).resolve()
    root = lib / "assets" / "projects" / PROJECT
    FIX.mkdir(parents=True, exist_ok=True)
    write_project(root)
    server = subprocess.Popen([sys.executable, "serve.py", str(a.port)], cwd=lib, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        asyncio.run(render(lib, a.port))
    finally:
        server.terminate()
        server.wait()
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
