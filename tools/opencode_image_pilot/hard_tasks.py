"""Hard task set for tools/opencode_image_pilot.py: engine renders of one known 3D scene.

The images come from render_scenes.py (same camera, light and ground in every variant; the base scene has five objects at known
places, every other image differs by exactly one edit). Categories: position, recognition, color, orientation, diff.
Scoring is deterministic: the model's one-line JSON is matched against synonym lists, never graded by another model.
"""

import re


def norm(v):
    return re.sub(r"[^a-z0-9]", "", str(v).lower())


def to_int(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


SYN = {
    "red": ("red", "crimson", "scarlet"), "orange": ("orange", "peach", "apricot", "tan"),
    "yellow": ("yellow", "cream", "beige", "gold"), "green": ("green", "lime"), "blue": ("blue", "periwinkle"),
    "purple": ("purple", "violet", "lavender", "magenta"), "white": ("white", "grey", "gray", "silver"),
    "cube": ("cube", "box", "block"), "sphere": ("sphere", "ball", "globe"), "cylinder": ("cylinder", "can", "drum"),
    "cone": ("cone", "pyramid"), "bar": ("bar", "plank", "beam", "log", "rod", "stick", "board", "slab", "box", "cuboid", "prism"),
}


def has(value, *keys):
    """True if the answer names a synonym of every one of the keys."""
    t = norm(value)
    return all(any(w in t for w in SYN.get(k, (k,))) for k in keys)


CHANGE = {"moved": ("move", "position", "shift", "translat", "relocat"), "recolored": ("color", "colour"),
          "removed": ("remov", "missing", "delet", "gone", "disappear"), "added": ("add", "new", "appear"),
          "rotated": ("rotat", "turn", "orient"), "scaled": ("scal", "size", "bigger", "larger", "enlarg", "grew"),
          "none": ("none", "nochange", "same", "identical", "nothing")}


def change_is(d, kind, obj=None):
    c = norm(d.get("change"))
    ok = any(w in c for w in CHANGE[kind]) and not (kind != "none" and any(w in c for w in CHANGE["none"]))
    return ok and (obj is None or has(d.get("object"), *obj))


def which(*keys):
    return lambda d: has(d.get("object"), *keys)


def starts(field, prefix):
    return lambda d: norm(d.get(field)).startswith(prefix)


DIFF_Q = ('Image 2 is image 1 after ONE edit to the scene, or after no edit at all. What changed? Reply '
          '{"object":"<short description, for example red cube>","change":"moved|recolored|removed|added|rotated|scaled|none"}.')
DIR_Q = ('The long yellow bar lies on the ground. Is it pointing toward the camera (along the viewing direction), lying across the '
         'screen from left to right, or diagonal? Reply {"direction":"toward"}, {"direction":"across"} or {"direction":"diagonal"}.')
TIP_Q = 'Which way does the tip of the orange cone point? Reply {"tip":"up"}, {"tip":"left"} or {"tip":"right"}.'
COUNT_Q = 'How many separate 3D objects stand on the ground (do not count the ground itself)? Reply {"count":N}.'
WHICH_Q = 'Which object is {what}? Reply {{"object":"<color and shape>"}}.'

# id, images, question, scorer(dict)->bool, pair group (every task of a group must pass in at least one run), category
HARD = [
    ("pos_leftmost", ["3d_base.png"], WHICH_Q.format(what="the leftmost on the screen"), which("red", "cube"), None, "position"),
    ("pos_rightmost", ["3d_base.png"], WHICH_Q.format(what="the rightmost on the screen"), which("orange", "cone"), None, "position"),
    ("pos_farthest", ["3d_base.png"], WHICH_Q.format(what="the farthest from the camera"), which("blue", "sphere"), None, "position"),
    ("pos_closest", ["3d_base.png"], WHICH_Q.format(what="the closest to the camera"), which("yellow", "bar"), None, "position"),
    ("pos_sphere_vs_cyl", ["3d_base.png"],
     'Is the blue sphere to the left or to the right of the green cylinder on the screen? Reply {"side":"left"} or {"side":"right"}.',
     starts("side", "left"), None, "position"),
    ("rec_green_shape", ["3d_base.png"], 'What 3D shape is the green object? Reply {"shape":"..."}.', lambda d: has(d.get("shape"), "cylinder"), None, "recognition"),
    ("rec_orange_shape", ["3d_base.png"], 'What 3D shape is the orange object? Reply {"shape":"..."}.', lambda d: has(d.get("shape"), "cone"), None, "recognition"),
    ("rec_blue_shape", ["3d_base.png"], 'What 3D shape is the blue object? Reply {"shape":"..."}.', lambda d: has(d.get("shape"), "sphere"), None, "recognition"),
    ("rec_count_5", ["3d_base.png"], COUNT_Q, lambda d: to_int(d.get("count")) == 5, "count", "recognition"),
    ("rec_count_4", ["3d_sphere_removed.png"], COUNT_Q, lambda d: to_int(d.get("count")) == 4, "count", "recognition"),
    ("rec_count_6", ["3d_white_cube_added.png"], COUNT_Q, lambda d: to_int(d.get("count")) == 6, "count", "recognition"),
    ("col_cube", ["3d_base.png"], 'What color is the cube? Reply {"color":"..."}.', lambda d: has(d.get("color"), "red"), None, "color"),
    ("col_cone", ["3d_base.png"], 'What color is the cone? Reply {"color":"..."}.', lambda d: has(d.get("color"), "orange"), None, "color"),
    ("col_bar", ["3d_base.png"], 'What color is the long bar on the ground? Reply {"color":"..."}.', lambda d: has(d.get("color"), "yellow"), None, "color"),
    ("ori_bar_toward", ["3d_base.png"], DIR_Q, starts("direction", "toward"), "bar_dir", "orientation"),
    ("ori_bar_across", ["3d_bar_across.png"], DIR_Q, starts("direction", "across"), "bar_dir", "orientation"),
    ("ori_bar_diagonal", ["3d_bar_diagonal.png"], DIR_Q, starts("direction", "diag"), "bar_dir", "orientation"),
    ("ori_cone_up", ["3d_base.png"], TIP_Q, starts("tip", "up"), "cone_tip", "orientation"),
    ("ori_cone_left", ["3d_cone_left.png"], TIP_Q, starts("tip", "left"), "cone_tip", "orientation"),
    ("ori_cone_right", ["3d_cone_right.png"], TIP_Q, starts("tip", "right"), "cone_tip", "orientation"),
    ("diff_moved", ["3d_base.png", "3d_cube_moved.png"], DIFF_Q, lambda d: change_is(d, "moved", ("cube",)), "diff", "diff"),
    ("diff_nudged", ["3d_base.png", "3d_cube_nudged.png"], DIFF_Q, lambda d: change_is(d, "moved", ("cube",)), "diff", "diff"),
    ("diff_recolored", ["3d_base.png", "3d_cylinder_purple.png"], DIFF_Q, lambda d: change_is(d, "recolored", ("cylinder",)), "diff", "diff"),
    ("diff_removed", ["3d_base.png", "3d_sphere_removed.png"], DIFF_Q, lambda d: change_is(d, "removed", ("sphere",)), "diff", "diff"),
    ("diff_added", ["3d_base.png", "3d_white_cube_added.png"], DIFF_Q, lambda d: change_is(d, "added"), "diff", "diff"),
    ("diff_rotated", ["3d_base.png", "3d_bar_across.png"], DIFF_Q, lambda d: change_is(d, "rotated", ("bar",)), "diff", "diff"),
    ("diff_scaled", ["3d_base.png", "3d_cube_scaled.png"], DIFF_Q, lambda d: change_is(d, "scaled", ("cube",)), "diff", "diff"),
    ("diff_none", ["3d_base.png", "3d_base_again.png"], DIFF_Q, lambda d: change_is(d, "none"), "diff", "diff"),
]
HARD_ARMS = ["glm53", "qwen_vl", "qwen_omni", "gemini38_or", "inkling"]
