import bpy, sys
__file__ = "/home/gpitton/giorgio_sim/render/blender_render.py"; exec(open(__file__).read().split("# ---------------------------------------------------------------- render")[0])
bpy.context.scene.frame_set(0)
for n in ("body_openarm_right_link4", "body_torso", "body_part_right_0", "body_amr", "body_h0_0"):
    o = bpy.data.objects.get(n)
    print("DBG", n, tuple(round(x, 3) for x in o.matrix_world.translation) if o else None)
big = sorted([(max(o.dimensions), o.name) for o in bpy.data.objects if o.type == "MESH"], reverse=True)[:6]
print("DBG big", big)
print("DBG nobj", len(bpy.data.objects))
