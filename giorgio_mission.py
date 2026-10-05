"""Giorgio v4 - missione completa: trasporto + inserimento guidati dalla visione (MuJoCo 3.8, fisica vera).

Stazione A (tavolo di carico): flaconi in posizioni casuali -> la Orbbec Gemini 336L (RGB-D) li trova dai tappi,
Giorgio ne prende due (uno per mano) e li PORTA in giro: l'AMR Tracer 2.0 guida fino al banco B.
Banco B: attrezzatura con fori quadrati da 56 mm (flacone Ø50: 3 mm di gioco). La visione trova i fori liberi dalla
profondita' e corregge l'errore di aggancio dell'AMR (~1-2 cm) -> inserimento. Poi torna ad A per il giro successivo.
Sicurezza: 2 SICK nanoScan3 (campi di marcia/aggancio/fermo), occhi-display che guardano e cambiano colore.

uso: python giorgio_mission.py [--video out.mp4] [--record out.pkl] [--seconds 120] [--no_humans] [--seed 3]
"""
import argparse
import math
import time

import mujoco
import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation as Rot

from giorgio_ik import ArmIK
from giorgio_model import DRIVE_HALF_TRACK, DRIVE_WHEEL_R, GROUP_ENV, GROUP_HUMAN, LOOKS, SCANNERS, build

ap = argparse.ArgumentParser()
ap.add_argument("--look", default="gb", choices=list(LOOKS))
ap.add_argument("--video", default="")
ap.add_argument("--record", default="")
ap.add_argument("--preview", default="")
ap.add_argument("--seconds", type=float, default=1e9)
ap.add_argument("--no_humans", action="store_true")
ap.add_argument("--seed", type=int, default=3)
args = ap.parse_args()
LK = LOOKS[args.look]
rng = np.random.default_rng(args.seed)

# ---------------------------------------------------------------- geometria della cella
BENCH_Z, PR, PH, PM = 0.90, 0.025, 0.16, 0.35
ZC = BENCH_Z + PH / 2
Z_GRASP = BENCH_Z + PH - 0.035                    # presa sul collo del flacone
DOCK = {"A": np.array([-2.4, 1.45, math.pi / 2]), "B": np.array([0.0, 0.0, 0.0])}
APPROACH = {"A": np.array([-2.4, 0.55]), "B": np.array([-0.9, 0.0])}
HOLE = 0.056                                       # foro quadrato 56 mm
HOLES_LOCAL = [(0.38, 0.08), (0.38, -0.08), (0.38, 0.15), (0.38, -0.15)]   # nel riferimento del banco B
FIX_X0, FIX_X1, FIX_Y, FIX_H = 0.33, 0.43, 0.21, 0.04
R_PROT = (1600 * 0.37 + 1128) / 1000              # ISO 13855, da fermo
R_WARN = R_PROT + 1.1


def local_to_world(dock, xl, yl):
    x, y, th = dock
    c, s = math.cos(th), math.sin(th)
    return np.array([x + c * xl - s * yl, y + s * xl + c * yl])


sp = build(args.look, hands="gripper", base="amr", fixed_base=False)
wb = sp.worldbody
LIGHT = LK.get("light", False)


def box(name, pos, half, material, collide=True, yaw=0.0):
    g = wb.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material, group=GROUP_ENV)
    if name.startswith("fix"):
        g.friction = [0.3, 0.01, 0.001]
    if yaw:
        g.quat = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    if not collide:
        g.contype = g.conaffinity = 0
    else:
        g.conaffinity = 3
    return g


def table(name, dock):
    """banco davanti alla posa di aggancio: piano da x_loc 0.16 a 0.80, gambe fuori dall'ingombro dell'AMR"""
    c = local_to_world(dock, 0.48, 0.0)
    th = dock[2]
    box(f"{name}_top", (c[0], c[1], BENCH_Z - 0.02), (0.32, 0.85, 0.02), "bench", yaw=th)
    for xl in (0.19, 0.77):
        for yl in (-0.8, 0.8):
            p = local_to_world(dock, xl, yl)
            box(f"{name}_leg_{xl}_{yl}", (p[0], p[1], (BENCH_Z - 0.04) / 2), (0.025, 0.025, (BENCH_Z - 0.04) / 2), "steel", yaw=th)
    p = local_to_world(dock, 0.80, 0.0)
    box(f"{name}_edge", (p[0], p[1], BENCH_Z - 0.03), (0.002, 0.85, 0.006), "accent", collide=False, yaw=th)


table("A", DOCK["A"])
table("B", DOCK["B"])
# attrezzatura a fori sul banco B (grafite): pareti attorno a 4 fori quadrati
CH = 0.006                                          # smusso d'invito 45 gradi x 6 mm su ogni foro
hz = BENCH_Z + (FIX_H - CH) / 2
ys = sorted([y for _, y in HOLES_LOCAL])
xs0, xs1 = 0.38 - HOLE / 2, 0.38 + HOLE / 2
box("fix_front", ((FIX_X0 + xs0) / 2, 0, hz), ((xs0 - FIX_X0) / 2, FIX_Y, (FIX_H - CH) / 2), "dark")
box("fix_back", ((xs1 + FIX_X1) / 2, 0, hz), ((FIX_X1 - xs1) / 2, FIX_Y, (FIX_H - CH) / 2), "dark")
edges = [-FIX_Y] + [v for y in ys for v in (y - HOLE / 2, y + HOLE / 2)] + [FIX_Y]
for i in range(0, len(edges), 2):
    y0, y1 = edges[i], edges[i + 1]
    if y1 - y0 > 1e-4:
        box(f"fix_mid{i}", (0.38, (y0 + y1) / 2, hz), (HOLE / 2, (y1 - y0) / 2, (FIX_H - CH) / 2), "dark")
TOP = BENCH_Z + FIX_H
for k, (hx_, hy_) in enumerate(HOLES_LOCAL):
    t, L, r2 = 0.002, CH * math.sqrt(2) / 2, math.sqrt(0.5)
    for e, (ox, oy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        ex, ey = hx_ + ox * HOLE / 2, hy_ + oy * HOLE / 2
        mid = np.array([ex + ox * CH / 2, ey + oy * CH / 2, TOP - CH / 2])
        n = np.array([-ox, -oy, 1.0]) * r2                    # normale verso il foro e verso l'alto
        c = mid - t * n
        if ox:
            q = [math.cos(-ox * math.pi / 8), 0, math.sin(-ox * math.pi / 8), 0]; size = (L, HOLE / 2 + CH, t)
        else:
            q = [math.cos(oy * math.pi / 8), math.sin(oy * math.pi / 8), 0, 0]; size = (HOLE / 2 + CH, L, t)
        g = wb.add_geom(name=f"chamfer{k}_{e}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(c), size=list(size), quat=q,
                        material="steel", group=GROUP_ENV, conaffinity=3, friction=[0.3, 0.01, 0.001])
# stazione A: vassoio chiaro
pA = local_to_world(DOCK["A"], 0.33, 0.0)
box("trayA", (pA[0], pA[1], BENCH_Z + 0.001), (0.16, 0.08, 0.001), "tray", collide=False, yaw=DOCK["A"][2])
# segnaletica a terra: corsia e stazioni
for i, y in enumerate(np.arange(-3.0, 3.01, 0.5)):
    box(f"aisle{i}", (-1.6, y, 0.002), (0.04, 0.18, 0.002), "yellow", collide=False)

# flaconi alla stazione A: posizioni casuali nella zona raggiungibile (2 per lato: esterno e interno)
PARTS = []
for side, sg in (("right", -1), ("left", 1)):
    for n, (ylo, yhi) in enumerate(((0.20, 0.235), (0.14, 0.165))):
        xl = rng.uniform(0.29, 0.335); yl = sg * rng.uniform(ylo, yhi)
        p = local_to_world(DOCK["A"], xl, yl)
        b = wb.add_body(name=f"part_{side}_{n}", pos=[p[0], p[1], ZC + 0.001])
        b.add_freejoint(name=f"part_{side}_{n}_free")
        b.add_geom(name=f"part_{side}_{n}_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[PR, PH / 2, 0], mass=PM,
                   material="part", friction=[0.5, 0.02, 0.002], condim=4, group=GROUP_ENV, conaffinity=3)
        b.add_geom(name=f"part_{side}_{n}_cap", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, PH / 2 + 0.006], size=[0.012, 0.006, 0],
                   material="accent", mass=0.005, contype=0, conaffinity=0, group=GROUP_ENV)
        PARTS.append(f"part_{side}_{n}")

N_SEG = 7
HUMANS = 0 if args.no_humans else 1
for h in range(HUMANS):
    for k in range(N_SEG):
        b = wb.add_body(name=f"h{h}_{k}", mocap=True, pos=[0, 0, -10])
        b.add_geom(name=f"h{h}_{k}_g", type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[0.05, 0.1, 0], contype=0, conaffinity=0,
                   group=GROUP_HUMAN, rgba=[0.5, 0.5, 0.5, 1])

m = sp.compile()
d = mujoco.MjData(m)
# base libera: compensazione di gravita' fatta dai motori (niente gravcomp "dal cielo")
m.body_gravcomp[:] = 0
GC_DOFS = [m.jnt_dofadr[j] for j in range(m.njnt) if m.jnt_type[j] in (2, 3) and not m.joint(j).name.startswith("drive")]
GC_TAU = np.array([m.jnt_actfrcrange[m.dof_jntid[k]][1] if m.jnt_actfrclimited[m.dof_jntid[k]] else 2000.0 for k in GC_DOFS])
FREE_Q = m.jnt_qposadr[m.joint("amr_free").id]
FREE_V = m.jnt_dofadr[m.joint("amr_free").id]
DT = m.opt.timestep
mujoco.mj_forward(m, d)
print(f"modello: {m.nbody} corpi, massa robot {m.body_subtreemass[m.body('amr').id]:.1f} kg", flush=True)


# ---------------------------------------------------------------- persona (passante sulla corsia x = -1.6)
class Person:
    def __init__(self, path, speed, vest, waits=None, t0=0.0):
        self.path = [np.array(p, float) for p in path]
        self.speed, self.vest, self.waits, self.t0 = speed, vest, waits or {}, t0
        self.pos, self.yaw, self.phase, self.moving = self.path[0].copy(), 0.0, 0.0, False
        self.i, self.tw, self.active = 0, 0.0, False

    def step(self, t, dt):
        self.active = t >= self.t0
        if not self.active:
            return
        if self.tw > 0:
            self.tw -= dt; self.moving = False
            return
        nxt = self.path[(self.i + 1) % len(self.path)]
        dv = nxt - self.pos
        dist = np.linalg.norm(dv)
        stp = self.speed * dt
        self.moving = True
        if dist <= stp:
            self.pos = nxt.copy(); self.i = (self.i + 1) % len(self.path)
            self.tw = self.waits.get(self.i, 0.0)
        else:
            self.pos += dv / dist * stp
            self.yaw = math.atan2(dv[1], dv[0])
        self.phase += stp / 0.75 * math.pi

    def segments(self):
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        fwd, lat = np.array([c, s, 0]), np.array([-s, c, 0])
        sw = 0.42 * math.sin(self.phase) if self.moving else 0.0
        P = np.array([self.pos[0], self.pos[1], 0.0]); up = np.array([0, 0, 1.0])
        dark, skin = (0.12, 0.12, 0.14), (0.75, 0.6, 0.5)
        out = []
        for k in (1, -1):
            ang = sw * k
            ax = -math.cos(ang) * up + math.sin(ang) * fwd
            out.append((P + lat * 0.1 * k + up * 0.92 + ax * 0.42, ax, 0.075, 0.36, dark))
            axa = -math.cos(-0.7 * ang) * up + math.sin(-0.7 * ang) * fwd
            out.append((P + lat * 0.22 * k + up * 1.45 + axa * 0.3, axa, 0.05, 0.26, self.vest if k > 0 else dark))
        out.append((P + up * 1.22, up, 0.17, 0.16, self.vest))
        out.append((P + up * 1.66, up, 0.105, 0.03, skin))
        out.append((P + up * 1.77 - fwd * 0.01, up, 0.115, 0.001, (0.95, 0.95, 0.95)))
        return out


people = [] if args.no_humans else [Person([(-1.6, -4.5), (-1.6, 4.5), (-1.6, -4.5)], 1.2, (1.0, 0.45, 0.05), waits={1: 6.0, 2: 10.0}, t0=8.0)]


def place_people():
    for h, p in enumerate(people):
        segs = p.segments() if p.active else []
        for k in range(N_SEG):
            mid = m.body_mocapid[m.body(f"h{h}_{k}").id]; gid = m.geom(f"h{h}_{k}_g").id
            if not segs:
                d.mocap_pos[mid] = [0, 0, -10]; continue
            c, ax, r, hh, col = segs[k]
            q = Rot.align_vectors([ax], [[0, 0, 1.0]])[0].as_quat()
            d.mocap_pos[mid] = c; d.mocap_quat[mid] = [q[3], q[0], q[1], q[2]]
            m.geom_size[gid] = [r, hh, 0]; m.geom_rgba[gid] = list(col) + [1]


# ---------------------------------------------------------------- scanner di sicurezza (raycast reale)
SCAN_FOV, SCAN_N, SCAN_MAX = math.radians(275), 276, 8.0
scan_sites = [m.site(f"scanner{k}").id for k in range(len(SCANNERS))]
GG = np.array([1, 1, 0, 0, 0, 0], np.uint8)
FIELDS = {"prot": 0.6, "warn": 1.0, "mode": "marcia"}


def yaw_of(body):
    R = d.body(body).xmat.reshape(3, 3)
    return math.atan2(R[1, 0], R[0, 0])


def scan_once():
    out = []
    th = yaw_of("amr")
    for k, sid in enumerate(scan_sites):
        o = d.site_xpos[sid].copy()
        a = SCANNERS[k][1] + th + np.linspace(-SCAN_FOV / 2, SCAN_FOV / 2, SCAN_N)
        vec = np.stack([np.cos(a), np.sin(a), np.zeros_like(a)], 1).reshape(-1)
        gid = np.zeros(SCAN_N, np.int32); dist = np.zeros(SCAN_N)
        mujoco.mj_multiRay(m, d, o, vec, GG, 1, -1, gid, dist, None, SCAN_N, SCAN_MAX)
        dist[dist < 0] = SCAN_MAX
        out.append((o, vec.reshape(-1, 3), dist))
    return out


REF = None


def safety():
    zone, hits = 0, []
    c = d.body("amr").xpos[:2]
    for k, (o, vec, dist) in enumerate(scan_once()):
        pts = o + vec * dist[:, None]
        intr = dist < (REF[k] - 0.07) if (FIELDS["mode"] == "fermo" and REF is not None) else dist < SCAN_MAX - 0.01
        dc = np.linalg.norm(pts[:, :2] - c, axis=1)
        z = np.where(intr & (dc < FIELDS["prot"]), 2, np.where(intr & (dc < FIELDS["warn"]), 1, 0))
        zone = max(zone, int(z.max())); hits.append((o, pts, z))
    return zone, hits


# ---------------------------------------------------------------- visione: Gemini 336L RGB-D
class Vision:
    W, H = 640, 400

    def __init__(self):
        self.rgb = mujoco.Renderer(m, self.H, self.W)
        self.dep = mujoco.Renderer(m, self.H, self.W); self.dep.enable_depth_rendering()
        self.cid = m.camera("gemini").id
        fy = (self.H / 2) / math.tan(math.radians(m.cam_fovy[self.cid]) / 2)
        self.K = (fy, fy, self.W / 2, self.H / 2)
        self.last, self.overlay, self.dets, self.title = None, None, [], ""

    def capture(self):
        self.rgb.update_scene(d, "gemini"); img = self.rgb.render().copy()
        self.dep.update_scene(d, "gemini"); depth = self.dep.render().copy()
        fx, fy, cx, cy = self.K
        u, v = np.meshgrid(np.arange(self.W), np.arange(self.H))
        Pc = np.stack([(u - cx) / fx * depth, -(v - cy) / fy * depth, -depth], -1)
        R = d.cam_xmat[self.cid].reshape(3, 3); t = d.cam_xpos[self.cid]
        Pw = Pc @ R.T + t
        self.last = (img, depth, Pw)
        return img, depth, Pw

    def find_bottles(self):
        """tappi arancioni (segmentazione colore) -> centro 3D dalla profondita'"""
        img, depth, Pw = self.capture()
        import cv2
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(int)      # tinta arancione + saturazione: robusto alle ombre
        mask = (hsv[..., 0] >= 5) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 110) & (hsv[..., 2] > 50) & (depth < 2.5)
        mask = ndimage.binary_closing(mask, iterations=2)
        lab, n = ndimage.label(mask)
        dets = []
        for i in range(1, n + 1):
            yy, xx = np.nonzero(lab == i)
            if len(yy) < 12:
                continue
            P = Pw[yy, xx]
            top = P[P[:, 2] > P[:, 2].max() - 0.004]          # solo la faccia superiore del tappo (niente bordo laterale)
            p = 0.5 * (top.min(0) + top.max(0)); p[2] = top[:, 2].mean()
            if not (BENCH_Z + PH - 0.02 < p[2] < BENCH_Z + PH + 0.04):
                continue
            dup = [dt for dt in dets if np.linalg.norm(dt["xy"] - p[:2]) < 0.03]
            if dup:                                       # stessa macchia spezzata da un'occlusione: unisco
                dt = dup[0]; dt["xy"] = 0.5 * (dt["xy"] + p[:2])
                b0 = dt["box"]; dt["box"] = (min(b0[0], xx.min()), min(b0[1], yy.min()), max(b0[2], xx.max()), max(b0[3], yy.max()))
                continue
            dets.append(dict(xy=p[:2], box=(xx.min(), yy.min(), xx.max(), yy.max()), kind="flacone"))
        self.dets, self.title = dets, "VISIONE: ricerca flaconi (colore tappo + profondita')"
        return dets

    def find_holes(self):
        """attrezzatura scura (colore + quota) -> dentro il suo ingombro, pixel 4 cm piu' bassi = fori liberi"""
        img, depth, Pw = self.capture()
        f = img.astype(int)
        dark = (f.max(-1) < 70) & (np.abs(Pw[..., 2] - (BENCH_Z + FIX_H - 0.006)) < 0.008)
        lab, n = ndimage.label(dark)
        if n == 0:
            self.dets = []; return []
        big = 1 + int(np.argmax(ndimage.sum(dark, lab, range(1, n + 1))))
        yy, xx = np.nonzero(lab == big)
        x0, x1, y0, y1 = xx.min(), xx.max(), yy.min(), yy.max()
        sub = np.zeros_like(dark)
        low = np.abs(Pw[..., 2] - BENCH_Z) < 0.012
        sub[y0:y1 + 1, x0:x1 + 1] = low[y0:y1 + 1, x0:x1 + 1]
        fb = Pw[lab == big]                                   # ingombro dell'attrezzatura nel mondo
        lo_, hi_ = fb[:, :2].min(0), fb[:, :2].max(0)
        inside = (Pw[..., 2] < BENCH_Z + FIX_H - 0.012) & (Pw[..., 2] > BENCH_Z - 0.005)   # pixel che guardano DENTRO un foro
        sub[y0:y1 + 1, x0:x1 + 1] = inside[y0:y1 + 1, x0:x1 + 1]
        lab2, n2 = ndimage.label(sub)
        tcam = d.cam_xpos[self.cid]
        dets = []
        for i in range(1, n2 + 1):
            yy, xx = np.nonzero(lab2 == i)
            if len(yy) < 30:
                continue
            p = Pw[yy, xx]
            if np.sum(p[:, 2] < BENCH_Z + 0.006) < 40:      # il fondo deve vedersi: un foro occupato mostra solo un anello
                continue
            z0 = BENCH_Z + FIX_H - 0.006                       # ogni raggio attraversa il fondo dello smusso: lo proietto li'
            q = tcam + (p - tcam) * ((z0 - tcam[2]) / (p[:, 2] - tcam[2]))[:, None]
            ctr = 0.5 * (q[:, :2].min(0) + q[:, :2].max(0))
            ext = q[:, :2].max(0) - q[:, :2].min(0)
            if not (np.all(ctr > lo_ + 0.02) and np.all(ctr < hi_ - 0.02)) or ext.min() < 0.03:
                continue
            dets.append(dict(xy=ctr, box=(xx.min(), yy.min(), xx.max(), yy.max()), kind="foro"))
        self.dets, self.title = dets, "VISIONE: fori liberi (profondita' Gemini 336L)"
        return dets

    def render_overlay(self, truth=None):
        import cv2
        if self.last is None:
            return None
        img = self.last[0].copy()
        for k, dt in enumerate(self.dets):
            x0, y0, x1, y1 = dt["box"]
            col = (60, 220, 120) if dt["kind"] == "flacone" else (60, 180, 255)
            cv2.rectangle(img, (int(x0) - 3, int(y0) - 3), (int(x1) + 3, int(y1) + 3), col, 2)
            cx, cy = int((x0 + x1) / 2), int((y0 + y1) / 2)
            cv2.drawMarker(img, (cx, cy), col, cv2.MARKER_CROSS, 14, 2)
            err = dt.get("err")
            txt = f"{dt['kind']} {k + 1}" + (f"  err {err:.1f} mm" if err is not None else "")
            cv2.putText(img, txt, (int(x0), max(12, int(y0) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, txt, (int(x0), max(12, int(y0) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
        cv2.putText(img, self.title, (8, self.H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, self.title, (8, self.H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        return img


vision = Vision()

# ---------------------------------------------------------------- braccia
ARM_ACT = {s: [m.actuator(f"{s}_joint{k}_ctrl").id for k in range(1, 8)] for s in ("right", "left")}
GRIP = {s: m.actuator(f"{s}_finger1_ctrl").id for s in ("right", "left")}
GRIP_OPEN = {"right": -0.785, "left": 0.785}
SGN = {"right": -1, "left": 1}
IK = {s: ArmIK(m, s, f"{s}_grasp") for s in ("right", "left")}


def R_grasp():
    """pinza verticale, chiusura lungo l'asse 'avanti' del robot"""
    return Rot.from_euler("z", yaw_of("amr") + math.pi / 2).as_matrix()


def smooth(u):
    return u * u * u * (10 - 15 * u + 6 * u * u)


class Seg:
    def __init__(self, kind, qa=None, qb=None, dur=0.5, grip=None, ev=None):
        self.kind, self.qa, self.qb, self.dur, self.grip, self.ev = kind, qa, qb, dur, grip, ev


class Arm:
    def __init__(self, s):
        self.s, self.sg, self.ik = s, SGN[s], IK[s]
        self.q = np.array([d.qpos[a] for a in self.ik.qadr]); self.grip = GRIP_OPEN[s]
        self.segs, self.i, self.t, self.held, self.target = [], 0, 0.0, None, None

    def solve(self, p, q0):
        q, ok, ep, er = self.ik.solve(d.qpos.copy(), q0, np.asarray(p, float), R_grasp())
        if not ok:
            print(f"[{self.s}] IK imprecisa su {np.round(p, 3)}: {ep * 1000:.1f} mm", flush=True)
        return q

    def line(self, pa, pb, q0, dur, n=10):
        qs, q, R = [], q0, R_grasp()
        for u in np.linspace(0, 1, n + 1)[1:]:
            q, _, _ = self.ik.solve1(d.qpos.copy(), q, pa + (pb - pa) * u, R); qs.append(q)
        segs, qp = [], q0
        for qn in qs:
            segs.append(Seg("lin", qp, qn, dur / n)); qp = qn
        return segs, qp

    def jmove(self, qa, qb):
        return Seg("joint", qa, qb, max(0.8, float(np.max(np.abs(qb - qa))) / 1.2 * 1.9))

    def pose_local(self, xl, yl, dz):
        x, y, th = d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")
        p = local_to_world((x, y, th), xl, yl)
        return np.array([p[0], p[1], Z_GRASP + dz])

    def plan_pose(self, xl, yl, dz):
        q = self.solve(self.pose_local(xl, self.sg * yl, dz), self.q)
        return [self.jmove(self.q, q)]

    def plan_pick(self, xy, part):
        a = np.array([xy[0], xy[1], Z_GRASP]); up = np.array([0, 0, 0.13])
        q_pre = self.solve(a + up, self.q)
        segs = [Seg("grip", dur=0.3, grip=GRIP_OPEN[self.s]), self.jmove(self.q, q_pre)]
        s1, q_g = self.line(a + up, a, q_pre, 0.9); segs += s1
        segs += [Seg("grip", dur=0.5, grip=0.0, ev=("grip", part)), Seg("wait", dur=0.25)]
        s2, q_up = self.line(a, a + np.array([0, 0, 0.16]), q_g, 0.8); segs += s2
        segs[-1].ev = ("picked", part)
        return segs

    def plan_insert(self, xy, part):
        # inserimento "a caduta guidata": fondo del flacone 12 mm sopra la bocca, apertura, le pareti del foro lo guidano
        b = np.array([xy[0], xy[1], Z_GRASP + (BENCH_Z + FIX_H + 0.012 - BENCH_Z)]); up = np.array([0, 0, 0.12])
        q_bu = self.solve(b + up, self.q)
        segs = [self.jmove(self.q, q_bu)]
        s3, q_b = self.line(b + up, b, q_bu, 1.0); segs += s3
        segs += [Seg("wait", dur=0.3), Seg("grip", dur=0.35, grip=GRIP_OPEN[self.s], ev=("release", part)), Seg("wait", dur=0.6)]
        s4, _ = self.line(b, b + up, q_b, 0.7); segs += s4
        segs[-1].ev = ("inserted", part)
        return segs

    def start(self, segs):
        self.segs, self.i, self.t, self._g0 = segs, 0, 0.0, self.grip

    @property
    def busy(self):
        return bool(self.segs)

    def step(self, dt, k):
        if not self.segs:
            return
        sg = self.segs[self.i]
        self.t += dt * k
        u = min(1.0, self.t / sg.dur)
        if sg.kind in ("joint", "lin"):
            self.q = sg.qa + (sg.qb - sg.qa) * (smooth(u) if sg.kind == "joint" else u)
        elif sg.kind == "grip":
            self.grip = self._g0 + (sg.grip - self._g0) * smooth(u)
        if u >= 1.0:
            if sg.ev:
                on_event(self, *sg.ev)
            self.i, self.t, self._g0 = self.i + 1, 0.0, self.grip
            if self.i >= len(self.segs):
                self.segs = []

    def apply(self):
        d.ctrl[ARM_ACT[self.s]] = self.q
        d.ctrl[GRIP[self.s]] = self.grip


# posa di partenza: robot agganciato in A, braccia in posa "pronto" (calcolata con la base nell'origine)
import itertools
q_ready = {}
for s_ in ("right", "left"):
    tgt_r = np.array([0.28, SGN[s_] * 0.24, Z_GRASP + 0.16]); R0 = Rot.from_euler("z", math.pi / 2).as_matrix()
    seeds = [np.array([-0.59, 2.38, 0.36, 1.63, 0.79, 0.3, 1.19])]
    if s_ == "left":     # braccio speculare: provo tutte le inversioni di segno della soluzione destra
        seeds = [seeds[0] * np.array(sg_) for sg_ in itertools.product((1, -1), repeat=7)]
    best = None
    for sd in seeds:
        sd = np.clip(sd, IK[s_].lo, IK[s_].hi)
        q, ep, er = IK[s_].solve1(d.qpos.copy(), sd, tgt_r, R0, 200)
        c = ep * 1000 + er * 100 + 0.05 * np.sum(np.abs(q - (IK[s_].lo + IK[s_].hi) / 2))
        if best is None or c < best[0]:
            best = (c, q, ep)
    q_ready[s_] = best[1]
    d.qpos[IK[s_].qadr] = best[1]; d.ctrl[ARM_ACT[s_]] = best[1]
    print(f"posa pronto {s_}: errore {best[2] * 1000:.1f} mm", flush=True)
d.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A"][0], DOCK["A"][1], 0.0]
d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(DOCK["A"][2] / 2), 0, 0, math.sin(DOCK["A"][2] / 2)]
mujoco.mj_forward(m, d)
arms = {s: Arm(s) for s in ("right", "left")}
for a in arms.values():
    a.grip = GRIP_OPEN[a.s]

stats = {"inserted": 0, "lost": 0, "trips": 0, "stops": 0, "vis_err": []}
mission = {"state": "settle", "t": 0.0, "trip": 0, "route": [], "seg": 0, "seg_t": 0.0, "log": []}


def log(msg):
    print(f"[t={d.time:6.1f}s] {msg}", flush=True)
    mission["log"] = (mission["log"] + [msg])[-4:]


def on_event(a, ev, part):
    if ev == "grip":
        a.held = part
    elif ev == "picked":
        z = d.body(part).xpos[2]
        if z < ZC + 0.08:
            log(f"{a.s}: presa fallita su {part}"); stats["lost"] += 1; a.held = None
    elif ev == "inserted":
        p = d.body(part).xpos; tgt = a.target
        err = 1000 * np.linalg.norm(p[:2] - tgt) if tgt is not None else -1
        ok = abs(p[2] - ZC) < 0.012 and err < 6
        stats["inserted" if ok else "lost"] += 1
        log(f"{a.s}: {part} {'INSERITO' if ok else 'NON INSERITO'} (centro a {err:.1f} mm dal foro vero)")
        a.held = None


# ---------------------------------------------------------------- guida AMR: primitive (retro, rotazione, vai, aggancio)
WL, WR = m.actuator("drive_left_vel").id, m.actuator("drive_right_vel").id
B_HALF, WHEEL_R = DRIVE_HALF_TRACK, DRIVE_WHEEL_R     # base attiva (giorgio_model.BASE)
drive = {"v": 0.0, "w": 0.0}


def route_to(st):
    x, y, th = d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")
    app = APPROACH[st]; dk = DOCK[st]
    p_back = np.array([x, y]) - 0.8 * np.array([math.cos(th), math.sin(th)])
    head = math.atan2(app[1] - p_back[1], app[0] - p_back[0])
    return [("rev", p_back), ("turn", head), ("go", app), ("turn", dk[2]), ("dock", dk)]


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def drive_step(k):
    """esegue la primitiva corrente; True a fine percorso"""
    x, y, th = d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")
    kind, tgt = mission["route"][mission["seg"]]
    v_ref = w_ref = 0.0; done = False
    if kind == "rev":
        dvec = tgt - [x, y]; dist = np.linalg.norm(dvec)
        v_ref = -min(0.25, 0.6 * dist + 0.04); done = dist < 0.02 or (dvec @ [math.cos(th), math.sin(th)]) > 0
        FIELDS.update(prot=0.45, warn=0.6)
    elif kind == "turn":
        e = wrap(tgt - th); w_ref = float(np.clip(2.0 * e, -0.7, 0.7))
        w_ref = math.copysign(max(abs(w_ref), 0.1), e); done = abs(e) < math.radians(0.5)
        FIELDS.update(prot=0.4, warn=0.55)                    # rotazione sul posto: campi stretti
    elif kind == "go":
        dvec = tgt - [x, y]; dist = np.linalg.norm(dvec)
        e = wrap(math.atan2(dvec[1], dvec[0]) - th)
        v_ref = min(0.55, 0.8 * dist + 0.05) * max(0.0, math.cos(e)); w_ref = float(np.clip(2.0 * e, -0.7, 0.7))
        done = dist < 0.03
        FIELDS.update(prot=0.45 + 0.9 * abs(drive["v"]), warn=0.75 + 0.9 * abs(drive["v"]))
    elif kind == "dock":
        dx, dy, dth = tgt
        c, s = math.cos(dth), math.sin(dth)
        along = (x - dx) * c + (y - dy) * s; lat = -(x - dx) * s + (y - dy) * c
        e = wrap(dth - th) - 1.5 * lat
        v_ref = float(np.clip(-0.6 * along, 0.04, 0.15)) if along < -0.003 else 0.0
        w_ref = float(np.clip(2.0 * e, -0.3, 0.3)) if v_ref > 0 else 0.0
        if v_ref == 0.0:
            mission["route"][mission["seg"]] = ("turn", dth)          # raddrizzamento finale sul posto
            mission["route"].append(("stop", None))
            done = False
        FIELDS.update(prot=0.38, warn=0.6)
    elif kind == "stop":
        done = np.linalg.norm(d.qvel[FREE_V:FREE_V + 6]) < 0.004
    v_ref *= k; w_ref *= k
    acc = 0.5 * DT
    drive["v"] += float(np.clip(v_ref - drive["v"], -2 * acc, acc)); drive["w"] = w_ref
    d.ctrl[WL] = (drive["v"] - drive["w"] * B_HALF) / WHEEL_R
    d.ctrl[WR] = (drive["v"] + drive["w"] * B_HALF) / WHEEL_R
    if done:
        print(f"    [guida] {kind} completato a t={d.time:.1f}s (x {x:.2f}, y {y:.2f}, yaw {math.degrees(th):.0f})", flush=True)
        mission["seg"] += 1
    return mission["seg"] >= len(mission["route"])


# ---------------------------------------------------------------- occhi-display
EYES = {"l": m.geom("eye_l").id, "r": m.geom("eye_r").id}
EYE_POS0 = {k: m.geom_pos[g].copy() for k, g in EYES.items()}
EYE_COL = {0: (0.45, 0.85, 1.0), 1: (1.0, 0.72, 0.15), 2: (1.0, 0.18, 0.12)}
eye = {"gaze": np.zeros(2), "next_blink": 2.5}
state = {"k": 1.0, "k_cmd": 1.0, "zone": 0, "clear_t": 0.0, "hits": [], "scan_t": 0.0}


def eyes_step():
    t = d.time
    cr = d.body("crown"); Rc = cr.xmat.reshape(3, 3)
    near = [np.r_[p.pos, 1.6] for p in people if p.active and np.linalg.norm(p.pos - d.body("amr").xpos[:2]) < 2.5]
    if near:
        tgt = min(near, key=lambda q: np.linalg.norm(q[:2] - cr.xpos[:2]))
    elif mission["state"].startswith("drive"):
        tgt = cr.xpos + Rc @ np.array([2.0, 0, -0.2])
    else:
        tgt = 0.5 * (d.site("right_grasp").xpos + d.site("left_grasp").xpos)
    v = Rc.T @ (tgt - cr.xpos)
    g = np.array([np.clip(math.atan2(v[1], v[0]) / 1.2, -1, 1), np.clip(math.atan2(v[2], math.hypot(v[0], v[1])) / 0.8, -1, 1)])
    eye["gaze"] += 0.15 * (g - eye["gaze"])
    blink = 0.0
    if t > eye["next_blink"]:
        u = (t - eye["next_blink"]) / 0.16
        blink = math.sin(math.pi * min(u, 1.0))
        if u >= 1.0:
            eye["next_blink"] = t + 3.0 + 2.0 * ((t * 7.31) % 1.0)
    for k_, gid in EYES.items():
        m.geom_pos[gid] = EYE_POS0[k_] + [0, 0.011 * eye["gaze"][0], 0.008 * eye["gaze"][1]]
        m.geom_size[gid] = [0.004, 0.0125, 0.017 * (1 - 0.85 * blink)]
        m.geom_rgba[gid] = list(EYE_COL[state["zone"]]) + [1]


# ---------------------------------------------------------------- missione
def teach_contour():
    global REF
    REF = [dd.copy() for _, _, dd in scan_once()]
    FIELDS.update(prot=R_PROT, warn=R_WARN, mode="fermo")


def mission_step(k):
    st = mission["state"]
    mission["t"] += DT
    if st == "settle" and mission["t"] > 0.5:
        teach_contour(); set_state("look_A")
    elif st == "look_A" and mission["t"] > 0.6 and not any(a.busy for a in arms.values()):
        dets = vision.find_bottles()
        assign = {}
        for s_, a in arms.items():           # per lato: il flacone piu' esterno ancora sul tavolo
            cands = []
            for dt in dets:
                yl = local_rel(dt["xy"])[1]
                if np.sign(yl) == a.sg:
                    cands.append((abs(yl), dt))
            if cands:
                assign[s_] = max(cands, key=lambda c: c[0])[1]
        for s_, dt in assign.items():
            part = min((p for p in PARTS if f"_{s_}_" in p and d.body(p).xpos[2] < ZC + 0.02 and
                        np.linalg.norm(d.body(p).xpos[:2] - dt["xy"]) < 0.05), key=lambda p: np.linalg.norm(d.body(p).xpos[:2] - dt["xy"]), default=None)
            if part is None:
                continue
            err = 1000 * np.linalg.norm(d.body(part).xpos[:2] - dt["xy"]); dt["err"] = err; stats["vis_err"].append(err)
            arms[s_].start(arms[s_].plan_pick(dt["xy"], part))
        log(f"visione: {len(dets)} flaconi trovati, errore medio {np.mean([dt.get('err', 0) for dt in assign.values()]):.1f} mm")
        if not assign:
            set_state("done")
        else:
            set_state("pick_A")
    elif st == "look_A" and mission["t"] <= 0.6 and not mission.get("cleared") and not any(a.busy for a in arms.values()):
        mission["cleared"] = True
        for a in arms.values():
            a.start(a.plan_pose(0.24, 0.34, 0.14))
    elif st == "pick_A" and not any(a.busy for a in arms.values()):
        if not any(a.held for a in arms.values()):
            set_state("look_A"); return
        for a in arms.values():              # posa di trasporto: flaconi alti sopra la base, vicini al busto
            a.start(a.plan_pose(0.27, 0.22, 0.16))
        set_state("carry")
    elif st == "carry" and not any(a.busy for a in arms.values()):
        mission["route"], mission["seg"] = route_to("B"), 0
        FIELDS["mode"] = "marcia"; set_state("drive_AB"); log("AMR: trasporto verso il banco B")
    elif st == "drive_AB" and drive_step(k):
        teach_contour(); set_state("look_B")
        x, y, th = d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")
        log(f"AMR agganciato a B: errore {1000 * x:.0f} / {1000 * y:.0f} mm, {math.degrees(th):.1f} gradi -> la visione corregge")
    elif st == "look_B" and mission["t"] > 0.6:
        holes = vision.find_holes()
        truth = [local_to_world(DOCK["B"], *h) for h in HOLES_LOCAL]
        for h in holes:
            tv = min(truth, key=lambda t_: np.linalg.norm(t_ - h["xy"])); h["err"] = 1000 * np.linalg.norm(tv - h["xy"]); h["true"] = tv
            stats["vis_err"].append(h["err"])
        for s_, a in arms.items():
            mine = [h for h in holes if np.sign(local_rel(h["xy"])[1]) == a.sg]
            if a.held and mine:
                h = min(mine, key=lambda h_: abs(local_rel(h_["xy"])[1]))     # il foro libero piu' interno
                a.target = h["true"]
                a.start(a.plan_insert(h["xy"], a.held))
        log(f"visione: {len(holes)} fori liberi, errore medio {np.mean([h['err'] for h in holes]) if holes else 0:.1f} mm")
        set_state("insert_B")
    elif st == "insert_B" and not any(a.busy for a in arms.values()):
        stats["trips"] += 1
        left = [p for p in PARTS if local_rel_station(d.body(p).xpos[:2], "A")[0] > 0.1 and d.body(p).xpos[2] > ZC - 0.02
                and np.linalg.norm(d.body(p).xpos[:2] - DOCK["A"][:2]) < 1.0]
        if left:
            for a in arms.values():
                a.start(a.plan_pose(0.24, 0.34, 0.14))        # braccia larghe: fuori dal campo della Gemini, senza ombre sui tappi
            set_state("back")
        else:
            log("missione completata: tutti i flaconi inseriti"); set_state("done")
    elif st == "back" and not any(a.busy for a in arms.values()):
        mission["route"], mission["seg"] = route_to("A"), 0
        FIELDS["mode"] = "marcia"; set_state("drive_BA"); log("AMR: ritorno alla stazione A")
    elif st == "drive_BA" and drive_step(k):
        teach_contour(); set_state("look_A")
    if st.startswith("drive"):
        pass
    else:
        d.ctrl[WL] = d.ctrl[WR] = 0.0


def set_state(s_):
    mission["state"], mission["t"] = s_, 0.0
    if s_ == "look_A":
        mission["cleared"] = False


def local_rel(xy):
    return local_rel_station(xy, None)


def local_rel_station(xy, st):
    if st is None:
        x, y, th = d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")
    else:
        x, y, th = DOCK[st]
    c, s = math.cos(th), math.sin(th)
    dx, dy = xy[0] - x, xy[1] - y
    return np.array([c * dx + s * dy, -s * dx + c * dy])


def control_step():
    t = d.time
    d.qfrc_applied[GC_DOFS] = np.clip(d.qfrc_bias[GC_DOFS], -GC_TAU, GC_TAU)
    if int(round(t / DT)) % 16 == 0:
        eyes_step()
    for p in people:
        p.step(t, DT)
    if people:
        place_people()
    state["scan_t"] += DT
    if state["scan_t"] >= 0.03 or not state["hits"]:
        state["scan_t"] = 0.0
        zone, state["hits"] = safety()
        if zone == 2:
            if state["zone"] != 2 and state["k_cmd"] > 0:
                stats["stops"] += 1; log("SCANNER: persona nel campo di protezione -> arresto")
            state["k_cmd"], state["clear_t"] = 0.0, 0.0
        else:
            state["clear_t"] += 0.03
            if state["clear_t"] > 1.0 or state["k_cmd"] > 0:
                state["k_cmd"] = 0.3 if zone == 1 else 1.0
        state["zone"] = zone
    k, kc = state["k"], state["k_cmd"]
    state["k"] = k = max(kc, k - DT / 0.3) if kc < k else min(kc, k + DT / 0.6)
    mission_step(k)
    for a in arms.values():
        a.step(DT, k); a.apply()
    mujoco.mj_step(m, d)


# ---------------------------------------------------------------- disegno e uscite
STATE_TXT = {"settle": "avvio", "look_A": "visione: cerca i flaconi (stazione A)", "pick_A": "presa dei flaconi",
             "carry": "posa di trasporto", "drive_AB": "AMR: trasporto A -> B", "look_B": "visione: cerca i fori (banco B)",
             "insert_B": "inserimento nei fori (gioco 3 mm)", "back": "pronto al ritorno", "drive_BA": "AMR: ritorno B -> A",
             "done": "missione completata"}
ZN = ["LIBERO", "AVVISO - velocita' 30%", "PROTEZIONE - arresto"]
ZCOL = [(80, 255, 110), (255, 215, 30), (255, 50, 50)]


def hud_lines():
    ve = stats["vis_err"]
    return [f"GIORGIO  //  OpenArm 2.0 + AgileX Tracer 2.0 + Gemini 336L + Insta360 X4",
            f"missione: {STATE_TXT[mission['state']]}" + (f"   v = {drive['v']:.2f} m/s" if mission['state'].startswith('drive') else ""),
            f"scanner ({FIELDS['mode']}): {ZN[state['zone']]}   campi {FIELDS['prot']:.2f} / {FIELDS['warn']:.2f} m",
            f"inseriti {stats['inserted']}  falliti {stats['lost']}  viaggi {stats['trips']}  arresti {stats['stops']}"
            + (f"   visione: errore medio {np.mean(ve):.1f} mm" if ve else "") + f"   t = {d.time:5.1f} s"]


def draw(scn):
    def line(a, b, rgba, w=1.5):
        if scn.ngeom >= scn.maxgeom:
            return
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_LINE, np.zeros(3), np.zeros(3), np.eye(3).reshape(-1), np.array(rgba, np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_LINE, w, np.asarray(a, float), np.asarray(b, float)); scn.ngeom += 1

    def dot(p, rgba, r=0.012):
        if scn.ngeom >= scn.maxgeom:
            return
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_SPHERE, np.array([r, 0, 0]), np.asarray(p, float), np.eye(3).reshape(-1), np.array(rgba, np.float32))
        scn.ngeom += 1
    for o, pts, z in state["hits"]:
        for i in range(0, len(pts), 4):
            if z[i] == 0 and i % 8:
                continue
            col = (1.0, 0.15, 0.1, 0.9) if z[i] == 2 else (1.0, 0.8, 0.1, 0.8) if z[i] == 1 else (0.35, 0.6, 0.75, 0.25)
            line(o, pts[i], col, 1.0)
    cx, cy = d.body("amr").xpos[:2]
    for rad, zl, base, hot in ((FIELDS["warn"], 1, (0.6, 0.5, 0.05, 0.8), (1.0, 0.85, 0.1, 1)), (FIELDS["prot"], 2, (0.6, 0.1, 0.08, 0.8), (1.0, 0.15, 0.1, 1))):
        a = np.linspace(0, 2 * math.pi, 73)
        col = hot if state["zone"] >= zl else base
        for i in range(72):
            line((cx + rad * math.cos(a[i]), cy + rad * math.sin(a[i]), 0.005), (cx + rad * math.cos(a[i + 1]), cy + rad * math.sin(a[i + 1]), 0.005), col, 2.5)
    if mission["state"] in ("look_A", "pick_A", "look_B", "insert_B"):
        for dt in vision.dets:                  # stime della visione nel mondo 3D
            z = Z_GRASP + 0.05 if dt["kind"] == "flacone" else BENCH_Z + FIX_H + 0.01
            dot((dt["xy"][0], dt["xy"][1], z), (0.2, 1.0, 0.45, 0.9) if dt["kind"] == "flacone" else (0.2, 0.7, 1.0, 0.9))


cam = mujoco.MjvCamera(); cam.distance = 3.2; cam.elevation = -26
writer = None
if args.video or args.preview:
    import cv2
    import imageio
    W, H = 1600, 900
    r = mujoco.Renderer(m, H, W)
    pano_r = mujoco.Renderer(m, 120, 240)
    wr = mujoco.Renderer(m, 108, 190)
    writer = imageio.get_writer(args.video, fps=30, quality=7, macro_block_size=8) if args.video else None

    def frame():
        b = d.body("amr").xpos
        cam.lookat[:] = 0.85 * np.array(cam.lookat) + 0.15 * np.array([b[0] * 0.6 - 0.6, b[1] * 0.6 + 0.4, 0.9])
        cam.azimuth = 215 + 15 * math.sin(d.time / 25)
        r.update_scene(d, cam); draw(r.scene)
        img = r.render().copy()
        vis = vision.render_overlay()
        if vis is not None:
            vis = cv2.resize(vis, (480, 300))
            img[20:320, W - 500:W - 20] = vis
            cv2.rectangle(img, (W - 502, 18), (W - 18, 322), (60, 220, 120), 2)
        for j, s_ in enumerate(("right", "left")):
            wr.update_scene(d, f"camera_wrist_{s_}"); wi = wr.render()
            x0 = W - 500 + j * 245
            img[335:443, x0:x0 + 190] = wi
            cv2.putText(img, f"polso {'dx' if s_ == 'right' else 'sx'}", (x0 + 5, 352), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        for i, txt in enumerate(hud_lines()):
            col = ZCOL[state["zone"]] if i == 2 else (235, 235, 240)
            cv2.putText(img, txt, (22, 38 + 30 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, txt, (22, 38 + 30 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.68, col, 2, cv2.LINE_AA)
        for i, txt in enumerate(mission["log"]):
            cv2.putText(img, txt, (22, H - 110 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, txt, (22, H - 110 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (250, 250, 250), 1, cv2.LINE_AA)
        return img

    cam.lookat[:] = [-1.2, 0.8, 0.9]
    t_next, wall0 = 0.0, time.time()
    while d.time < args.seconds and mission["state"] != "done" or (mission["state"] == "done" and d.time < mission.get("t_end", d.time + 3)):
        if mission["state"] == "done" and "t_end" not in mission:
            mission["t_end"] = d.time + 3.0
        control_step()
        if d.time >= t_next:
            t_next += 1 / 30
            if writer is not None:
                writer.append_data(frame())
        if args.preview and d.time > float(args.preview.split(":")[1]) if ":" in args.preview else False:
            break
    if writer is not None:
        writer.close(); print("video:", args.video)
elif args.record:
    import pickle
    geoms = []
    for g in range(m.ngeom):
        if m.geom_group[g] > 2 or (m.geom_rgba[g][3] == 0 and m.geom_matid[g] < 0):
            continue
        mat = m.material(m.geom_matid[g]).name if m.geom_matid[g] >= 0 else ""
        rgba = m.mat_rgba[m.geom_matid[g]] if m.geom_matid[g] >= 0 else m.geom_rgba[g]
        e = dict(name=m.geom(g).name, type=int(m.geom_type[g]), size=m.geom_size[g].copy(), body=int(m.geom_bodyid[g]),
                 pos=m.geom_pos[g].copy(), quat=m.geom_quat[g].copy(), mat=mat, rgba=np.array(rgba).copy(), body_name=m.body(m.geom_bodyid[g]).name)
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[g]
            e["vert"] = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]].copy()
            e["face"] = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]].copy()
        geoms.append(e)
    XP, XQ, ZONE, SIZES, EYE, ST = [], [], [], [], [], []
    hum = [m.geom(f"h{h}_{k}_g").id for h in range(HUMANS) for k in range(N_SEG)]
    t_next = 0.0
    while d.time < args.seconds and not (mission["state"] == "done" and mission["t"] > 2.0):
        control_step()
        if d.time >= t_next:
            t_next += 1 / 30
            XP.append(d.xpos.copy()); XQ.append(d.xquat.copy()); ZONE.append(state["zone"]); ST.append(mission["state"])
            SIZES.append(np.array([m.geom_size[g] for g in hum]) if hum else np.zeros((0, 3)))
            EYE.append(np.concatenate([np.r_[m.geom_pos[g], m.geom_size[g], m.geom_rgba[g][:3]] for g in EYES.values()]))
    pickle.dump(dict(geoms=geoms, xpos=np.array(XP), xquat=np.array(XQ), zone=np.array(ZONE), hum=hum, hum_sizes=np.array(SIZES),
                     eyes=np.array(EYE), states=ST, body_names=[m.body(i).name for i in range(m.nbody)], r_prot=R_PROT, r_warn=R_WARN,
                     stats=stats), open(args.record, "wb"))
    print(f"registrati {len(XP)} fotogrammi -> {args.record}", flush=True)
else:
    import mujoco.viewer
    with mujoco.viewer.launch_passive(m, d) as v:
        v.cam.lookat[:] = [-1.2, 0.8, 0.9]; v.cam.distance = 4.5; v.cam.azimuth = 215; v.cam.elevation = -30
        last = 0.0
        while v.is_running() and d.time < args.seconds:
            t0 = time.time()
            for _ in range(int((1 / 60) / DT)):
                control_step()
            with v.lock():
                v.user_scn.ngeom = 0
                draw(v.user_scn)
            v.set_texts([(mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPLEFT, "\n".join(hud_lines()), "")])
            if time.time() - last > 0.2:
                last = time.time()
                vis = vision.render_overlay()
                if vis is not None:
                    v.set_images([(mujoco.MjrRect(v.viewport.width - 650, v.viewport.height - 410, 640, 400), vis)])
            v.sync()
            time.sleep(max(0.0, 1 / 60 - (time.time() - t0)))
print(f"FINE t={d.time:.1f}s: inseriti {stats['inserted']}, falliti {stats['lost']}, viaggi {stats['trips']}, arresti {stats['stops']}, "
      f"errore visione medio {np.mean(stats['vis_err']) if stats['vis_err'] else 0:.1f} mm", flush=True)
