"""Sequenza video del CAD meccanico (cad/out): assemblato -> esploso con orbita lenta, look tecnico su fondo scuro (Workbench).
uso: blender -b -P cad_anim.py -- out_dir"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

OUTD = Path(sys.argv[sys.argv.index("--") + 1]); OUTD.mkdir(parents=True, exist_ok=True)
CAD = Path.home() / "giorgio_sim/cad/out"
meta = json.loads((CAD / "exploded" / "exploded.json").read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_shadows = True; sh.show_cavity = True
sh.cavity_type = "BOTH"; sh.show_object_outline = True; sh.object_outline_color = (0.0, 0.0, 0.0)
sh.show_specular_highlight = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.018, 0.018, 0.022)
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
NF = 170
sc.frame_start, sc.frame_end = 1, NF


def ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


objs = []
for p in meta["parts"]:
    f = CAD / "stl" / p["file"]
    if not f.exists():
        continue
    bpy.ops.wm.stl_import(filepath=str(f))
    ob = bpy.context.selected_objects[0]; ob.name = p["name"]; ob.scale = (0.001,) * 3
    c = p["color"]; ob.color = (c[0] * 1.05, c[1] * 1.05, c[2] * 1.05, 1.0)
    objs.append((ob, Vector(p["explode"]) * 0.001))
for fr in range(1, NF + 1):
    u = ease((fr - 30) / 90)
    for ob, ev in objs:
        ob.location = ev * u * 1.15
        ob.keyframe_insert("location", frame=fr)
def bounds(u):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for ob, ev in objs:
        for c in ob.bound_box:
            w = Vector(c) * 0.001 + ev * u * 1.15
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi
lo0, hi0 = bounds(0.0); lo1, hi1 = bounds(1.0)
print("bbox", lo0, hi0, lo1, hi1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40
tgt0, tgt1 = (lo0 + hi0) / 2, (lo1 + hi1) / 2
H0, H1 = (hi0 - lo0).z, (hi1 - lo1).z
for fr in range(1, NF + 1):
    v = fr / NF; az = math.radians(20 + 55 * v); e_ = ease((fr - 30) / 90)
    d = (H0 + (H1 - H0) * e_) * 2.55
    tgt = tgt0.lerp(tgt1, ease((fr - 30) / 90))
    cam.location = tgt + Vector((d * math.cos(az), -d * math.sin(az), 0.30 * d))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)
sc.render.filepath = str(OUTD / "f_####")
bpy.ops.render.render(animation=True)
print("CAD_ANIM_OK")
