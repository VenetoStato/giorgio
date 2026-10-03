"""Quick Blender preview of the CAD exports (assembled + exploded), colours from out/exploded/exploded.json.

    ~/tools/blender-4.5.9-linux-x64/blender -b -P cad/render_blender.py -- [assembled|exploded|both]

Writes cad/out/render_assembled.png and cad/out/render_exploded.png (Workbench engine, fast, no GPU needed).
The same JSON (per-part file, colour, material, explode vector) is meant for a proper Cycles scene later.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "both"
meta = json.loads((OUT / "exploded" / "exploded.json").read_text())


def scene(exploded):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "OBJECT"
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1800
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.93, 0.93, 0.94)
    for p in meta["parts"]:
        f = (OUT / "exploded" / p["file"]) if exploded else (OUT / "stl" / p["file"])
        if not f.exists():
            f = OUT / "exploded" / p["file"]
            if not f.exists():
                continue
            off = [-v for v in p["explode"]]
        else:
            off = [0, 0, 0]
        bpy.ops.wm.stl_import(filepath=str(f))
        ob = bpy.context.selected_objects[0]
        ob.name = p["name"]
        ob.scale = (0.001, 0.001, 0.001)
        ob.location = Vector(off) * 0.001
        c = p["color"]
        ob.color = (c[0], c[1], c[2], 1.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    d = 3.6 if exploded else 2.6
    az = math.radians(35)
    tgt = Vector((0, 0, 0.85 if exploded else 0.75))
    cam.location = tgt + Vector((d * math.cos(az), -d * math.sin(az), 0.55 * d))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc.render.filepath = str(OUT / ("render_exploded.png" if exploded else "render_assembled.png"))
    bpy.ops.render.render(write_still=True)


if mode in ("assembled", "both"):
    scene(False)
if mode in ("exploded", "both"):
    scene(True)
