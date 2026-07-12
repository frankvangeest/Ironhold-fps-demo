#!/usr/bin/env python3
"""
Fix broken texture URI references in all GLTF files under assets/models/.

GLTF files reference textures with bare filenames (e.g. "T_Trim_01_Normal.png")
but the textures live in assets/textures/, two levels up from any model subfolder.
This script rewrites those URIs to the correct relative path:
  "T_Trim_01_Normal.png"  ->  "../../textures/T_Trim_01_Normal.png"

Only rewrites URIs for textures that actually exist in assets/textures/.
Leaves any other image URIs untouched.

Usage:
    python scripts/fix_gltf_texture_paths.py           # apply fixes
    python scripts/fix_gltf_texture_paths.py --dry-run # preview only
"""
import json
import sys
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
MODELS_DIR = ASSETS_DIR / "models"
TEXTURES_DIR = ASSETS_DIR / "textures"
RELATIVE_PREFIX = "../../textures/"

dry_run = "--dry-run" in sys.argv


def available_textures():
    return {p.name for p in TEXTURES_DIR.iterdir() if p.is_file()}


def fix_gltf(gltf_path, known_textures):
    with open(gltf_path, encoding="utf-8") as f:
        data = json.load(f)

    images = data.get("images", [])
    changed = []
    for img in images:
        uri = img.get("uri", "")
        name = Path(uri).name
        if name in known_textures and not uri.startswith(RELATIVE_PREFIX):
            old = uri
            img["uri"] = RELATIVE_PREFIX + name
            changed.append((old, img["uri"]))

    return data, changed


def main():
    known_textures = available_textures()
    gltf_files = sorted(MODELS_DIR.rglob("*.gltf"))

    total_files = 0
    total_changes = 0

    for gltf_path in gltf_files:
        data, changed = fix_gltf(gltf_path, known_textures)
        if not changed:
            continue
        rel = gltf_path.relative_to(ASSETS_DIR)
        total_files += 1
        total_changes += len(changed)
        if dry_run:
            print(f"  [dry-run] {rel}")
            for old, new in changed:
                print(f"    {old!r:40s} -> {new!r}")
        else:
            with open(gltf_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent="\t")
            print(f"  Fixed: {rel}  ({len(changed)} texture(s))")

    if total_files == 0:
        print("No GLTF files needed fixing.")
    else:
        verb = "[dry-run] Would fix" if dry_run else "Fixed"
        print(f"\n{verb} {total_changes} texture URI(s) across {total_files} GLTF file(s).")
        if dry_run:
            print("Run without --dry-run to apply.")


if __name__ == "__main__":
    main()
