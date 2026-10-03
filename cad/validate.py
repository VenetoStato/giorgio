"""Giorgio CAD: assembly build + validation + exports (headless).

    cd ~/giorgio_sim/cad && .env/bin/python validate.py [--no-export] [--poses N]

Outputs: VALIDATION.md, out/bom_parts.csv, out/bom_fasteners.csv, out/mass_properties.json,
         out/step/*.step, out/stl/*.stl, out/giorgio_assembly.step/.stl, out/exploded/*.stl + out/exploded/exploded.json
Requires data/arm_traj.npz + data/arm_meshes (run sim_export.py once; it reads the MuJoCo model read-only).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

import fasteners as F
import geom as G
import model as M
from params import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DATA = HERE / "data"
REPORT = []
REPORT_ROWS = []
BUTTON_PRESS = set()
CHECKS = []          # (section, name, status, detail)


def check(section, name, ok, detail, warn=False, assumed=False):
    st = ("WARN" if assumed else "PASS") if ok else ("WARN" if warn else "FAIL")
    CHECKS.append((section, name, st, detail))
    return ok


def log(*a):
    print(*a, flush=True)


# ====================================================================== assembly helpers
def bolt_motion(b, parts):
    mo = {parts[pn].motion for pn, _ in b.stack if pn in parts}
    mo.discard("")
    return mo.pop() if mo else ""


def add_bolt_parts(parts, bolts):
    """fastener solids become parts (category fastener) so they are interference-checked and exported"""
    for b in bolts:
        mo = bolt_motion(b, parts)
        for kind, shp in F.bolt_solids(b, parts):
            nm = f"{b.name}__{kind}"
            p = G.Part(nm, shp, "S235 / 1.4301", f"{b.std} {b.thread}x{b.L:g} {b.grade}" if kind == "bolt" else kind,
                       category="fastener", color=(0.15, 0.15, 0.16) if kind == "bolt" else (0.7, 0.7, 0.72),
                       explode=parts[b.stack[0][0]].explode, motion=mo)
            p.bolt = b.name
            parts[nm] = p


def moved(p, lift=0.0, shuttle=0.0):
    if p.motion == "lift" and lift:
        return p.shape.translate(G.V(0, 0, lift))
    if p.motion == "shuttle" and shuttle:
        return p.shape.translate(G.V(0, shuttle, 0))
    return p.shape


# ====================================================================== 1. interference
def same_joint(a, b, parts, bolts_by_name):
    """pairs that touch by design: a fastener and the parts of its own stack"""
    for x, y in ((a, b), (b, a)):
        px = parts[x]
        if getattr(px, "bolt", None):
            bb = bolts_by_name[px.bolt]
            if y in [pn for pn, _ in bb.stack]:
                return True
            if getattr(parts[y], "bolt", None) == px.bolt:
                return True
    return False


def interference(parts, bolts_by_name, lift=0.0, shuttle=0.0, only_moving=False, label=""):
    names = [n for n, p in parts.items() if p.check_interference]
    shapes = {n: moved(parts[n], lift, shuttle) for n in names}
    bbs = {n: G.bbox_of(s) for n, s in shapes.items()}
    res = []
    npairs = 0
    t0 = time.time()
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if only_moving and not (parts[a].motion or parts[b].motion):
                continue
            A, B = bbs[a], bbs[b]
            if np.any(A[1] < B[0] - 0.01) or np.any(B[1] < A[0] - 0.01):
                continue
            npairs += 1
            try:
                v = shapes[a].intersect(shapes[b]).Volume()
            except Exception as e:  # noqa: BLE001
                v = float("nan")
            if not (v <= 1.0):       # > 1 mm3 or nan
                res.append((a, b, v / 1000.0, same_joint(a, b, parts, bolts_by_name)))
    log(f"  interference {label}: {npairs} candidate pairs, {len(res)} with overlap > 0.001 cm3, {time.time() - t0:.0f}s")
    return res, npairs


# ====================================================================== 2. arm sweep (FCL on meshes)
STATIC_FOR_ARMS = ["SH04a_torso_shell_front", "SH04b_torso_shell_rear", "P27_torso_shell_bracket_front", "P28_torso_shell_bracket_rear", "SH05_head_shell", "SH03_waist_cover", "SH06_coffee_housing", "S07_coffee_machine_inissia_EN80",
                   "P26_cup_stack_holder", "P20_tray_half_L", "P20_tray_half_R", "P19_tray_carrier", "S05_orbbec_gemini_336L",
                   "P18_gemini_bracket", "SH01_base_skirt", "S04_insta360_X4", "P17_insta360_mast", "P21_coffee_shelf",
                   "P24_shuttle_cup_carrier", "SH02_column_cover_fixed", "S02_nanoScan3_0", "S02_nanoScan3_1"]


def body_link0_mesh():
    m = trimesh.load(M.OA_STL)
    m.apply_translation([0, 0, TORSO_Z])
    return m


def arm_sweep(parts, nposes=200):
    from trimesh.collision import CollisionManager
    z = np.load(DATA / "arm_traj.npz", allow_pickle=True)
    bodies = [str(b) for b in z["bodies"]]
    src = [str(s) for s in z["src"]]
    N = len(src)
    idx = sorted(set(np.linspace(0, N - 1, min(nposes, N)).astype(int).tolist()) | {N - 1})
    meshes = {b: trimesh.load(DATA / "arm_meshes" / f"{b}.stl") for b in bodies if (DATA / "arm_meshes" / f"{b}.stl").exists()}
    arm, arm_nb = CollisionManager(), CollisionManager()
    for b, m in meshes.items():
        arm.add_object(b, m)
        if "base_link" not in b:
            arm_nb.add_object(b, m)
    statics = {}
    for n in STATIC_FOR_ARMS:
        if n in parts:
            cm = CollisionManager()
            cm.add_object(n, G.shape_to_trimesh(parts[n].shape, tol=0.5))
            statics[n] = cm
    cm = CollisionManager()
    cm.add_object("OA_body_link0(STL)", body_link0_mesh())
    statics["OA_body_link0(STL)"] = cm
    per_obj = {n: (1e9, ("-", "-")) for n in statics}
    hits = defaultdict(set)
    t0 = time.time()
    for k in idx:
        for b in meshes:
            arm.set_transform(b, z[b][k])
            if "base_link" not in b:
                arm_nb.set_transform(b, z[b][k])
        for n, cmn in statics.items():
            mgr = arm_nb if n.startswith("OA_body") else arm
            if n == "S07_coffee_machine_inissia_EN80":
                # pressione del pulsante: contatto voluto delle dita con la testa della macchina (ultimi 25 mm in alto, lato erogatore)
                c_, nms_, data_ = mgr.in_collision_other(cmn, return_names=True, return_data=True)
                ztop = COF_SH + INISSIA["H"]
                if c_ and all(dd.point[2] >= ztop - 25 and dd.point[1] <= -45 and any("finger" in x for x in dd.names) for dd in data_):
                    BUTTON_PRESS.add(f"{src[k]}#{k}")
                    continue
            d, nm = mgr.min_distance_other(cmn, return_names=True)
            if d < per_obj[n][0]:
                per_obj[n] = (d, (nm[0], f"{src[k]}#{k}"))
            if d <= 1e-6:
                hits[n].add(k)
    log(f"  arm sweep: {len(idx)} poses x {len(statics)} parts in {time.time() - t0:.0f}s")
    return per_obj, hits, len(idx), Counter(src[k] for k in idx)


# ====================================================================== 3. footprint
def footprint(parts):
    from shapely.geometry import MultiPoint, Point, Polygon
    from shapely.ops import unary_union
    a, b, e2 = M.SK["a"] + 6, M.SK["b"] + 6, M.SK["e2"]
    skirt = Polygon(G.superellipse_pts(a, b, e2, 256))
    base_names = {"tracer2_base", "SH01_base_skirt", "P12_bumper_EPDM", "S02_nanoScan3_0", "S02_nanoScan3_1", "P09_scanner_pod_bracket_0",
                  "P09_scanner_pod_bracket_1", "S03_roboteq_RPCOL90_100", "P10_charge_collector_bracket"}
    hulls = {}
    for n, p in parts.items():
        if p.category == "fastener":
            continue
        tm = G.shape_to_trimesh(p.shape, tol=1.0)
        hulls[n] = MultiPoint(tm.vertices[:, :2]).convex_hull
    base_fp = unary_union([skirt] + [hulls[n] for n in base_names if n in hulls])
    # bracci in posa di riposo (home) dalle mesh
    z = np.load(DATA / "arm_traj.npz", allow_pickle=True)
    arm_pts = []
    for b in [str(x) for x in z["bodies"]]:
        f = DATA / "arm_meshes" / f"{b}.stl"
        if f.exists():
            m = trimesh.load(f)
            m.apply_transform(z[b][-1])
            arm_pts.append(m.vertices[:, :2])
    hulls["OpenArm arms (home pose)"] = MultiPoint(np.vstack(arm_pts)).convex_hull
    hulls["OA_body_link0"] = MultiPoint(body_link0_mesh().vertices[:, :2]).convex_hull
    outside = {}
    for n, h in hulls.items():
        if n in base_names:
            continue
        d = h.difference(skirt.buffer(0.5)).area
        if d > 1.0:
            outside[n] = d
    allfp = unary_union(list(hulls.values()))
    bx = allfp.bounds
    return skirt, base_fp, outside, bx


# ====================================================================== 4. mass properties + tipping
def mass_props(parts, extra=()):
    rows = []
    for n, p in parts.items():
        m = p.mass()
        if m <= 0:
            continue
        c = getattr(p, "com_override", None)
        c = p.com() if c is None else c
        rows.append((n, m, c, p.motion))
    for e in extra:
        rows.append(e)
    return rows


def total(rows, lift=0.0, exclude=()):
    m = sum(r[1] for r in rows if r[0] not in exclude)
    c = sum(r[1] * (np.asarray(r[2]) + (np.array([0, 0, lift]) if r[3] == "lift" else 0)) for r in rows if r[0] not in exclude) / m
    return m, c


def tipping(m, c, poly=(281.0, 255.0)):
    sx, sy = poly
    g = GRAV
    z = c[2] / 1000
    return dict(fwd=g * (sx - c[0]) / 1000 / z, back=g * (sx + c[0]) / 1000 / z, left=g * (sy - c[1]) / 1000 / z, right=g * (sy + c[1]) / 1000 / z,
                slope_lat_deg=math.degrees(math.atan((sy - abs(c[1])) / c[2])), slope_long_deg=math.degrees(math.atan((sx - abs(c[0])) / c[2])))


# ====================================================================== 5. fasteners
SUPPORT = {   # group -> (support part, predicate on supported part names, extra point loads [(F_vec N, point mm)], single-bolt contact half-width)
}


def group_defs(parts):
    lift = {n for n, p in parts.items() if p.motion == "lift" and not getattr(p, "bolt", None)}
    def by(prefixes):
        return {n for n in parts if any(n.startswith(x) for x in prefixes) and not getattr(parts[n], "bolt", None)}
    coffee = by(["P21", "P22", "S07", "P23", "S08", "S09", "P24", "S10", "P25", "P26", "SH06"])
    base_all = {n for n in parts if not getattr(parts[n], "bolt", None) and n != "tracer2_base" and not n.startswith("tnut_rail")}
    above_bracket = lift - by(["S01", "P15", "P02", "SH03"])
    D = {
        "G1 adapter->Tracer rails": ("tracer2_base", base_all, "payload", 0),
        "G2 column foot->adapter": ("P01_base_adapter_plate", lift | by(["W01", "P13", "P14"]), "payload", 0),
        "G3 profile->torso bracket": ("S01_column_profile_item8_80x80L", lift - by(["S01", "P15"]), "payload", 40.0),
        "G4 torso bracket->body_link0": ("P02_column_to_torso_bracket", above_bracket, "payload", 0),
        "G8 battery tray->adapter": ("P01_base_adapter_plate", by(["P03", "E01", "P04", "P05"]), None, 0),
        "G8b battery hold-down": ("P03_battery_tray", by(["E01"]), "uplift", 0),
        "G9 e-plates->adapter": ("P01_base_adapter_plate", by(["P06", "E02", "E05", "E04"]), None, 0),
        "G10 scanner 0->pod": ("P09_scanner_pod_bracket_0", by(["S02_nanoScan3_0"]), None, 0),
        "G10 scanner 1->pod": ("P09_scanner_pod_bracket_1", by(["S02_nanoScan3_1"]), None, 0),
        "G11 pod 0->adapter": ("P01_base_adapter_plate", by(["S02_nanoScan3_0", "P09_scanner_pod_bracket_0"]), None, 0),
        "G11 pod 1->adapter": ("P01_base_adapter_plate", by(["S02_nanoScan3_1", "P09_scanner_pod_bracket_1"]), None, 0),
        "G12 collector->bracket": ("P10_charge_collector_bracket", by(["S03"]), "dock", 0),
        "G12b collector bracket->adapter": ("P01_base_adapter_plate", by(["S03", "P10"]), "dock", 0),
        "G13 skirt->standoffs": ("P11", by(["SH01", "P12"]), "lean", 0),
        "G14 waist cover->bracket": ("P02_column_to_torso_bracket", by(["SH03"]), None, 0),
        "G15 neck plate->body_link0": ("OA_body_link0", by(["SH05", "P16", "P17", "S04"]), None, 0),
        "G16 head shell->neck plate": ("P16_head_neck_plate", by(["SH05"]), None, 0),
        "G17 mast->neck plate": ("P16_head_neck_plate", by(["P17", "S04"]), None, 0),
        "G18 Gemini->bracket": ("P18_gemini_bracket", by(["S05"]), None, 0),
        "G19 Gemini bracket->post": ("OA_body_link0", by(["S05", "P18"]), None, 0),
        "G20 tray carrier->post": ("OA_body_link0", by(["P19", "P20", "S06"]), "flasks", 0),
        "G21 coffee uprights->adapter": ("P01_base_adapter_plate", coffee, None, 0),
        "G22 shelf->uprights": ("P22", coffee - by(["P22"]), None, 0),
        "G23 MGN12 rail->shelf": ("P21_coffee_shelf", by(["P23", "S08", "S09", "P24"]), "cup", 0),
        "G24 cup carrier->carriage": ("S09_MGN12H_carriage", by(["P24"]), "cup", 0),
        "G25 actuator bracket->shelf": ("P21_coffee_shelf", by(["P25", "S10_"]), "actuator", 0),
        "G26 cup holder->shelf": ("P21_coffee_shelf", by(["P26"]), "cups", 0),
        "G27 housing->shelf": ("P21_coffee_shelf", by(["SH06"]), None, 0),
        "G28 torso shell bracket front->post": ("OA_body_link0", by(["P27", "SH04a"]), None, 0),
        "G28 torso shell bracket rear->post": ("OA_body_link0", by(["P28", "SH04b"]), None, 0),
        "G29 torso shell front half->bracket": ("P27_torso_shell_bracket_front", by(["SH04a"]), None, 0),
        "G29 torso shell rear half->bracket": ("P28_torso_shell_bracket_rear", by(["SH04b"]), None, 0),
    }
    return D


def extra_loads(kind):
    """returns list of (mass kg, point mm) point masses and list of (force N vec, point) external forces"""
    if kind == "payload":
        return [(ARM_PAYLOAD_PEAK, (550.0, 250.0, 1100.0)), (ARM_PAYLOAD_PEAK, (550.0, -250.0, 1100.0))], []
    if kind == "flasks":
        return [(6 * 0.35, (BUF_X, 0.0, BUF_Z + 60))], []
    if kind == "cup":
        return [(0.15, (COF_X, COF_Y_OUT, SHUTTLE_PLATE_Z + 40))], []
    if kind == "cups":
        return [(0.10, (COF_STACK[0], COF_STACK[1], COF_SH + COF_STACK_Z + 40))], []
    if kind == "dock":
        return [], [(np.array([-200.0, 0, 0]), np.array([400.0, 0, 140.0]))]          # docking push 200 N (ASSUMED)
    if kind == "lean":
        return [], [(np.array([0, 0, -300.0]), np.array([0.0, 0, 300.0]))]            # person leaning 300 N (ASSUMED)
    if kind == "actuator":
        return [], [(np.array([0, -90.0, 0]), np.array([-302.0, -150.0, 626.0]))]     # P16 64:1 max 90 N (SOURCED)
    return [], []


LOAD_CASES = [   # name, base acceleration a (in g); loads on body = m (a - g)
    ("LC1 static 1g", (0, 0, 0)),
    ("LC2 braking 0.5g fwd", (-0.5, 0, 0)), ("LC2 braking 0.5g rev", (0.5, 0, 0)),
    ("LC2 lateral 0.5g L", (0, 0.5, 0)), ("LC2 lateral 0.5g R", (0, -0.5, 0)),
    ("LC3 bump +2g", (0, 0, 2.0)),
    ("LC4 bump+braking", (-0.5, 0, 2.0)), ("LC4 bump+lateral", (0, 0.5, 2.0)),
    ("LC5 rebound (net -1g)", (0, 0, -2.0)),
    ("LC6 Tracer e-stop 2.2 m/s2 (2 m/s in 0.9 m)", (-2.2 / 9.81, 0, 0)),
]


def fastener_analysis(parts, bolts, rows):
    D = group_defs(parts)
    mass_of = {r[0]: (r[1], np.asarray(r[2])) for r in rows}
    groups = defaultdict(list)
    for b in bolts:
        groups[b.group].append(b)
    out = []
    for gname, bl in groups.items():
        if gname not in D:
            out.append(dict(group=gname, ok=False, note="no load definition"))
            continue
        sup_name, sset, kind, single_w = D[gname]
        pm, ext = extra_loads(kind)
        ms = [(mass_of[n][0], mass_of[n][1]) for n in sset if n in mass_of] + [(m_, np.array(p_)) for m_, p_ in pm]
        mtot = sum(m_ for m_, _ in ms)
        cog = sum(m_ * c_ for m_, c_ in ms) / mtot if mtot > 0 else np.zeros(3)
        # geometria del gruppo
        pts, s_dirs = [], []
        for b in bl:
            pn, hn = b.stack[-1]
            h = parts[pn].holes[hn]
            a, _ = F.bolt_frame(b, parts)
            pts.append(np.array(h.p, float))
            sup_is_tip = sup_name.startswith(tuple([b.stack[-1][0][:3]])) or b.stack[-1][0].startswith(sup_name) or sup_name.startswith(b.stack[-1][0])
            if any(pn_.startswith(sup_name) for pn_, _ in b.stack[-1:]):
                s_dirs.append(-a)            # sostegno dal lato della filettatura: il pezzo sostenuto e' dal lato della testa
            else:
                s_dirs.append(a)
        pts = np.array(pts)
        O = pts.mean(0)
        r = pts - O
        J = sum(np.dot(ri, ri) * np.eye(3) - np.outer(ri, ri) for ri in r)
        Jp = np.linalg.pinv(J, rcond=1e-6)
        n = len(bl)
        worst = None
        for lcn, acc in LOAD_CASES:
            if kind == "uplift" and lcn != "LC5 rebound (net -1g)":
                continue
            a_ = np.array(acc) * GRAV
            Fv = mtot * (a_ - np.array([0, 0, -GRAV]))
            Mv = np.cross((cog - O) / 1000.0, Fv) * 1000.0          # N.mm
            for Fe, Pe in ext:
                Fv = Fv - Fe
                Mv = Mv - np.cross((Pe - O), Fe)
            if gname.startswith(("G1 ", "G2 ", "G3 ", "G4 ")):
                Mv = Mv + np.array([80e3, 80e3, 0.0])               # coppie di picco J1/J2 dei due bracci (reazione)
            theta = Jp @ Mv
            Mres = Mv - J @ theta
            T_list, V_list = [], []
            for i, b in enumerate(bl):
                f = Fv / n + np.cross(theta, r[i])
                s = s_dirs[i]
                fn = float(f @ s)
                T = max(0.0, -fn)
                V = float(np.linalg.norm(f - fn * s))
                T_list.append(T)
                V_list.append(V)
            # momento non sostenibile dallo schema (bulloni allineati / bullone unico): leva di contatto
            if np.linalg.norm(Mres) > 1.0:
                lever = single_w if single_w > 0 else 15.0
                for i in range(n):
                    T_list[i] += np.linalg.norm(Mres) / lever / n
            cand = (max(T_list), sum(V_list), max(V_list), lcn, T_list, V_list)
            if worst is None or cand[0] + cand[1] / 3 > worst[0] + worst[1] / 3:
                worst = cand
        Tmax, Vsum, Vmax, lcn, T_list, V_list = worst
        b0 = bl[0]
        Fp = F.proof_load(b0.thread, b0.grade)
        FV = b0.preload_frac * Fp
        d = float(b0.thread[1:])
        torque = F.K_TORQUE * FV * d / 1000.0
        Fb = FV + F.PHI * Tmax
        ok_bolt = Fb <= 0.9 * Fp
        slip_cap = sum(F.MU * max(0.0, FV - (1 - F.PHI) * t) for t in T_list)
        ok_slip = slip_cap >= 1.25 * Vsum
        shear_cap = 0.6 * F.GRADES[b0.grade]["Rm"] * F.ISO[b0.thread]["As"] / 1.25
        ok_shear = Vmax <= shear_cap
        # filettatura femmina
        last_part = parts[b0.stack[-1][0]]
        fem_note, fem_ok = "", True
        if b0.female == "tap":
            mat = getattr(last_part, "tap_material", None) or last_part.material
            Rm_int = F.TAPPED_MATS.get(mat, dict(Rm=200))["Rm"]
            Le = min(r_["engagement_mm"] for r_ in [F.check_bolt(bb, parts) for bb in bl])
            Fstrip = 0.6 * Rm_int * 0.75 * math.pi * d * Le
            fem_ok = Fstrip >= 1.25 * (FV + F.PHI * Tmax)
            fem_note = f"strip {Fstrip / 1000:.1f} kN ({mat}, Le {Le:.1f}) vs {1.25 * (FV + F.PHI * Tmax) / 1000:.2f} kN req; = {Fstrip / Fp:.2f} x proof"
        elif b0.female == "insert":
            po = F.INSERTS[b0.thread]["pullout"]
            fem_ok = po >= 1.5 * (FV + Tmax)
            fem_note = f"insert pull-out {po:.0f} N (ESTIMATE) vs 1.5 x {FV + Tmax:.0f} N"
        elif b0.female == "tnut":
            fa = F.TNUTS[b0.nut_spec]["F_allow"]
            fem_ok = fa >= FV + Tmax
            fem_note = f"T-nut allow {fa:.0f} N ({F.TNUTS[b0.nut_spec]['src']}) vs F_V+T {FV + Tmax:.0f} N"
        elif b0.female == "nut":
            fem_note = "ISO 4032 nut 8 >= bolt 8.8"
        ok = ok_bolt and (ok_slip or ok_shear) and fem_ok
        out.append(dict(group=gname, n=n, spec=f"{b0.std} {b0.thread}x{b0.L:g} {b0.grade}", mass=mtot, lc=lcn,
                        Tmax=Tmax, Vsum=Vsum, Vmax=Vmax, FV=FV, torque=torque, Fb=Fb, Fp=Fp, ok_bolt=ok_bolt, slip_cap=slip_cap,
                        ok_slip=ok_slip, shear_cap=shear_cap, ok_shear=ok_shear, fem_note=fem_note, fem_ok=fem_ok, ok=ok,
                        assumed=b0.assumed))
    return out


def edge_checks(parts, bolts):
    res = []
    seen = set()
    for b in bolts:
        for pn, hn in b.stack:
            if (pn, hn) in seen:
                continue
            seen.add((pn, hn))
            p = parts[pn]
            if p.category in ("purchased", "fastener"):
                continue
            h = p.holes[hn]
            e, d0 = F.edge_distance(p, h)
            kind = G.MATERIALS[p.material]["kind"]
            if kind == "plastic":
                need_wall = F.INSERTS[b.thread]["wall"] if h.kind == "insert" else max(1.5, 0.5 * d0)
                ok = e is None or (e - d0 / 2) >= need_wall - 1e-6
                crit = f"wall >= {need_wall:.1f} mm"
            else:
                ok = e is None or e >= 1.2 * d0 - 1e-6
                crit = f"e >= 1.2 d0 = {1.2 * d0:.1f} mm"
            res.append(dict(part=pn, hole=hn, d0=d0, e=e, ok=ok, crit=crit))
    return res


# ====================================================================== 6. exports
def export_all(parts, arm_home):
    from cadquery import exporters
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    (OUT / "exploded").mkdir(parents=True, exist_ok=True)
    meta = []
    comp = []
    allm = []
    for n, p in parts.items():
        if p.category == "fastener" and getattr(p, "bolt", None):
            tm = G.shape_to_trimesh(p.shape, tol=0.3)
        else:
            if p.category != "fastener":
                exporters.export(p.shape, str(OUT / "step" / f"{n}.step"))
            tm = G.shape_to_trimesh(p.shape, tol=0.3 if p.category != "shell" else 0.6)
        if p.mesh_file:
            tm = trimesh.load(p.mesh_file)
            tm.apply_translation(getattr(p, "mesh_offset", (0, 0, 0)))
        if p.category != "fastener" or not getattr(p, "bolt", None):
            tm.export(OUT / "stl" / f"{n}.stl")
        comp.append(p.shape)
        allm.append(tm)
        ex = tm.copy()
        ex.apply_translation(np.array(p.explode, float))
        ex.export(OUT / "exploded" / f"{n}.stl")
        meta.append(dict(name=n, file=f"{n}.stl", category=p.category, material=p.material, process=p.process,
                         color=list(p.color or G.MATERIALS[p.material]["color"]), explode=list(map(float, p.explode)), motion=p.motion,
                         finish=suggest_finish(p)))
    for b, tm in arm_home.items():
        tm.export(OUT / "stl" / f"{b}.stl")
        ex = tm.copy()
        ex.apply_translation([0, 0, 360])
        ex.export(OUT / "exploded" / f"{b}.stl")
        allm.append(tm)
        meta.append(dict(name=b, file=f"{b}.stl", category="purchased", material="OpenArm 2.0 (Enactic)", process="purchased",
                         color=[0.86, 0.86, 0.84], explode=[0, 0, 360.0], motion="arm", finish="as supplied / paint"))
    (OUT / "exploded" / "exploded.json").write_text(json.dumps(dict(units="mm", frame="robot base frame (x fwd, y left, z up)",
                                                                   note="explode vector = translation to apply for the exploded view",
                                                                   parts=meta), indent=1))
    asm = cq.Compound.makeCompound(comp)
    exporters.export(asm, str(OUT / "giorgio_assembly.step"))
    trimesh.util.concatenate(allm).export(OUT / "giorgio_assembly.stl")


def suggest_finish(p):
    if p.category == "shell":
        return "SLS PA12, vapour-smoothed + primer + soft-touch paint (warm white RAL 9010), accent bands per look"
    if p.material.startswith("EN AW"):
        return "black anodised (structure) / clear anodised (column)" if p.category == "custom" else "as supplied"
    if p.material.startswith("PA12"):
        return "MJF PA12 dyed black or painted"
    return "as supplied"


# ====================================================================== main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--poses", type=int, default=200)
    ap.add_argument("--skip-sweep", action="store_true")
    args = ap.parse_args()
    t00 = time.time()
    parts, bolts = M.build()
    log(f"model: {len(parts)} parts, {len(bolts)} bolts")
    bolts_by_name = {b.name: b for b in bolts}
    add_bolt_parts(parts, bolts)
    # shape validity
    bad = [n for n, p in parts.items() if not p.shape.isValid()]
    check("Model", "all B-rep solids valid", not bad, f"{len(parts)} solids, invalid: {bad[:5]}")

    # ---------------- fasteners geometry
    gres = [F.check_bolt(b, parts) for b in bolts]
    nbad = [g for g in gres if not g["ok_geom"]]
    check("Fasteners", "hole alignment (coaxial, parallel, contiguous stack)", not any("offset" in i or "parallel" in i or "contiguous" in i or "missing" in i
                                                                                      for g in gres for i in g["issues"]),
          f"{len(gres)} bolts; worst threaded-hole axis offset {max(g['coax_offset_mm'] for g in gres):.3f} mm, worst angle {max(g['angle_deg'] for g in gres):.2f} deg, worst stack gap {max(g['max_gap_mm'] for g in gres):.2f} mm")
    check("Fasteners", "hole sizes per ISO 273 / ISO 2306 tap drill / insert spec", not any("ISO" in i or "insert bore" in i for g in gres for i in g["issues"]),
          "clearance holes medium series unless noted; tapped = d - P; inserts Kerb Konus 860")
    eng_bad = [g for g in gres if any("engagement" in i or "bottom" in i or "protrusion" in i for i in g["issues"])]
    check("Fasteners", "thread engagement / no bottoming", not eng_bad,
          f"min Le/req ratio {min(g['engagement_mm'] / max(1e-9, g['engagement_req_mm']) for g in gres):.2f}; failing: {[g['name'] for g in eng_bad][:6]}")
    other = [(g["name"], i) for g in gres for i in g["issues"] if not any(k in i for k in ("offset", "parallel", "contiguous", "missing", "ISO", "insert bore", "engagement", "bottom", "protrusion"))]
    if other:
        check("Fasteners", "other bolt issues", False, str(other[:6]))
    log("  edge distances...")
    eres = edge_checks(parts, bolts)
    ebad = [e for e in eres if not e["ok"]]
    check("Fasteners", "edge distance / wall around holes", not ebad,
          f"{len(eres)} holes checked; e >= 1.2 d0 (EN 1999-1-1 min) in metal, insert wall per Kerb Konus in PA12; failing: {[(e['part'], e['hole'], round(e['e'] or 0, 1)) for e in ebad][:8]}")

    # ---------------- interference
    log("interference...")
    r0, n0 = interference(parts, bolts_by_name, 0.0, 0.0, label="lift 0, shuttle out")
    r1, n1 = interference(parts, bolts_by_name, STROKE, COF_Y_IN - COF_Y_OUT, only_moving=True, label=f"lift {STROKE:.0f}, shuttle in")
    rmid, _ = interference(parts, bolts_by_name, STROKE / 2, (COF_Y_IN - COF_Y_OUT) / 2, only_moving=True, label="mid stroke")

    def classify(res):
        fails, minor = [], []
        for a, b, v, joint in res:
            fast = parts[a].category == "fastener" or parts[b].category == "fastener"
            lim = 0.005 if fast else 0.1
            (fails if (v != v or v > lim) else minor).append((a, b, v, joint))
        return fails, minor
    f0, m0 = classify(r0)
    f1, m1 = classify(r1)
    fm, mm = classify(rmid)
    check("Interference", "static assembly (lift 0, shuttle out), all part pairs", not f0,
          f"{n0} bbox-overlapping pairs checked with exact OCC boolean; {len(f0)} overlaps > 0.1 cm3 (0.005 cm3 for fasteners); {len(m0)} minor/touching")
    check("Interference", f"moving parts at lift {STROKE:.0f} mm + shuttle under spout", not f1, f"{n1} pairs; {len(f1)} overlaps")
    check("Interference", "moving parts at mid stroke", not fm, f"{len(fm)} overlaps")

    # ---------------- shuttle clearance to machine along the stroke
    sh_parts = [n for n, p in parts.items() if p.motion == "shuttle" and not getattr(p, "bolt", None)]
    fixed_near = ["S07_coffee_machine_inissia_EN80", "SH06_coffee_housing", "P21_coffee_shelf", "S10_actuonix_P16_150"]
    dmin = 1e9
    from trimesh.collision import CollisionManager
    cmf = CollisionManager()
    for n in fixed_near:
        cmf.add_object(n, G.shape_to_trimesh(parts[n].shape, 0.3))
    for s in np.linspace(0, COF_Y_IN - COF_Y_OUT, 8):
        cms = CollisionManager()
        for n in sh_parts:
            if n in ("S10b_actuonix_rod",):
                continue
            cms.add_object(n, G.shape_to_trimesh(parts[n].shape.translate(G.V(0, s, 0)), 0.3))
        d, nm = cms.min_distance_other(cmf, return_names=True)
        if d < dmin:
            dmin, who = d, (nm, round(float(s)))
    check("Clearance", "shuttle stroke (140 mm) vs machine/housing/shelf/actuator", dmin >= 1.0,
          f"min clearance {dmin:.1f} mm ({who[0][0]} vs {who[0][1]} at +{who[1]} mm); guide rail contact excluded")

    # ---------------- arm sweep
    if not args.skip_sweep:
        log("arm sweep...")
        per_obj, hits, npose, srcs = arm_sweep(parts, args.poses)
        REPORT.append(("arm_sweep", per_obj, hits, npose, srcs))
        for sname, (d, who) in sorted(per_obj.items(), key=lambda x: x[1][0]):
            nh = len(hits.get(sname, ()))
            ok = d >= 5.0 and nh == 0
            warn = (not ok) and nh == 0 and d > 0
            check("Arm sweep", f"arms vs {sname}", ok, f"min clearance {d:.1f} mm ({who[0]} @ {who[1]}); poses in contact: {nh}/{npose}"
                  + (f"; {len(BUTTON_PRESS)} poses with the intended finger contact on the machine top (button press) excluded" if sname.startswith("S07") else ""), warn=warn)

    # ---------------- copertura di body_link0 (piastra di base e cima) da parte dei gusci
    log("body_link0 coverage...")
    blm = body_link0_mesh()
    S_ = M.TORSO_SH
    tor = G.superellipsoid_solid(S_["a"], S_["b"], S_["c"], S_["e1"], S_["e2"], center=(S_["cx"], 0, S_["zc"]), taper=M.torso_taper)
    waist = G.box(-28 - 134, -28 + 134, -100, 100, 562, 838)
    ztop_cut = TORSO_Z + 771
    def covered(p):
        x, y, z = p
        if 562 <= z <= 838 and waist.isInside(G.V(*p), 0.1):
            return True
        if z <= ztop_cut and tor.isInside(G.V(*p), 0.1):
            return True
        if z >= ztop_cut and math.hypot(x, y) <= 64:
            return True
        return False
    V_ = blm.vertices
    plate = V_[V_[:, 2] <= TORSO_Z + 8.5]
    top = V_[(V_[:, 2] >= TORSO_Z + 730) & (np.abs(V_[:, 1]) <= 68)]
    rng = np.random.default_rng(0)
    def frac(P):
        P = P[rng.choice(len(P), min(len(P), 1500), replace=False)]
        c = [covered(p) for p in P]
        return sum(c) / len(c), P[~np.array(c)]
    fp, mp = frac(plate)
    ft, mt = frac(top)
    check("Covers", "OpenArm body_link0 base plate (250x190 at z 580-588) inside the waist cover", fp >= 0.999,
          f"{fp * 100:.1f}% of {min(len(plate), 1500)} sampled STL vertices covered" + (f"; exposed e.g. {np.round(mp[:3], 0).tolist()}" if len(mp) else ""))
    check("Covers", "OpenArm body_link0 top (z 1310-1353, |y|<=68) inside torso shell / under neck plate", ft >= 0.999,
          f"{ft * 100:.1f}% of {min(len(top), 1500)} sampled STL vertices covered" + (f"; exposed e.g. {np.round(mt[:3], 0).tolist()}" if len(mt) else ""))

    # ---------------- footprint
    log("footprint...")
    skirt, base_fp, outside, bx = footprint(parts)
    check("Footprint", "upper body + arms (home) inside the base skirt outline", not outside,
          f"parts outside skirt plan: {[(k, round(v)) for k, v in outside.items()][:8]}")
    tb = np.array(bx)
    check("Footprint", "overall plan envelope", True,
          f"x {tb[0]:.0f}..{tb[2]:.0f}, y {tb[1]:.0f}..{tb[3]:.0f} mm (Tracer 702 x 610; sim skirt 762 x 672); scanner pods protrude at 2 corners", warn=False)

    # ---------------- mass
    log("mass...")
    st = json.loads((DATA / "sim_static.json").read_text())
    arm_rows = [(f"arm:{b}", v[0], np.array(v[1:]), "lift") for b, v in st["arm_body_mass_com"].items()]
    misc = [("wiring+connectors+LEDs+displays (ESTIMATE)", 3.0, np.array([-50.0, 0, 230.0]), "")]
    rows = mass_props(parts, arm_rows + misc)
    global REPORT_ROWS
    REPORT_ROWS = rows
    m0_, c0 = total(rows, 0.0)
    m_up = sum(r[1] for r in rows if r[3] == "lift")
    REPORT.append(("mass", rows, m0_, c0))
    tip0 = tipping(m0_, c0)
    def grp(sel):
        rr = [r for r in rows if sel(r)]
        mm = sum(r[1] for r in rr)
        return dict(mass_kg=round(mm, 2), com_mm=(sum(r[1] * np.asarray(r[2]) for r in rr) / mm).round(1).tolist()) if mm else {}
    OUT.mkdir(exist_ok=True)
    (OUT / "mass_properties.json").write_text(json.dumps(dict(
        total=grp(lambda r: True), tracer=grp(lambda r: r[0] == "tracer2_base"),
        base_fixed_excl_tracer=grp(lambda r: r[0] != "tracer2_base" and r[3] != "lift"),
        lifted_excl_arms=grp(lambda r: r[3] == "lift" and not r[0].startswith("arm:")),
        arms=grp(lambda r: r[0].startswith("arm:")),
        coffee=grp(lambda r: r[0].split("__")[0][:3] in ("P21", "P22", "P23", "P24", "P25", "P26", "S07", "S08", "S09", "S10", "SH0") and r[0].startswith(("P2", "S07", "S08", "S09", "S10", "SH06"))),
        battery=grp(lambda r: r[0].startswith("E01")),
        per_item={r[0]: round(r[1], 4) for r in rows}), indent=1))
    rows_pl = rows + [("payload L 4.1kg", ARM_PAYLOAD_NOM, np.array([300.0, 150.0, 1030.0]), "lift"), ("payload R 4.1kg", ARM_PAYLOAD_NOM, np.array([300.0, -150.0, 1030.0]), "lift")]
    m1_, c1 = total(rows_pl, 0.0)
    tip1 = tipping(m1_, c1)
    rows_w = [r if not r[0].startswith("arm:") else (r[0], r[1], r[2] + np.array([150.0, 0, 0]), r[3]) for r in rows] + \
        [("payload L 6kg", ARM_PAYLOAD_PEAK, np.array([550.0, 250.0, 1100.0]), "lift"), ("payload R 6kg", ARM_PAYLOAD_PEAK, np.array([550.0, -250.0, 1100.0]), "lift")]
    m2_, c2 = total(rows_w, STROKE)
    tip2 = tipping(m2_, c2)
    REPORT.append(("tipping", [("nominal (lift 0, arms home, no payload)", m0_, c0, tip0), ("work (lift 0, 2 x 4.1 kg at hands)", m1_, c1, tip1),
                               (f"worst (lift {STROKE:.0f}, arms forward, 2 x 6 kg at 0.55 m reach)", m2_, c2, tip2)]))
    sup = m0_ - TR_MASS
    pay = 2 * PRODUCT_PAYLOAD_ARM + TRAY_PAYLOAD
    ext_rows = [r for r in rows if r[0] != "tracer2_base"] + [("tray payload", TRAY_PAYLOAD, np.array([BUF_X, 0.0, BUF_Z + 40]), "lift")]
    me, ce = total(ext_rows, 0.0)
    ext_w = ext_rows + [("arm obj L", PRODUCT_PAYLOAD_ARM, np.array([300.0, 150.0, 1030.0]), "lift"), ("arm obj R", PRODUCT_PAYLOAD_ARM, np.array([300.0, -150.0, 1030.0]), "lift")]
    mw, cw = total(ext_w, 0.0)
    ext_b = [r for r in ext_rows if not r[0].startswith(("P2", "S07", "S08", "S09", "S10", "SH06"))] if False else None
    REPORT.append(("budget", sup, pay, me, ce, mw, cw))
    check("Mass", f"HARD: superstructure + product payload (2 x {PRODUCT_PAYLOAD_ARM:g} kg arms + {TRAY_PAYLOAD:.1f} kg tray) <= {MASS_LIMIT:.0f} kg (Tracer manual p.3); target <= {MASS_TARGET:.0f} kg",
          sup + pay <= MASS_TARGET, f"superstructure {sup:.1f} kg + payload {pay:.1f} kg = {sup + pay:.1f} kg (margin {MASS_LIMIT - sup - pay:.1f} kg to 100 kg)",
          warn=sup + pay <= MASS_LIMIT)
    check("Mass", "extension CoG within ±20 mm of the Tracer centre of rotation (drive axle, ASSUMED at x=0,y=0), nominal: arms home, tray loaded",
          abs(ce[0]) <= 20 and abs(ce[1]) <= 20, f"extension {me:.1f} kg, CoG ({ce[0]:.1f}, {ce[1]:.1f}, {ce[2]:.0f}) mm")
    check("Mass", "extension CoG, work posture (2 x 3 kg held at x 300 mm)", abs(cw[0]) <= 20 and abs(cw[1]) <= 20,
          f"{mw:.1f} kg, CoG ({cw[0]:.1f}, {cw[1]:.1f}, {cw[2]:.0f}) mm (transient while handling)", warn=True)
    check("Mass", "info: superstructure + 2 x 6 kg OpenArm PEAK payload (not the product rating)", True,
          f"robot {m0_:.1f} kg, superstructure {sup:.1f} kg, + peak payload = {sup + 2 * ARM_PAYLOAD_PEAK:.1f} kg, + nominal 2 x 4.1 kg = {sup + 2 * ARM_PAYLOAD_NOM:.1f} kg; sim robot {st['sim_robot_mass_kg']:.1f} kg",
          )
    check("Stability", "no tipping at 0.5 g braking/lateral (nominal)", min(tip0["fwd"], tip0["back"], tip0["left"], tip0["right"]) >= 0.5 * GRAV,
          f"tipping accel fwd/back/left/right = {tip0['fwd']:.2f}/{tip0['back']:.2f}/{tip0['left']:.2f}/{tip0['right']:.2f} m/s2; CoG {np.round(c0, 0)} mm")
    check("Stability", "no tipping at 0.5 g (worst: lift max, arms forward, 2 x 6 kg)", min(tip2["fwd"], tip2["back"], tip2["left"], tip2["right"]) >= 0.5 * GRAV,
          f"fwd/back/left/right = {tip2['fwd']:.2f}/{tip2['back']:.2f}/{tip2['left']:.2f}/{tip2['right']:.2f} m/s2; CoG {np.round(c2, 0)} mm",
          warn=min(tip2.values()) >= 2.2)
    check("Stability", "no tipping at Tracer emergency stop (2.2 m/s2, manual: 2 m/s in 0.9 m), all configs",
          min(min(t["fwd"], t["back"], t["left"], t["right"]) for t in (tip0, tip1, tip2)) >= 2.2, "see table")

    # ---------------- fastener loads
    log("fastener loads...")
    fa = fastener_analysis(parts, bolts, rows)
    REPORT.append(("fast", fa, gres, eres))
    for g in fa:
        if "note" in g:
            check("Bolt loads", g["group"], False, g["note"])
            continue
        check("Bolt loads", g["group"], g["ok"],
              f"{g['n']}x {g['spec']}; carried {g['mass']:.1f} kg; worst {g['lc']}: T={g['Tmax']:.0f} N, V_sum={g['Vsum']:.0f} N; "
              f"F_V={g['FV']:.0f} N ({g['torque']:.1f} N.m); bolt {g['Fb'] / g['Fp'] * 100:.0f}% proof; slip {'OK' if g['ok_slip'] else 'NO'} "
              f"({g['slip_cap']:.0f}/{1.25 * g['Vsum']:.0f} N); shear {g['Vmax']:.0f}/{g['shear_cap']:.0f} N; {g['fem_note']}"
              + (f" — ASSUMED: {g['assumed']}" if g['assumed'] else ""), assumed=bool(g["assumed"]))

    # ---------------- exports
    if not args.no_export:
        log("exports...")
        z = np.load(DATA / "arm_traj.npz", allow_pickle=True)
        arm_home = {}
        for b in [str(x) for x in z["bodies"]]:
            f = DATA / "arm_meshes" / f"{b}.stl"
            if f.exists():
                m = trimesh.load(f)
                m.apply_transform(z[b][-1])
                arm_home[b] = m
        export_all(parts, arm_home)
    write_bom(parts, bolts)
    write_report(parts, bolts, gres, time.time() - t00, (f0, m0, f1, fm))
    log(f"done in {time.time() - t00:.0f}s")


def write_bom(parts, bolts):
    OUT.mkdir(exist_ok=True)
    with open(OUT / "bom_parts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["part", "category", "material", "process", "mass_kg", "mass_source", "motion", "notes"])
        for n, p in parts.items():
            if getattr(p, "bolt", None):
                continue
            w.writerow([n, p.category, p.material, p.process, f"{p.mass():.3f}", p.mass_src, p.motion, p.notes])
    cnt = Counter()
    for b in bolts:
        fem = {"tap": "", "insert": f" + Kerb Konus 860 {b.thread} insert", "nut": f" + ISO 4032 {b.thread} nut-8 + ISO 7089 washer",
               "tnut": f" + {b.nut_spec}"}[b.female]
        wsh = " + ISO 7089 washer 200HV" if b.washer else ""
        cnt[(f"{b.std} {b.thread}x{b.L:g}", b.grade, wsh + fem, b.group)] += 1
    with open(OUT / "bom_fasteners.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fastener", "grade", "with", "joint group", "qty"])
        for (a, g, wt, grp), q in sorted(cnt.items(), key=lambda x: x[0][3]):
            w.writerow([a, g, wt.strip(" +"), grp, q])


def write_report(parts, bolts, gres, dt, inter):
    f0, m0, f1, fm = inter
    L = []
    L.append("# Giorgio CAD — validation report\n")
    L.append(f"Generated by `cad/validate.py` ({time.strftime('%Y-%m-%d %H:%M')}, {dt:.0f} s). Units mm / kg / N. "
             "Frame: robot base (x forward, y left, z up, origin on the floor at the Tracer centre). "
             f"{len([p for p in parts.values() if not getattr(p, 'bolt', None)])} parts, {len(bolts)} bolted joints.\n")
    npass = sum(1 for c in CHECKS if c[2] == "PASS")
    nfail = sum(1 for c in CHECKS if c[2] == "FAIL")
    nwarn = sum(1 for c in CHECKS if c[2] == "WARN")
    L.append(f"**Summary: {npass} PASS, {nwarn} WARN, {nfail} FAIL.** WARN = passes the hard limit but not the target margin, "
             "or depends on an ASSUMED interface.\n")
    L.append("| Section | Check | Result | Numbers |\n|---|---|---|---|")
    for s, n, st, d in CHECKS:
        L.append(f"| {s} | {n} | **{st}** | {d} |")
    L.append("")
    if f0 or f1 or fm:
        L.append("## Interference failures\n\n| config | part A | part B | overlap cm3 |\n|---|---|---|---|")
        for tag, lst in (("lift 0", f0), (f"lift {STROKE:.0f}", f1), ("mid", fm)):
            for a, b, v, j in lst:
                L.append(f"| {tag} | {a} | {b} | {v:.3f} |")
        L.append("")
    if m0:
        L.append("<details><summary>Touching / sub-threshold contacts (lift 0)</summary>\n\n| part A | part B | overlap cm3 |\n|---|---|---|")
        for a, b, v, j in m0:
            L.append(f"| {a} | {b} | {v:.4f} |")
        L.append("\n</details>\n")
    for item in REPORT:
        if item[0] == "mass":
            _, rows, m, c = item
            L.append("## Mass properties (lift 0, arms in home pose)\n")
            L.append(f"Total **{m:.1f} kg**, CoG ({c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f}) mm. Custom parts: CAD volume x density; purchased: datasheet "
                     "masses; arms: MuJoCo/URDF inertials (incl. grippers); wiring allowance 3 kg ESTIMATE.\n")
            agg = defaultdict(float)
            for n, mm_, cc, mo in rows:
                key = ("OpenArm 2.0 arms + grippers" if n.startswith("arm:") else n.split("__")[0])
                agg[key] += mm_
            big = sorted(agg.items(), key=lambda x: -x[1])
            L.append("| item | kg |\n|---|---|")
            for k, v in big[:30]:
                L.append(f"| {k} | {v:.2f} |")
            rest = sum(v for k, v in big[30:])
            L.append(f"| (other {len(big) - 30} items: bolts, T-nuts, liners, small brackets) | {rest:.2f} |\n")
        if item[0] == "budget":
            _, sup, pay, me, ce, mw, cw = item
            import json as _j
            bef = _j.loads((HERE / "mass_budget_before.json").read_text())["per_item"]
            now = {r[0]: r[1] for r in REPORT_ROWS}
            def cat(n):
                n0 = n.split("__")[0]
                if n0.startswith("arm:"): return "OpenArm arms + grippers"
                if n0.startswith("B_") or n0.startswith("tnut"): return "fasteners + T-nuts"
                for k, v in (("E01", "48 V battery"), ("E0", "electronics"), ("P01", "base adapter plate"), ("W01", "column sleeve"), ("S01", "column profile"),
                             ("P13", "column liners/pads"), ("P14", "column liners/pads"), ("P15", "column liners/pads"), ("P02", "column-to-torso bracket"), ("OA_body", "OpenArm body_link0"),
                             ("SH0", "shells"), ("P12", "bumper"), ("P2", "coffee module + tray/shell brackets"), ("S07", "coffee module + tray/shell brackets"),
                             ("S08", "coffee module + tray/shell brackets"), ("S09", "coffee module + tray/shell brackets"), ("S10", "coffee module + tray/shell brackets"),
                             ("tracer", "Tracer 2.0"), ("wiring", "wiring allowance")):
                    if n0.startswith(k): return v
                return "brackets, sensors, misc"
            cb, cn = defaultdict(float), defaultdict(float)
            for k_, v_ in bef.items(): cb[cat(k_)] += v_
            for k_, v_ in now.items(): cn[cat(k_)] += v_
            L.append("## Mass budget (Tracer manual: payload <= 100 kg binding; target <= 90 kg)\n")
            L.append("| group | before (kg) | now (kg) | delta |\n|---|---|---|---|")
            for k_ in sorted(set(cb) | set(cn), key=lambda k: -cn.get(k, 0)):
                L.append(f"| {k_} | {cb.get(k_, 0):.2f} | {cn.get(k_, 0):.2f} | {cn.get(k_, 0) - cb.get(k_, 0):+.2f} |")
            tb, tn = sum(cb.values()), sum(cn.values())
            L.append(f"| **robot total** | **{tb:.1f}** | **{tn:.1f}** | **{tn - tb:+.1f}** |")
            L.append(f"| superstructure (total − Tracer 55 kg) | {tb - 55:.1f} | {sup:.1f} | {sup - tb + 55:+.1f} |")
            L.append(f"| + product payload (2 × {PRODUCT_PAYLOAD_ARM:g} kg arms + {TRAY_PAYLOAD:.1f} kg tray) | {tb - 55 + pay:.1f} | **{sup + pay:.1f}** | |")
            L.append(f"\nExtension (superstructure + tray payload) CoG nominal ({ce[0]:.1f}, {ce[1]:.1f}, {ce[2]:.0f}) mm; with 2 × 3 kg held at x = 300 mm: ({cw[0]:.1f}, {cw[1]:.1f}, {cw[2]:.0f}) mm. "
                     "Centre of rotation ASSUMED at the plan centre (drive axle mid-length, as in the sim; the manual shows no axle position).\n")
        if item[0] == "tipping":
            L.append("## Static tipping (support polygon x ±281, y ±255 mm: Tracer casters, as in the sim's stability test)\n")
            L.append("| configuration | mass kg | CoG mm | a_tip fwd / back / left / right (m/s2) | max lateral slope |\n|---|---|---|---|---|")
            for nm, m, c, t in item[1]:
                L.append(f"| {nm} | {m:.1f} | ({c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f}) | {t['fwd']:.2f} / {t['back']:.2f} / {t['left']:.2f} / {t['right']:.2f} | {t['slope_lat_deg']:.0f} deg |")
            L.append("\nSim (video/stabilita.txt): work 85.2 kg, CoG z 413 mm, static fwd/back/lat 6.4/7.0/6.0 m/s2; worst (col +0.40 m) 92.7 kg, CoG z 711, 3.0/4.7/3.5 m/s2.\n")
        if item[0] == "arm_sweep":
            _, per_obj, hits, npose, srcs = item
            L.append(f"## Arm sweep\n\n{npose} poses sampled from the recorded missions ({dict(srcs)}) + home pose; arm link visual meshes "
                     "(OpenArm MJCF) vs CAD parts, FCL exact mesh distance. Recordings are at column lift 0.\n")
            L.append("| static part | min clearance mm | closest arm body @ pose | poses in contact |\n|---|---|---|---|")
            for s, (d, who) in sorted(per_obj.items(), key=lambda x: x[1][0]):
                L.append(f"| {s} | {d:.1f} | {who[0]} @ {who[1]} | {len(hits.get(s, ()))} |")
            L.append("")
        if item[0] == "fast":
            _, fa, gres_, eres = item
            L.append("## Bolted joints (worst load case per group)\n")
            L.append("Method: elastic bolt-group (centroid + polar) distribution of the force/moment of the supported mass under each load case; "
                     f"load factor Φ={F.PHI}, μ={F.MU}, preload F_V = fraction of ISO 898-1 proof load, torque T = {F.K_TORQUE}·F_V·d. "
                     "Load cases: 1 g static; ±0.5 g braking / lateral; +2 g bump (3 g total); bump + 0.5 g; rebound (net −1 g). "
                     "Groups G1–G4 also carry 2 × 6 kg peak payload at 0.55 m reach and the reaction of the shoulder motors' peak torques (2 × 40 N·m about x and y).\n")
            L.append("| group | bolts | carried kg | worst LC | T max N | ΣV N | F_V N / torque N·m | bolt % proof | slip | female thread / nut | result |\n|---|---|---|---|---|---|---|---|---|---|---|")
            for g in fa:
                if "note" in g:
                    continue
                L.append(f"| {g['group']} | {g['n']}× {g['spec']} | {g['mass']:.1f} | {g['lc']} | {g['Tmax']:.0f} | {g['Vsum']:.0f} | {g['FV']:.0f} / {g['torque']:.2f} | "
                         f"{g['Fb'] / g['Fp'] * 100:.0f}% | {'OK' if g['ok_slip'] else 'slips → shear ' + ('OK' if g['ok_shear'] else 'FAIL')} | {g['fem_note']} | "
                         f"**{'PASS' if g['ok'] else 'FAIL'}**{' (ASSUMED interface)' if g['assumed'] else ''} |")
            L.append("\n<details><summary>Per-bolt geometric checks</summary>\n\n| bolt | spec | axis offset mm | angle deg | max gap mm | Le mm | Le req mm | issues |\n|---|---|---|---|---|---|---|---|")
            for g in gres_:
                L.append(f"| {g['name']} | {g['std']} {g['thread']}x{g['L']:g} {g['grade']} | {g['coax_offset_mm']} | {g['angle_deg']} | {g['max_gap_mm']} | {g['engagement_mm']} | {g['engagement_req_mm']} | {'; '.join(g['issues']) or '-'} |")
            L.append("\n</details>\n\n<details><summary>Edge distances</summary>\n\n| part | hole | d0 mm | e mm | criterion | ok |\n|---|---|---|---|---|---|")
            for e in eres:
                L.append(f"| {e['part']} | {e['hole']} | {e['d0']:.1f} | {'>2.5 d0' if e['e'] is None else round(e['e'], 1)} | {e['crit']} | {'yes' if e['ok'] else 'NO'} |")
            L.append("\n</details>\n")
    (HERE / "VALIDATION.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
