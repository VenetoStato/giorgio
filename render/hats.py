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
    """cappellino a visiera piatta portato al contrario: 6 spicchi con cuciture e occhielli, bottone in cima, pannello
    strutturato (ora dietro) piu' alto, visiera piatta larga con l'adesivo dorato rotondo ancora attaccato e il sotto verde;
    sulla fronte l'apertura bordata con la cinghietta a bottoni."""
    R, RY, H = 0.098, 0.106, 0.070
    z0 = 0.030
    def crown(u, v):
        t = 2 * math.pi * u
        c, s_ = math.cos(t), math.sin(t)
        back = max(0.0, -c) ** 1.5                       # pannello strutturato: piu' alto e dritto (e' dietro, cappello girato)
        r = math.cos(v * math.pi / 2) ** (0.85 - 0.35 * back)
        z = z0 + (H + 0.010 * back) * math.sin(v * math.pi / 2) ** (0.9 - 0.3 * back)
        return (R * c * r, RY * s_ * r, z)
    nu, nv = 144, 36
    V, F = grid(crown, nu, nv, cap_last=True)
    AW, AH = 0.036, 0.030                                # apertura (semiassi) sulla fronte
    def in_arch(x, y, z):
        return x > 0.04 and (y / AW) ** 2 + ((z - z0) / AH) ** 2 < 1.0
    keep = [f for f in F if not in_arch(*np.mean([V[i] for i in f], axis=0))]
    o = mods(mesh_obj("hat_snap", V, keep, par, c0), thick=0.003, sub=2)
    blk = fabric("twill_nero", (0.0012, 0.0012, 0.0014), (0.0045, 0.0045, 0.005), scale=1600.0, bump=0.35)
    try:
        blk.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.0
    except Exception:
        pass
    def on_crown(y, z):                                  # punto della calotta (lato fronte) a quota z e ascissa y
        best = None
        for v in np.linspace(0, 0.6, 121):
            x0, _, zc = crown(0.0, v)
            if zc >= z:
                rr = x0 / R
                return (R * rr * math.sqrt(max(0.0, 1 - (y / (RY * rr)) ** 2)), y, z)
        return (0.0, y, z)
    # bordino dell'apertura (nastro)
    bind = [on_crown(AW * math.cos(a) * 1.04, z0 + AH * math.sin(a) * 1.04) for a in np.linspace(0, math.pi, 40)]
    bind = [(x + 0.0015, y, z) for x, y, z in bind]
    tube("hat_snap_binding", bind, 0.0022, par, c0, solid("snap_binding", (0.003, 0.003, 0.0035), 0.6))
    # cinghietta di plastica con i bottoni
    strap_m = solid("snap_strap", (0.008, 0.008, 0.009), 0.35)
    pts = [on_crown(y, z0 + 0.006) for y in np.linspace(-AW * 1.15, AW * 1.15, 30)]
    pts = [(x + 0.002, y, z) for x, y, z in pts]
    tube("hat_snap_strap", pts, 0.0032, par, c0, strap_m)
    for y in np.linspace(-0.022, 0.022, 5):
        x, y_, z = on_crown(y, z0 + 0.006)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0026, depth=0.003, vertices=20)
        sd = bpy.context.object; sd.name = "hat_snap_stud"; sd.parent = par
        sd.location = c0 + Vector((x + 0.0045, y_, z)); sd.rotation_euler = Euler((0, math.pi / 2, math.atan2(y_, x)))
        sd.data.materials.append(strap_m)
    # visiera piatta, larga, dietro
    vb = []; nb = 64
    for k in range(nb + 1):
        t = math.pi / 2 + math.pi * k / nb
        c, s_ = math.cos(t), math.sin(t)
        for r_ in (0.0, 1.0):
            d = 0.092 * r_ * max(0.0, -c) ** 0.55
            vb.append((R * c * 0.99 - d, RY * s_ * (1 + 0.03 * r_), z0 + 0.002))
    fb = [(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1) for k in range(nb)]
    brim = mods(mesh_obj("hat_snap_brim", vb, fb, par, c0), thick=0.005, sub=2, bevel=0.0018)
    under = mesh_obj("hat_snap_under", [(x, y, z - 0.0058) for x, y, z in vb], fb, par, c0)
    under.data.materials.append(solid("snap_sottovisiera", (0.010, 0.060, 0.025), 0.8))
    # cuciture concentriche sulla visiera
    stitch = solid("snap_stitch", (0.02, 0.02, 0.022), 0.9)
    for kk, f_ in enumerate((0.35, 0.55, 0.75)):
        pts = []
        for t in np.linspace(math.pi / 2 + 0.25, 3 * math.pi / 2 - 0.25, 50):
            c, s_ = math.cos(t), math.sin(t)
            d = 0.092 * f_ * max(0.0, -c) ** 0.55
            pts.append((R * c * 0.99 - d, RY * s_ * (1 + 0.03 * f_), z0 + 0.0022))
        tube(f"hat_snap_stitch{kk}", pts, 0.0005, par, c0, stitch)
    # adesivo dorato rotondo sulla visiera (lasciato attaccato, come si usa)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.0008, vertices=48)
    st = bpy.context.object; st.name = "hat_snap_sticker"; st.parent = par
    st.location = c0 + Vector((-R - 0.045, 0.034, z0 + 0.0032))
    st.data.materials.append(solid("snap_oro", (0.85, 0.62, 0.20), 0.25, metal=1.0))
    # cuciture dei 6 spicchi, occhielli e bottone
    seam = solid("snap_seam", (0.0, 0.0, 0.0), 0.95)
    for k in range(6):
        u = k / 6
        tube(f"hat_snap_seam{k}", [tuple(np.array(crown(u, v)) * 1.006 + np.array([0, 0, 0.0005])) for v in np.linspace(0.04, 0.97, 30)
                                   if not in_arch(*crown(u, v))], 0.0008, par, c0, seam)
        ex, ey, ez = crown(u + 1 / 12, 0.62)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0028, minor_radius=0.0008, major_segments=20, minor_segments=8)
        ey_ = bpy.context.object; ey_.name = f"hat_snap_eyelet{k}"; ey_.parent = par
        ey_.location = c0 + Vector((ex * 1.01, ey * 1.01, ez + 0.0005))
        ey_.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((ex / R, ey / RY, (ez - z0) / H)).normalized()).to_euler()
        ey_.data.materials.append(seam)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0075, segments=24, ring_count=12)
    bt = bpy.context.object; bt.name = "hat_snap_btn"; bt.parent = par; bt.location = c0 + Vector((0, 0, z0 + H + 0.004))
    bt.scale = (1, 1, 0.55)
    for ob in (o, brim, bt):
        ob.data.materials.append(blk)
    return [o, brim, bt]


HATS = {"coppola": coppola, "bustina": bustina, "snapback": snapback}


def add_hat(kind):
    hs = bpy.data.objects.get("head_shell")
    if hs is None or hs.parent is None or kind not in HATS:
        return []
    return HATS[kind](hs.parent, Vector(hs.location))
