"""Blender renders of the Giorgio AMR from the CadQuery exports (amr/out) + the unchanged superstructure (cad/out/stl).

    ~/tools/blender-4.5.9-linux-x64/blender -b -P amr/render_amr.py -- --view hero --out amr/renders/amr_hero.png
    ... -- --view turntable --frames 0 119 --out amr/renders/frames/turn/f_####.jpg

views: hero (base, covers on), open (covers + deck hidden: bays, batteries, waist, cables), exploded, cables (top, harness
highlighted), robot (full Giorgio, waist yaw --yaw), dock (docked on the dock), part (single part --part NAME),
turntable / explode_anim / waist_anim / dock_anim (animations, --frames a b).
look: dark studio (same mood as the video) or --light (white product).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--view", default="hero")
ap.add_argument("--out", default="amr/renders/out.png")
ap.add_argument("--frames", type=int, nargs=2, default=None)
ap.add_argument("--yaw", type=float, default=0.0)
ap.add_argument("--part", default="")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
ap.add_argument("--light", action="store_true")
ap.add_argument("--no_robot", action="store_true")
args = ap.parse_args(argv)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CAD = HERE.parent / "cad" / "out"
sys.path.insert(0, str(HERE))
import amr_params as AP  # noqa: E402

META = json.loads((OUT / "parts.json").read_text())
KEEP = AP.KEEP_PREFIX

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dev
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
        break
    except Exception:
        continue
sc.cycles.samples = args.samples
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPTIX"
except Exception:
    pass
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.render.film_transparent = False


def mat(name, color, rough=0.45, metal=0.0, coat=0.0, emit=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m


def material_for(p):
    n, mt, cat = p["name"], p["material"], p["category"]
    c = tuple(p["color"])
    if cat == "harness":
        return mat(f"harness_{c}", c, 0.5, emit=0.6)
    if (n.startswith("K0") and "rubber" not in n) or n.startswith("A02"):
        return mat("cover", (0.80, 0.80, 0.78), 0.32, coat=0.4)
    if "EN AW" in mt:
        return mat("alu", (0.78, 0.79, 0.81), 0.28, metal=1.0)
    if mt == "S355MC":
        return mat("steel_pc", (0.16, 0.17, 0.18), 0.5, coat=0.2)
    if "steel" in mt:
        return mat("steel", (0.6, 0.6, 0.62), 0.25, metal=1.0)
    if mt in ("POM-C", "PA12 (MJF)"):
        return mat("plastic_w", (0.9, 0.9, 0.88), 0.5)
    if mt == "EPDM":
        return mat("rubber", (0.04, 0.04, 0.045), 0.8)
    return mat(f"p_{n[:3]}_{c}", c, 0.4, metal=0.0, coat=0.2)


def load_stl(path, name, m, parent=None):
    bpy.ops.wm.stl_import(filepath=str(path))
    o = bpy.context.selected_objects[0]
    o.name = name
    o.scale = (0.001, 0.001, 0.001)
    o.data.materials.clear()
    o.data.materials.append(m)
    for poly in o.data.polygons:
        poly.use_smooth = False
    if parent:
        o.parent = parent
    return o


# ------------------------------------------------------------------ scene objects
waist = bpy.data.objects.new("WAIST", None)
sc.collection.objects.link(waist)
waist.rotation_euler[2] = math.radians(args.yaw)
OBJ = {}
hide_covers = args.view in ("open", "cables")
for p in META:
    if p.get("category") == "keepout" or p.get("group") == "keepout":      # rev B2: invisible check solids are never rendered
        continue
    if p["group"] == "dock" and args.view not in ("dock", "dock_anim", "part"):
        continue
    if hide_covers and (p["name"].startswith("K0") or p["name"] in ("A02_top_deck", "W07_deck_guard_disc")):
        continue
    if args.view in ("cables", "open") and p["name"].startswith(("W06", "W08", "W09", "W10")):
        continue
    src = OUT / ("stl" if args.view != "exploded" else "exploded") / p["file"]
    par = waist if p["group"] == "waist_rot" else None
    OBJ[p["name"]] = load_stl(src, p["name"], material_for(p), par)

show_robot = args.view in ("robot", "dock", "dock_anim", "waist_anim") and not args.no_robot
if show_robot:
    white = mat("shell_white", (0.9, 0.9, 0.88), 0.35, coat=0.5)
    graph = mat("graphite", (0.08, 0.08, 0.09), 0.45)
    for f in sorted((CAD / "stl").glob("*.stl")):
        n = f.stem
        if not n.startswith(KEEP) or n.startswith("tnut"):
            continue
        m = white if n.startswith(("SH", "openarm")) else graph if n.startswith(("S0", "E1")) else mat("alu", (0.78, 0.79, 0.81), 0.28, metal=1.0)
        OBJ[n] = load_stl(f, n, m, waist)

if args.view == "part":
    for n, o in OBJ.items():
        o.hide_render = n != args.part

# ------------------------------------------------------------------ studio
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = ((0.30, 0.31, 0.33, 1) if args.view == 'part' else (0.92, 0.92, 0.93, 1)) if args.light else (0.012, 0.012, 0.014, 1)
bg.inputs[1].default_value = 0.6 if args.light else 0.08
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.object
floor.data.materials.append(mat("floor", ((0.22, 0.23, 0.25) if args.view == "part" else (0.85, 0.85, 0.86)) if args.light else (0.02, 0.02, 0.022), 0.35 if not args.light else 0.6))
if args.view == "part":
    floor.location.z = -0.001 + min((OBJ[args.part].matrix_world @ Vector(c)).z for c in OBJ[args.part].bound_box) if args.part in OBJ else 0


def area(name, loc, size, power, color=(1, 1, 1), target=(0, 0, 0.4)):
    l = bpy.data.lights.new(name, "AREA")
    l.size = size
    l.energy = power
    l.color = color
    o = bpy.data.objects.new(name, l)
    sc.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


area("key", (2.2, -2.0, 2.6), 2.5, 380)
area("fill", (-2.4, -1.2, 1.4), 3.0, 90, (0.85, 0.9, 1.0))
area("rim", (-1.5, 2.4, 2.2), 1.5, 420 if not args.light else 200, (0.75, 0.85, 1.0))
area("top", (0, 0, 4.0), 3.0, 120)
if not args.light:     # accent strip (video orange)
    area("accent", (1.6, 2.2, 0.25), 1.2, 120, (1.0, 0.48, 0.1))

cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.lens = 50


def look(pos, tgt, lens=50):
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens


V = {"hero": ((1.65, -1.45, 1.05), (0, 0, 0.17), 50), "open": ((1.05, -1.0, 1.45), (0, 0, 0.12), 40),
     "exploded": ((2.3, -2.1, 1.6), (0, 0, 0.2), 42), "cables": ((0.0, -0.05, 2.2), (0, 0, 0.15), 40),
     "robot": ((3.3, -2.9, 1.7), (0, 0, 0.8), 45), "dock": ((1.2, -2.6, 1.3), (-0.4, 0, 0.35), 40),
     "part": ((1.2, -1.1, 0.9), (0, 0, 0.2), 60)}

if args.view == "part" and args.part in OBJ:
    o = OBJ[args.part]
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    ctr = sum(bb, Vector()) / 8
    size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    look(ctr + Vector((1.0, -0.9, 0.75)).normalized() * max(size, 0.06) * (1.55 if size > 0.3 else 2.6), ctr, 50)
elif args.view in V:
    look(*V[args.view])

# ------------------------------------------------------------------ animations
anim = args.view in ("turntable", "explode_anim", "waist_anim", "dock_anim")
if anim:
    a, b = args.frames
    sc.frame_start, sc.frame_end = a, b
    n = b - a + 1
    if args.view == "turntable":
        for f in range(a, b + 1):
            t = (f - a) / n
            ang = math.radians(-40 + 360 * t)
            look((2.1 * math.cos(ang), 2.1 * math.sin(ang), 1.0), (0, 0, 0.17), 50)
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    elif args.view == "explode_anim":
        look((2.4, -2.2, 1.6), (0, 0, 0.2), 42)
        for p in META:
            o = OBJ.get(p["name"])
            if not o:
                continue
            e = Vector(p["explode"]) * 0.001
            o.location = (0, 0, 0); o.keyframe_insert("location", frame=a + int(0.15 * n))
            o.location = e; o.keyframe_insert("location", frame=a + int(0.75 * n))
    elif args.view == "waist_anim":
        look((3.3, -2.9, 1.7), (0, 0, 0.8), 45)
        for f, yv in ((a, 0), (a + int(0.3 * n), 90), (a + int(0.65 * n), -90), (b, 0)):
            waist.rotation_euler[2] = math.radians(yv); waist.keyframe_insert("rotation_euler", frame=f)
    elif args.view == "dock_anim":
        look((1.0, -2.8, 1.25), (-0.45, 0, 0.35), 38)
        root = bpy.data.objects.new("ROBOT", None); sc.collection.objects.link(root)
        for o in list(OBJ.values()):
            if o.parent is None and not o.name.startswith("X0"):
                o.parent = root
        waist.parent = root
        for f, xv in ((a, 0.9), (a + int(0.7 * n), 0.0), (b, 0.0)):
            root.location = (xv, 0, 0); root.keyframe_insert("location", frame=f)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            try:
                for fc in o.animation_data.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = "BEZIER"
            except Exception:
                pass

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
if anim:
    sc.render.image_settings.file_format = "JPEG" if args.out.endswith(".jpg") else "PNG"
    sc.render.image_settings.quality = 92
    sc.render.filepath = args.out.replace("####.jpg", "").replace("####.png", "")
    bpy.ops.render.render(animation=True)
else:
    sc.render.filepath = args.out
    bpy.ops.render.render(write_still=True)
print("RENDER_DONE", args.out)
