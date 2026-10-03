"""Fasteners: ISO tables, bolt/washer/nut solids, joint definitions and the checks.

Sources (standard values, see SOURCES.md):
  ISO 273 clearance holes, ISO 2306/ISO 261 tap drills (d - P), ISO 898-1 proof loads (8.8: 580 MPa x As for <= M16),
  ISO 3506-1 (A2-70: Rp0.2 450 MPa), ISO 4762 / ISO 7380 / ISO 10642 heads, ISO 7089 washers, ISO 4032 nuts.
Simple and conservative bolted-joint model (centroid method), see README "Fastener check method".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

import geom as G

# ------------------------------------------------------------------ ISO tables (mm, N)
#          P     As     fine  medium coarse tapdrill  ISO4762 dk,k  ISO7380 dk,k  ISO7089 d1,d2,h  ISO4032 s,m
ISO = {
    "M3": dict(P=0.5, As=5.03, fine=3.2, medium=3.4, coarse=3.6, tap=2.5, shcs=(5.5, 3.0), bh=(5.7, 1.65), wsh=(3.2, 7.0, 0.5), nut=(5.5, 2.4)),
    "M4": dict(P=0.7, As=8.78, fine=4.3, medium=4.5, coarse=4.8, tap=3.3, shcs=(7.0, 4.0), bh=(7.6, 2.2), wsh=(4.3, 9.0, 0.8), nut=(7.0, 3.2)),
    "M5": dict(P=0.8, As=14.2, fine=5.3, medium=5.5, coarse=5.8, tap=4.2, shcs=(8.5, 5.0), bh=(9.5, 2.75), wsh=(5.3, 10.0, 1.0), nut=(8.0, 4.7)),
    "M6": dict(P=1.0, As=20.1, fine=6.4, medium=6.6, coarse=7.0, tap=5.0, shcs=(10.0, 6.0), bh=(10.5, 3.3), wsh=(6.4, 12.0, 1.6), nut=(10.0, 5.2)),
    "M8": dict(P=1.25, As=36.6, fine=8.4, medium=9.0, coarse=10.0, tap=6.8, shcs=(13.0, 8.0), bh=(14.0, 4.4), wsh=(8.4, 16.0, 1.6), nut=(13.0, 6.8)),
    "M10": dict(P=1.5, As=58.0, fine=10.5, medium=11.0, coarse=12.0, tap=8.5, shcs=(16.0, 10.0), bh=(17.5, 5.5), wsh=(10.5, 20.0, 2.0), nut=(16.0, 8.4)),
    "M12": dict(P=1.75, As=84.3, fine=13.0, medium=13.5, coarse=14.5, tap=10.2, shcs=(18.0, 12.0), bh=(21.0, 6.6), wsh=(13.0, 24.0, 2.5), nut=(18.0, 10.8)),
}
GRADES = {"8.8": dict(Rm=800, Rp=640, proof=580), "A2-70": dict(Rm=700, Rp=450, proof=450), "10.9": dict(Rm=1000, Rp=900, proof=830)}

# heat-set inserts Kerb Konus S-Lok 860 (catalogue en.ds.30 p.31): hole d, length, min wall; pull-out = ESTIMATE (not published)
INSERTS = {
    "M3": dict(hole=4.0, L=5.8, od=4.6, wall=2.3, pullout=1000.0),
    "M4": dict(hole=5.6, L=8.2, od=6.3, wall=2.5, pullout=1500.0),
    "M5": dict(hole=6.4, L=9.5, od=7.0, wall=2.7, pullout=2000.0),
}
# T-slot nuts: (thickness = engaged thread, allowable load N)
TNUTS = {
    "item 8 St M8 (0.0.026.18)": dict(thread="M8", m=7.5, F_allow=5000.0, src="SOURCED item24"),
    "item 8 St M6": dict(thread="M6", m=6.0, F_allow=4000.0, src="ESTIMATE (item 8 range)"),
    "slot-6 T-nut M5 (Tracer rail, ASSUMED)": dict(thread="M5", m=4.0, F_allow=1000.0, src="ASSUMED"),
    "slot-8 T-nut M6 (OpenArm post, ASSUMED)": dict(thread="M6", m=5.0, F_allow=2500.0, src="ASSUMED"),
}

# minimum engagement (Le/d) of a tapped thread in the given material, steel 8.8 bolt; and internal thread Rm
TAPPED_MATS = {
    "EN AW-6082-T6": dict(min_ratio=1.25, Rm=310),
    "EN AW-6063-T66 (profile)": dict(min_ratio=1.5, Rm=245),
    "EN AW-6060-T66": dict(min_ratio=1.5, Rm=215),
    "EN AW-5754-H22": dict(min_ratio=1.6, Rm=220),
    "S235 / 1.4301": dict(min_ratio=0.8, Rm=500),
    "OpenArm body plate (Al, ASSUMED 5052)": dict(min_ratio=1.25, Rm=230),
    "manufacturer thread (datasheet max insertion)": dict(min_ratio=0.7, Rm=200),
}

PHI = 0.2          # load factor (share of external axial load seen by the bolt), assumed
MU = 0.15          # friction coefficient in the interfaces (dry Al/Al, Al/steel), conservative
K_TORQUE = 0.20    # nut factor T = K F d (dry, zinc-plated)


def clearance_ok(thread, d, slot=False):
    t = ISO[thread]
    return t["fine"] - 1e-6 <= d <= t["coarse"] + 1e-6, f"ISO 273 {thread}: fine {t['fine']} / medium {t['medium']} / coarse {t['coarse']}"


def proof_load(thread, grade):
    return GRADES[grade]["proof"] * ISO[thread]["As"]


# ------------------------------------------------------------------ joint data model
@dataclass
class Bolt:
    """one fastener instance"""
    name: str
    thread: str
    L: float                      # nominal length (under head; countersunk: overall)
    std: str = "ISO 4762"         # ISO 4762 SHCS | ISO 7380 button | ISO 10642 csk | ISO 4017 hex | stud
    grade: str = "8.8"
    washer: bool = True           # ISO 7089 under head
    stack: list = field(default_factory=list)    # [(part_name, hole_name), ...] head side -> thread side
    female: str = "tap"           # tap | insert | nut | tnut
    nut_spec: str = ""            # for nut/tnut: ISO 4032 or TNUTS key
    torque_Nm: float = 0.0        # tightening torque (computed if 0)
    preload_frac: float = 0.6     # preload as fraction of proof load (metal joints)
    group: str = ""               # connection group (load analysis)
    assumed: str = ""             # note if the interface is assumed


def washer_t(b: Bolt):
    return ISO[b.thread]["wsh"][2] if b.washer else 0.0


def head_h(b: Bolt):
    if b.std == "DIN 7984":
        return {"M12": 7.0, "M8": 5.0, "M6": 4.0}[b.thread]
    if b.std == "ISO 7380":
        return ISO[b.thread]["bh"][1]
    if b.std == "ISO 10642":
        return 0.0
    return ISO[b.thread]["shcs"][1]


def head_d(b: Bolt):
    if b.std == "DIN 7984":
        return {"M12": 18.0, "M8": 13.0, "M6": 10.0}[b.thread]
    if b.std == "ISO 7380":
        return ISO[b.thread]["bh"][0]
    if b.std == "ISO 10642":
        return 2.0 * ISO[b.thread]["shcs"][0] / 1.0 * 0.0 + {"M3": 6.72, "M4": 8.96, "M5": 11.2, "M6": 13.44, "M8": 17.92}[b.thread]
    return ISO[b.thread]["shcs"][0]


def bolt_frame(b: Bolt, parts):
    """bolt axis (unit, head->tip) and the point where the under-head face sits (on the first part, minus washer)"""
    p0, h0 = b.stack[0]
    h = parts[p0].holes[h0]
    a = np.array(h.axis, float); a /= np.linalg.norm(a)
    seat = np.array(h.p, float) + a * (h.cbore[1] if h.cbore else 0.0)
    return a, seat - a * washer_t(b)


def bolt_solids(b: Bolt, parts):
    """simplified solids: head + shank at the thread minor diameter (so it fits tap-drill holes), washer, nut"""
    a, under_head = bolt_frame(b, parts)
    P = ISO[b.thread]["P"]
    d = float(b.thread[1:])
    d_min = d - 1.0825 * P * 1.0 - 0.1
    out = []
    if b.std == "ISO 10642":
        # countersunk: cone head inside the part; model only the shank from the head top
        shank = G.cyl(d_min / 2, b.L, under_head, a)
        out.append(("bolt", shank))
    else:
        hh = head_h(b)
        head = G.cyl(head_d(b) / 2 - 0.05, hh, under_head - a * hh, a)
        shank = G.cyl(d_min / 2, b.L, under_head, a)
        out.append(("bolt", head.fuse(shank)))
    if b.washer:
        w = ISO[b.thread]["wsh"]
        out.append(("washer", G.cyl(w[1] / 2, w[2] - 0.02, under_head + a * 0.01, a).cut(G.cyl(w[0] / 2 + 0.05, w[2] + 1, under_head - a * 0.5, a))))
    if b.female == "nut":
        # nut after the last hole exit
        pn, hn = b.stack[-1]
        hl = parts[pn].holes[hn]
        exit_ = np.array(hl.p, float) + np.array(hl.axis, float) / np.linalg.norm(hl.axis) * hl.depth
        s, m = ISO[b.thread]["nut"]
        wsh = ISO[b.thread]["wsh"]
        nw = G.cyl(wsh[1] / 2, wsh[2] - 0.02, exit_ + a * 0.01, a).cut(G.cyl(wsh[0] / 2 + 0.05, wsh[2] + 1, exit_ - a * 0.5, a))
        nut = G.cyl(s / 2 * 1.08, m, exit_ + a * wsh[2], a).cut(G.cyl(d_min / 2 + 0.1, m + 1, exit_ + a * (wsh[2] - 0.5), a))
        out.append(("washer", nw))
        out.append(("nut", nut))
    return out


# ------------------------------------------------------------------ geometric checks
def _hole_interval(h, a, origin):
    """entry/exit coordinate of a hole along the bolt axis (s measured from origin)"""
    ha = np.array(h.axis, float); ha /= np.linalg.norm(ha)
    s0 = float((np.array(h.p, float) - origin) @ a)
    s1 = s0 + h.depth * float(ha @ a)
    return min(s0, s1), max(s0, s1)


def check_bolt(b: Bolt, parts, tol_coax=0.05):
    """returns dict of results for one bolt"""
    res = dict(name=b.name, thread=b.thread, L=b.L, std=b.std, grade=b.grade, group=b.group, issues=[])
    a, under_head = bolt_frame(b, parts)
    d = float(b.thread[1:])
    P = ISO[b.thread]["P"]
    # --- coaxiality + parallelism + hole sizes
    worst_off, worst_ang = 0.0, 0.0
    intervals = []
    for i, (pn, hn) in enumerate(b.stack):
        if pn not in parts or hn not in parts[pn].holes:
            res["issues"].append(f"missing hole {pn}.{hn}")
            continue
        h = parts[pn].holes[hn]
        ha = np.array(h.axis, float); ha /= np.linalg.norm(ha)
        ang = math.degrees(math.acos(min(1.0, abs(float(ha @ a)))))
        worst_ang = max(worst_ang, ang)
        v = np.array(h.p, float) - under_head
        off_vec = v - (v @ a) * a
        if h.kind == "slot" and h.slot_len > 0:
            sd = np.array(h.slot_dir, float); sd /= np.linalg.norm(sd)
            along = float(off_vec @ sd)
            perp = np.linalg.norm(off_vec - along * sd)
            off = perp + max(0.0, abs(along) - h.slot_len / 2)
        else:
            off = float(np.linalg.norm(off_vec))
        last = i == len(b.stack) - 1
        if h.kind in ("clear", "slot", "nut"):
            allow = (h.d - d) / 2 - 0.02
            ok_d, ref = clearance_ok(b.thread, h.d)
            if not ok_d:
                res["issues"].append(f"{pn}.{hn}: clearance d={h.d} not ISO 273 ({ref})")
        elif h.kind == "tap":
            allow = tol_coax
            if abs(h.d - ISO[b.thread]["tap"]) > 0.051:
                res["issues"].append(f"{pn}.{hn}: tap drill {h.d} != {ISO[b.thread]['tap']} (ISO 2306)")
        elif h.kind == "insert":
            allow = tol_coax
            if abs(h.d - INSERTS[b.thread]["hole"]) > 0.051:
                res["issues"].append(f"{pn}.{hn}: insert bore {h.d} != {INSERTS[b.thread]['hole']} (Kerb Konus 860)")
        else:
            allow = tol_coax
        if off > allow + 1e-6:
            res["issues"].append(f"{pn}.{hn}: axis offset {off:.3f} mm > allowed {allow:.3f}")
        worst_off = max(worst_off, off if h.kind in ("tap", "insert") or last else 0.0)
        intervals.append((pn, hn, h, *_hole_interval(h, a, under_head)))
    if worst_ang > 0.5:
        res["issues"].append(f"axes not parallel: {worst_ang:.2f} deg")
    res["coax_offset_mm"] = round(worst_off, 3)
    res["angle_deg"] = round(worst_ang, 3)
    # --- contiguity of the clamped stack (gaps between parts along the axis)
    gaps = []
    for (p1, h1n, h1, s0a, s1a), (p2, h2n, h2, s0b, s1b) in zip(intervals[:-1], intervals[1:]):
        gaps.append(s0b - s1a)
    res["max_gap_mm"] = round(max(gaps), 3) if gaps else 0.0
    if gaps and (max(gaps) > 0.25 or min(gaps) < -0.05):
        res["issues"].append(f"stack not contiguous: gaps {np.round(gaps, 2).tolist()} mm")
    cb0 = parts[b.stack[0][0]].holes[b.stack[0][1]].cbore
    if intervals and abs(intervals[0][3] - washer_t(b) + (cb0[1] if cb0 else 0.0)) > 0.05 and b.std != "ISO 10642":
        res["issues"].append(f"head not seated on first part (s0={intervals[0][3]:.2f})")
    # --- thread engagement
    tip = b.L if b.std != "ISO 10642" else b.L - 0.0
    if b.std == "ISO 10642":
        tip = b.L - (intervals[0][4] - intervals[0][3]) * 0
    fem = intervals[-1] if intervals else None
    Le, req, mat_note = 0.0, 0.0, ""
    if fem is not None:
        pn, hn, h, s0, s1 = fem
        if b.female in ("tap", "insert"):
            thread_len = h.depth if b.female == "tap" else min(h.depth, INSERTS[b.thread]["L"])
            Le = max(0.0, min(tip, s0 + thread_len) - s0)
            if b.female == "tap":
                mat = parts[pn].material if parts[pn].material in TAPPED_MATS else getattr(parts[pn], "tap_material", parts[pn].material)
                mat = getattr(parts[pn], "tap_material", None) or mat
                ratio = TAPPED_MATS.get(mat, dict(min_ratio=1.5))["min_ratio"]
                req = ratio * d
                mat_note = f"{mat}, Le/d >= {ratio}"
                blind = getattr(h, "blind", False) if hasattr(h, "blind") else False
                if tip > s0 + h.depth + 1e-6 and getattr(parts[pn], "blind_taps", False):
                    res["issues"].append("bolt bottoms in blind tapped hole")
            else:
                req = 0.9 * INSERTS[b.thread]["L"]
                mat_note = "heat-set insert, Le >= 0.9 L_insert"
                if tip > s0 + h.depth - 0.5:
                    res["issues"].append(f"bolt tip {tip - s0:.1f} mm beyond insert bore depth {h.depth:.1f} - bottoming")
        elif b.female in ("nut", "tnut"):
            if b.female == "nut":
                wsh = ISO[b.thread]["wsh"][2]
                m = ISO[b.thread]["nut"][1]
                Le = max(0.0, min(tip - (s1 + wsh), m))
                req = m
                mat_note = "ISO 4032 nut, full nut + >= 1P protrusion"
                if tip - (s1 + wsh + m) < P - 1e-6:
                    res["issues"].append(f"protrusion beyond nut {tip - (s1 + wsh + m):.1f} < 1P")
            else:
                tn = TNUTS[b.nut_spec]
                Le = max(0.0, min(tip - s0, tn["m"]))
                req = tn["m"]
                mat_note = f"T-nut {b.nut_spec}"
                res["tnut_overrun_mm"] = round(tip - s0 - tn["m"], 2)
    res["engagement_mm"] = round(Le, 2)
    res["engagement_req_mm"] = round(req, 2)
    res["engagement_note"] = mat_note
    if Le + 1e-6 < req:
        res["issues"].append(f"thread engagement {Le:.1f} < required {req:.1f} mm ({mat_note})")
    res["ok_geom"] = not res["issues"]
    return res


def edge_distance(part, h, rmax_factor=2.5, nang=16):
    """smallest distance from the hole axis (at mid depth) to material boundary other than the hole itself,
    found by classifying points on growing circles (OCC solid classifier). Returns (e, d0)"""
    a = np.array(h.axis, float); a /= np.linalg.norm(a)
    c = np.array(h.p, float) + a * h.depth * 0.5
    u = np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u)
    v = np.cross(a, u)
    r = h.d / 2 + 0.3
    rmax = rmax_factor * h.d + (h.slot_len / 2 if h.kind == "slot" else 0)
    # ritaglio locale del pezzo attorno al foro: classificazione molto piu' veloce
    R_ = rmax + 2
    crop = G.box(c[0] - R_, c[0] + R_, c[1] - R_, c[1] + R_, c[2] - R_, c[2] + R_)
    try:
        shp = part.shape.intersect(crop)
    except Exception:  # noqa: BLE001
        shp = part.shape
    sd = np.array(h.slot_dir, float) / max(1e-9, np.linalg.norm(h.slot_dir)) if h.kind == "slot" else None
    while r <= rmax:
        for k in range(nang):
            t = 2 * math.pi * k / nang
            dirv = math.cos(t) * u + math.sin(t) * v
            p = c + r * dirv
            if sd is not None:
                # for slots measure from the nearest slot-end centre line
                along = float(dirv @ sd) * r
                p = c + r * dirv + sd * np.sign(along) * h.slot_len / 2
            if not shp.isInside(G.V(*p), 1e-3):
                return r, h.d
        r += 0.5
    return None, h.d
