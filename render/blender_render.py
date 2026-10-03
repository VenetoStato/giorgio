"""Render da studio di Giorgio-P (Blender 4.5, Cycles) dalla registrazione MuJoCo (anim.npz + anim.json).

blender -b -P blender_render.py -- --look gb --still 240 --out still.png
blender -b -P blender_render.py -- --look gb --frames 0 360 1 --out frames/f_####.png
Looks: gb (bianco satinato da studio, stile prodotto industriale), eva, akira (scuri, neon).
"""
import argparse
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--look", default="gb", choices=["gb", "eva", "akira"])
ap.add_argument("--still", type=int, default=-1)
ap.add_argument("--frames", type=int, nargs=3, default=None)
ap.add_argument("--out", default="still.png")
ap.add_argument("--samples", type=int, default=96)
ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
ap.add_argument("--cam", default="hero", choices=["hero", "orbit", "close", "product", "track", "face"])
ap.add_argument("--data", default="anim")
ap.add_argument("--cpos", type=float, nargs=3, default=None)
ap.add_argument("--cpos2", type=float, nargs=3, default=None)
ap.add_argument("--ctgt", type=float, nargs=3, default=None)
ap.add_argument("--lens", type=float, default=45)
ap.add_argument("--explode", type=int, default=0, help="vista esplosa: N fotogrammi sulla posa --still")
ap.add_argument("--amt", type=float, default=1.0, help="ampiezza dell'esploso (0 = solo giro di camera)")
ap.add_argument("--labels", default="", help="json con le posizioni 2D delle etichette (vista esplosa)")
ap.add_argument("--debug_py", default="")
ap.add_argument("--jpg", action="store_true", help="fotogrammi in JPEG (molto piu' leggeri)")
ap.add_argument("--fast", action="store_true", help="denoiser OptiX + dati persistenti (animazioni)")
ap.add_argument("--lc", type=float, nargs=2, default=[0.0, 0.0], help="centro del set luci (x y)")
ap.add_argument("--xray", action="store_true", help="zaino caffe' trasparente: si vede la macchina dentro")
ap.add_argument("--xray_base", action="store_true", help="carenatura della base trasparente: batteria, convertitori, contattori, cavi")
ap.add_argument("--hide", default="", help="prefissi di oggetti da nascondere (virgole)")
ap.add_argument("--dark", action="store_true", help="studio scuro (stile prodotto): fondale nero, luci di taglio")
ap.add_argument("--no_rings", action="store_true", help="niente anelli dei campi di sicurezza sul pavimento")
ap.add_argument("--objlabels", default="", help="oggetti da etichettare (nomi separati da virgola) -> json in --labels")
ap.add_argument("--no_cap", action="store_true", help="senza cappellino")
ap.add_argument("--no_ledface", action="store_true", help="volto con gli occhi/baffi 3D invece della matrice LED")
ap.add_argument("--solo", action="store_true", help="solo il robot (niente banco, flaconi, persone): foto prodotto")
args = ap.parse_args(argv)
HERE = os.path.dirname(os.path.abspath(__file__))
A = np.load(os.path.join(HERE, f"{args.data}.npz"))
J = json.load(open(os.path.join(HERE, f"{args.data}.json")))
XP, XQ, ZONE = A["xpos"], A["xquat"], A["zone"]
NF = len(XP)

# ---------------------------------------------------------------- scena vuota
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for dev_type in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dev_type
        prefs.get_devices()
        if any(d.type == dev_type for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == dev_type
            break
    except Exception:
        pass
sc.cycles.device = "GPU"
sc.cycles.samples = args.samples
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
if args.fast:
    sc.cycles.denoiser = "OPTIX"; sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast" if args.look == "gb" else "AgX - Punchy"
sc.render.fps = 30

# ---------------------------------------------------------------- materiali
def principled(name, base, rough=0.4, metal=0.0, coat=0.0, emit=None, emit_str=0.0, trans=0.0, ior=1.45, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.15
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


if args.look == "gb":
    SHELL = principled("shell", (0.80, 0.80, 0.78), 0.3, coat=0.4, sss=0.02)       # bianco satinato
    GRAPH = principled("graphite", (0.012, 0.013, 0.015), 0.38, coat=0.25)
    ALU = principled("alu", (0.62, 0.63, 0.65), 0.42, metal=0.9)
    ACC = principled("accent", (0.9, 0.9, 0.9), 0.3, emit=(1.0, 0.62, 0.3), emit_str=2.5)   # filo di luce caldo
    VISOR = principled("visor", (0.008, 0.008, 0.01), 0.03, coat=1.0, emit=(0.55, 0.85, 1.0), emit_str=0.0)
    WALL = principled("cyc", (0.42, 0.42, 0.43), 0.7)
    BENCHM = principled("bench", (0.82, 0.8, 0.76), 0.45, coat=0.1)
    BOTTLE = principled("bottle", (0.93, 0.93, 0.92), 0.25, sss=0.15)
    CAP = principled("cap", (1.0, 0.42, 0.12), 0.35)
    HUMAN = principled("human", (0.6, 0.6, 0.6), 0.55)
    TRAYM = principled("tray", (0.2, 0.21, 0.23), 0.5)
    SCAN = principled("scanner", (0.95, 0.72, 0.05), 0.35)
    world_col, world_str = (0.6, 0.62, 0.66), 0.15
else:
    pal = {"eva": ((0.30, 0.12, 0.50), (0.45, 0.95, 0.15), (1.0, 0.42, 0.05)), "akira": ((0.70, 0.04, 0.03), (0.95, 0.95, 0.92), (0.2, 0.9, 1.0))}[args.look]
    SHELL = principled("shell", pal[0], 0.3, coat=0.5)
    GRAPH = principled("graphite", (0.02, 0.02, 0.025), 0.4, coat=0.2)
    ALU = principled("alu", (0.5, 0.5, 0.52), 0.3, metal=0.95)
    ACC = principled("accent", pal[1], 0.3, emit=pal[1], emit_str=4.0)
    VISOR = principled("visor", (0.01, 0.01, 0.01), 0.04, coat=1.0, emit=pal[2], emit_str=6.0)
    WALL = principled("cyc", (0.03, 0.03, 0.04), 0.5)
    BENCHM = principled("bench", (0.06, 0.06, 0.07), 0.35, coat=0.3)
    BOTTLE = principled("bottle", (0.8, 0.82, 0.86), 0.2)
    CAP = principled("cap", pal[1], 0.3, emit=pal[1], emit_str=2.0)
    HUMAN = principled("human", (0.25, 0.25, 0.27), 0.5)
    TRAYM = principled("tray", (0.03, 0.03, 0.03), 0.5)
    SCAN = principled("scanner", (0.95, 0.72, 0.05), 0.35)
    world_col, world_str = (0.02, 0.02, 0.03), 0.3

MATMAP = {"armor": SHELL, "pale_silver": SHELL, "matte_black": GRAPH, "dark": GRAPH, "metal_silver": ALU, "steel": ALU,
          "accent": ACC, "visor": VISOR, "cam": GRAPH, "scanner": SCAN, "bench": BENCHM, "tray": TRAYM, "part": BOTTLE}
SKIP_MATS = {"floor", "neon0", "neon1", "yellow"}          # ambiente "cyberpunk" della sim: sostituito dallo studio
SKIP_NAMES = ("pillar", "pneon", "shelf", "aisle", "horn", "tray_kit_line", "core", "amr_light", "shell_back",
              "shell_chest_line", "ear", "d435_lens", "forearm_", "pauldron_left_stripe", "pauldron_right_stripe")

# ---------------------------------------------------------------- geometria
def capsule_mesh(name, r, hh):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for v in bm.verts:
        v.co.z += hh if v.co.z > 0 else -hh if v.co.z < 0 else 0
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me


def ellipsoid(name, rx, ry, rz):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32)
    o = bpy.context.object; o.scale = (rx, ry, rz); bpy.ops.object.transform_apply(scale=True)
    o.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def torso_shell(name):
    """busto a V: tronco di cono ellittico (vita stretta, petto largo) con bordi arrotondati"""
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.085, radius2=0.155, depth=0.30)
    o = bpy.context.object; o.name = name
    o.scale = (0.72, 1.0, 1.0); bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.045; bev.segments = 10; bev.limit_method = "ANGLE"
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    for p in o.data.polygons:
        p.use_smooth = True
    return o


DESIGN = {}   # i gusci di design ora sono mesh vere nel modello (shells.py)
POS_OVERRIDE = {}
BEVEL_BIG = ("pauldron", "amr_", "column", "forearm", "d435i", "scanner")


def prim_object(g):
    t, s = g["type"], g["size"]
    name = g["name"] or f"g{id(g)}"
    if name in DESIGN:
        POS_OVERRIDE[name] = DESIGN[name][1]
        return DESIGN[name][0]()
    if t == 6:      # box
        bpy.ops.mesh.primitive_cube_add(size=2)
        o = bpy.context.object; o.scale = (s[0], s[1], s[2])
        bpy.ops.object.transform_apply(scale=True)
        bev = o.modifiers.new("bevel", "BEVEL")
        big = any(k in name for k in BEVEL_BIG)
        bev.width = min(0.05 if big else 0.02, (0.45 if big else 0.35) * min(s)); bev.segments = 8 if big else 5; bev.limit_method = "NONE"
    elif t == 2:    # sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=s[0], segments=48, ring_count=24)
        o = bpy.context.object
    elif t == 5:    # cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=s[0], depth=2 * s[1], vertices=64)
        o = bpy.context.object
        bev = o.modifiers.new("bevel", "BEVEL"); bev.width = min(0.006, 0.2 * s[0]); bev.segments = 3
        bev.limit_method = "ANGLE"
    elif t == 4:    # ellissoide (occhi-display)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
        o = bpy.context.object; o.scale = (s[0], s[1], s[2]); bpy.ops.object.transform_apply(scale=True)
    elif t == 3:    # capsule
        o = bpy.data.objects.new(name, capsule_mesh(name, s[0], s[1])); bpy.context.collection.objects.link(o)
    else:
        return None
    o.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def mesh_object(g, i):
    v, f = A[f"v{i}"], A[f"f{i}"]
    me = bpy.data.meshes.new(g["name"] or f"mesh{i}")
    me.from_pydata(v.tolist(), [], f.tolist())
    me.update()
    o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    mod = o.modifiers.new("smooth", "NODES")
    try:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        o.modifiers.remove(mod)
    except Exception:
        o.modifiers.remove(mod)
    return o


bodies = {}
def body_empty(bid):
    if bid not in bodies:
        e = bpy.data.objects.new(f"body_{J['body_names'][bid]}", None)
        bpy.context.collection.objects.link(e)
        e.rotation_mode = "QUATERNION"
        bodies[bid] = e
    return bodies[bid]


NSEG = J.get("n_seg", 7)
hum_names = {f"h{h}_{k}_g": j for j, (h, k) in enumerate([(h, k) for h in range(len(J["hum"]) // NSEG) for k in range(NSEG)])}
HS = A["hum_sizes"]
HRGB = A["hum_rgba"] if "hum_rgba" in A.files else None
_hmats = {}


def human_mat(nm, j):
    """stoffa / pelle / capelli / scarpe dal colore registrato (primo fotogramma in cui la persona e' in scena)"""
    k = int(nm.split("_")[1])
    col = (0.5, 0.5, 0.5)
    if HRGB is not None and HRGB.shape[1] > j:
        bid_ = J["body_names"].index(nm[:-2]) if nm[:-2] in J["body_names"] else None
        vis = np.nonzero(XP[:, bid_, 2] > -5)[0] if bid_ is not None else np.nonzero(HS[:, j, 0] > 1e-3)[0]
        if len(vis):
            col = tuple(float(c) ** 2.2 for c in HRGB[vis[0], j, :3])     # sRGB -> lineare
    key = (k, col)
    if key in _hmats:
        return _hmats[key]
    if NSEG == 17 and k in (2, 3, 9, 10):            # pelle
        mt = principled(f"skin{len(_hmats)}", col, 0.45, sss=0.25)
    elif NSEG == 17 and k == 4:                      # capelli o casco
        mt = principled(f"hair{len(_hmats)}", col, 0.25 if sum(col) > 2.4 else 0.6, coat=0.5 if sum(col) > 2.4 else 0.0)
    elif NSEG == 17 and k in (15, 16):               # scarpe
        mt = principled(f"shoe{len(_hmats)}", col, 0.35, coat=0.3)
    else:                                            # tessuto
        mt = principled(f"cloth{len(_hmats)}", col, 0.78)
        try:
            mt.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.4
        except Exception:
            pass
    _hmats[key] = mt
    return mt
for i, g in enumerate(J["geoms"]):
    if g["mat"] in SKIP_MATS or any(k in (g["name"] or "") for k in SKIP_NAMES):
        continue
    if g["type"] == 0:           # piano
        continue
    nm = g["name"] or ""
    bnm = J["body_names"][g["body"]]
    if args.solo and (bnm.startswith(("h0_", "h1_", "h2_", "h3_", "tote", "hand_cup", "part_")) or (bnm == "world" and not nm.startswith("floor"))):
        continue
    if nm in hum_names:          # persone: misura del segmento dalla registrazione
        j = hum_names[nm]
        sz = HS[:, j, :].max(0)
        if sz[0] < 1e-3:
            continue
        g = dict(g, size=sz.tolist())
    o = mesh_object(g, i) if g.get("mesh") else prim_object(g)
    if o is None:
        continue
    mat = MATMAP.get(g["mat"])
    if nm in hum_names:
        mat = human_mat(nm, hum_names[nm])
    SPECIAL = {"cm_body": lambda: principled("macchina_grafite", (0.035, 0.036, 0.040), 0.3, coat=0.5),
               "cm_head": lambda: principled("macchina_nero", (0.015, 0.015, 0.017), 0.25, coat=0.6),
               "cm_lever": lambda: principled("macchina_nero2", (0.02, 0.02, 0.022), 0.3, coat=0.4),
               "cm_tank": lambda: principled("tank_glass", (0.85, 0.92, 1.0), 0.05, trans=1.0, ior=1.49),
               "cup_ring": lambda: principled("ring_glass", (0.85, 0.92, 1.0), 0.08, trans=1.0, ior=1.49),
               "cm_logo": lambda: principled("logo", (0.85, 0.85, 0.85), 0.3, metal=0.8),
               "cup_g": lambda: principled("paper_cup", (0.94, 0.93, 0.90), 0.55, sss=0.1),
               "cm_bin": lambda: principled("macchina_nero3", (0.02, 0.02, 0.022), 0.35)}
    if nm in SPECIAL:
        mat = SPECIAL[nm]()
    if nm.startswith("cup_stack"):
        mat = SPECIAL["cup_g"]()
    if mat is None:
        rgba = g["rgba"]
        mat = principled(f"m{i}", tuple(rgba[:3]), 0.4)
    if nm.startswith("part_") and nm.endswith("_cap"):
        mat = CAP
    o.data.materials.clear(); o.data.materials.append(mat)
    o.parent = body_empty(g["body"])
    o.rotation_mode = "QUATERNION"
    o.location = Vector(POS_OVERRIDE.get(nm, g["pos"])); o.rotation_quaternion = Quaternion(g["quat"])

# ---------------------------------------------------------------- animazione dei corpi (fcurve dirette: veloce)
def bake(obj, frames):
    bid = [k for k, v in bodies.items() if v is obj][0]
    for i, f in enumerate(frames):
        obj.location = Vector(XP[f, bid].tolist()); obj.rotation_quaternion = Quaternion(XQ[f, bid].tolist())
        if len(frames) > 1:
            obj.keyframe_insert("location", frame=i); obj.keyframe_insert("rotation_quaternion", frame=i)


if args.frames:
    F = np.arange(args.frames[0], min(args.frames[1], NF), args.frames[2])
elif args.explode:
    F = np.full(args.explode, min(args.still, NF - 1))
else:
    F = np.array([min(args.still, NF - 1)])
for e in bodies.values():
    bake(e, F)
sc.frame_start, sc.frame_end = 0, len(F) - 1

# ---------------------------------------------------------------- geom animati (occhi, baffi, tazzina, vapore, LED)
AN = A["anim"] if "anim" in A.files else np.zeros((NF, 0, 14))
GEO = {g["name"]: g for g in J["geoms"]}
LEDFACE = (not args.no_ledface) and "face" in A.files and A["face"].shape[0] == NF
for k, nm in enumerate(J.get("anim_names", [])):
    o = bpy.data.objects.get(nm)
    if o is None or AN.shape[1] <= k:
        continue
    if LEDFACE and nm.startswith(("eye_", "mus_")):      # sostituiti dalla matrice LED
        o.hide_render = True
        continue
    glow = nm.startswith(("eye", "mus", "coffee_led", "charger_led", "status_led", "cm_btn1"))
    base = AN[F[0], k, 10:13]
    mt = principled(nm + "_m", tuple(base) if not glow else (0.02, 0.02, 0.02), 0.25 if "steam" not in nm else 0.5,
                    emit=tuple(base), emit_str=6.0 if glow else 0.0)
    if nm.startswith("mus"):                          # baffi in silicone morbido lattiginoso, retroilluminati dal LED
        mt = principled(nm + "_m", (0.9, 0.88, 0.84), 0.45, sss=0.6, emit=tuple(base), emit_str=2.2)
    if "steam" in nm:
        mt.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
    o.data.materials.clear(); o.data.materials.append(mt)
    sz0 = np.maximum(np.array(GEO[nm]["size"]), 1e-6)
    bsdf = mt.node_tree.nodes["Principled BSDF"]
    for i, f in enumerate(F):
        e = AN[f, k]
        o.location = Vector(e[0:3].tolist()); o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Quaternion(e[3:7].tolist())
        sz = np.maximum(e[7:10], 1e-6); t_ = GEO[nm]["type"]
        o.scale = (sz[0] / sz0[0], sz[0] / sz0[0], sz[1] / sz0[1]) if t_ == 5 else (sz[0] / sz0[0],) * 3 if t_ == 2 else tuple(sz / sz0) if t_ == 4 else (1, 1, 1)
        hidden = e[13] < 0.05
        o.hide_render = bool(hidden)
        (bsdf.inputs["Emission Color"] if glow else bsdf.inputs["Base Color"]).default_value = (*e[10:13].tolist(), 1)
        if len(F) > 1:
            o.keyframe_insert("location", frame=i); o.keyframe_insert("rotation_quaternion", frame=i); o.keyframe_insert("scale", frame=i)
            o.keyframe_insert("hide_render", frame=i)
            (bsdf.inputs["Emission Color"] if glow else bsdf.inputs["Base Color"]).keyframe_insert("default_value", frame=i)

# ---------------------------------------------------------------- cappellino rosso con la G (italianita' in chiave comica)
def add_cap():
    hs_ = bpy.data.objects.get("head_shell")
    if hs_ is None or hs_.parent is None:
        return
    par = hs_.parent; c0 = Vector(hs_.location)
    def child(o_):
        o_.parent = par
        return o_
    # calotta: mezza sfera morbida un filo piu' grande della testa
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32)
    dome = bpy.context.object; dome.name = "cap_dome"
    bm_ = bmesh.new(); bm_.from_mesh(dome.data)
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z < -0.05], context="VERTS")
    bm_.to_mesh(dome.data); bm_.free()
    dome.scale = (0.094, 0.103, 0.064); bpy.ops.object.transform_apply(scale=True)
    for p_ in dome.data.polygons:
        p_.use_smooth = True
    sol = dome.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.004
    child(dome); dome.location = c0 + Vector((-0.004, 0, 0.042))
    # visiera: mezzaluna piena davanti, leggermente inclinata in giu'
    verts_ = [(0.0, 0.0, 0.0)] + [(0.078 * math.cos(t_), 0.095 * math.sin(t_), 0.0) for t_ in np.linspace(-math.pi / 2, math.pi / 2, 48)]
    faces_ = [(0, i_, i_ + 1) for i_ in range(1, 48)]
    me_ = bpy.data.meshes.new("cap_brim"); me_.from_pydata(verts_, [], faces_); me_.update()
    brim = bpy.data.objects.new("cap_brim", me_); bpy.context.collection.objects.link(brim)
    sol2 = brim.modifiers.new("sol", "SOLIDIFY"); sol2.thickness = 0.005
    bv = brim.modifiers.new("bev", "BEVEL"); bv.width = 0.0015; bv.segments = 3
    child(brim); brim.location = c0 + Vector((0.035, 0, 0.040)); brim.rotation_euler = Euler((0, math.radians(10), 0))
    # tondo bianco con la G verde
    bpy.ops.mesh.primitive_cylinder_add(radius=0.021, depth=0.002, vertices=64)
    disc = bpy.context.object; disc.name = "cap_disc"; child(disc)
    nrm = Vector((0.80, 0, 0.60)).normalized()
    disc.location = c0 + Vector((-0.004, 0, 0.042)) + Vector((0.094 * nrm.x * 0.98, 0, 0.064 * nrm.z * 0.98)) + nrm * 0.002
    disc.rotation_mode = "QUATERNION"; disc.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(nrm)
    cu = bpy.data.curves.new("capG", "FONT"); cu.body = "G"; cu.size = 0.036; cu.extrude = 0.0012; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    try:
        cu.font = bpy.data.fonts.load("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf")
    except Exception:
        pass
    gtxt = bpy.data.objects.new("cap_G", cu); bpy.context.collection.objects.link(gtxt); child(gtxt)
    gtxt.location = disc.location + nrm * 0.0016
    gtxt.rotation_mode = "QUATERNION"
    gtxt.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(nrm) @ Quaternion(Vector((0, 0, 1)), math.radians(90))
    red = principled("cap_red", (0.16, 0.0015, 0.003), 0.5, coat=0.05)
    try:
        red.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.6
    except Exception:
        pass
    for o_ in (dome, brim):
        o_.data.materials.append(red)
    disc.data.materials.append(principled("cap_white", (0.9, 0.9, 0.88), 0.4))
    gtxt.data.materials.append(principled("cap_green", (0.0, 0.2, 0.05), 0.35))


if not args.no_cap:
    add_cap()

# ---------------------------------------------------------------- tricolore: tre fasce alte 22 mm attorno alla base (ben visibili)
for k_, (z_, col_, rough_) in enumerate(((0.1395, (0.0, 0.287, 0.061), 0.3), (0.114, (0.88, 0.885, 0.88), 0.25), (0.0885, (0.617, 0.024, 0.038), 0.3))):
    o_ = bpy.data.objects.get(f"tricolore{k_}")
    if o_ is None:
        continue
    vv_ = np.array([v.co[:] for v in o_.data.vertices]); ext_ = vv_.max(0) - vv_.min(0)
    ax_ = int(np.argmin(ext_))                          # asse sottile della fascia (MuJoCo riallinea le mesh)
    sc_ = [1.012, 1.012, 1.012]; sc_[ax_] = 0.0255 / max(ext_[ax_], 1e-4)       # fasce contigue da 25 mm, appena sporgenti
    o_.scale = tuple(sc_)
    o_.location.z = z_
    mt_ = principled(f"tricolore_m{k_}", col_, rough_, coat=0.3, emit=col_, emit_str=0.35 if not args.dark else 1.2)
    o_.data.materials.clear(); o_.data.materials.append(mt_)

# ---------------------------------------------------------------- volto: matrice LED RGB 64 x 32 dietro la visiera
if LEDFACE:
    sys.path.insert(0, HERE)
    import ledface
    from mathutils import kdtree
    fg = bpy.data.objects.get("face_glass")
    if fg is not None:
        vv = np.array([v.co[:] for v in fg.data.vertices])
        front = vv[vv[:, 0] > 0]
        kd = kdtree.KDTree(len(front))
        for i_, p_ in enumerate(front):
            kd.insert((0.0, p_[1], p_[2]), i_)
        kd.balance()
        NYG, NZG = 64, 32
        ys, zs = np.linspace(-0.064, 0.064, NYG + 1), np.linspace(-0.032, 0.032, NZG + 1)
        verts, faces, uvs = [], [], []
        # il frame locale della mesh e' ruotato (MuJoCo la riallinea): passo da (y, z) "del volto" alle coordinate locali
        qn = fg.rotation_quaternion.to_matrix()
        def to_local(yw, zw):
            v_ = qn.inverted() @ Vector((0.0, yw, zw))
            return v_[1], v_[2]
        for iz, z_ in enumerate(zs):
            for iy, y_ in enumerate(ys):
                ly, lz = to_local(y_, z_)
                near = kd.find_n((0.0, ly, lz), 4)
                x_ = float(np.mean([front[n_[1]][0] for n_ in near])) + 0.0012
                verts.append((x_, ly, lz))
        for iz in range(NZG):
            for iy in range(NYG):
                a_ = iz * (NYG + 1) + iy
                faces.append((a_, a_ + 1, a_ + NYG + 2, a_ + NYG + 1))
        me = bpy.data.meshes.new("led_panel"); me.from_pydata(verts, [], faces); me.update()
        uvl = me.uv_layers.new(name="UV")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index; iz, iy = divmod(vi, NYG + 1)
                uvl.data[li].uv = (iy / NYG, iz / NZG)       # +y del robot = destra di chi guarda
            poly.use_smooth = True
        led = bpy.data.objects.new("led_panel", me); bpy.context.collection.objects.link(led)
        led.parent = fg.parent; led.rotation_mode = "QUATERNION"
        led.location = fg.location.copy(); led.rotation_quaternion = fg.rotation_quaternion.copy()
        # una PNG per fotogramma, dallo stato del volto registrato
        FC = A["face"]
        tdir = os.path.join(HERE, "ledtex", args.out.replace("/", "_").replace("#", "").replace(".png", "").strip("_") or "led")
        os.makedirs(tdir, exist_ok=True)
        img = None
        for i_, f_ in enumerate(F):
            code, gx, gy, blink, tt = [float(v) for v in FC[f_]]
            im = ledface.led_image_big(ledface.draw_px(code, gx, gy, blink, tt))[::-1]   # matrice 32 x 16, LED grandi
            if img is None:
                img = bpy.data.images.new("ledtmp", im.shape[1], im.shape[0], alpha=False)
            img.pixels.foreach_set(im.ravel())
            img.filepath_raw = os.path.join(tdir, f"led_{i_ + 1:04d}.png"); img.file_format = "PNG"; img.save()
        mt = bpy.data.materials.new("led_mat"); mt.use_nodes = True
        nt = mt.node_tree; bs = nt.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1); bs.inputs["Roughness"].default_value = 0.25
        bs.inputs["Coat Weight"].default_value = 1.0; bs.inputs["Coat Roughness"].default_value = 0.03
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(os.path.join(tdir, "led_0001.png"))
        tx.image.source = "SEQUENCE"
        tx.image_user.frame_duration = len(F); tx.image_user.frame_start = 0; tx.image_user.frame_offset = 0
        tx.image_user.use_auto_refresh = True
        tx.interpolation = "Cubic"
        nt.links.new(tx.outputs["Color"], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = 7.0
        led.data.materials.append(mt)
        bpy.data.images.remove(img)

LOGO = os.path.join(HERE, "logo", "logo.png")
for o_ in [o for o in bpy.data.objects if o.name.startswith("logo_")]:     # logo (tazzina con la G) come decalcomania sul guscio
    mt_ = bpy.data.materials.new("logo_" + o_.name); mt_.use_nodes = True; nt_ = mt_.node_tree
    bs_ = nt_.nodes["Principled BSDF"]; bs_.inputs["Roughness"].default_value = 0.35
    tc_ = nt_.nodes.new("ShaderNodeTexCoord"); sx_ = nt_.nodes.new("ShaderNodeSeparateXYZ"); cb_ = nt_.nodes.new("ShaderNodeCombineXYZ")
    nt_.links.new(tc_.outputs["Generated"], sx_.inputs[0])
    thin_x = o_.dimensions.x < min(o_.dimensions.y, o_.dimensions.z)
    if thin_x:                                      # petto: normale +x; chi guarda il robot ha +y a destra -> u lungo +y
        nt_.links.new(sx_.outputs["Y"], cb_.inputs["X"])
    else:                                           # zaino: normale -y, u lungo x
        nt_.links.new(sx_.outputs["X"], cb_.inputs["X"])
    nt_.links.new(sx_.outputs["Z"], cb_.inputs["Y"])
    im_ = nt_.nodes.new("ShaderNodeTexImage"); im_.image = bpy.data.images.load(LOGO, check_existing=True); im_.extension = "CLIP"
    nt_.links.new(cb_.outputs[0], im_.inputs["Vector"])
    nt_.links.new(im_.outputs["Color"], bs_.inputs["Base Color"]); nt_.links.new(im_.outputs["Alpha"], bs_.inputs["Alpha"])
    mt_.blend_method = "BLEND" if hasattr(mt_, "blend_method") else None
    o_.data.materials.clear(); o_.data.materials.append(mt_)

if args.hide:
    for o_ in list(bpy.data.objects):
        if o_.name.startswith(tuple(h_.strip() for h_ in args.hide.split(","))):
            o_.hide_render = True
if args.xray_base:                                      # carenatura della base in vetro: si vede l'impianto elettrico
    for o_ in list(bpy.data.objects):
        if o_.name in ("base_cover", "scan_window", "bumper", "status_led0") or o_.name.startswith("tricolore"):
            mt_ = principled(o_.name + "_xray", (0.85, 0.9, 1.0), 0.05, trans=0.0)
            b_ = mt_.node_tree.nodes["Principled BSDF"]; b_.inputs["Alpha"].default_value = 0.10 if o_.name == "base_cover" else 0.22
            b_.inputs["Emission Color"].default_value = (0.5, 0.75, 1.0, 1); b_.inputs["Emission Strength"].default_value = 0.06
            o_.data.materials.clear(); o_.data.materials.append(mt_)
        if o_.name.startswith("pw_cable"):
            mt_ = principled(o_.name + "_glow", (1.0, 0.45, 0.1), 0.3)
            b_ = mt_.node_tree.nodes["Principled BSDF"]; b_.inputs["Emission Color"].default_value = (1.0, 0.45, 0.1, 1)
            b_.inputs["Emission Strength"].default_value = 4.0
            o_.data.materials.clear(); o_.data.materials.append(mt_)

if args.xray:                                           # guscio dello zaino in vetro: si vede la macchina dentro
    for nm_ in ("cm_housing", "cm_band", "cm_vent"):
        o_ = bpy.data.objects.get(nm_)
        if o_ is not None:
            mt_ = principled(nm_ + "_xray", (0.85, 0.9, 1.0), 0.05, trans=0.0)
            b_ = mt_.node_tree.nodes["Principled BSDF"]; b_.inputs["Alpha"].default_value = 0.12 if nm_ == "cm_housing" else 0.3
            b_.inputs["Emission Color"].default_value = (0.5, 0.75, 1.0, 1); b_.inputs["Emission Strength"].default_value = 0.08
            o_.data.materials.clear(); o_.data.materials.append(mt_)

# ---------------------------------------------------------------- vista esplosa: gruppi che si separano (riferimento robot)
EXPL = {}
if args.explode:
    ia = J["body_names"].index("amr")
    qa = XQ[F[0], ia]; Rr = Quaternion(qa.tolist()).to_matrix()
    def group(o):
        bn = o.parent.name[5:] if o.parent else ""
        n = o.name
        if n.startswith("tray"):
            return "vassoio", (0.30, 0, 0.32)
        if n.startswith(("coffee", "cup", "capsule", "steam", "cm_")):
            return "caffe", (-0.40, 0, 0.22)
        if n.startswith("scanner"):
            return "scanner", (0.22 * np.sign(o.location.x or 1), 0.22 * np.sign(o.location.y or 1), 0.0)
        if bn.startswith("part_"):
            return None, None
        if bn == "amr" or bn.startswith("drive"):
            return "base", (0, 0, 0.0)          # la base resta a terra: tutto il resto sale
        if bn == "column":
            return "colonna", (0, 0, 0.22)
        if bn == "crown":
            return "testa", (0.0, 0, 0.80)
        if bn.startswith("openarm_left") or bn.startswith("left_"):
            return "braccio_sx", (0, 0.36, 0.42)
        if bn.startswith("openarm_right") or bn.startswith("right_"):
            return "braccio_dx", (0, -0.36, 0.42)
        if bn == "torso":
            return "busto", (0, 0, 0.45)
        return None, None
    n_ = len(F)
    sc.frame_set(0); bpy.context.view_layer.update()
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o.parent is None:
            continue
        gname, off = group(o)
        if gname is None:
            continue
        wo = Rr @ Vector(off)
        Rp = o.parent.matrix_world.to_3x3().inverted()
        lo = Rp @ wo
        l0 = o.location.copy()
        EXPL.setdefault(gname, []).append(o)
        for i in range(n_):
            u = min(1.0, max(0.0, (i / n_ - 0.08) / 0.35)); u = u * u * (3 - 2 * u)
            o.location = l0 + lo * u * args.amt
            o.keyframe_insert("location", frame=i)

# ---------------------------------------------------------------- studio: fondale curvo, luci
def cyclorama():
    prof = [(-x, 0.0) for x in np.linspace(-6.0, 0.0, 2)]  # pavimento da x=6 a x=0 (relativo alla parete)
    R = 2.0
    pts = [(6.0, 0.0), (0.0, 0.0)]
    pts = [(x, 0.0) for x in np.linspace(25.0, 0.0, 8)]
    for a in np.linspace(0, math.pi / 2, 16)[1:]:
        pts.append((-R * math.sin(a), R - R * math.cos(a)))
    pts.append((-R, 7.0))
    verts, faces = [], []
    ys = np.linspace(-25, 25, 2)
    for y in ys:
        for x, z in pts:
            verts.append((x, y, z))
    n = len(pts)
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))
    me = bpy.data.meshes.new("cyc"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("cyclorama", me); bpy.context.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    o.location = (-6.8, 0, 0)
    o.data.materials.append(WALL)
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2


cyclorama()


def area(name, loc, rot, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.color = color; ld.shape = shape
    ld.size = size; ld.size_y = size_y or size
    lo = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo)
    lo.location = loc; lo.rotation_euler = Euler(rot)
    return lo


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


k = 0.55 if args.look == "gb" else 0.5
L1 = area("key", (2.6, -2.4, 3.2), (0, 0, 0), 2.5, 900 * k, (1.0, 0.96, 0.92)); aim(L1, (0.2, 0, 1.0))
L2 = area("fill", (2.2, 2.8, 1.8), (0, 0, 0), 3.0, 320 * k, (0.92, 0.95, 1.0)); aim(L2, (0.2, 0, 1.0))
L3 = area("rim", (-1.8, -1.2, 2.8), (0, 0, 0), 1.5, 600 * k, (1.0, 0.98, 0.95)); aim(L3, (0.0, 0, 1.2))
L4 = area("top", (0.3, 0, 4.0), (0, 0, 0), 4.0, 500 * k, shape="RECTANGLE", size_y=2.0); aim(L4, (0.3, 0, 0))
for L_ in (L1, L2, L3, L4):
    L_.location.x += args.lc[0]; L_.location.y += args.lc[1]
if args.dark:                                           # studio scuro: fondale quasi nero, due luci di taglio fredde, chiave morbida
    WALL.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
    WALL.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
    world_col, world_str = (0.01, 0.01, 0.012), 0.05
    L1.data.energy *= 0.38; L2.data.energy *= 0.12; L4.data.energy *= 0.06
    for nm_, loc_ in (("rimL", (-1.2, 2.2, 2.4)), ("rimR", (-1.4, -2.3, 2.2))):
        Lr = area(nm_, (loc_[0] + args.lc[0], loc_[1] + args.lc[1], loc_[2]), (0, 0, 0), 0.6, 900, (0.85, 0.92, 1.0), size_y=2.4)
        aim(Lr, (args.lc[0], args.lc[1], 1.0))
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*world_col, 1); bg.inputs[1].default_value = world_str

# ---------------------------------------------------------------- campi di sicurezza: anelli di luce sul pavimento
def ring(name, r, col):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, major_segments=256, minor_segments=8, location=(0, 0, 0.004))
    o = bpy.context.object; o.name = name; o.scale.z = 0.3
    m = principled(name + "_m", (0.1, 0.1, 0.1), 0.5, emit=col, emit_str=3.0)
    o.data.materials.append(m)
    return o, m


ring_w, mw = ring("ring_warn", J["r_warn"], (1.0, 0.75, 0.15))
if args.no_rings:
    ring_w.hide_render = True
ring_p, mp = ring("ring_prot", J["r_prot"], (1.0, 0.18, 0.12))
if args.no_rings:
    ring_p.hide_render = True
for i, f in enumerate(F):        # intensita' secondo lo stato dello scanner
    z = int(ZONE[f])
    for m_, lvl in ((mw, 1), (mp, 2)):
        s = m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = 18.0 if z >= lvl and (lvl == 2 or z == 1) else 2.0
        s.keyframe_insert("default_value", frame=i)

# ---------------------------------------------------------------- camera
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 42
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0
tgt = Vector((0.15, 0.0, 1.0))
if args.cpos is not None:                                # inquadratura esplicita: ha sempre la precedenza
    cam.location = tuple(args.cpos); tgt = Vector(args.ctgt); cam.data.lens = args.lens
elif args.cam == "close":
    cam.location = (1.35, -0.95, 1.45); tgt = Vector((0.25, -0.05, 1.05)); cam.data.lens = 50
elif args.cam == "hero":
    cam.location = (2.0, -2.35, 1.95); tgt = Vector((0.12, 0.0, 1.18)); cam.data.lens = 45
elif args.cam == "face":
    bid = J["body_names"].index("crown"); c = XP[F[0], bid]
    cam.location = (c[0] + 0.75, c[1] - 0.45, c[2] + 0.05); tgt = Vector((c[0] + 0.05, c[1], c[2] - 0.02)); cam.data.lens = 85
elif args.cam == "product":
    cam.location = (3.3, -2.2, 1.35); tgt = Vector((0.05, 0.0, 0.85)); cam.data.lens = 50
focus = bpy.data.objects.new("focus", None); bpy.context.collection.objects.link(focus); focus.location = tgt
cam.data.dof.focus_object = focus
aim(cam, tgt)
if args.cpos2 is not None and len(F) > 1:
    p0, p1 = Vector(args.cpos), Vector(args.cpos2)
    for i in range(len(F)):
        u = i / (len(F) - 1); u = u * u * (3 - 2 * u)
        cam.location = p0.lerp(p1, u); aim(cam, tgt)
        cam.keyframe_insert("location", frame=i); cam.keyframe_insert("rotation_euler", frame=i)
if args.cam == "track" and len(F) > 1:
    bid = J["body_names"].index("amr"); cam.data.lens = 40
    for i, f in enumerate(F):
        b = XP[f, bid]
        focus.location = Vector((b[0] + 0.15, b[1], 1.0))
        cam.location = (b[0] + 2.2 - 0.6 * i / len(F), b[1] - 2.5, 1.9)
        aim(cam, focus.location)
        cam.keyframe_insert("location", frame=i); cam.keyframe_insert("rotation_euler", frame=i); focus.keyframe_insert("location", frame=i)
if args.cam == "orbit" and len(F) > 1:
    cam.data.lens = 45
    for i in range(len(F)):
        a = math.radians(-78 + 40 * i / (len(F) - 1))     # di lato-davanti, sopra il banco
        cam.location = (0.15 + 2.6 * math.cos(a), 2.6 * math.sin(a), 1.75)
        aim(cam, tgt)
        cam.keyframe_insert("location", frame=i); cam.keyframe_insert("rotation_euler", frame=i)

# ---------------------------------------------------------------- bagliore dei LED (compositor)
sc.use_nodes = True
ntc = sc.node_tree
for n_ in list(ntc.nodes):
    ntc.nodes.remove(n_)
rl_ = ntc.nodes.new("CompositorNodeRLayers"); gl_ = ntc.nodes.new("CompositorNodeGlare"); co_ = ntc.nodes.new("CompositorNodeComposite")
gl_.glare_type = "FOG_GLOW"; gl_.quality = "HIGH"; gl_.threshold = 1.2; gl_.size = 7
try:
    gl_.mix = -0.55
except Exception:
    pass
ntc.links.new(rl_.outputs["Image"], gl_.inputs["Image"]); ntc.links.new(gl_.outputs["Image"], co_.inputs["Image"])

# ---------------------------------------------------------------- render
if args.debug_py:
    exec(open(args.debug_py).read()); sys.exit(0)
if args.labels and args.objlabels:
    from bpy_extras.object_utils import world_to_camera_view
    names_ = [n_.strip() for n_ in args.objlabels.split(",")]
    out = []
    for i in range(len(F)):
        sc.frame_set(i)
        row = {}
        for n_ in names_:
            o_ = bpy.data.objects.get(n_)
            if o_ is None:
                continue
            bb = [o_.matrix_world @ Vector(c_) for c_ in o_.bound_box]
            c_ = sum(bb, Vector((0, 0, 0))) / 8
            v = world_to_camera_view(sc, cam, c_)
            row[n_] = [v.x, 1 - v.y]
        out.append(row)
    json.dump(out, open(os.path.join(HERE, args.labels), "w"))
elif args.labels and EXPL:
    from bpy_extras.object_utils import world_to_camera_view
    out = []
    for i in range(len(F)):
        sc.frame_set(i)
        dg = bpy.context.evaluated_depsgraph_get()
        row = {}
        for gname, objs in EXPL.items():
            pts = [o.matrix_world.translation for o in objs]
            c = sum(pts, Vector((0, 0, 0))) / len(pts)
            v = world_to_camera_view(sc, cam, c)
            row[gname] = [v.x, 1 - v.y]
        out.append(row)
    json.dump(out, open(os.path.join(HERE, args.labels), "w"))
if args.frames or args.explode:
    sc.render.filepath = os.path.join(HERE, args.out)
    if args.jpg:
        sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 93
    else:
        sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
else:
    sc.frame_set(0)
    sc.render.filepath = os.path.join(HERE, args.out)
    bpy.ops.render.render(write_still=True)
print("RENDER OK ->", args.out)
