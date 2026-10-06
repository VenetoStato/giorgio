"""Giorgio-P in cella collaborativa: fisica vera (Newton + MuJoCo Warp), persone che passano, due laser scanner di sicurezza.

Giorgio (busto su colonna e base mobile, due braccia a 7 giunti con pinza) preleva pezzi dai vassoi di ingresso
e compone il kit al centro del banco. Due scanner di sicurezza 2D a 270 gradi sugli spigoli opposti della base
coprono 360 gradi a 18 cm da terra (come SICK microScan3 / Pilz PSENscan):
  - campo di AVVISO     -> velocita' ridotta (SLS, 30%)
  - campo di PROTEZIONE -> arresto controllato (SS1) e riavvio automatico 1 s dopo che il campo e' libero
La rilevazione usa solo i raggi: ogni raggio ha un contorno di riferimento appreso a cella vuota, e una persona
e' vista quando un raggio torna piu' corto del riferimento dentro un campo. L'operatore entra a cambiare i vassoi
(Giorgio si ferma), un passante attraversa la corsia (Giorgio rallenta).

uso: python giorgio_cell.py [--look eva|akira|gits|blame|cyber] [--speed 1] [--headless] [--video out.mp4] [--seconds 90]
"""
import argparse
import math
import os
import sys
import time

import numpy as np
import warp as wp
from scipy.spatial.transform import Rotation as Rot

sys.path.insert(0, os.path.expanduser("~/palletizer_demo"))
import newton  # noqa: E402
import newton.viewer  # noqa: E402
from core import DT, FPS, I, R_DOWN, SUB, VIS, Arm, Runner, Seg, contact_cfg, dsmooth, make_solver, smooth  # noqa: E402
from giorgio_urdf import EFFORT, arm_urdf  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--look", default="eva", choices=["eva", "akira", "gits", "blame", "cyber"])
ap.add_argument("--speed", type=int, default=1)
ap.add_argument("--headless", action="store_true")
ap.add_argument("--video", default="")
ap.add_argument("--preview", default="")
ap.add_argument("--seconds", type=float, default=1e9)
ap.add_argument("--no_humans", action="store_true")
args = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# ---------------------------------------------------------------- estetica
LOOKS = {   # corazza, accento (neon), giunti/"muscolo", visiera, luci ambiente
    "eva":   dict(armor=(0.34, 0.16, 0.52), accent=(0.45, 0.95, 0.15), joint=(0.10, 0.09, 0.12), visor=(1.0, 0.42, 0.05), neon=((0.9, 0.2, 0.9), (0.45, 0.95, 0.15))),
    "akira": dict(armor=(0.78, 0.06, 0.05), accent=(0.95, 0.95, 0.92), joint=(0.09, 0.09, 0.10), visor=(0.2, 0.9, 1.0), neon=((1.0, 0.15, 0.1), (0.2, 0.9, 1.0))),
    "gits":  dict(armor=(0.80, 0.77, 0.70), accent=(0.20, 0.55, 1.00), joint=(0.16, 0.17, 0.19), visor=(1.0, 0.15, 0.15), neon=((0.2, 0.55, 1.0), (0.1, 0.9, 0.7))),
    "blame": dict(armor=(0.30, 0.31, 0.32), accent=(0.85, 0.86, 0.82), joint=(0.05, 0.05, 0.06), visor=(0.92, 0.96, 1.0), neon=((0.7, 0.75, 0.8), (0.95, 0.5, 0.2))),
    "cyber": dict(armor=(0.07, 0.07, 0.08), accent=(0.98, 0.90, 0.08), joint=(0.20, 0.20, 0.22), visor=(0.1, 0.95, 0.95), neon=((0.98, 0.9, 0.08), (0.1, 0.95, 0.95))),
}
LK = LOOKS[args.look]

# ---------------------------------------------------------------- layout (robot rivolto verso +x)
SH_Z = 1.25                                  # quota spalle (colonna elevabile)
SH_Y = 0.24
BENCH_X0, BENCH_X1, BENCH_Z = 0.22, 0.82, 0.88
PART_R, PART_H, PART_M = 0.018, 0.06, 0.15   # pezzo cilindrico (es. boccola)
# per lato: 3 pezzi in ingresso (esterno) -> 3 posti nel kit (centro)
SLOTS_IN = [(0.31, 0.42), (0.39, 0.42), (0.35, 0.34)]
SLOTS_KIT = [(0.31, 0.14), (0.39, 0.14), (0.35, 0.07)]
BASE_HX, BASE_HY, BASE_H = 0.30, 0.26, 0.24
SCAN_Z = 0.18
SCANNERS = [((BASE_HX, -BASE_HY), -math.pi / 4), ((-BASE_HX, BASE_HY), 3 * math.pi / 4)]   # posizione, direzione centrale
SCAN_FOV, SCAN_N, SCAN_MAX = math.radians(270), 271, 8.0
R_WARN, R_PROT = 2.4, 1.15                    # [m] dal centro robot (ISO 13855: S = K*T + C, vedi README)

b = newton.ModelBuilder()
newton.solvers.SolverMuJoCo.register_custom_attributes(b)
b.add_ground_plane(cfg=contact_cfg(0.7), color=(0.06, 0.06, 0.075))
arms = []
for side in (-1, 1):
    urdf, GRASP = arm_urdf(side)
    a = Arm(b, urdf, f"giorgio_arm_{'r' if side < 0 else 'l'}", base_pos=(0.02, side * SH_Y, SH_Z), q_home=np.zeros(7),
            effort_ref=tuple(10 * e for e in EFFORT), vmax=[2.0] * 7, tip="tool0", recolor=False)
    a.side = side
    arms.append(a)
# colori per tipo di geometria: box = corazza, cilindri = attuatori, sfere = giunti (accento)
for i in range(b.shape_count):
    bi = b.shape_body[i]
    if bi < 0:
        continue
    lab = b.body_label[bi]
    if "finger" in lab:
        b.shape_color[i] = LK["accent"]
    elif "gripper" in lab:
        b.shape_color[i] = LK["joint"]
    elif "giorgio" in lab:
        gt = b.shape_type[i]
        b.shape_color[i] = LK["armor"] if gt == newton.GeoType.BOX else LK["accent"] if gt == newton.GeoType.SPHERE else LK["joint"]


def box(x, y, z, hx, hy, hz, col, cfg=VIS):
    return b.add_shape_box(-1, wp.transform(wp.vec3(x, y, z), I), hx=hx, hy=hy, hz=hz, cfg=cfg, color=col)


# corpo fisso: base mobile (AMR), colonna telescopica, busto
A, J, C = LK["armor"], LK["joint"], LK["accent"]
box(0, 0, BASE_H / 2 + 0.04, BASE_HX, BASE_HY, BASE_H / 2, J)
box(0, 0, BASE_H + 0.045, BASE_HX - 0.02, BASE_HY - 0.02, 0.005, A)
for sx in (-1, 1):                                                            # fascia luminosa
    box(sx * (BASE_HX + 0.002), 0, 0.17, 0.003, BASE_HY - 0.04, 0.012, C)
for sy in (-1, 1):
    b.add_shape_cylinder(-1, wp.transform(wp.vec3(0, sy * (BASE_HY - 0.02), 0.08), wp.quat_from_axis_angle(wp.vec3(1, 0, 0), math.pi / 2)),
                         radius=0.08, half_height=0.03, cfg=VIS, color=(0.03, 0.03, 0.03))
for (sx, sy), _ in SCANNERS:                                                  # scanner (giallo sicurezza)
    b.add_shape_cylinder(-1, wp.transform(wp.vec3(sx, sy, SCAN_Z), I), radius=0.05, half_height=0.045, cfg=VIS, color=(0.95, 0.8, 0.05))
box(-0.02, 0, 0.62, 0.09, 0.09, 0.38, A)                                      # colonna: stadio basso
box(-0.02, 0, 1.0, 0.07, 0.07, 0.12, J)                                       # stadio alto
box(0.0, 0, 1.13, 0.10, 0.13, 0.07, J)                                        # bacino/vita
box(0.0, 0, 1.30, 0.12, 0.20, 0.12, A)                                        # torace
box(0.115, 0, 1.31, 0.012, 0.13, 0.08, J)                                     # placca petto
box(0.128, 0, 1.31, 0.002, 0.10, 0.006, C)                                    # linea luminosa
b.add_shape_sphere(-1, wp.transform(wp.vec3(0.13, 0, 1.36), I), radius=0.035, cfg=VIS, color=(0.9, 0.1, 0.1))  # "core" (EVA)
box(0.0, 0, 1.44, 0.04, 0.04, 0.03, J)                                        # collo
for sy in (-1, 1):
    box(0.02, sy * (SH_Y - 0.05), SH_Z + 0.06, 0.08, 0.06, 0.035, A)          # spallacci fissi

# banco
BC = (0.11, 0.115, 0.13)
box((BENCH_X0 + BENCH_X1) / 2, 0, BENCH_Z - 0.02, (BENCH_X1 - BENCH_X0) / 2, 0.85, 0.02, BC, contact_cfg(0.6, 5.0))
for x in (BENCH_X0 + 0.04, BENCH_X1 - 0.04):
    for y in (-0.8, 0.8):
        box(x, y, (BENCH_Z - 0.04) / 2, 0.025, 0.025, (BENCH_Z - 0.04) / 2, (0.2, 0.2, 0.22))
box(BENCH_X1 - 0.005, 0, BENCH_Z - 0.035, 0.004, 0.85, 0.006, LK["neon"][0])  # bordo neon
TRAY_IN, TRAY_KIT = (0.08, 0.10, 0.12), (0.03, 0.03, 0.035)
for side in (-1, 1):
    box(0.35, side * 0.39, BENCH_Z + 0.002, 0.075, 0.08, 0.002, TRAY_IN)
    box(0.35, side * 0.105, BENCH_Z + 0.002, 0.075, 0.075, 0.002, TRAY_KIT)
    box(0.35, side * 0.105 + 0.077, BENCH_Z + 0.003, 0.075, 0.002, 0.003, C)

# ambiente: pilastri con fasce neon, scaffale, recinzione bassa sul retro
for k, (px, py) in enumerate([(-2.8, -3.2), (2.6, -3.2), (-2.8, 3.4), (2.6, 3.4)]):
    box(px, py, 2.0, 0.2, 0.2, 2.0, (0.08, 0.08, 0.09))
    for zz in (0.9, 2.3, 3.4):
        box(px + 0.202, py, zz, 0.003, 0.15, 0.03, LK["neon"][k % 2])
for x in np.arange(-2.4, 2.41, 1.2):                                          # scaffale sul fondo (y = 3.0)
    box(x, 3.0, 1.0, 0.58, 0.25, 0.01, (0.15, 0.15, 0.17))
    box(x, 3.0, 1.8, 0.58, 0.25, 0.01, (0.15, 0.15, 0.17))
    box(x - 0.58, 3.0, 1.1, 0.02, 0.25, 1.1, (0.2, 0.2, 0.22))
    for bx in (-0.3, 0.1, 0.35):
        box(x + bx, 3.0, 1.15, 0.12, 0.18, 0.14, (0.35, 0.27, 0.18))
for y in np.arange(-2.5, 2.51, 0.5):                                          # segnaletica a terra: corsia
    box(-2.0, y, 0.002, 0.04, 0.18, 0.002, (0.9, 0.75, 0.05))

# pezzi
parts, part_shape, part_side = [], [], []
dens = PART_M / (math.pi * PART_R ** 2 * PART_H)
for side in (-1, 1):
    for x, y in SLOTS_IN:
        body = b.add_body(xform=wp.transform(wp.vec3(x, side * y, BENCH_Z + PART_H / 2 + 0.001), I))
        part_shape.append(b.shape_count)
        b.add_shape_cylinder(body, radius=PART_R, half_height=PART_H / 2, cfg=contact_cfg(0.8, 30.0, density=dens), color=(0.75, 0.77, 0.8))
        parts.append(body); part_side.append(side)

m = b.finalize()
pipe, solver, contacts = make_solver(m, 4000)
s0, s1, ctl = m.state(), m.state(), m.control()
newton.eval_fk(m, s0.joint_q, s0.joint_qd, s0)

# ---------------------------------------------------------------- viewer
if args.video or args.preview:
    viewer = newton.viewer.ViewerGL(width=1600, height=900, headless=True)
elif args.headless:
    viewer = newton.viewer.ViewerNull(num_frames=10 ** 9)
else:
    viewer = newton.viewer.ViewerGL(width=1700, height=950)
viewer.set_model(m)
if isinstance(viewer, newton.viewer.ViewerGL):
    viewer.set_camera(wp.vec3(3.3, -2.9, 2.3), -24.0, 140.0)
    r = viewer.renderer
    r.sky_upper, r.sky_lower = (0.02, 0.02, 0.05), (0.06, 0.03, 0.09)
    r.ambient_sky, r.ambient_ground = (0.55, 0.5, 0.75), (0.25, 0.15, 0.3)
    r._light_color = (1.0, 0.92, 0.95)
    r.line_width = 2.0


# ---------------------------------------------------------------- persone (animate, solo grafica: la fisica non le "vede")
class Person:
    def __init__(self, path, speed, vest, waits=None, t0=0.0, loop=True):
        self.path = [np.array(p, float) for p in path]
        self.speed, self.vest, self.waits, self.t0, self.loop = speed, vest, waits or {}, t0, loop
        self.pos, self.yaw, self.phase, self.moving = self.path[0].copy(), 0.0, 0.0, False
        self.i, self.tw, self.active = 0, 0.0, False

    def step(self, t, dt):
        if t < self.t0:
            self.active = False
            return
        self.active = True
        if self.tw > 0:
            self.tw -= dt; self.moving = False
            return
        nxt = self.path[(self.i + 1) % len(self.path)]
        d = nxt - self.pos
        dist = np.linalg.norm(d)
        step = self.speed * dt
        self.moving = True
        if dist <= step:
            self.pos = nxt.copy(); self.i = (self.i + 1) % len(self.path)
            self.tw = self.waits.get(self.i, 0.0)
            if self.i == 0 and not self.loop:
                self.t0 = 1e9
        else:
            self.pos += d / dist * step
            self.yaw = math.atan2(d[1], d[0])
        self.phase += step / 0.75 * math.pi

    def capsules(self):
        """(centro, asse, raggio, semi-lunghezza, colore) dei segmenti del corpo"""
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        fwd, lat = np.array([c, s, 0]), np.array([-s, c, 0])
        sw = 0.42 * math.sin(self.phase) if self.moving else 0.0
        P = np.array([self.pos[0], self.pos[1], 0.0])
        out = []
        dark, skin = (0.08, 0.08, 0.1), (0.75, 0.6, 0.5)
        for k, sg in ((1, 1), (-1, -1)):
            hip = P + lat * 0.1 * k + np.array([0, 0, 0.92])
            ang = sw * sg
            axis = -math.cos(ang) * np.array([0, 0, 1.0]) + math.sin(ang) * fwd
            out.append((hip + axis * 0.42, axis, 0.075, 0.36, dark))                 # gamba
            sh = P + lat * 0.22 * k + np.array([0, 0, 1.45])
            axa = -math.cos(-0.7 * ang) * np.array([0, 0, 1.0]) + math.sin(-0.7 * ang) * fwd
            out.append((sh + axa * 0.3, axa, 0.05, 0.26, self.vest if k > 0 else dark))  # braccio
        out.append((P + np.array([0, 0, 1.22]), np.array([0, 0, 1.0]), 0.17, 0.16, self.vest))   # busto (gilet alta visibilita')
        out.append((P + np.array([0, 0, 1.66]), np.array([0, 0, 1.0]), 0.105, 0.03, skin))       # testa
        out.append((P + np.array([0, 0, 1.77]) - fwd * 0.01, np.array([0, 0, 1.0]), 0.115, 0.0, (0.95, 0.95, 0.95)))  # casco
        return out

    def legs_at(self, z):
        """centri delle gambe alla quota z (per i raggi degli scanner)"""
        return [(c + a * ((z - c[2]) / a[2]))[:2] for c, a, r, h, _ in self.capsules()[:4:2]]


ORANGE, YELLOW = (1.0, 0.45, 0.05), (0.85, 0.95, 0.1)
people = [] if args.no_humans else [
    # operatore: dal fondo entra fino al banco (lato opposto a Giorgio), cambia i vassoi, riparte
    Person([(-1.6, 3.6), (-1.6, 1.4), (1.25, 0.9), (1.25, 0.0), (1.25, 0.9), (-1.6, 1.4)], 1.1, ORANGE, waits={3: 6.0}, t0=26.0),
    # passante sulla corsia (x = -2.0): non entra nel campo di protezione
    Person([(-2.0, -4.5), (-2.0, 4.5)], 1.3, YELLOW, t0=8.0),
]

# ---------------------------------------------------------------- scanner di sicurezza (raycast 2D sulla scena)
STATIC = []                                                    # ostacoli fissi a quota scanner (gambe banco, pilastri)
for x in (BENCH_X0 + 0.04, BENCH_X1 - 0.04):
    for y in (-0.8, 0.8):
        STATIC.append((x - 0.025, y - 0.025, x + 0.025, y + 0.025))
for px, py in [(-2.8, -3.2), (2.6, -3.2), (-2.8, 3.4), (2.6, 3.4)]:
    STATIC.append((px - 0.2, py - 0.2, px + 0.2, py + 0.2))
STATIC.append((-3.0, 2.75, 3.0, 3.25))                         # scaffale (montanti/bancali bassi)


def scan_dirs(heading):
    a = heading + np.linspace(-SCAN_FOV / 2, SCAN_FOV / 2, SCAN_N)
    return np.stack([np.cos(a), np.sin(a)], 1)


SC = [(np.array(p, float), scan_dirs(h)) for p, h in SCANNERS]


def raycast(o, D, circles):
    t = np.full(len(D), SCAN_MAX)
    with np.errstate(divide="ignore", invalid="ignore"):
        for x0, y0, x1, y1 in STATIC:                          # slab test
            tx0, tx1 = (x0 - o[0]) / D[:, 0], (x1 - o[0]) / D[:, 0]
            ty0, ty1 = (y0 - o[1]) / D[:, 1], (y1 - o[1]) / D[:, 1]
            tn = np.maximum(np.minimum(tx0, tx1), np.minimum(ty0, ty1))
            tf = np.minimum(np.maximum(tx0, tx1), np.maximum(ty0, ty1))
            hit = (tf >= tn) & (tn > 0)
            t = np.where(hit, np.minimum(t, tn), t)
    for c, rad in circles:
        oc = o - c
        bq = D @ oc
        disc = bq ** 2 - (oc @ oc - rad ** 2)
        th = -bq - np.sqrt(np.maximum(disc, 0))
        t = np.where((disc > 0) & (th > 0), np.minimum(t, th), t)
    return t


REF = [raycast(o, D, []) for o, D in SC]                       # contorno di riferimento (cella vuota, teach-in)


def safety_scan():
    circles = [(c, 0.075) for p in people if p.active for c in p.legs_at(SCAN_Z)]
    hits, zone = [], 0
    for (o, D), ref in zip(SC, REF):
        tr = raycast(o, D, circles)
        pts = o + D * tr[:, None]
        intr = tr < ref - 0.05                                  # qualcosa di nuovo davanti al contorno appreso
        dc = np.linalg.norm(pts, axis=1)
        z = np.where(intr & (dc < R_PROT), 2, np.where(intr & (dc < R_WARN), 1, 0))
        zone = max(zone, int(z.max()))
        hits.append((o, pts, z))
    return zone, hits


# ---------------------------------------------------------------- compito: kitting a due mani
OPEN_F, CLOSE_F = 0.032, PART_R - 0.006
APP = 0.12
READY = []


def flange(xy, side, dz=0.0):
    return np.array([xy[0], side * xy[1], BENCH_Z + max(PART_H / 2, 0.03) + GRASP + dz])


def solve_multi(a, p, R, q0):
    """IK su 7 giunti: piu' semi, tiene la soluzione valida piu' vicina alla postura attuale"""
    rng = np.random.default_rng(int(1000 * abs(p[0] + p[1])))
    p_loc, R_loc = a.Rb.T @ (p - a.base), a.Rb.T @ R
    best = None
    for k in range(24):
        seed = q0 if k == 0 else np.clip(q0 + rng.normal(0, 0.5 + 0.05 * k, 7), a.chain.lower, a.chain.upper)
        q, ok = a._solve1(p_loc, R_loc, seed, q0, 150)
        if ok:
            cost = float(np.sum(np.abs(q - q0)) + 0.3 * np.sum(np.abs(q[4:])))
            if best is None or cost < best[0]:
                best = (cost, q)
    if best is None:
        raise RuntimeError(f"punto non raggiungibile {np.round(p, 3)}")
    return best[1]


def cart_solve(self, p, R, q0=None, iters=60, multi=False):     # passi cartesiani: IK dalla postura corrente
    q0 = self.q_ref if q0 is None else np.asarray(q0, float)
    return self._solve1(self.Rb.T @ (np.asarray(p, float) - self.base), self.Rb.T @ R, q0, q0, iters)[0]


Arm.solve = cart_solve


class SafeRunner(Runner):
    """Runner con override di velocita' k (0..1) comandato dalla sicurezza"""
    k = 1.0

    def step(self, on_event):
        if not self.segs:
            self.arm.qd_ref = np.zeros(self.arm.n)
            return
        sg = self.segs[self.i]
        self.t += self.k / FPS
        u = min(self.t / sg.dur, 1.0)
        a = self.arm
        if sg.kind == "joint":
            a.q_ref = sg.a + (sg.b - sg.a) * smooth(u)
            a.qd_ref = (sg.b - sg.a) * dsmooth(u) / sg.dur * self.k
        elif sg.kind == "cart":
            p = np.asarray(sg.a) + (np.asarray(sg.b) - sg.a) * smooth(u)
            qn = a.solve(p, sg.R)
            a.qd_ref = (qn - a.q_ref) * FPS
            a.q_ref = qn
        else:
            a.qd_ref = np.zeros(a.n)
        if u >= 1.0:
            if sg.ev:
                on_event(a, sg.ev)
            self.i, self.t = self.i + 1, 0.0
            if self.i >= len(self.segs):
                self.segs = []


R_G = R_DOWN                                                  # pinza verso il basso, dita che chiudono lungo y
for a in arms:
    q_ready = solve_multi(a, flange((0.33, 0.27), a.side, 0.16), R_G, np.array([-0.8, -0.2 * a.side, 0, -1.3, 0, -0.5, 0]))
    a.q_ready = q_ready
    a.set_state(s0, q_ready)
    a.q_home = q_ready
newton.eval_fk(m, s0.joint_q, s0.joint_qd, s0)
runners = [SafeRunner(a) for a in arms]
st = {a.side: {"n": 0, "held": -1} for a in arms}
stats = {"placed": 0, "lost": 0, "kits": 0, "stops": 0, "slow_s": 0.0, "stop_s": 0.0}


def plan_pick(a, n):
    side = a.side
    pa, pb = SLOTS_IN[n], SLOTS_KIT[n]
    up_a, dn_a = flange(pa, side, APP), flange(pa, side)
    up_b, dn_b = flange(pb, side, APP), flange(pb, side, 0.003)
    q1 = solve_multi(a, up_a, R_G, a.q_ref)
    q2 = solve_multi(a, up_b, R_G, q1)
    t1, t2 = a.move_time(a.q_ref, q1, 0.9), a.move_time(q1, q2, 0.9)
    return [Seg("joint", a.q_ref.copy(), q1, t1), Seg("cart", up_a, dn_a, 0.5, R=R_G), Seg("wait", dur=0.3, ev="close"),
            Seg("wait", dur=0.25), Seg("cart", dn_a, up_a, 0.45, R=R_G), Seg("joint", q1, q2, t2),
            Seg("cart", up_b, dn_b, 0.5, R=R_G), Seg("wait", dur=0.25, ev="open"), Seg("wait", dur=0.2),
            Seg("cart", dn_b, up_b, 0.4, R=R_G, ev="placed")]


def part_index(side, n):
    return (0 if side < 0 else 3) + n


def on_event(a, e):
    sd = st[a.side]
    if e == "close":
        a.finger_target = CLOSE_F; a.payload = PART_M
    elif e == "open":
        a.finger_target = OPEN_F; a.payload = 0.0
    elif e == "placed":
        k = part_index(a.side, sd["n"])
        pp = s0.body_q.numpy()[parts[k], :3]
        tgt = np.array([SLOTS_KIT[sd["n"]][0], a.side * SLOTS_KIT[sd["n"]][1]])
        err = 1000 * np.linalg.norm(pp[:2] - tgt)
        ok = err < 15 and abs(pp[2] - (BENCH_Z + PART_H / 2)) < 0.01
        stats["placed" if ok else "lost"] += 1
        print(f"[t={t:6.1f}s] braccio {'dx' if a.side < 0 else 'sx'}: pezzo {sd['n'] + 1}/3 {'nel kit' if ok else 'PERSO'}"
              f" (errore {err:.1f} mm)", flush=True)
        sd["n"] += 1


def go_ready(a):
    return [Seg("joint", a.q_ref.copy(), a.q_ready, a.move_time(a.q_ref, a.q_ready, 0.9))]


def swap_trays():
    """l'operatore porta via il kit completo e rimette 3+3 pezzi grezzi nei vassoi di ingresso"""
    jq, jqd = s0.joint_q.numpy(), s0.joint_qd.numpy()
    qs, qds = m.joint_q_start.numpy(), m.joint_qd_start.numpy()
    for k, body in enumerate(parts):
        side, n = part_side[k], k % 3
        j = list(m.joint_child.numpy()).index(body)
        jq[qs[j]:qs[j] + 7] = [SLOTS_IN[n][0], side * SLOTS_IN[n][1], BENCH_Z + PART_H / 2 + 0.001, 0, 0, 0, 1]
        jqd[qds[j]:qds[j] + 6] = 0
    s0.joint_q.assign(jq); s0.joint_qd.assign(jqd)
    newton.eval_fk(m, s0.joint_q, s0.joint_qd, s0)
    for sd in st.values():
        sd["n"] = 0
    stats["kits"] += 1
    print(f"[t={t:6.1f}s] operatore: kit {stats['kits']} ritirato, vassoi ricaricati", flush=True)


# ---------------------------------------------------------------- HUD
hud = {"zone": 0, "k": 1.0, "txt": ""}
ZN = ["LIBERO - velocita' piena", "AVVISO - velocita' ridotta 30%", "PROTEZIONE - arresto SS1"]
ZC = [(0.3, 1.0, 0.4, 1.0), (1.0, 0.85, 0.1, 1.0), (1.0, 0.2, 0.2, 1.0)]


def ui(imgui):
    imgui.text_colored(imgui.ImVec4(*LK["accent"], 1.0), f"GIORGIO-P  //  look: {args.look}")
    imgui.text_colored(imgui.ImVec4(*ZC[hud["zone"]]), f"SCANNER: {ZN[hud['zone']]}")
    imgui.text(f"override velocita': {100 * hud['k']:.0f}%")
    imgui.text(f"pezzi nel kit: {stats['placed']}  persi: {stats['lost']}  kit ritirati: {stats['kits']}")
    imgui.text(f"arresti: {stats['stops']}  tempo rallentato: {stats['slow_s']:.0f}s  fermo: {stats['stop_s']:.0f}s")


if isinstance(viewer, newton.viewer.ViewerGL) and not (args.video or args.preview):
    viewer.register_ui_callback(ui, "side")


def circle(rad, n=96, z=0.004):
    a = np.linspace(0, 2 * math.pi, n + 1)
    p = np.stack([rad * np.cos(a), rad * np.sin(a), np.full_like(a, z)], 1)
    return p[:-1], p[1:]


def v3(x):
    return wp.array(np.asarray(x, np.float32), dtype=wp.vec3)


def draw_overlay(hits):
    st_, en_, co_ = [], [], []
    for o, pts, z in hits:                                      # raggi (uno ogni 3), rossi se vedono un'intrusione
        for i in range(0, len(pts), 3):
            st_.append((o[0], o[1], SCAN_Z)); en_.append((pts[i, 0], pts[i, 1], SCAN_Z))
            co_.append((1.0, 0.15, 0.1) if z[i] == 2 else (1.0, 0.8, 0.1) if z[i] == 1 else (0.1, 0.55, 0.65))
    zone = hud["zone"]
    for rad, zl, base in ((R_WARN, 1, (0.6, 0.5, 0.05)), (R_PROT, 2, (0.6, 0.1, 0.08))):
        a_, b_ = circle(rad)
        col = (1.0, 0.85, 0.1) if (zone >= zl and zl == 1) else (1.0, 0.15, 0.1) if zone == 2 and zl == 2 else base
        st_ += a_.tolist(); en_ += b_.tolist(); co_ += [col] * len(a_)
    viewer.log_lines("/scan", v3(st_), v3(en_), v3(co_))
    # persone
    caps = [cp for p in people if p.active for cp in p.capsules()]
    if caps:
        xf, sc, cl = [], [], []
        for c, ax, rad, hh, col in caps:
            q = Rot.align_vectors([ax], [[0, 0, 1.0]])[0].as_quat() if hh > 0 else np.array([0, 0, 0, 1.0])
            xf.append(wp.transform(wp.vec3(*c), wp.quat(*q))); sc.append((rad, rad, max(hh, 1e-3))); cl.append(col)
        viewer.log_capsules("/people", None, wp.array(xf, dtype=wp.transform), v3(sc), v3(cl), None)
    else:
        viewer.log_capsules("/people", None, None, None, None, None, hidden=True)
    # testa di Giorgio: guarda la persona piu' vicina, altrimenti le mani
    near = [p.pos for p in people if p.active and np.linalg.norm(p.pos) < R_WARN + 0.5]
    tgt = min(near, key=np.linalg.norm) if near else np.array([0.5, 0.0])
    yaw = math.atan2(tgt[1], tgt[0])
    pitch = -0.35 if not near else 0.05
    qh = Rot.from_euler("zy", [yaw, -pitch])
    hc = np.array([0.0, 0.0, 1.56])
    parts_h = [((0, 0, 0), (0.085, 0.075, 0.075), A), ((0.075, 0, 0.005), (0.02, 0.07, 0.022), LK["visor"]),
               ((0.0, 0, 0.09), (0.02, 0.02, 0.03), C)]
    xf, sc, cl = [], [], []
    for off, half, col in parts_h:
        xf.append(wp.transform(wp.vec3(*(hc + qh.apply(off))), wp.quat(*qh.as_quat()))); sc.append(half); cl.append(col)
    for k_, (off, half, col) in enumerate(parts_h):
        viewer.log_shapes(f"/head{k_}", newton.GeoType.BOX, half, wp.array([xf[k_]], dtype=wp.transform), v3([col]))
    # corno (EVA-01): box inclinato in avanti
    qhorn = qh * Rot.from_euler("y", 0.6)
    viewer.log_shapes("/horn", newton.GeoType.BOX, (0.012, 0.01, 0.07),
                      wp.array([wp.transform(wp.vec3(*(hc + qh.apply((0.06, 0, 0.1)))), wp.quat(*qhorn.as_quat()))], dtype=wp.transform),
                      v3([LK["visor"] if args.look != "eva" else (0.95, 0.9, 0.85)]))


# ---------------------------------------------------------------- ciclo
writer = None
if args.video:
    import imageio
    writer = imageio.get_writer(args.video, fps=30, quality=8, macro_block_size=8)
if args.preview:
    for p in people:
        p.t0 = 0.0
    people[0].pos = np.array([1.25, 0.6]) if people else None
    for p in people:
        p.active = True
    zone, hits = safety_scan(); hud["zone"] = zone
    for _ in range(3):
        viewer.begin_frame(0.0); viewer.log_state(s0); draw_overlay(hits); viewer.end_frame()
    import imageio
    imageio.imwrite(args.preview, viewer.get_frame().numpy()[..., :3], quality=92)
    print("anteprima:", args.preview); raise SystemExit

t, wall0, clear_t, k_cmd = 0.0, time.time(), 0.0, 1.0
waiting_swap = False
frame_i = 0
while viewer.is_running() and t < args.seconds:
    for _ in range(args.speed):
        for p in people:
            p.step(t, 1.0 / FPS)
        zone, hits = safety_scan()
        # logica di sicurezza: SS1 su protezione, SLS su avviso, riavvio automatico dopo 1 s di campo libero
        if zone == 2:
            if hud["zone"] != 2 and k_cmd > 0:
                stats["stops"] += 1
                print(f"[t={t:6.1f}s] SCANNER: intrusione nel campo di protezione -> arresto", flush=True)
            k_cmd, clear_t = 0.0, 0.0
        else:
            clear_t += 1.0 / FPS
            if clear_t > 1.0 or k_cmd > 0:
                k_cmd = 0.3 if zone == 1 else 1.0
        hud["zone"] = zone
        # rampa di decelerazione/accelerazione (SS1: ~0.3 s a zero)
        k = hud["k"]
        k = max(k_cmd, k - 1.0 / (0.3 * FPS)) if k_cmd < k else min(k_cmd, k + 1.0 / (0.6 * FPS))
        hud["k"] = k
        stats["slow_s"] += (1.0 / FPS) if 0 < k_cmd < 1 else 0.0
        stats["stop_s"] += (1.0 / FPS) if k_cmd == 0 else 0.0
        # compito
        for a, rn in zip(arms, runners):
            rn.k = k
            sd = st[a.side]
            if not rn.busy:
                if sd["n"] < 3:
                    rn.start(plan_pick(a, sd["n"]))
                elif np.linalg.norm(a.q_ref - a.q_ready) > 1e-3:
                    rn.start(go_ready(a))
            rn.step(on_event)
            a.control(s0, ctl)
        # l'operatore cambia i vassoi quando e' fermo al banco e il kit e' completo
        op = people[0] if people else None
        done = all(sd["n"] >= 3 for sd in st.values()) and not any(rn.busy for rn in runners)
        if op is not None and op.active and op.tw > 0 and np.linalg.norm(op.pos - [1.25, 0.0]) < 0.05 and done and k == 0.0:
            swap_trays()
        if op is None and done:
            swap_trays()
        for _ in range(SUB):
            pipe.collide(s0, contacts); solver.step(s0, s1, ctl, contacts, DT); s0, s1 = s1, s0
        t += 1.0 / FPS
    viewer.begin_frame(t); viewer.log_state(s0); draw_overlay(hits); viewer.end_frame()
    if writer is not None and frame_i % 2 == 0:
        img = viewer.get_frame().numpy()[..., :3].copy()
        writer.append_data(img)
    frame_i += 1
    if args.headless and frame_i % (5 * FPS) == 0:
        print(f"[t={t:6.1f}s] zona {zone} k={k:.2f} kit={stats['kits']} pezzi={stats['placed']} (wall {time.time() - wall0:.0f}s)", flush=True)

if writer is not None:
    writer.close(); print("video:", args.video)
print(f"FINE t={t:.1f}s: pezzi nel kit {stats['placed']}, persi {stats['lost']}, kit {stats['kits']}, arresti {stats['stops']}, "
      f"rallentato {stats['slow_s']:.0f}s, fermo {stats['stop_s']:.0f}s", flush=True)
viewer.close()
