#!/usr/bin/env python3
"""
Scan all GLTF files under assets/models/ and report:
  - What texture URIs each GLTF references
  - Whether those textures exist relative to the GLTF (broken if not)
  - A summary of missing textures and where they actually live

Usage:
    python scripts/scan_gltf_textures.py
"""
import json
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
MODELS_DIR = ASSETS_DIR / "models"
TEXTURES_DIR = ASSETS_DIR / "textures"


def scan_gltf(gltf_path):
    with open(gltf_path, encoding="utf-8") as f:
        data = json.load(f)
    images = data.get("images", [])
    return [img["uri"] for img in images if "uri" in img]


def main():
    gltf_files = sorted(MODELS_DIR.rglob("*.gltf"))
    if not gltf_files:
        print("No GLTF files found under assets/models/")
        return

    all_missing = {}   # uri -> set of gltf files that need it
    all_found_elsewhere = {}  # uri -> where it actually lives

    print(f"Scanning {len(gltf_files)} GLTF files...\n")

    for gltf_path in gltf_files:
        uris = scan_gltf(gltf_path)
        if not uris:
            continue
        broken = []
        for uri in uris:
            expected = gltf_path.parent / uri
            if not expected.exists():
                broken.append(uri)
                all_missing.setdefault(uri, set()).add(gltf_path)
                tex_name = Path(uri).name
                candidate = TEXTURES_DIR / tex_name
                if candidate.exists():
                    all_found_elsewhere[uri] = candidate

        if broken:
            rel = gltf_path.relative_to(ASSETS_DIR)
            print(f"  {rel}")
            for b in broken:
                found = " -> found in assets/textures/" if b in all_found_elsewhere else " -> NOT FOUND anywhere"
                print(f"    [X] {b}{found}")

    if not all_missing:
        print("All texture references are intact.")
        return

    print(f"\n--- Summary ---")
    print(f"Unique missing texture URIs: {len(all_missing)}")
    in_tex = {u for u in all_missing if u in all_found_elsewhere}
    not_found = {u for u in all_missing if u not in all_found_elsewhere}
    print(f"  Found in assets/textures/: {len(in_tex)}")
    print(f"  Not found anywhere: {len(not_found)}")

    if in_tex:
        print("\nTextures that exist in assets/textures/ (can be fixed by path correction):")
        for uri in sorted(in_tex):
            count = len(all_missing[uri])
            print(f"  {uri}  (used by {count} GLTF file(s))")

    if not_found:
        print("\nTextures missing entirely:")
        for uri in sorted(not_found):
            print(f"  {uri}")

    print("\nRecommended fix:")
    print("  Update GLTF image URIs from bare filenames to relative paths like")
    print("  '../../textures/T_Trim_01_Normal.png'")
    print("  Run: python scripts/fix_gltf_texture_paths.py")


if __name__ == "__main__":
    main()
