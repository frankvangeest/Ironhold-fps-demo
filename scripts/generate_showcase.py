#!/usr/bin/env python3
"""
Generate showcase RON files from all GLTF assets under assets/models/.
Uses model_metadata.json for actual bounding-box dimensions so models are spaced
correctly and lifted off the ground by their pivot offset.

Writes:
  assets/projects/scifi_fps/assets.ron             (full model catalog)
  assets/projects/scifi_fps/prefabs/prefabs.ron    (flycam + all model prefabs)
  assets/projects/scifi_fps/scenes/showcase.scene.ron

Usage:
    python scripts/generate_showcase.py
"""
import json
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
MODELS_DIR = ASSETS_DIR / "models"
PROJECT_DIR = ASSETS_DIR / "projects" / "scifi_fps"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

COLS_PER_ROW = 10
COL_GAP = 0.6      # gap between adjacent model edges (x direction)
ROW_GAP = 1.5      # gap between row footprints (z direction)
CAT_GAP = 8.0      # extra z gap between categories
Y_LIFT = 0.001     # base y offset to prevent z-fighting with the ground


def key_of(name: str) -> str:
    return name.lower()


def model_path_of(gltf_path):
    return gltf_path.relative_to(ASSETS_DIR).as_posix() + "#Scene0"


def scan_models():
    result = {}
    for gltf in sorted(MODELS_DIR.rglob("*.gltf")):
        cat = gltf.parent.name
        result.setdefault(cat, []).append(gltf)
    return {k: sorted(v, key=lambda p: p.stem) for k, v in sorted(result.items())}


def load_metadata():
    if not METADATA_PATH.exists():
        print(f"WARNING: {METADATA_PATH} not found. Run scan_gltf_metadata.py first.")
        return {}
    data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return data.get("models", {})


# ─── assets.ron ──────────────────────────────────────────────────────────────

def write_assets_ron(categories):
    path = PROJECT_DIR / "assets.ron"
    lines = ["(", "    schema_version: 1,", "    models: {"]
    for cat, files in categories.items():
        lines.append(f"        // {cat}")
        for f in files:
            k = key_of(f.stem)
            p = model_path_of(f)
            lines.append(f'        "{k}": ( path: "{p}" ),')
    lines += ["    },", "    textures: {},", "    audio: {},", "    effects: {},", "    materials: {},", ")"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ASSETS_DIR.parent)}")


# ─── prefabs/prefabs.ron ─────────────────────────────────────────────────────

EXISTING_PREFABS = """\
        // Player capsule
        "player": (
            kind: Primitive,
            model: "",
            shape: Capsule3d,
            components: (
                tags: ["player"],
                movement: (
                    walk_speed: 5.0,
                    run_speed: 8.0,
                ),
            ),
            primitive: (
                radius: 0.4,
                height: 1.8,
                color: (0.22, 0.52, 0.88),
                roughness: 0.30,
                metallic: 0.10,
            ),
        ),

        // Static ground surface
        "ground": (
            kind: Primitive,
            model: "",
            shape: Cuboid,
            components: (),
            primitive: (
                size: (60.0, 1.0, 60.0),
                color: (0.30, 0.32, 0.28),
                roughness: 0.95,
                physics: true,
            ),
        ),

        // Free-fly showcase camera — hold LMB/RMB and move mouse to look
        "flycam": (
            kind: Prop,
            model: "",
            components: (
                tags: ["flycam"],
                flycam: (
                    speed: 15.0,
                    fast_speed: 50.0,
                    sensitivity: 0.002,
                ),
            ),
        ),"""


def write_prefabs_ron(categories):
    path = PROJECT_DIR / "prefabs" / "prefabs.ron"
    lines = [
        "(", "    schema_version: 2,", "    prefabs: {", "",
        EXISTING_PREFABS, "",
    ]
    for cat, files in categories.items():
        lines.append(f"        // {cat}")
        for f in files:
            k = key_of(f.stem)
            lines += [
                f'        "{k}": (', "            kind: Prop,",
                f'            model: "{k}",', "            components: (),", "        ),",
            ]
        lines.append("")
    lines += ["    }", ")"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ASSETS_DIR.parent)}")


# ─── Layout ──────────────────────────────────────────────────────────────────

def row_x_positions(models_in_row, meta):
    """Compute centred x positions for a list of models using their actual widths."""
    half_ws = []
    for f in models_in_row:
        k = key_of(f.stem)
        m = meta.get(k)
        # Use the larger of width and depth as the footprint half-extent in x,
        # so corner pieces (square footprint) are spaced by their full footprint.
        # Clamp max footprint at 5 to prevent one outlier from blowing out a row.
        fp = min(max(m["width"], m["depth"]) if m else 1.0, 5.0)
        half_ws.append(max(fp / 2, 0.2))

    positions = []
    cursor = 0.0
    for i, hw in enumerate(half_ws):
        if i > 0:
            cursor += COL_GAP
        cursor += hw
        positions.append(cursor)
        cursor += hw

    total = cursor
    return [x - total / 2 for x in positions], max(half_ws) * 2 + COL_GAP


def layout_entities(categories, meta):
    entities = []
    z = 0.0

    for cat, files in categories.items():
        n = len(files)
        rows = (n + COLS_PER_ROW - 1) // COLS_PER_ROW

        for row_idx in range(rows):
            start = row_idx * COLS_PER_ROW
            row_files = files[start: start + COLS_PER_ROW]

            xs, _ = row_x_positions(row_files, meta)

            # Row z spacing: based on the deepest model in this row
            max_depth = max(
                (min(meta.get(key_of(f.stem), {}).get("depth", 1.0), 5.0) for f in row_files),
                default=1.0,
            )
            row_center_z = z + max_depth / 2

            for col_idx, f in enumerate(row_files):
                k = key_of(f.stem)
                m = meta.get(k)
                py_offset = m["pivot_y_offset"] if m else 0.0
                y_place = py_offset + Y_LIFT

                entities.append({
                    "id": k + "_s",
                    "prefab": k,
                    "x": xs[col_idx],
                    "y": y_place,
                    "z": row_center_z,
                    "label": f.stem,
                })

            z += max_depth + ROW_GAP

        z += CAT_GAP

    return entities, z


# ─── scenes/showcase.scene.ron ───────────────────────────────────────────────

def write_showcase_scene(categories, meta):
    entities, total_depth = layout_entities(categories, meta)
    path = PROJECT_DIR / "scenes" / "showcase.scene.ron"

    lines = [
        "(", '    schema_version: 2,', '    name: "showcase",', "",
        "    lighting: (",
        "        ambient: (0.22, 0.25, 0.32),",
        "        ambient_brightness: 200.0,",
        "        directional: (",
        "            color: (1.0, 0.95, 0.85),",
        "            intensity: 30000.0,",
        "            rotation_euler_deg: (-50.0, 25.0, 0.0),",
        "            shadows_enabled: true,",
        f"            shadow_distance: {total_depth + 20.0:.0f}.0,",
        "            cascade_overlap: 0.5,",
        "        ),",
        "    ),", "",
        "    label_depth_scale: (",
        "        reference_distance: 12.0,",
        "        min_scale: 0.2,",
        "    ),", "",
        "    entities: [", "",
        "        // Flycam",
        "        (",
        '            id: "cam",',
        '            prefab: "flycam",',
        "            transform: (",
        "                translation: (0.0, 5.0, -8.0),",
        "                rotation_euler_deg: (0.0, 0.0, 0.0),",
        "                scale: (1.0, 1.0, 1.0),",
        "            ),",
        "        ),", "",
        "        // Ground — scaled to cover the full showcase layout",
        "        (",
        '            id: "showcase_ground",',
        '            prefab: "ground",',
        "            transform: (",
        f"                translation: (0.0, -0.5, {total_depth / 2:.1f}),",
        "                rotation_euler_deg: (0.0, 0.0, 0.0),",
        f"                scale: (3.0, 1.0, {max(3.0, total_depth / 60.0 + 1.0):.1f}),",
        "            ),",
        "        ),", "",
    ]

    for e in entities:
        lines += [
            "        (",
            f'            id: "{e["id"]}",',
            f'            prefab: "{e["prefab"]}",',
            "            transform: (",
            f'                translation: ({e["x"]:.3f}, {e["y"]:.4f}, {e["z"]:.3f}),',
            "                rotation_euler_deg: (0.0, 0.0, 0.0),",
            "                scale: (1.0, 1.0, 1.0),",
            "            ),",
            f'            label: (text: "{e["label"]}"),',
            "        ),", "",
        ]

    lines += [
        "    ],", "",
        "    ui: [",
        "        Label((",
        '            id: "flycam_position",',
        '            text: "",',
        "            position: (16.0, 16.0),",
        "            size: (400.0, 24.0),",
        "        )),",
        "        Label((",
        '            id: "hint",',
        '            text: "SHOWCASE  |  Hold LMB/RMB + mouse = look  |  WASD = fly  |  Shift = fast",',
        "            position: (16.0, 48.0),",
        "            size: (700.0, 24.0),",
        "        )),",
        "    ],",
        ")",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"Wrote {path.relative_to(ASSETS_DIR.parent)}"
        f"  ({len(entities)} entities, ~{total_depth:.0f} units depth)"
    )


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    categories = scan_models()
    meta = load_metadata()
    total = sum(len(v) for v in categories.values())
    print(f"Found {total} models across {len(categories)} categories")
    print(f"Loaded metadata for {len(meta)} models\n")

    write_assets_ron(categories)
    write_prefabs_ron(categories)
    write_showcase_scene(categories, meta)


if __name__ == "__main__":
    main()
