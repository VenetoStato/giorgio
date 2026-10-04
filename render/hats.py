"""Cappelli di Giorgio (render Blender): coppola in tweed, bustina da barista, cappellino a visiera piatta girato.
Geometria parametrica in metri, nel frame del corpo della testa; c0 = centro del guscio della testa.
La calotta della testa e' circa un ellissoide di semiassi (0.085, 0.095, 0.082) centrato in c0."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector

HEAD_C = Vector((0.0, 0.0, 0.0))
HEAD_R = (0.085, 0.095, 0.082)          # guscio della testa misurato nel render (semiassi)


def head_z(x, y):
    """quota della calotta della testa nel punto (x, y) (frame testa, relativo a c0)"""
    u = ((x - HEAD_C.x) / HEAD_R[0]) ** 2 + ((y - HEAD_C.y) / HEAD_R[1]) ** 2
    return HEAD_C.z + HEAD_R[2] * math.sqrt(max(0.0, 1.0 - u))


# ------------------------------------------------------------------ utilita'
def mesh_obj(name, V, F, par, loc, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = smooth
    o.parent = par; o.location = loc
    return o


def grid(fn, nu, nv, closed_u=True, cap_last=False):
    """superficie parametrica fn(u, v) -> (x, y, z); u chiusa"""
    V, F = [], []
    for j in range(nv + 1):
        for i in range(nu):
            V.append(fn(i / nu, j / nv))
    for j in range(nv):
        for i in range(nu if closed_u else nu - 1):
            a = j * nu + i; b = j * nu + (i + 1) % nu
            F.append((a, b, b + nu, a + nu))
    if cap_last:                                        # chiude l'ultimo anello con un ventaglio
        c = len(V); last = nv * nu
        V.append(tuple(float(a) for a in np.mean([V[last + i] for i in range(nu)], axis=0)))
        F += [(last + i, last + (i + 1) % nu, c) for i in range(nu)]
    return V, F


def mods(o, thick=0.0, sub=2, bevel=0.0):
    if thick:
        s = o.modifiers.new("sol", "SOLIDIFY"); s.thickness = thick; s.offset = -1.0
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
    if sub:
        m = o.modifiers.new("sub", "SUBSURF"); m.levels = 1; m.render_levels = sub
    return o


def fabric(name, c1, c2, scale=900.0, weave="noise", rough=0.92, bump=0.35):
    """tessuto: colore che varia tra c1 e c2 (trama), rilievo fine, niente lucido"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Specular IOR Level"].default_value = 0.12
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    fac = nz.outputs["Fac"]
    if weave == "herringbone":                          # spina di pesce: onde a dente di sega alternate
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "DIAGONAL"
        wv.wave_profile = "TRI"; wv.inputs["Scale"].default_value = scale * 0.32; wv.inputs["Distortion"].default_value = 1.5
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        nt.links.new(wv.outputs["Fac"], mul.inputs[0]); nt.links.new(nz.outputs["Fac"], mul.inputs[1])
        fac = mul.outputs[0]
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.2; ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(fac, ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], bs.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0004
    nt.links.new(fac, bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    try:
        bs.inputs["Sheen Weight"].default_value = 0.15; bs.inputs["Sheen Tint"].default_value = (*c2, 1)
    except Exception:
        pass
    return m


def solid(name, col, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m


def tube(name, pts, r, par, loc, mat):
    """cucitura/filetto: curva con spessore"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (float(q[0]), float(q[1]), float(q[2]), 1.0)
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    o.parent = par; o.location = loc; o.data.materials.append(mat)
    return o


# ------------------------------------------------------------------ coppola
def coppola(par, c0):
    """coppola siciliana: pannello superiore morbido e piatto, piu' largo del giro testa, che scivola in avanti
    e copre l'attacco della visierina; fianchi bombati; bottone automatico davanti"""
    R, RY = 0.087, 0.097                                # giro testa
    z0 = 0.028
    def ztop(x, y):                                     # pannello: alto dietro, scende verso la visiera
        s = min(1.2, max(0.0, (x + 0.09) / 0.21))
        return 0.099 - 0.056 * s ** 1.6 - 0.012 * (abs(y) / 0.11) ** 3
    def crown(u, v):
        t = 2 * math.pi * u
        c, s_ = math.cos(t), math.sin(t)
        fr = max(0.0, c)
        bx, by = R * c, RY * s_
        rx = bx * 1.07 + 0.030 * fr ** 2.0              # il pannello e' piu' largo e sporge in avanti
        ry = by * 1.08
        if v <= 0.3:                                    # fianco bombato: dal giro testa al bordo (arrotondato) del pannello
            w = v / 0.3
            e = math.sin(w * math.pi / 2)
            x = bx + (rx - bx) * e
            y = by + (ry - by) * e
            z = z0 + (ztop(rx, ry) - 0.004 - z0) * (1 - math.cos(w * math.pi / 2)) ** 0.8
        else:                                           # pannello superiore, appena bombato
            w = (v - 0.3) / 0.7
            k = 1 - w
            x = 0.010 + (rx - 0.010) * k
            y = ry * k
            z = ztop(x, y) - 0.004 * k ** 6 + 0.005 * (1 - k * k)
        return (x, y, z)
    V, F = grid(crown, 128, 40, cap_last=True)
    o = mods(mesh_obj("hat_coppola", V, F, par, c0), thick=0.003, sub=2)
    # visierina corta e rigida, sotto il pannello
    vb = []
    nb = 48
    for k in range(nb + 1):
        t = -math.pi / 2 + math.pi * k / nb
        for r_ in (0.0, 1.0):
            ex = 0.052 * r_
            vb.append((R * math.cos(t) * 1.0 + ex * max(0.0, math.cos(t)) ** 0.6,
                       RY * math.sin(t) * (1 + 0.04 * r_), z0 + 0.004 - 0.008 * r_ * math.cos(t)))
    fb = [(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1) for k in range(nb)]
    brim = mods(mesh_obj("hat_coppola_brim", vb, fb, par, c0), thick=0.0045, sub=2, bevel=0.0012)
    # bottone che unisce pannello e visiera
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0055, depth=0.004, vertices=32)
    bt = bpy.context.object; bt.name = "hat_coppola_snap"; bt.parent = par
    bt.location = c0 + Vector((R * 1.07 + 0.024, 0, ztop(R * 1.07 + 0.024, 0) - 0.006))
    tw = fabric("tweed", (0.006, 0.0055, 0.005), (0.024, 0.020, 0.016), scale=700.0, weave="herringbone", bump=0.6)
    for ob in (o, brim, bt):
        ob.data.materials.append(tw)
    # cuciture: giro del pannello
    seam = solid("cucitura_tweed", (0.03, 0.026, 0.022), 0.9)
    pts = []
    for k in range(97):
        x, y, z = crown(k / 96, 0.31)
        pts.append((x, y, z + 0.0015))
    tube("hat_coppola_seam", pts, 0.0007, par, c0, seam)
    return [o, brim, bt]


# ------------------------------------------------------------------ bustina da barista
def bustina(par, c0):
    """bustina (berretto da barista piegato): due fianchi che si chiudono in una cresta, risvolto alto tutto intorno,
    filetto color caffe' sul bordo del risvolto e sulla cresta. Portata un po' di sbieco."""
    RX, RY = 0.100, 0.060                               # base (lunga davanti-dietro, stretta sui lati)
    def h(x):                                           # profilo della cresta: rialzata alle punte, piu' bassa al centro
        a = abs(x) / RX
        return 0.066 - 0.006 * a ** 2 - 0.260 * max(0.0, a - 0.88)
    def body(u, v):
        t = 2 * math.pi * u
        c, s_ = math.cos(t), math.sin(t)
        x = RX * c
        w = RY * s_
        hz = max(0.012, h(x))
        y = w * (1 - v ** 1.8) + math.copysign(0.0012, s_) * v   # fianchi quasi dritti, si chiudono in alto sulla piega
        z = hz * (v ** 0.85) + 0.004 * math.sin(v * math.pi) * abs(s_)
        return (x, y, z)
    base_z = head_z(0.0, RY) - 0.008                     # appoggia sulla calotta (il risvolto copre il contatto)
    loc = c0 + Vector((-0.004, 0, base_z))
    V, F = grid(body, 128, 24)
    o = mods(mesh_obj("hat_bustina", V, F, par, loc), thick=0.0022, sub=2)
    # risvolto: fascia alta 20 mm leggermente svasata, fuori dai fianchi
    def cuff(u, v):
        t = 2 * math.pi * u
        k = 1.014 - 0.006 * v
        return (RX * k * math.cos(t), RY * k * math.sin(t), -0.001 + 0.018 * v)
    V2, F2 = grid(cuff, 128, 4)
    cf = mods(mesh_obj("hat_bustina_cuff", V2, F2, par, loc), thick=0.0018, sub=2)
    cot = fabric("cotone_bianco", (0.36, 0.355, 0.345), (0.46, 0.455, 0.44), scale=1400.0, bump=0.25)
    for ob in (o, cf):
        ob.data.materials.append(cot)
    piping = solid("filetto_caffe", (0.13, 0.055, 0.025), 0.6)
    pts = [(RX * 1.012 * math.cos(2 * math.pi * k / 96), RY * 1.012 * math.sin(2 * math.pi * k / 96), 0.0172) for k in range(97)]
    tube("hat_bustina_piping", pts, 0.0011, par, loc, piping)
    pts2 = [(x, 0.0, max(0.012, h(x)) + 0.0008) for x in np.linspace(-RX * 0.96, RX * 0.96, 60)]
    tube("hat_bustina_ridge", pts2, 0.0009, par, loc, piping)
    em = []
    for ob in [o, cf] + em + [bpy.data.objects["hat_bustina_piping"], bpy.data.objects["hat_bustina_ridge"]]:
        ob.rotation_euler = Euler((math.radians(10), math.radians(-2), 0))
    return [o, cf]


# ------------------------------------------------------------------ cappellino a visiera piatta, girato all'indietro
def snapback(par, c0):
    """6 spicchi con cuciture, bottone in cima, visiera piatta dietro; davanti (sulla fronte) l'apertura con la chiusura a bottoni"""
    R, RY, H = 0.100, 0.108, 0.080
    z0 = 0.036
    def crown(u, v):
        t = 2 * math.pi * u
        c, s_ = math.cos(t), math.sin(t)
        r = math.cos(v * math.pi / 2) ** 0.85
        back = max(0.0, -c)                              # la parte alta e strutturata del cappellino e' dietro (girato)
        z = z0 + (H + 0.006 * back) * math.sin(v * math.pi / 2) ** 0.9
        return (R * c * r, RY * s_ * r, z)
    nu, nv = 120, 30
    V, F = grid(crown, nu, nv, cap_last=True)
    # apertura della chiusura sulla fronte: tolgo le facce davanti in basso (arco)
    keep = []
    for f in F:
        cx = np.mean([V[i][0] for i in f]); cy = np.mean([V[i][1] for i in f]); cz = np.mean([V[i][2] for i in f])
        arch = cx > 0.05 and ((cy / 0.040) ** 2 + ((cz - z0) / 0.032) ** 2) < 1.0
        if not arch:
            keep.append(f)
    o = mods(mesh_obj("hat_snap", V, keep, par, c0), thick=0.003, sub=2)
    # cinghietta con i bottoni sotto l'arco
    pts = [(R * 0.995 * math.cos(a), RY * 0.995 * math.sin(a), z0 + 0.005) for a in np.linspace(-0.42, 0.42, 30)]
    strap_m = solid("snap_strap", (0.01, 0.01, 0.011), 0.6)
    tube("hat_snap_strap", pts, 0.0035, par, c0, strap_m)
    stud = solid("snap_stud", (0.02, 0.02, 0.022), 0.35, metal=0.0)
    for a in np.linspace(-0.30, 0.30, 6):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0028, depth=0.003, vertices=20)
        sd = bpy.context.object; sd.name = "hat_snap_stud"; sd.parent = par
        sd.location = c0 + Vector((R * 1.02 * math.cos(a), RY * 1.02 * math.sin(a), z0 + 0.005))
        sd.rotation_euler = Euler((0, math.pi / 2, a)); sd.data.materials.append(stud)
    # visiera piatta (dietro), leggermente curva sui lati
    vb = []; nb = 48
    for k in range(nb + 1):
        t = math.pi / 2 + math.pi * k / nb             # meta' posteriore
        c, s_ = math.cos(t), math.sin(t)
        for r_ in (0.0, 1.0):
            vb.append((R * c - 0.078 * r_ * max(0.0, -c) ** 0.7, RY * s_ * (1 + 0.02 * r_), z0 + 0.003 - 0.004 * r_ * abs(s_)))
    fb = [(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1) for k in range(nb)]
    brim = mods(mesh_obj("hat_snap_brim", vb, fb, par, c0), thick=0.005, sub=2, bevel=0.0015)
    # cuciture dei 6 spicchi e bottone in cima
    seam = solid("snap_seam", (0.0, 0.0, 0.0), 0.95)
    for k in range(6):
        u = (k + 0.5) / 6
        tube(f"hat_snap_seam{k}", [tuple(np.array(crown(u, v)) * 1.006 + np.array([0, 0, 0.0005])) for v in np.linspace(0.02, 0.97, 30)],
             0.0008, par, c0, seam)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0075, segments=24, ring_count=12)
    bt = bpy.context.object; bt.name = "hat_snap_btn"; bt.parent = par; bt.location = c0 + Vector((0, 0, z0 + H + 0.004))
    bt.scale = (1, 1, 0.55)
    blk = fabric("twill_nero", (0.0012, 0.0012, 0.0014), (0.004, 0.004, 0.0045), scale=1600.0, bump=0.3)
    try:
        blk.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.0
    except Exception:
        pass
    for ob in (o, brim, bt):
        ob.data.materials.append(blk)
    return [o, brim, bt]


HATS = {"coppola": coppola, "bustina": bustina, "snapback": snapback}


def add_hat(kind):
    hs = bpy.data.objects.get("head_shell")
    if hs is None or hs.parent is None or kind not in HATS:
        return []
    return HATS[kind](hs.parent, Vector(hs.location))
