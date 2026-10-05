"""Giorgio-P (componenti reali) in cella collaborativa - MuJoCo 3.8 (stesso motore di Newton/SolverMuJoCo).

Robot: AgileX Tracer 2.0 + colonna + busto e braccia Enactic OpenArm 2.0 (MJCF ufficiale, motori Damiao con
coppie reali e compensazione di gravita' dentro i limiti) + mani Inspire RH56DFTP + RealSense D435i (testa) e
D405 (polsi) + 2 SICK nanoScan3.
Compito: kitting a due mani di flaconi (Ø50 x 160 mm, 0.35 kg) tenuti SOLO per attrito delle dita.
Sicurezza: i due scanner fanno raycast vero sulla scena (mj_multiRay) contro un contorno appreso a cella vuota;
campo di avviso -> velocita' ridotta, campo di protezione (ISO 13855) -> arresto SS1, riavvio automatico.

uso: python giorgio_real.py [--look eva|akira|gits|blame|cyber] [--video out.mp4 --seconds 90] [--no_humans]
"""
import argparse
import math
import time

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation as Rot

from giorgio_ik import ArmIK
from giorgio_model import DRIVE_HALF_TRACK, DRIVE_WHEEL_R, GROUP_ENV, GROUP_HUMAN, LOOKS, SCAN_Z, SCANNERS, build

ap = argparse.ArgumentParser()
ap.add_argument("--look", default="gb", choices=list(LOOKS))
ap.add_argument("--base", default="amr", choices=["cart", "amr"])
ap.add_argument("--video", default="")
ap.add_argument("--preview", default="")
ap.add_argument("--seconds", type=float, default=1e9)
ap.add_argument("--no_humans", action="store_true")
ap.add_argument("--hands", default="gripper", choices=["gripper", "inspire", "leap"],
                help="gripper = pinza originale OpenArm 2.0 (default); inspire = mani RH56DFTP (presa sperimentale)")
ap.add_argument("--debug", action="store_true")
ap.add_argument("--record", default="", help="registra geometria + pose a 30 fps (npz) per il render in Blender")
ap.add_argument("--no_cams", action="store_true")
ap.add_argument("--close", action="store_true", help="inquadratura ravvicinata sulla mano destra")
args = ap.parse_args()
LK = LOOKS[args.look]
LIGHT = LK.get("light", False)

# ---------------------------------------------------------------- cella
BENCH_Z, BENCH_X0, BENCH_X1, BENCH_HY = 0.90, 0.16, 0.80, 0.85
PR, PH, PM = 0.025, 0.16, 0.35                        # flacone
ZC = BENCH_Z + PH / 2                                  # quota centro pezzo
if args.hands in ("gripper", "leap"):                    # zone raggiunte (mappa IK)
    SLOTS_IN = [(0.30, 0.24), (0.30, 0.17)]
    SLOTS_KIT = [(0.38, 0.08), (0.38, 0.15)]
else:
    SLOTS_IN = [(0.30, 0.24), (0.33, 0.17)]
    SLOTS_KIT = [(0.31, 0.06), (0.37, 0.11)]
# ISO 13855 (scanner orizzontale a H=180 mm): S = K*T + C, K=1600 mm/s, T = 70 ms scanner + 300 ms SS1 dei bracci,
# C = 1200 - 0.4*H = 1128 mm  ->  S ~ 1.72 m dal bordo della macchina (qui: dal centro robot, conservativo)
R_PROT = (1600 * 0.37 + 1128) / 1000
R_WARN = R_PROT + 1.1

MOBILE = args.base == "amr"
sp = build(args.look, hands=args.hands, base=args.base, fixed_base=not MOBILE)
wb = sp.worldbody


def box(name, pos, half, material, group=GROUP_ENV, collide=True, body=None):
    g = (body or wb).add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material, group=group)
    if not collide:
        g.contype = g.conaffinity = 0
    else:
        g.conaffinity = 3                                  # bit 2: toccabile dalle mani
    return g


box("bench_top", ((BENCH_X0 + BENCH_X1) / 2, 0, BENCH_Z - 0.02), ((BENCH_X1 - BENCH_X0) / 2, BENCH_HY, 0.02), "bench")
for x in (BENCH_X0 + 0.03, BENCH_X1 - 0.03):
    for y in (-BENCH_HY + 0.05, BENCH_HY - 0.05):
        box(f"leg_{x:.2f}_{y:.2f}", (x, y, (BENCH_Z - 0.04) / 2), (0.025, 0.025, (BENCH_Z - 0.04) / 2), "steel")
box("bench_neon", (BENCH_X1 + 0.001, 0, BENCH_Z - 0.03), (0.002, BENCH_HY, 0.006), "accent" if LIGHT else "neon0", collide=False)
for sg in (-1, 1):
    xi, yi = np.mean(SLOTS_IN, 0); xk, yk = np.mean(SLOTS_KIT, 0)
    box(f"tray_in{sg}", (xi, sg * yi, BENCH_Z + 0.001), (0.05, 0.075, 0.001), "tray", collide=False)
    box(f"tray_kit{sg}", (xk, sg * yk, BENCH_Z + 0.001), (0.05, 0.075, 0.001), "tray", collide=False)
    box(f"tray_kit_line{sg}", (xk - 0.052, sg * yk, BENCH_Z + 0.002), (0.002, 0.075, 0.002), "accent", collide=False)

for k, (px, py) in enumerate([] if LIGHT else [(-2.8, -3.2), (2.6, -3.2), (-2.8, 3.4), (2.6, 3.4)]):
    box(f"pillar{k}", (px, py, 2.0), (0.2, 0.2, 2.0), "dark")
    for j, zz in enumerate((0.9, 2.3, 3.4)):
        box(f"pneon{k}_{j}", (px + 0.202, py, zz), (0.003, 0.15, 0.03), f"neon{k % 2}", collide=False)
for i, x in enumerate(np.arange(-2.4, 2.41, 1.2)):
    box(f"shelf_a{i}", (x, 3.0, 1.0), (0.58, 0.25, 0.01), "steel" if LIGHT else "dark")
    box(f"shelf_b{i}", (x, 3.0, 1.8), (0.58, 0.25, 0.01), "steel" if LIGHT else "dark")
    box(f"shelf_p{i}", (x - 0.58, 3.0, 1.1), (0.02, 0.25, 1.1), "steel")
for i, y in enumerate(np.arange(-2.5, 2.51, 0.5)):
    box(f"aisle{i}", (-2.2, y, 0.002), (0.04, 0.18, 0.002), "yellow", collide=False)

parts = []
for sg, s in ((-1, "right"), (1, "left")):
    for n, (x, y) in enumerate(SLOTS_IN):
        b = wb.add_body(name=f"part_{s}_{n}", pos=[x, sg * y, ZC + 0.001])
        b.add_freejoint(name=f"part_{s}_{n}_free")
        b.add_geom(name=f"part_{s}_{n}_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[PR, PH / 2, 0], mass=PM,
                   material="part", friction=[1.0, 0.02, 0.002], condim=4, group=GROUP_ENV, conaffinity=3)
        b.add_geom(name=f"part_{s}_{n}_cap", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, PH / 2 + 0.006], size=[0.012, 0.006, 0],
                   material="accent", mass=0.005, contype=0, conaffinity=0, group=GROUP_ENV)
        parts.append((s, n, b.name))

# persone: ogni segmento e' un corpo mocap (solo visivo + visto dagli scanner, gruppo 1)
N_SEG = 7
HUMANS = 0 if args.no_humans else 2
for h in range(HUMANS):
    for k in range(N_SEG):
        b = wb.add_body(name=f"h{h}_{k}", mocap=True, pos=[0, 0, -10])
        b.add_geom(name=f"h{h}_{k}_g", type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[0.05, 0.1, 0], contype=0, conaffinity=0,
                   group=GROUP_HUMAN, rgba=[0.5, 0.5, 0.5, 1])

m = sp.compile()
d = mujoco.MjData(m)
if MOBILE:
    # base libera: niente gravcomp "dal cielo"; la compensazione di gravita' la fanno i motori (entro la coppia massima)
    m.body_gravcomp[:] = 0
    GC_DOFS = [m.jnt_dofadr[j] for j in range(m.njnt) if m.jnt_type[j] in (2, 3) and not m.joint(j).name.startswith("drive")]
    GC_TAU = np.array([m.jnt_actfrcrange[m.dof_jntid[k]][1] if m.jnt_actfrclimited[m.dof_jntid[k]] else 2000.0 for k in GC_DOFS])
    FREE_Q = m.jnt_qposadr[m.joint("amr_free").id]
mujoco.mj_forward(m, d)
print(f"modello: {m.nbody} corpi, {m.nu} attuatori, massa robot {m.body_subtreemass[m.body('amr').id]:.1f} kg; "
      f"campo protezione {R_PROT:.2f} m, avviso {R_WARN:.2f} m", flush=True)


# ---------------------------------------------------------------- persone
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
        P = np.array([self.pos[0], self.pos[1], 0.0])
        up = np.array([0, 0, 1.0])
        dark, skin = (0.08, 0.08, 0.1), (0.75, 0.6, 0.5)
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


ORANGE, YELLOW = (1.0, 0.45, 0.05), (0.85, 0.95, 0.1)
people = [] if args.no_humans else [
    # operatore: arriva quando il kit e' pronto, ritira e ricarica al banco (Giorgio si ferma), poi sta lontano ~25 s
    Person([(3.6, 2.6), (1.3, 0.9), (1.3, 0.0), (1.3, 0.9), (3.6, 2.6)], 1.2, ORANGE, waits={2: 6.0, 4: 22.0}, t0=19.0 + (14.0 if MOBILE else 0.0)),
    Person([(-2.2, -4.5), (-2.2, 4.5)], 1.3, YELLOW, t0=1.0 if MOBILE else 8.0),
]


def place_people():
    for h, p in enumerate(people):
        segs = p.segments() if p.active else []
        for k in range(N_SEG):
            bid = m.body(f"h{h}_{k}").id
            mid = m.body_mocapid[bid]
            gid = m.geom(f"h{h}_{k}_g").id
            if not segs:
                d.mocap_pos[mid] = [0, 0, -10]
                continue
            c, ax, r, hh, col = segs[k]
            q = Rot.align_vectors([ax], [[0, 0, 1.0]])[0].as_quat()
            d.mocap_pos[mid] = c
            d.mocap_quat[mid] = [q[3], q[0], q[1], q[2]]
            m.geom_size[gid] = [r, hh, 0]
            m.geom_rgba[gid] = list(col) + [1]


# ---------------------------------------------------------------- scanner (raycast reale sulla scena)
SCAN_FOV, SCAN_N, SCAN_MAX = math.radians(275), 276, 8.0
scan_sites = [m.site(f"scanner{k}").id for k in range(len(SCANNERS))]
GG = np.array([1, 1, 0, 0, 0, 0], np.uint8)            # vedono ambiente (0) e persone (1), non il robot (2)


def scan_once():
    out = []
    for k, sid in enumerate(scan_sites):
        o = d.site_xpos[sid].copy()
        Rb = d.body("amr").xmat.reshape(3, 3)
        h = SCANNERS[k][1] + math.atan2(Rb[1, 0], Rb[0, 0])     # il campo ruota con l'AMR
        a = h + np.linspace(-SCAN_FOV / 2, SCAN_FOV / 2, SCAN_N)
        vec = np.stack([np.cos(a), np.sin(a), np.zeros_like(a)], 1).reshape(-1)
        gid = np.zeros(SCAN_N, np.int32); dist = np.zeros(SCAN_N)
        mujoco.mj_multiRay(m, d, o, vec, GG, 1, -1, gid, dist, None, SCAN_N, SCAN_MAX)
        dist[dist < 0] = SCAN_MAX
        out.append((o, vec.reshape(-1, 3), dist))
    return out


mission = {"state": "work", "t_dock": None}
mujoco.mj_forward(m, d)
REF = [dist.copy() for _, _, dist in scan_once()]    # teach-in del contorno a cella vuota (rifatto dopo l'aggancio se mobile)


FIELDS = {"prot": R_PROT, "warn": R_WARN}


def safety():
    zone, hits = 0, []
    c = d.body("amr").xpos[:2]
    rp, rw = FIELDS["prot"], FIELDS["warn"]
    for (o, vec, dist), ref in zip(scan_once(), REF):
        pts = o + vec * dist[:, None]
        if mission["state"] == "work":
            intr = dist < ref - 0.07                       # da fermo: nuovo oggetto davanti al contorno appreso (70 mm)
        else:
            intr = dist < SCAN_MAX - 0.01                  # in marcia: qualunque oggetto nel campo (field set di marcia)
        dc = np.linalg.norm(pts[:, :2] - c, axis=1)
        z = np.where(intr & (dc < rp), 2, np.where(intr & (dc < rw), 1, 0))
        zone = max(zone, int(z.max()))
        hits.append((o, pts, z))
    return zone, hits


# ---------------------------------------------------------------- controllo braccia e mani
LEAP_J = [f"{f}_{j}" for f in ("if", "mf", "rf") for j in ("mcp", "rot", "pip", "dip")] + ["th_cmc", "th_axl", "th_mcp", "th_ipl"]
if args.hands == "leap":
    HAND_ACT = {s: {j: m.actuator(f"{s}_{j}_act").id for j in LEAP_J} for s in ("right", "left")}
elif args.hands == "inspire":
    HAND_ACT = {s: {f: m.actuator(f"{s}_{f}_joint_ctrl").id for f in ("thumb_1", "thumb_2", "index_1", "middle_1", "ring_1", "little_1")}
                for s in ("right", "left")}
else:   # pinza OpenArm: un attuatore, 0 = chiusa, +-0.785 = aperta (138 mm)
    HAND_ACT = {s: {"grip": m.actuator(f"{s}_finger1_ctrl").id} for s in ("right", "left")}
GRIP_OPEN = {"right": -0.785, "left": 0.785}
ARM_ACT = {s: [m.actuator(f"{s}_joint{k}_ctrl").id for k in range(1, 8)] for s in ("right", "left")}
SGN = {"right": -1, "left": 1}
if args.hands == "leap":
    # dita in avanti, pollice in alto, palmo verso il flacone (mano sul lato esterno)
    R_GRASP_S = {"right": np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]]), "left": np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])}
    R_GRASP = None
    Z_GRASP = ZC + 0.02
    LEAP_CLOSE_F = {f"{f}_{j}": v for f in ("if", "mf", "rf") for j, v in (("mcp", 1.5), ("pip", 1.3), ("dip", 1.0))}
    # pollice come battuta sul lato posteriore del flacone (ricerca sulla cinematica), poi le dita lo spingono contro
    LEAP_THUMB_STOP = {"right": {"th_cmc": 1.95, "th_axl": 0.1, "th_mcp": 1.2, "th_ipl": 0.0},
                       "left": {"th_cmc": 2.09, "th_axl": -0.1, "th_mcp": 1.2, "th_ipl": 0.0}}
    LEAP_CLOSE_T = {"th_cmc": 0.0, "th_axl": 0.0, "th_mcp": 0.0, "th_ipl": 0.0}
elif args.hands == "inspire":
    R_GRASP = np.eye(3)                                # dita in avanti, pollice in alto, palmo verso il pezzo
    Z_GRASP = ZC
else:
    R_GRASP = Rot.from_euler("z", 90, degrees=True).as_matrix()   # pinza verticale, chiusura lungo x
    Z_GRASP = BENCH_Z + PH - 0.035                     # presa sul collo del flacone
IK = {s: ArmIK(m, s, f"{s}_grasp") for s in ("right", "left")}
FINGERS = ("index_1", "middle_1", "ring_1", "little_1")
TH2_CLOSE, F_CLOSE = 0.6, 1.35


def smooth(u):
    return u * u * u * (10 - 15 * u + 6 * u * u)


class Seg:
    def __init__(self, kind, qa=None, qb=None, dur=0.5, hand=None, ev=None):
        self.kind, self.qa, self.qb, self.dur, self.hand, self.ev = kind, qa, qb, dur, hand, ev


class ArmTask:
    def __init__(self, s):
        self.s, self.sg = s, SGN[s]
        self.ik = IK[s]
        self.R = R_GRASP_S[s] if R_GRASP is None else R_GRASP
        self.q = np.array([d.qpos[a] for a in self.ik.qadr])
        self.hand = {f: 0.0 for f in HAND_ACT[s]}
        if "thumb_1" in self.hand:
            self.hand["thumb_1"] = 1.1
        elif "grip" in self.hand:
            self.hand["grip"] = GRIP_OPEN[s]
        self.segs, self.i, self.t, self.n, self.held = [], 0, 0.0, 0, None

    def solve(self, p, q0):
        q, ok, ep, er = self.ik.solve(d.qpos.copy(), q0, np.asarray(p, float), self.R)
        if not ok:
            print(f"[{self.s}] IK imprecisa su {np.round(p, 3)}: {ep * 1000:.1f} mm {er:.3f} rad", flush=True)
        return q

    def line(self, pa, pb, q0, dur, n=12):
        """segmento cartesiano: catena di IK con seme progressivo -> spline di giunto"""
        qs, q = [], q0
        for u in np.linspace(0, 1, n + 1)[1:]:
            q, _, _ = self.ik.solve1(d.qpos.copy(), q, pa + (pb - pa) * u, self.R)
            qs.append(q)
        segs, qp = [], q0
        for qn in qs:
            segs.append(Seg("lin", qp, qn, dur / n)); qp = qn
        return segs, qp

    def jmove(self, qa, qb):
        dur = max(0.8, float(np.max(np.abs(qb - qa))) / 1.2 * 1.9)
        return Seg("joint", qa, qb, dur)

    def plan(self, n):
        sg = self.sg
        a = np.array([SLOTS_IN[n][0], sg * SLOTS_IN[n][1], Z_GRASP])
        b = np.array([SLOTS_KIT[n][0], sg * SLOTS_KIT[n][1], Z_GRASP + 0.004])
        side = np.array([0, 0, 0.16 if args.hands == "leap" else 0.12])   # avvicinamento verticale dall'alto
        up = np.array([0, 0, 0.20 if args.hands == "leap" else 0.13])   # trasferimento sopra le teste dei flaconi
        q_pre = self.solve(a + side, self.q)
        segs = [self.jmove(self.q, q_pre)]
        s1, q_g = self.line(a + side, a, q_pre, 0.9); segs += s1
        if "if_mcp" in self.hand:     # LEAP: prima le dita avvolgono, poi il pollice chiude
            stop = LEAP_THUMB_STOP[self.s]
            squeeze = dict(stop, th_ipl=0.5, th_mcp=stop["th_mcp"] + 0.25)
            segs += [Seg("hand", dur=1.2, hand=dict(stop, **LEAP_CLOSE_F), ev="soft"), Seg("hand", dur=0.3, hand=squeeze, ev="grip"),
                     Seg("wait", dur=0.25)]
        elif "grip" in self.hand:
            segs += [Seg("hand", dur=0.5, hand={"grip": 0.0}, ev="grip"), Seg("wait", dur=0.25)]
        else:
            segs += [Seg("hand", dur=0.4, hand={"thumb_2": TH2_CLOSE}), Seg("hand", dur=0.6, hand={f: F_CLOSE for f in FINGERS}, ev="grip"),
                     Seg("wait", dur=0.2)]
        s2, q_up = self.line(a, a + up, q_g, 0.7); segs += s2
        q_bu = self.solve(b + up, q_up)
        segs.append(self.jmove(q_up, q_bu))
        s3, q_b = self.line(b + up, b, q_bu, 0.8); segs += s3
        if "if_mcp" in self.hand:
            segs += [Seg("hand", dur=0.4, hand={j: 0.0 for j in LEAP_CLOSE_T}), Seg("hand", dur=0.5, hand={j: 0.0 for j in LEAP_CLOSE_F}, ev="release"),
                     Seg("wait", dur=0.15)]
        elif "grip" in self.hand:
            segs += [Seg("hand", dur=0.4, hand={"grip": GRIP_OPEN[self.s]}, ev="release"), Seg("wait", dur=0.15)]
        else:
            segs += [Seg("hand", dur=0.5, hand={f: 0.0 for f in FINGERS}), Seg("hand", dur=0.3, hand={"thumb_2": 0.0}, ev="release")]
        s4, q_r = self.line(b, b + side, q_b, 0.6); segs += s4
        s5, q_r2 = self.line(b + side, b + side + up, q_r, 0.5); segs += s5
        segs[-1].ev = "placed"
        return segs

    def start(self, segs):
        self.segs, self.i, self.t = segs, 0, 0.0
        self._h0 = dict(self.hand)

    def step(self, dt, k, on_event):
        if not self.segs:
            return
        sg = self.segs[self.i]
        self.t += dt * k
        u = min(1.0, self.t / sg.dur)
        if sg.kind in ("joint", "lin"):
            uu = smooth(u) if sg.kind == "joint" else u
            self.q = sg.qa + (sg.qb - sg.qa) * uu
        elif sg.kind == "hand":
            for f, v in sg.hand.items():
                self.hand[f] = self._h0[f] + (v - self._h0[f]) * smooth(u)
        if u >= 1.0:
            if sg.ev:
                on_event(self, sg.ev)
            self.i, self.t = self.i + 1, 0.0
            self._h0 = dict(self.hand)
            if self.i >= len(self.segs):
                self.segs = []

    @property
    def busy(self):
        return bool(self.segs)

    def apply(self):
        d.ctrl[ARM_ACT[self.s]] = self.q
        for f, v in self.hand.items():
            d.ctrl[HAND_ACT[self.s][f]] = v


# posa iniziale "pronto": mani sopra il banco (a braccia pendenti finirebbero sotto il piano)
for s_ in ("right", "left"):
    q_r, ok, _, _ = IK[s_].solve(d.qpos.copy(), np.array([-0.6, -0.6 * SGN[s_], 0, 1.6, 0, 0, 0]) * np.array([SGN[s_] * -1, 1, 1, 1, 1, 1, 1]),
                                 np.array([0.28, SGN[s_] * (0.30 if args.hands == "leap" else 0.20), Z_GRASP + (0.22 if args.hands == "leap" else 0.14)]),
                                 R_GRASP_S[s_] if R_GRASP is None else R_GRASP)
    d.qpos[IK[s_].qadr] = q_r
    d.ctrl[ARM_ACT[s_]] = q_r
mujoco.mj_forward(m, d)
PATH = np.array([(-3.0, -1.3), (-1.7, -1.3), (-1.05, -0.45), (-0.85, 0.0), (0.0, 0.0)])   # stazione A -> banco B
if MOBILE:
    d.qpos[FREE_Q:FREE_Q + 3] = [PATH[0][0], PATH[0][1], 0.0]
    mission["state"] = "drive"
    mujoco.mj_forward(m, d)
arms = [ArmTask("right"), ArmTask("left")]
stats = {"placed": 0, "lost": 0, "kits": 0, "stops": 0, "slow_s": 0.0, "stop_s": 0.0}
NPER = len(SLOTS_IN)


def part_pos(s, n):
    return d.body(f"part_{s}_{n}").xpos.copy()


def on_event(a, ev):
    if ev == "placed":
        pp = part_pos(a.s, a.n)
        tgt = np.array([SLOTS_KIT[a.n][0], a.sg * SLOTS_KIT[a.n][1]])
        err = 1000 * np.linalg.norm(pp[:2] - tgt)
        tilt = math.degrees(math.acos(min(1.0, abs(d.body(f"part_{a.s}_{a.n}").xmat[8]))))
        ok = err < 20 and abs(pp[2] - ZC) < 0.012 and tilt < 10
        stats["placed" if ok else "lost"] += 1
        print(f"[t={d.time:6.1f}s] {a.s}: flacone {a.n + 1}/{NPER} {'nel kit' if ok else 'PERSO'} (errore {err:.0f} mm, incl {tilt:.0f} gradi)", flush=True)
        a.n += 1
    elif ev == "soft" and args.hands == "leap":
        pass
    elif ev == "grip":
        pp = part_pos(a.s, a.n)
        qa = np.array([d.qpos[j] for j in a.ik.qadr])
        print(f"[t={d.time:6.1f}s] {a.s}: presa flacone {a.n + 1} (pos {np.round(pp, 3).tolist()}) mano {np.round(d.site(a.s + '_grasp').xpos, 3).tolist()}"
              f" errore giunti {np.round(qa - a.q, 3).tolist()}", flush=True)


def swap_trays():
    for s, n, bn in parts:
        j = m.body(bn).jntadr[0]
        qa, va = m.jnt_qposadr[j], m.jnt_dofadr[j]
        d.qpos[qa:qa + 7] = [SLOTS_IN[n][0], SGN[s] * SLOTS_IN[n][1], ZC + 0.001, 1, 0, 0, 0]
        d.qvel[va:va + 6] = 0
    for a in arms:
        a.n = 0
    stats["kits"] += 1
    print(f"[t={d.time:6.1f}s] operatore: kit {stats['kits']} ritirato, flaconi ricaricati", flush=True)


# ---------------------------------------------------------------- disegno (raggi, campi, HUD)
def draw(scn, hits, zone):
    def line(a, b, rgba, w=1.5):
        if scn.ngeom >= scn.maxgeom:
            return
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_LINE, np.zeros(3), np.zeros(3), np.eye(3).reshape(-1), np.array(rgba, np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_LINE, w, np.asarray(a, float), np.asarray(b, float))
        scn.ngeom += 1
    for o, pts, z in hits:
        for i in range(0, len(pts), 3):
            if LIGHT and z[i] == 0 and i % 2:
                continue
            col = (1.0, 0.15, 0.1, 0.9) if z[i] == 2 else (1.0, 0.8, 0.1, 0.8) if z[i] == 1 else ((0.35, 0.6, 0.75, 0.25) if LIGHT else (0.1, 0.55, 0.65, 0.35))
            line(o, pts[i], col, 1.0)
    cx, cy = d.body("amr").xpos[:2]
    for rad, zl, base, hot in ((FIELDS["warn"], 1, (0.6, 0.5, 0.05, 0.8), (1.0, 0.85, 0.1, 1)), (FIELDS["prot"], 2, (0.6, 0.1, 0.08, 0.8), (1.0, 0.15, 0.1, 1))):
        a = np.linspace(0, 2 * math.pi, 73)
        col = hot if zone == zl or (zl == 1 and zone >= 1) else base
        for i in range(72):
            line((cx + rad * math.cos(a[i]), cy + rad * math.sin(a[i]), 0.005), (cx + rad * math.cos(a[i + 1]), cy + rad * math.sin(a[i + 1]), 0.005), col, 2.5)


ZN = ["LIBERO - velocita' piena", "AVVISO - velocita' ridotta 30%", "PROTEZIONE - arresto SS1"]
ZCOL = [(80, 255, 110), (255, 215, 30), (255, 50, 50)]


def hud_lines(zone, k):
    return [f"GIORGIO-P  //  {args.base}  //  OpenArm 2.0 + {dict(inspire='Inspire RH56DFTP', leap='LEAP Hand', gripper='pinza OpenArm')[args.hands]}  //  look: {args.look}",
            f"SCANNER nanoScan3: {ZN[zone]}   (prot {FIELDS['prot']:.2f} m / avviso {FIELDS['warn']:.2f} m)",
            f"missione: {dict(drive='AMR in marcia A -> B', work='al banco B: kitting')[mission['state']]}" + (f"   v = {drive['v']:.2f} m/s" if mission['state'] == 'drive' else ""),
            f"override velocita': {100 * k:.0f}%    t = {d.time:5.1f} s",
            f"flaconi nel kit {stats['placed']}  persi {stats['lost']}  kit ritirati {stats['kits']}  arresti {stats['stops']}"]


# ---------------------------------------------------------------- ciclo
DT = m.opt.timestep
state = {"k": 1.0, "k_cmd": 1.0, "zone": 0, "clear_t": 0.0, "hits": [], "scan_t": 0.0}


WL, WR = (m.actuator("drive_left_vel").id, m.actuator("drive_right_vel").id) if MOBILE else (None, None)
B_HALF, WHEEL_R_ = DRIVE_HALF_TRACK, DRIVE_WHEEL_R    # base attiva (giorgio_model.BASE)
drive = {"v": 0.0, "w": 0.0}


def base_pose():
    p = d.body("amr").xpos; R = d.body("amr").xmat.reshape(3, 3)
    return p[0], p[1], math.atan2(R[1, 0], R[0, 0])


def drive_step(k):
    """pure pursuit sul percorso A->B; velocita' dai campi di sicurezza (k); aggancio lento e preciso al banco"""
    x, y, th = base_pose()
    goal = PATH[-1]
    dist_goal = math.hypot(goal[0] - x, goal[1] - y)
    # punto di mira a 0.35 m lungo il percorso
    seg_pts = np.vstack([np.linspace(PATH[i], PATH[i + 1], 40) for i in range(len(PATH) - 1)])
    i0 = int(np.argmin(np.linalg.norm(seg_pts - [x, y], axis=1)))
    ahead = seg_pts[i0:]
    j = np.argmax(np.linalg.norm(ahead - [x, y], axis=1) > 0.35) if len(ahead) > 1 else 0
    tgt = ahead[j] if np.linalg.norm(ahead[j] - [x, y]) > 0.05 else goal
    alpha = (math.atan2(tgt[1] - y, tgt[0] - x) - th + math.pi) % (2 * math.pi) - math.pi
    v_ref = 0.5 if dist_goal > 0.9 else max(0.04, 0.5 * dist_goal / 0.9) if dist_goal > 0.25 else 0.06
    v_ref *= k
    FIELDS["prot"] = 0.45 + 0.9 * abs(drive["v"]); FIELDS["warn"] = FIELDS["prot"] + 0.45     # commutazione campi con la velocita'
    if dist_goal < 0.35:
        FIELDS["prot"], FIELDS["warn"] = 0.38, 0.6                                               # campi di aggancio
    arrived = x >= goal[0] - 0.003
    if arrived:
        v_ref, alpha = 0.0, 0.0
    w_ref = 2.0 * math.sin(alpha) * max(abs(v_ref), 0.05) / 0.35
    if arrived:                                    # raddrizzamento sul posto (guida differenziale): yaw -> 0
        w_ref = float(np.clip(-2.0 * th, -0.3, 0.3)) if abs(th) > math.radians(0.4) else 0.0
    acc = 0.5 / FPS_C
    drive["v"] += float(np.clip(v_ref - drive["v"], -2 * acc, acc))
    drive["w"] = float(np.clip(w_ref, -0.8, 0.8))
    d.ctrl[WL] = (drive["v"] - drive["w"] * B_HALF) / WHEEL_R_
    d.ctrl[WR] = (drive["v"] + drive["w"] * B_HALF) / WHEEL_R_
    if arrived and abs(drive["v"]) < 1e-3 and w_ref == 0.0 and np.linalg.norm(d.qvel[FREE_V:FREE_V + 6]) < 0.003:
        mission["state"] = "work"; mission["t_dock"] = d.time
        d.ctrl[WL] = d.ctrl[WR] = 0.0
        FIELDS["prot"], FIELDS["warn"] = R_PROT, R_WARN
        global REF
        REF = [dd.copy() for _, _, dd in scan_once()]                                            # teach-in del contorno da fermo
        print(f"[t={d.time:6.1f}s] AMR agganciato al banco: errore x {1000 * (x - goal[0]):.0f} mm, y {1000 * y:.0f} mm, "
              f"yaw {math.degrees(th):.1f} gradi -> campi da fermo, contorno appreso", flush=True)


FPS_C = 1.0 / m.opt.timestep
FREE_V = m.jnt_dofadr[m.joint("amr_free").id] if MOBILE else 0


EYES = {"l": m.geom("eye_l").id, "r": m.geom("eye_r").id}
EYE_POS0 = {k: m.geom_pos[g].copy() for k, g in EYES.items()}
EYE_COL = {0: (0.45, 0.85, 1.0), 1: (1.0, 0.72, 0.15), 2: (1.0, 0.18, 0.12)}
eye_state = {"gaze": np.zeros(2), "next_blink": 3.0}


def eyes_step():
    """occhi-display: guardano la persona piu' vicina (o le mani al lavoro), sbattono le palpebre, colore = stato sicurezza"""
    t = d.time
    crown = d.body("crown"); Rc = crown.xmat.reshape(3, 3)
    near = [np.r_[p.pos, 1.6] for p in people if p.active and np.linalg.norm(p.pos - d.body("amr").xpos[:2]) < FIELDS["warn"] + 1.0]
    if near:
        tgt = min(near, key=lambda q: np.linalg.norm(q[:2] - crown.xpos[:2]))
    elif mission["state"] == "drive":
        tgt = crown.xpos + Rc @ np.array([2.0, 0, -0.3])
    else:
        tgt = 0.5 * (d.site("right_grasp").xpos + d.site("left_grasp").xpos)
    v = Rc.T @ (tgt - crown.xpos)
    g = np.array([np.clip(math.atan2(v[1], v[0]) / 1.2, -1, 1), np.clip(math.atan2(v[2], math.hypot(v[0], v[1])) / 0.8, -1, 1)])
    eye_state["gaze"] += 0.15 * (g - eye_state["gaze"])
    blink = 0.0
    if t > eye_state["next_blink"]:
        u = (t - eye_state["next_blink"]) / 0.16
        blink = math.sin(math.pi * min(u, 1.0))
        if u >= 1.0:
            eye_state["next_blink"] = t + 3.0 + 2.0 * ((t * 7.31) % 1.0)
    col = EYE_COL[state["zone"]]
    for k, gid in EYES.items():
        p0 = EYE_POS0[k]
        m.geom_pos[gid] = p0 + [0, 0.011 * eye_state["gaze"][0], 0.008 * eye_state["gaze"][1]]
        m.geom_size[gid] = [0.004, 0.0125, 0.017 * (1 - 0.85 * blink)]
        m.geom_rgba[gid] = list(col) + [1]


def control_step():
    t = d.time
    if int(round(t / DT)) % 16 == 0:
        eyes_step()
    if MOBILE:
        d.qfrc_applied[GC_DOFS] = np.clip(d.qfrc_bias[GC_DOFS], -GC_TAU, GC_TAU)
    for p in people:
        p.step(t, DT)
    if people:
        place_people()
    state["scan_t"] += DT
    if state["scan_t"] >= 0.03 or not state["hits"]:          # nanoScan3: tempo di risposta ~ 70 ms, scan ogni 30 ms
        state["scan_t"] = 0.0
        zone, state["hits"] = safety()
        if zone == 2:
            if state["zone"] != 2 and state["k_cmd"] > 0:
                stats["stops"] += 1
                print(f"[t={t:6.1f}s] SCANNER: intrusione nel campo di protezione -> arresto", flush=True)
            state["k_cmd"], state["clear_t"] = 0.0, 0.0
        else:
            state["clear_t"] += 0.03
            if state["clear_t"] > 1.0 or state["k_cmd"] > 0:
                state["k_cmd"] = 0.3 if zone == 1 else 1.0
        state["zone"] = zone
    k, kc = state["k"], state["k_cmd"]
    k = max(kc, k - DT / 0.3) if kc < k else min(kc, k + DT / 0.6)
    state["k"] = k
    stats["slow_s"] += DT if 0 < kc < 1 else 0.0
    stats["stop_s"] += DT if kc == 0 else 0.0
    if mission["state"] == "drive":
        drive_step(k)
        for a in arms:
            a.apply()
    else:
        for a in arms:
            if not a.busy and a.n < NPER:
                a.start(a.plan(a.n))
            a.step(DT, k, on_event)
            a.apply()
    done = mission["state"] == "work" and all(a.n >= NPER and not a.busy for a in arms)
    op = people[0] if people else None
    if done and ((op is None) or (op.active and op.tw > 0 and np.linalg.norm(op.pos - [1.3, 0.0]) < 0.05 and k == 0.0)):
        swap_trays()
    mujoco.mj_step(m, d)


class Pano:
    """Insta360: 6 viste a cubo dal punto degli obiettivi -> immagine equirettangolare (come lo stitching della camera)"""
    FACES = ("px", "nx", "py", "ny", "pz", "nz")

    def __init__(self, W=384, H=192, face=192):
        self.W, self.H, self.f = W, H, face
        lon = np.pi - 2 * np.pi * (np.arange(W) + 0.5) / W
        lat = np.pi / 2 - np.pi * (np.arange(H) + 0.5) / H
        LON, LAT = np.meshgrid(lon, lat)
        D = np.stack([np.cos(LAT) * np.cos(LON), np.cos(LAT) * np.sin(LON), np.sin(LAT)], -1)
        cams = [m.camera(f"pano_{n}").id for n in self.FACES]
        self.cams = [m.camera(f"pano_{n}").name for n in self.FACES]
        R = [m.cam_mat0[c].reshape(3, 3) for c in cams]          # assi camera nel corpo (colonne: x, y, z)
        view = np.stack([-r[:, 2] for r in R])                    # direzione di vista = -z camera
        k = np.argmax(D @ view.T, -1)
        self.k = k
        self.row = np.zeros((H, W), int); self.col = np.zeros((H, W), int)
        for i, r in enumerate(R):
            msk = k == i
            dd = D[msk]
            cz = dd @ (-r[:, 2]); cx = dd @ r[:, 0]; cy = dd @ r[:, 1]
            u, v = cx / cz, cy / cz
            self.col[msk] = np.clip(((u + 1) / 2 * face).astype(int), 0, face - 1)
            self.row[msk] = np.clip(((1 - (v + 1) / 2) * face).astype(int), 0, face - 1)
        self.r = mujoco.Renderer(m, face, face)

    def render(self):
        faces = []
        for c in self.cams:
            self.r.update_scene(d, c); faces.append(self.r.render().copy())
        F = np.stack(faces)
        return F[self.k, self.row, self.col]


def inset_views(rc_w, rc_g, pano):
    """immagini dei sensori: 360, Gemini, polsi"""
    out = {"pano": pano.render()}
    rc_g.update_scene(d, "gemini"); out["gemini"] = rc_g.render().copy()
    for s_ in ("right", "left"):
        rc_w.update_scene(d, f"camera_wrist_{s_}"); out[s_] = rc_w.render().copy()
    return out


cam = mujoco.MjvCamera()
cam.lookat[:] = [0.25, 0, 0.95]; cam.distance = 2.6; cam.azimuth = 228; cam.elevation = -24
if args.close:
    cam.lookat[:] = [0.3, -0.22, 1.0]; cam.distance = 0.8; cam.azimuth = 120; cam.elevation = -25

if args.record:
    # geometria: ogni geom visibile (gruppi 0-2) con mesh/primitive nel suo frame, corpo, materiale
    geoms = []
    for g in range(m.ngeom):
        if m.geom_group[g] > 2 or m.geom_rgba[g][3] == 0 and m.geom_matid[g] < 0:
            continue
        mat = m.material(m.geom_matid[g]).name if m.geom_matid[g] >= 0 else ""
        rgba = m.mat_rgba[m.geom_matid[g]] if m.geom_matid[g] >= 0 else m.geom_rgba[g]
        e = dict(name=m.geom(g).name, type=int(m.geom_type[g]), size=m.geom_size[g].copy(), body=int(m.geom_bodyid[g]),
                 pos=m.geom_pos[g].copy(), quat=m.geom_quat[g].copy(), mat=mat, rgba=np.array(rgba).copy(),
                 body_name=m.body(m.geom_bodyid[g]).name)
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[g]
            e["vert"] = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]].copy()
            e["face"] = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]].copy()
        geoms.append(e)
    XP, XQ, ZONE, SIZES, EYE = [], [], [], [], []
    hum = [m.geom(f"h{h}_{k}_g").id for h in range(HUMANS) for k in range(N_SEG)]
    t_next, wall0 = 0.0, time.time()
    while d.time < args.seconds:
        control_step()
        if d.time >= t_next:
            t_next += 1 / 30
            XP.append(d.xpos.copy()); XQ.append(d.xquat.copy()); ZONE.append(state["zone"])
            EYE.append(np.concatenate([np.r_[m.geom_pos[g], m.geom_size[g], m.geom_rgba[g][:3]] for g in EYES.values()]))
            SIZES.append(np.array([m.geom_size[g] for g in hum]) if hum else np.zeros((0, 3)))
    import pickle
    pickle.dump(dict(geoms=geoms, xpos=np.array(XP), xquat=np.array(XQ), zone=np.array(ZONE), hum=hum,
                     hum_sizes=np.array(SIZES), eyes=np.array(EYE), body_names=[m.body(i).name for i in range(m.nbody)],
                     r_prot=R_PROT, r_warn=R_WARN, stats=stats), open(args.record, "wb"))
    print(f"registrati {len(XP)} fotogrammi, {len(geoms)} geom in {time.time() - wall0:.0f}s -> {args.record}", flush=True)
elif args.video or args.preview:
    import cv2
    import imageio
    W, H = 1600, 900
    r = mujoco.Renderer(m, H, W)
    rc_w = mujoco.Renderer(m, 108, 190)
    rc_g = mujoco.Renderer(m, 240, 384)
    pano = Pano()
    writer = imageio.get_writer(args.video, fps=30, quality=8, macro_block_size=8) if args.video else None
    t_next, wall0 = 0.0, time.time()

    def frame():
        r.update_scene(d, cam)
        draw(r.scene, state["hits"], state["zone"])
        img = r.render().copy()
        V = inset_views(rc_w, rc_g, pano)
        x0 = W - 404
        boxes = [(V["pano"], 20, x0, "Insta360 X4 - 360 gradi"), (V["gemini"], 232, x0, "Orbbec Gemini 336L"),
                 (V["right"], 492, x0, "polso dx"), (V["left"], 492, x0 + 194, "polso sx")]
        for im, y0, xx, lbl in boxes:
            hh, ww = im.shape[:2]
            img[y0:y0 + hh, xx:xx + ww] = im
            cv2.rectangle(img, (xx - 2, y0 - 2), (xx + ww + 1, y0 + hh + 1), (120, 120, 140), 2)
            cv2.putText(img, lbl, (xx + 6, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, lbl, (xx + 6, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        for i, txt in enumerate(hud_lines(state["zone"], state["k"])):
            col = ZCOL[state["zone"]] if i == 1 else (230, 230, 240)
            cv2.putText(img, txt, (24, 40 + 32 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, txt, (24, 40 + 32 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.75, col, 2, cv2.LINE_AA)
        return img

    if args.preview:
        for _ in range(int(2.0 / DT)):
            control_step()
        imageio.imwrite(args.preview, frame()); print("anteprima:", args.preview); raise SystemExit
    while d.time < args.seconds:
        control_step()
        if d.time >= t_next:
            t_next += 1 / 30
            if not args.close:
                cam.azimuth = 228 + 30 * math.sin(d.time / 30)
            writer.append_data(frame())
        if int(d.time / DT) % int(10 / DT) == 0:
            print(f"[t={d.time:6.1f}s] zona {state['zone']} k={state['k']:.2f} pezzi {stats['placed']} (wall {time.time() - wall0:.0f}s)", flush=True)
    writer.close(); print("video:", args.video)
else:
    import mujoco.viewer
    with mujoco.viewer.launch_passive(m, d) as v:
        v.cam.lookat[:] = cam.lookat; v.cam.distance = cam.distance; v.cam.azimuth = cam.azimuth; v.cam.elevation = cam.elevation
        try:
            rc = None if args.no_cams else True
            if rc:
                rc_w = mujoco.Renderer(m, 108, 190); rc_g = mujoco.Renderer(m, 240, 384); pano = Pano()
        except Exception as e:                           # contesto GL offscreen non disponibile accanto al viewer
            print("finestre telecamere disattivate:", e); rc = None
        last_cam = 0.0
        while v.is_running() and d.time < args.seconds:
            t0 = time.time()
            for _ in range(int((1 / 60) / DT)):
                control_step()
            with v.lock():
                v.user_scn.ngeom = 0
                draw(v.user_scn, state["hits"], state["zone"])
            # set_texts/set_images prendono da soli il lock del viewer: chiamarli dentro v.lock() = blocco
            v.set_texts([(mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPLEFT, "\n".join(hud_lines(state["zone"], state["k"])), "")])
            if rc is not None and time.time() - last_cam > 0.15:
                last_cam = time.time()
                V = inset_views(rc_w, rc_g, pano)
                Wv, Hv = v.viewport.width, v.viewport.height
                imgs = [(mujoco.MjrRect(Wv - 394, Hv - 202, 384, 192), V["pano"]), (mujoco.MjrRect(Wv - 394, Hv - 452, 384, 240), V["gemini"]),
                        (mujoco.MjrRect(Wv - 394, Hv - 570, 190, 108), V["right"]), (mujoco.MjrRect(Wv - 200, Hv - 570, 190, 108), V["left"])]
                v.set_images(imgs)
            v.sync()
            if args.debug and int(d.time * 60) % 120 == 0:
                print(f'[gui] t={d.time:.1f} wall={time.time():.1f}', flush=True)
            time.sleep(max(0.0, 1 / 60 - (time.time() - t0)))
print(f"FINE t={d.time:.1f}s: flaconi nel kit {stats['placed']}, persi {stats['lost']}, kit {stats['kits']}, arresti {stats['stops']}, "
      f"rallentato {stats['slow_s']:.0f}s, fermo {stats['stop_s']:.0f}s", flush=True)
