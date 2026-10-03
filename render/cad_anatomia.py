"""Sequenza "anatomia" dal CAD (cad/out): un gruppo di componenti alla volta si accende, il resto resta una sagoma scura.
Camera in lenta orbita. Uscita: <out>/f_####.jpg + <out>/gruppi.json (fotogramma di inizio/fine di ogni gruppo).
uso: blender -b -P cad_anatomia.py -- out_dir"""
import bpy, json, math, re, sys
from pathlib import Path
from mathutils import Vector

OUTD = Path(sys.argv[sys.argv.index("--") + 1]); OUTD.mkdir(parents=True, exist_ok=True)
CAD = Path.home() / "giorgio_sim/cad/out"
meta = json.loads((CAD / "exploded" / "exploded.json").read_text())
# gruppi in ordine dal basso verso l'alto: (chiave, regex sui nomi delle parti)
GROUPS = [("base", r"^B00_|tracer|ranger|theron"),
          ("power", r"^E01_|^P03_|^P04_|^P05_|^E09_"),
          ("electronics", r"^E0[2-8]_|^E1[1-3]_|^P0[6-8]_|^P30_|^P31_"),
          ("scanners", r"^S02_|^P09_"),
          ("structure", r"^P01_|^P29_|^S01_|^P02_|^P11_|^P27_|^P28_|^P16_"),
          ("arms", r"^OA_|^openarm_"),
          ("head", r"^S04_|^S05_|^P17_|^P18_|^SH05_"),
          ("coffee", r"^P2[1-6]_|^S0[7-9]_|^S10|^SH06_"),
          ("tray", r"^P19_|^P20_|^S06_"),
          ("shells", r"^SH0[1-4]")]
HOLD, FADE = 66, 12                                  # fotogrammi per gruppo, dissolvenza dell'accensione
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_shadows = False; sh.show_cavity = True; sh.cavity_type = "BOTH"
sh.show_object_outline = True; sh.object_outline_color = (0.0, 0.0, 0.0); sh.show_specular_highlight = True
sh.show_xray = True; sh.xray_alpha = 0.55                 # vista in trasparenza: si vedono anche batteria ed elettronica dentro la base
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.018, 0.018, 0.022)
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
objs = {}
for p in meta["parts"]:
    f = CAD / "stl" / p["file"]
    if not f.exists():
        continue
    bpy.ops.wm.stl_import(filepath=str(f))
    ob = bpy.context.selected_objects[0]; ob.name = p["name"]; ob.scale = (0.001,) * 3
    g = next((k for k, rx in GROUPS if re.search(rx, p["name"], re.I)), None)
    objs[ob] = (g, p["color"])
NG = len(GROUPS); NF = NG * HOLD + 30
sc.frame_start, sc.frame_end = 1, NF
DIM = (0.07, 0.07, 0.08)
HI = (1.0, 0.50, 0.12)                                  # gruppo acceso: arancio Giorgio
for fr in range(1, NF + 1):
    gi = min(NG - 1, max(0, (fr - 15) // HOLD)); g_on = GROUPS[gi][0]
    u = min(1.0, max(0.0, ((fr - 15) - gi * HOLD) / FADE))
    for ob, (g, col) in objs.items():
        c = [DIM[i] + (HI[i] - DIM[i]) * u for i in range(3)] if g == g_on else list(DIM)
        ob.color = (c[0], c[1], c[2], 1.0)
        ob.keyframe_insert("color", frame=fr)
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for ob in objs:
    for c in ob.bound_box:
        w = Vector(c) * 0.001
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
tgt = (lo + hi) / 2; H = (hi - lo).z
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
for fr in range(1, NF + 1):
    az = math.radians(25 + 70 * fr / NF); d = H * 1.75
    cam.location = tgt + Vector((d * math.cos(az), -d * math.sin(az), 0.22 * d))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)
json.dump({"hold": HOLD, "start": 15, "groups": [k for k, _ in GROUPS], "nf": NF}, open(OUTD / "gruppi.json", "w"))
sc.render.filepath = str(OUTD / "f_####")
bpy.ops.render.render(animation=True)
print("ANATOMIA_OK")
