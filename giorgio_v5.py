"""Giorgio v5 - ciclo continuo (in loop): carico di 12 flaconi nel buffer a bordo, trasporto, inserimento guidato dalla visione.

Stazione A: 12 flaconi -> la Gemini 336L li trova (colore tappo HSV + profondita'), le due braccia li caricano nei
2 portaflaconi laterali del robot (6 + 6). L'AMR Tracer 2.0 guida con traiettorie morbide (curve di Hermite, velocita'
limitata dalla curvatura) fino al banco B. La visione trova i 12 fori (con smusso d'invito) e corregge l'errore di
aggancio; Giorgio scarica il buffer inserendo i flaconi. Un operatore svuota B e ricarica A: quando entra nell'area
Giorgio si ferma (occhi rossi, baffi giu'), i passanti in corsia lo fanno rallentare o fermare.

uso: python giorgio_v5.py [--video out.mp4] [--record out.pkl] [--cycles 1] [--no_humans]
"""
import argparse
import itertools
import math
import os
import time

import mujoco
import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation as Rot

from giorgio_ik import ArmIK
from giorgio_model import AMR_OUT, BASE, BAT_WH, CHARGE_W, DOCK_FACE_X, DOCK_REAR_X, DRIVE_HALF_TRACK, DRIVE_WHEEL_R
from giorgio_model import BUF_Z, BUFFER_SLOTS, COF_LIFT, COF_MH, COF_SH, COF_STACK, COF_STACK_Z, COF_X, COF_Y_IN, COF_Y_OUT, GROUP_ENV, GROUP_HUMAN, LOOKS, SCANNERS, build

ap = argparse.ArgumentParser()
ap.add_argument("--look", default="gb", choices=list(LOOKS))
ap.add_argument("--video", default="")
ap.add_argument("--record", default="")
ap.add_argument("--cycles", type=int, default=1)
ap.add_argument("--seconds", type=float, default=1e9)
ap.add_argument("--no_humans", action="store_true")
ap.add_argument("--seed", type=int, default=3)
ap.add_argument("--agent", default="", help="comandi a tempo per l'agente: 't:testo|t:testo'")
ap.add_argument("--soc", type=float, default=0.85, help="stato di carica iniziale della batteria (0-1)")
ap.add_argument("--bat_wh", type=float, default=BAT_WH, help="capacita' batteria di sistema [Wh] (AMR rev B: 2x Discover DLP-GC2-48V = 3070 Wh, "
                "amr/; Ranger Mini: pacco 48 V 15s 30 Ah = 1440 Wh)")
ap.add_argument("--hands", default="gripper", help="gripper | orca+amazing | ... (destra+sinistra)")
ap.add_argument("--speedup", type=int, default=1, help="video: un fotogramma ogni N/30 s (timelapse)")
args = ap.parse_args()
LK = LOOKS[args.look]
rng = np.random.default_rng(args.seed)

# ---------------------------------------------------------------- cella
BENCH_Z, PR, PH, PM = 0.90, 0.025, 0.16, 0.35
ZC = BENCH_Z + PH / 2
Z_GRASP = BENCH_Z + PH - 0.035
DOCK = {"A": np.array([-2.4, 1.45, math.pi / 2]), "B": np.array([0.0, 0.0, 0.0])}
# angolo caffe' K: macchina a capsule (classe Essenza Mini, 84 x 204 x 330 mm) sul bancone, erogatore verso il robot
CUP_R, CUP_H, CUP_M = 0.03, 0.08, 0.015
CUP_TOP0 = COF_SH + COF_STACK_Z + 0.006 + 0.012 * 5               # fondo del bicchiere in cima alla pila
GRID = [(0.30, 0.08), (0.39, 0.08), (0.30, 0.155), (0.39, 0.155)]       # 4 fori per lato; passo 90 mm lungo la chiusura          # per lato (y con segno), riferimento stazione
HOLE, FIX_H, CH = 0.056, 0.04, 0.006
FIX_X0, FIX_X1 = 0.30 - 0.028 - 0.016, 0.39 + 0.028 + 0.016
FIX_Y = 0.155 + 0.028 + 0.016
R_PROT = (1600 * 0.37 + 1128) / 1000
R_WARN = R_PROT + 1.1
GRIP_PART = {"right": -0.42, "left": 0.42}         # apertura parziale (~80 mm): non tocca i vicini


def local_to_world(dock, xl, yl):
    x, y, th = dock
    c, s = math.cos(th), math.sin(th)
    return np.array([x + c * xl - s * yl, y + s * xl + c * yl])


sp = build(args.look, hands=args.hands, base="amr", fixed_base=False, buffer=True, coffee=True)
wb = sp.worldbody


def box(name, pos, half, material, collide=True, yaw=0.0, quat=None, fric=None):
    g = wb.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material, group=GROUP_ENV)
    if quat is not None:
        g.quat = quat
    elif yaw:
        g.quat = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    if fric is not None:
        g.friction = fric
    if not collide:
        g.contype = g.conaffinity = 0
    else:
        g.conaffinity = 3
    return g


def table(name, dock):
    c = local_to_world(dock, 0.48, 0.0); th = dock[2]
    box(f"{name}_top", (c[0], c[1], BENCH_Z - 0.02), (0.32, 0.85, 0.02), "bench", yaw=th)
    for xl in (0.19, 0.77):
        for yl in (-0.8, 0.8):
            p = local_to_world(dock, xl, yl)
            box(f"{name}_leg_{xl}_{yl}", (p[0], p[1], (BENCH_Z - 0.04) / 2), (0.025, 0.025, (BENCH_Z - 0.04) / 2), "steel", yaw=th)
    p = local_to_world(dock, 0.80, 0.0)
    box(f"{name}_edge", (p[0], p[1], BENCH_Z - 0.03), (0.002, 0.85, 0.006), "accent", collide=False, yaw=th)


table("B", DOCK["B"])
table("A", DOCK["A"])
# vassoio di kitting sul banco A: 8 alloggi bassi (sponde 15 mm) dove l'operatore rimette i flaconi
for sg_ in (-1, 1):
    for xl_ in (0.30, 0.39):
        for yl_ in (0.08, 0.155):
            for e_, (ox_, oy_) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
                q_ = local_to_world(DOCK["A"], xl_ + ox_ * 0.034, sg_ * yl_ + oy_ * 0.034)
                box(f"kit_{sg_}_{xl_}_{yl_}_{e_}", (q_[0], q_[1], BENCH_Z + 0.0075), (0.004 if ox_ else 0.038, 0.038 if ox_ else 0.004, 0.0075),
                    "steel", yaw=DOCK["A"][2], fric=[0.3, 0.01, 0.001])
cupb = wb.add_body(name="cup", pos=[0, 0, 3.0])                 # posizionato sulla pila del robot all'avvio
cupb.add_freejoint(name="cup_free")
cupb.add_geom(name="cup_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[CUP_R, CUP_H / 2, 0], mass=CUP_M, rgba=[0.97, 0.96, 0.93, 1],
              friction=[0.9, 0.02, 0.002], condim=4, conaffinity=3, group=GROUP_ENV)
cupb.add_geom(name="cup_band", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, 0.005], size=[CUP_R + 0.0008, 0.012, 0], rgba=[1.0, 0.55, 0.2, 1],
              contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
cupb.add_geom(name="cup_coffee", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, -CUP_H / 2 + 0.002], size=[CUP_R - 0.003, 0.0005, 0],
              rgba=[0.33, 0.17, 0.06, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
for i in range(3):
    cupb.add_geom(name=f"cup_steam{i}", type=mujoco.mjtGeom.mjGEOM_SPHERE, pos=[0.004 * (i - 1), 0, CUP_H / 2 + 0.03 + 0.03 * i],
                  size=[0.013 + 0.005 * i, 0, 0], rgba=[1, 1, 1, 0], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
for i, (xl, yl) in enumerate(((0.0, -0.95), (0.0, 0.95), (-0.55, 0.0), (0.55, 0.0))):   # baia di carico A: segnaletica a terra
    p_ = local_to_world(DOCK["A"], xl, yl)
    box(f"bayA{i}", (p_[0], p_[1], 0.002), (0.02 if abs(yl) > 0 else 0.5, 0.5 if abs(yl) > 0 else 0.02, 0.002), "yellow", collide=False,
        yaw=DOCK["A"][2])
# attrezzatura a 12 fori con smusso sul banco B (riferimento B = mondo)
xs_ = sorted({x for x, _ in GRID}); ys_ = sorted({sg * y for sg in (-1, 1) for _, y in GRID})
HOLES = [(x, y) for x in xs_ for y in ys_]          # l'attrezzatura ha tutti i fori della griglia (8)
hz = BENCH_Z + (FIX_H - CH) / 2; Hh = (FIX_H - CH) / 2; FR = [0.3, 0.01, 0.001]
xe = [FIX_X0] + [v for x in xs_ for v in (x - HOLE / 2, x + HOLE / 2)] + [FIX_X1]
ye = [-FIX_Y] + [v for y in ys_ for v in (y - HOLE / 2, y + HOLE / 2)] + [FIX_Y]
for i in range(0, len(xe), 2):                     # pareti piene in x (tra le file di fori)
    if xe[i + 1] - xe[i] > 1e-4:
        box(f"fix_x{i}", ((xe[i] + xe[i + 1]) / 2, 0, hz), ((xe[i + 1] - xe[i]) / 2, FIX_Y, Hh), "dark", fric=FR)
for j, x in enumerate(xs_):                        # dentro ogni fila: pareti in y tra i fori
    for i in range(0, len(ye), 2):
        if ye[i + 1] - ye[i] > 1e-4:
            box(f"fix_y{j}_{i}", (x, (ye[i] + ye[i + 1]) / 2, hz), (HOLE / 2, (ye[i + 1] - ye[i]) / 2, Hh), "dark", fric=FR)
TOP = BENCH_Z + FIX_H
for k, (hx_, hy_) in enumerate(HOLES):             # smussi a 45 gradi
    t, L, r2 = 0.002, CH * math.sqrt(2) / 2, math.sqrt(0.5)
    for e, (ox, oy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        ex, ey = hx_ + ox * HOLE / 2, hy_ + oy * HOLE / 2
        mid = np.array([ex + ox * CH / 2, ey + oy * CH / 2, TOP - CH / 2])
        c = mid - t * np.array([-ox, -oy, 1.0]) * r2
        if ox:
            q = [math.cos(-ox * math.pi / 8), 0, math.sin(-ox * math.pi / 8), 0]; size = (L, HOLE / 2 + CH, t)
        else:
            q = [math.cos(oy * math.pi / 8), math.sin(oy * math.pi / 8), 0, 0]; size = (HOLE / 2 + CH, L, t)
        box(f"chamfer{k}_{e}", c, size, "steel", quat=q, fric=FR)
for i, y in enumerate(np.arange(-3.0, 3.01, 0.5)):          # segnaletica: corsia
    box(f"aisle{i}", (-1.6, y, 0.002), (0.04, 0.18, 0.002), "yellow", collide=False)
# stazione di ricarica C: piastra di contatto + colonnina con LED
CHG = np.array([-3.0, -2.6, -math.pi / 2])
if BASE == "amr_revB":
    # dock rev B (amr/out/stl X01..X07, frame base del robot agganciato): RoboPad RPBAS90 a z 0.120, faccia a 8 mm dal retro del robot,
    # caricatore NPB-1700-48 sotto la cover, AprilTag + catarifrangente. Il robot agganciato ha la posa CHG ruotata di 180 gradi.
    q_dk = [math.cos((CHG[2] + math.pi) / 2), 0, 0, math.sin((CHG[2] + math.pi) / 2)]
    for f_, col_ in (("X01_dock_frame", (0.25, 0.26, 0.28)), ("X02_robopad_base_RPBAS90", (0.85, 0.45, 0.1)), ("X03_pad_mount", (0.55, 0.57, 0.6)),
                     ("X06_apriltag_reflector_plate", (0.95, 0.95, 0.95)), ("X07_dock_cover", (0.92, 0.92, 0.9))):
        sp.add_mesh(name=f"dock_{f_}", file=str(AMR_OUT / f"stl/{f_}.stl"), scale=[0.001] * 3)
        wb.add_geom(name=f"charger_{f_[:3]}", type=mujoco.mjtGeom.mjGEOM_MESH, meshname=f"dock_{f_}", pos=[CHG[0], CHG[1], 0.0], quat=q_dk,
                    rgba=list(col_) + [1], contype=0, conaffinity=0, group=GROUP_ENV)
    pc = local_to_world(CHG, 0.56, 0.0)                  # ingombro solido: cover + piastra del pad (x locale 0.425..0.698, z 0..0.52)
    g_ = box("charger_post", (pc[0], pc[1], 0.26), (0.136, 0.255, 0.26), "armor", yaw=CHG[2]); g_.material = ""; g_.rgba = [0, 0, 0, 0]
    box("charger_led", (pc[0], pc[1], 0.373), (0.10, 0.2, 0.004), "accent", collide=False, yaw=CHG[2])
else:                                                    # Ranger Mini: stazione di ricarica AgileX (kit NAVIS), in retromarcia
    pc = local_to_world(CHG, 0.46, 0.0)                      # stazione di ricarica AgileX (kit NAVIS): il robot ci entra in retromarcia
    box("charger_post", (pc[0], pc[1], 0.35), (0.06, 0.12, 0.35), "armor", yaw=CHG[2])
    pl = local_to_world(CHG, 0.375, 0.0)                     # piastra a molla con due lamelle di contatto, all'altezza dei pattini del robot
    box("charger_plate", (pl[0], pl[1], 0.15), (0.009, 0.09, 0.04), "dark", collide=False, yaw=CHG[2])
    for k_, sy_ in enumerate((-0.03, 0.03)):                   # contatti della stazione, contro la piastra a spazzole posteriore del robot
        q_ = local_to_world(CHG, 0.365, sy_)
        g_ = box(f"charger_lamella{k_}", (q_[0], q_[1], 0.15), (0.002, 0.02, 0.02), "steel", collide=False, yaw=CHG[2])
        g_.material = ""; g_.rgba = [0.75, 0.48, 0.22, 1]
    box("charger_led", (pc[0], pc[1], 0.66), (0.062, 0.1, 0.01), "accent", collide=False, yaw=CHG[2])

# 12 flaconi alla stazione A (griglia con piccolo gioco casuale)
PARTS, HOME = [], {}
for side, sg in (("right", -1), ("left", 1)):
    for n, (xl, yl) in enumerate(GRID):
        name = f"part_{side}_{n}"
        HOME[name] = (xl + rng.uniform(-0.004, 0.004), sg * yl + rng.uniform(-0.004, 0.004))
        b = wb.add_body(name=name, pos=[-7.0 + 0.1 * n, 4.0 + 0.1 * sg, ZC + 0.001])     # magazzino fuori scena
        b.add_freejoint(name=f"{name}_free")
        b.add_geom(name=f"{name}_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[PR, PH / 2, 0], mass=PM, material="part",
                   friction=[0.5, 0.02, 0.002], condim=4, group=GROUP_ENV, conaffinity=3)
        b.add_geom(name=f"{name}_cap", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, PH / 2 + 0.006], size=[0.012, 0.006, 0],
                   material="accent", mass=0.005, contype=0, conaffinity=0, group=GROUP_ENV)
        PARTS.append(name)
def a_pocket(p):
    xy = local_to_world(DOCK["A"], *HOME[p])
    return np.array([xy[0], xy[1], ZC + 0.001])


hand_cup = wb.add_body(name="hand_cup", mocap=True, pos=[0, 0, -5])
hand_cup.add_geom(name="hand_cup_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.028, 0.032, 0], rgba=[0.97, 0.97, 0.95, 1],
                  contype=0, conaffinity=0, group=GROUP_ENV)
# cassetta dell'operatore (per svuotare B e ricaricare A)
tote = wb.add_body(name="tote", mocap=True, pos=[0, 0, -5])
CR_L, CR_W, CR_H = 0.16, 0.085, 0.06             # cassetta: 320 x 170 x 120 mm (lato lungo trasversale alla persona)
for nm_, pos_, sz_ in (("tote_g", (0, 0, -CR_H + 0.004), (CR_W, CR_L, 0.004)),
                       ("tote_w0", (CR_W - 0.004, 0, 0), (0.004, CR_L, CR_H)), ("tote_w1", (-CR_W + 0.004, 0, 0), (0.004, CR_L, CR_H)),
                       ("tote_w2", (0, CR_L - 0.004, 0), (CR_W, 0.004, CR_H)), ("tote_w3", (0, -CR_L + 0.004, 0), (CR_W, 0.004, CR_H))):
    tote.add_geom(name=nm_, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos_), size=list(sz_), material="accent", contype=0, conaffinity=0, group=GROUP_ENV)

for nm_, (dx_, dy_) in (("Marco", (1.6, -2.55)), ("Sara", (-4.6, 3.75))):     # scrivanie
    box(f"desk_{nm_}", (dx_, dy_, 0.37), (0.4, 0.3, 0.37), "bench")
# persone articolate: 17 pezzi (bacino, busto, collo, testa, capelli/casco, braccia con gomito, mani, gambe con ginocchio, scarpe)
H_TYPES = ["E", "E", "C", "E", "E", "C", "C", "C", "C", "E", "E", "C", "C", "C", "C", "E", "E"]
N_SEG = len(H_TYPES)
NH = 0 if args.no_humans else 4                   # 0 = operatore, 1-2 = passanti, 3 = persona servita dall'agente
for h in range(NH):
    for k in range(N_SEG):
        b = wb.add_body(name=f"h{h}_{k}", mocap=True, pos=[0, 0, -10])
        b.add_geom(name=f"h{h}_{k}_g", type=mujoco.mjtGeom.mjGEOM_ELLIPSOID if H_TYPES[k] == "E" else mujoco.mjtGeom.mjGEOM_CAPSULE,
                   size=[0.05, 0.05, 0.1], contype=0, conaffinity=0, group=GROUP_HUMAN, rgba=[0.5, 0.5, 0.5, 1])

for name in PARTS:                                   # clip a molla del buffer = vincolo weld attivabile
    sp.add_equality(name=f"clip_{name}", type=mujoco.mjtEq.mjEQ_WELD, name1=name, name2="amr", objtype=mujoco.mjtObj.mjOBJ_BODY,
                    active=0, solref=[0.01, 1])
m = sp.compile()
d = mujoco.MjData(m)
m.body_gravcomp[:] = 0
GC_DOFS = [m.jnt_dofadr[j] for j in range(m.njnt) if m.jnt_type[j] in (2, 3) and not m.joint(j).name.startswith(("drive", "caster"))]
GC_TAU = np.array([m.jnt_actfrcrange[m.dof_jntid[k]][1] if m.jnt_actfrclimited[m.dof_jntid[k]] else 2000.0 for k in GC_DOFS])
FREE_Q = m.jnt_qposadr[m.joint("amr_free").id]
FREE_V = m.jnt_dofadr[m.joint("amr_free").id]
DT = m.opt.timestep
mujoco.mj_forward(m, d)
print(f"modello: {m.nbody} corpi, massa robot {m.body_subtreemass[m.body('amr').id]:.1f} kg", flush=True)


# ---------------------------------------------------------------- persone
H_LOOKS = {   # camicia/maglia, pantaloni, pelle, capelli, casco (None = capelli), gilet alta visibilita'
    "operatore": dict(shirt=(0.20, 0.24, 0.30), pants=(0.16, 0.18, 0.22), skin=(0.80, 0.62, 0.50), hair=(0.20, 0.14, 0.10), helmet=(0.95, 0.95, 0.93), vest=(1.0, 0.78, 0.05)),
    "Marco": dict(shirt=(0.30, 0.45, 0.70), pants=(0.20, 0.20, 0.24), skin=(0.85, 0.68, 0.56), hair=(0.12, 0.09, 0.07), helmet=None, vest=None),
    "Sara": dict(shirt=(0.78, 0.40, 0.45), pants=(0.15, 0.17, 0.25), skin=(0.72, 0.52, 0.40), hair=(0.35, 0.20, 0.10), helmet=None, vest=None),
    "passante": dict(shirt=(0.55, 0.57, 0.52), pants=(0.25, 0.27, 0.32), skin=(0.62, 0.45, 0.34), hair=(0.06, 0.05, 0.05), helmet=None, vest=(1.0, 0.45, 0.10)),
    "passante2": dict(shirt=(0.92, 0.92, 0.90), pants=(0.30, 0.25, 0.20), skin=(0.88, 0.72, 0.62), hair=(0.55, 0.42, 0.25), helmet=None, vest=None),
}
SHOE = (0.10, 0.10, 0.11)


def _frame(z, x_hint):
    """matrice di rotazione con asse z dato e asse x il piu' vicino possibile a x_hint"""
    z = z / np.linalg.norm(z)
    x = x_hint - np.dot(x_hint, z) * z
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(z, [0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x /= np.linalg.norm(x)
    return np.stack([x, np.cross(z, x), z], 1)


def _ik2(S, T, L1, L2, hint):
    """braccio a 2 segmenti: gomito nel piano di S, T e della direzione suggerita"""
    v = T - S; D = float(np.clip(np.linalg.norm(v), 0.05, L1 + L2 - 1e-3)); u = v / max(np.linalg.norm(v), 1e-9)
    a = (L1 ** 2 - L2 ** 2 + D ** 2) / (2 * D); h = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
    pp = hint - np.dot(hint, u) * u
    pp = pp / np.linalg.norm(pp) if np.linalg.norm(pp) > 1e-6 else np.array([0, 0, -1.0])
    return S + a * u + h * pp, S + D * u


class Person:
    def __init__(self, path, speed, vest, waits=None, t0=0.0, look="passante"):
        self.path = [np.array(p, float) for p in path]
        self.speed, self.vest, self.waits, self.t0 = speed, vest, waits or {}, t0
        self.pos, self.yaw, self.phase, self.moving = self.path[0].copy(), 0.0, 0.0, False
        self.i, self.tw, self.active = 0, 0.0, False
        self.look = H_LOOKS[look]; self.r_reach, self.reach_tgt, self.carry = 0.0, None, False
        self.face_yaw, self.hand_r = None, None
        self.v_s = 0.0                                   # velocita' filtrata (avvio/arresto morbidi del passo)
        self.stop_at_end, self.crate, self.crate_c = False, False, None

    def step(self, t, dt):
        self.active = t >= self.t0
        if not self.active:
            return
        self.cb = min(1.0, getattr(self, "cb", 0.0) + dt / 1.2) if self.carry else 0.0
        self.sb = float(np.clip(getattr(self, "sb", 0.0) + (dt / 0.9 if getattr(self, "sip", False) else -dt / 0.9), 0.0, 1.0))
        goal_r = 1.0 if self.reach_tgt is not None else 0.0
        self.r_reach += float(np.clip(goal_r - self.r_reach, -dt / 0.8, dt / 0.8))
        at_end = self.stop_at_end and self.i == len(self.path) - 1
        if self.tw > 0 or at_end:
            self.tw = max(0.0, self.tw - dt); self.moving = False
            self.v_s = max(0.0, self.v_s - dt * 2.0)
            if self.face_yaw is not None:
                self.yaw += float(np.clip((self.face_yaw - self.yaw + math.pi) % (2 * math.pi) - math.pi, -dt * 2.5, dt * 2.5))
            self.phase += self.v_s * dt / 0.75 * math.pi
            return
        nxt = self.path[(self.i + 1) % len(self.path)]
        dv = nxt - self.pos
        dist = np.linalg.norm(dv)
        if dist < 1e-6 and all(np.linalg.norm(q - self.pos) < 1e-6 for q in self.path):   # persona ferma (alla scrivania)
            self.moving = False; self.v_s = max(0.0, self.v_s - dt * 2.0)
            if self.face_yaw is not None:
                self.yaw += float(np.clip((self.face_yaw - self.yaw + math.pi) % (2 * math.pi) - math.pi, -dt * 2.5, dt * 2.5))
            return
        try:                                             # cede il passo al robot (nessuno attraversa Giorgio)
            rb = base_pose()[:2]
            ahead = self.pos + (dv / max(dist, 1e-9)) * min(0.35, dist)
            if not getattr(self, "near_ok", False) and np.linalg.norm(ahead - rb) < 0.62 and np.linalg.norm(ahead - rb) < np.linalg.norm(self.pos - rb) + 1e-3:
                self.blocked = getattr(self, "blocked", 0.0) + dt
                self.moving = False; self.v_s = max(0.0, self.v_s - dt * 3.0)
                if self.blocked > 2.5:                   # aggira: ripianifica fino al prossimo punto chiave
                    goal = self.path[-1] if self.stop_at_end else nxt
                    pts = plan_path(self.pos.copy(), np.asarray(goal, float), (), infl=0.30, robot=rb)
                    keep_end = self.stop_at_end
                    self.path = [self.pos.copy()] + [np.asarray(q, float) for q in pts[1:]] + [np.asarray(goal, float)]
                    self.i, self.blocked = 0, 0.0
                    if hasattr(self, "keys") and self.keys and not keep_end:
                        self.keys = []
                return
            self.blocked = 0.0
        except NameError:
            pass
        self.v_s = min(self.speed, self.v_s + dt * 1.5)
        stp = self.v_s * dt
        self.moving = True
        if dist <= stp:
            self.pos = nxt.copy(); self.i = (self.i + 1) % len(self.path)
            self.tw = self.waits.get(self.i, 0.0)
            if self.i in getattr(self, "keys", []):
                self.ki = self.keys.index(self.i)
        else:
            self.pos += dv / dist * stp
            yd = math.atan2(dv[1], dv[0])
            self.yaw += float(np.clip((yd - self.yaw + math.pi) % (2 * math.pi) - math.pi, -dt * 4.0, dt * 4.0))   # gira con naturalezza
        self.phase += stp / 0.75 * math.pi

    def segments(self):
        """17 pezzi (centro, rotazione, semiassi, colore): cammino con ginocchia e gomiti, testa che guarda il robot, presa con la mano"""
        L = self.look; c, s_ = math.cos(self.yaw), math.sin(self.yaw)
        f, l, u = np.array([c, s_, 0]), np.array([-s_, c, 0]), np.array([0, 0, 1.0])
        P = np.array([self.pos[0], self.pos[1], 0.0])
        g = min(1.0, self.v_s / 0.5)                     # ampiezza del passo
        ph = self.phase
        legs = []
        for k in (1, -1):                                # 1 = sinistra, -1 = destra
            phk = ph if k > 0 else ph + math.pi
            th = 0.38 * g * math.sin(phk)
            kn = 0.08 + g * (0.75 * max(0.0, math.cos(phk)) ** 1.5 + 0.12)
            d1 = -u * math.cos(th) + f * math.sin(th)
            d2 = -u * math.cos(th - kn) + f * math.sin(th - kn)
            legs.append((k, d1, d2, th - kn))
        # altezza del bacino: il piede piu' basso tocca terra
        low = min(0.45 * d1[2] + 0.44 * d2[2] for _, d1, d2, _ in legs)
        pz = 0.075 - low + 0.0
        pel = P + u * pz
        lean = 0.06 * g
        if self.reach_tgt is not None:                   # si china per arrivare in basso (scrivania)
            lean += self.r_reach * float(np.clip((1.12 - self.reach_tgt[2]) * 1.6, 0.0, 0.55))
        up_t = _frame(u * math.cos(lean) + f * math.sin(lean), f)[:, 2]
        out = []
        out.append((pel + u * 0.03, _frame(u, f), (0.115, 0.175, 0.10), L["pants"]))                  # 0 bacino
        tor = pel + up_t * 0.30
        out.append((tor, _frame(up_t, f), (0.12, 0.195, 0.27), L["vest"] or L["shirt"]))              # 1 busto
        neck = pel + up_t * 0.585
        out.append((neck, _frame(up_t, f), (0.048, 0.035, 0), L["skin"]))                             # 2 collo
        # testa: guarda il robot se vicino
        hy = 0.0
        try:
            rb = base_pose()[:2]; dv = rb - self.pos
            if np.linalg.norm(dv) < 3.5:
                hy = float(np.clip((math.atan2(dv[1], dv[0]) - self.yaw + math.pi) % (2 * math.pi) - math.pi, -1.0, 1.0))
        except Exception:
            pass
        fh = f * math.cos(hy) + l * math.sin(hy)
        head = pel + up_t * 0.725
        out.append((head, _frame(u, fh), (0.10, 0.086, 0.118), L["skin"]))                           # 3 testa
        if L["helmet"] is not None:
            out.append((head + u * 0.055 - fh * 0.005, _frame(u, fh), (0.115, 0.105, 0.075), L["helmet"]))   # 4 casco
        else:
            out.append((head + u * 0.04 - fh * 0.014, _frame(u, fh), (0.104, 0.093, 0.09), L["hair"]))     # 4 capelli
        # braccia: oscillazione nel cammino, oppure presa/trasporto (IK a 2 segmenti)
        arms = []
        for k in (1, -1):
            sh = pel + up_t * 0.50 + l * 0.205 * k
            phk = ph + math.pi if k > 0 else ph
            al = 0.32 * g * math.sin(phk)
            el = 0.18 + 0.25 * g
            a1 = -u * math.cos(al) + f * math.sin(al) + l * 0.06 * k
            a1 /= np.linalg.norm(a1)
            a2 = -u * math.cos(al + el) + f * math.sin(al + el) + l * 0.03 * k
            a2 /= np.linalg.norm(a2)
            E, W = sh + 0.29 * a1, sh + 0.29 * a1 + 0.27 * a2
            if self.crate:                                   # cassetta davanti alla pancia, una mano per sponda
                cc = pel + f * 0.30; cc[2] = 1.0; self.crate_c = cc
                Th = cc + l * (CR_L - 0.012) * k + u * (CR_H - 0.005)
                if k < 0 and self.r_reach > 1e-3 and self.reach_tgt is not None:
                    Th = (1 - self.r_reach) * Th + self.r_reach * (np.asarray(self.reach_tgt, float) - f * 0.0)
                E, W = _ik2(sh, Th - (Th - sh) / max(np.linalg.norm(Th - sh), 1e-6) * 0.075, 0.29, 0.27, -u + l * 0.6 * k)
                a1 = (E - sh) / np.linalg.norm(E - sh); a2 = (W - E) / np.linalg.norm(W - E)
            elif k < 0 and (self.r_reach > 1e-3 or self.carry):
                if self.carry:
                    Tc = sh + f * 0.32 - u * 0.36 + l * 0.10
                    Ts = head + f * 0.13 - u * 0.13 + l * 0.03           # sorso: bicchiere alla bocca
                    Tc = Tc + (Ts - Tc) * (0.5 - 0.5 * math.cos(math.pi * getattr(self, "sb", 0.0)))
                    cf = getattr(self, "carry_from", Tc)
                    T = cf + (Tc - cf) * (0.5 - 0.5 * math.cos(math.pi * self.cb))
                else:
                    T = np.asarray(self.reach_tgt, float) - f * 0.05 if self.reach_tgt is not None else W
                r = 1.0 if self.carry else self.r_reach
                Tb = (1 - r) * W + r * T
                Tb = Tb - (Tb - sh) / max(np.linalg.norm(Tb - sh), 1e-6) * 0.075 * r   # il bersaglio e' il centro della mano, non il polso
                E, W = _ik2(sh, Tb, 0.29, 0.27, -u + l * 0.5 * k)
                a1 = (E - sh) / np.linalg.norm(E - sh); a2 = (W - E) / np.linalg.norm(W - E)
            arms.append((k, sh, E, W, a1, a2))
        for k, sh, E, W, a1, a2 in arms:
            out.append(((sh + E) / 2, _frame(a1, f), (0.047, 0.125, 0), L["vest"] or L["shirt"] if False else L["shirt"]))   # 5,6 braccio
        for k, sh, E, W, a1, a2 in arms:
            out.append(((E + W) / 2, _frame(a2, f), (0.039, 0.115, 0), L["shirt"]))                  # 7,8 avambraccio (maniche lunghe)
        for k, sh, E, W, a1, a2 in arms:
            hc = W + a2 * 0.075
            out.append((hc, _frame(a2, l * k), (0.022, 0.044, 0.07), L["skin"]))                      # 9,10 mani
            if k < 0:
                self.hand_r = hc
        for k, d1, d2, fa in legs:
            hip = pel + l * 0.095 * k - u * 0.02
            out.append((hip + d1 * 0.225, _frame(d1, f), (0.068, 0.17, 0), L["pants"]))               # 11,12 coscia
        for k, d1, d2, fa in legs:
            hip = pel + l * 0.095 * k - u * 0.02; kn_ = hip + d1 * 0.45
            out.append((kn_ + d2 * 0.215, _frame(d2, f), (0.052, 0.18, 0), L["pants"]))               # 13,14 stinco
        for k, d1, d2, fa in legs:
            hip = pel + l * 0.095 * k - u * 0.02; ank = hip + d1 * 0.45 + d2 * 0.44
            pt = float(np.clip(fa, -0.35, 0.35)) * 0.6
            fx = f * math.cos(pt) + u * math.sin(pt)
            out.append((ank + f * 0.055 - u * 0.035, _frame(np.cross(fx, l), fx), (0.13, 0.05, 0.04), SHOE))   # 15,16 scarpe
        return out


people = []


def spawn(idx, path, speed, vest, waits=None, look=None):
    """persona su percorso pianificato (A*): aggira banchi, scrivanie e il robot; i nodi 'chiave' restano quelli dati"""
    rb = base_pose()[:2]
    full, key, w2 = [np.asarray(path[0], float)], [0], {}
    for i in range(1, len(path)):
        a_, b_ = np.asarray(path[i - 1], float), np.asarray(path[i], float)
        if np.linalg.norm(b_ - a_) > 0.05:
            seg = plan_path(a_, b_, (), infl=0.30, robot=rb)[1:]
        else:
            seg = [b_]
        full += [np.asarray(q, float) for q in seg]
        key.append(len(full) - 1)
        if waits and i in waits:
            w2[len(full) - 1] = waits[i]
    if look is None:
        look = {0: "operatore", 1: "passante", 2: "passante2"}.get(idx, "Marco")
    p = Person(full, speed, vest, w2, t0=d.time, look=look)
    p.idx = idx; p.once = True; p.keys = key
    people[:] = [q for q in people if q.idx != idx] + [p]
    return p


def place_people():
    used = set()
    for p in people:
        h = p.idx; used.add(h)
        if h >= NH:
            continue
        segs = p.segments() if p.active else []
        for k in range(N_SEG):
            mid = m.body_mocapid[m.body(f"h{h}_{k}").id]; gid = m.geom(f"h{h}_{k}_g").id
            if not segs:
                d.mocap_pos[mid] = [0, 0, -10]; continue
            c, Rm, sz, col = segs[k]
            q = Rot.from_matrix(Rm).as_quat()
            d.mocap_pos[mid] = c; d.mocap_quat[mid] = [q[3], q[0], q[1], q[2]]
            m.geom_size[gid] = [sz[0], sz[1], sz[2]] if H_TYPES[k] == "E" else [sz[0], sz[1], 0]; m.geom_rgba[gid] = list(col) + [1]
    for h in range(NH):
        if h not in used:
            for k in range(N_SEG):
                d.mocap_pos[m.body_mocapid[m.body(f"h{h}_{k}").id]] = [0, 0, -10]


# ---------------------------------------------------------------- scanner
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
    if FIELDS["mode"] == "servizio":                   # consegna: robot fermo, persona attesa vicino al retro
        pass
    zone, hits = 0, []
    c = d.body("amr").xpos[:2]
    for k, (o, vec, dist) in enumerate(scan_once()):
        pts = o + vec * dist[:, None]
        if FIELDS["mode"] == "fermo" and REF is not None:
            ref_min = ndimage.minimum_filter1d(REF[k], 7, mode="nearest")    # tolleranza angolare sul contorno (+-3 raggi)
            intr = dist < ref_min - 0.07
        else:
            intr = dist < SCAN_MAX - 0.01
        dc = np.linalg.norm(pts[:, :2] - c, axis=1)
        z = np.where(intr & (dc < FIELDS["prot"]), 2, np.where(intr & (dc < FIELDS["warn"]), 1, 0))
        zone = max(zone, int(z.max())); hits.append((o, pts, z))
    return zone, hits




# ---------------------------------------------------------------- visione
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
            ql = np.array([local_rel(pt_) for pt_ in q[:, :2]])         # nel frame del robot: x = verso il banco
            qlx = (ql[:, 0].min(), ql[:, 0].max(), 0.5 * (ql[:, 1].min() + ql[:, 1].max()))
            if not (np.all(ctr > lo_ + 0.02) and np.all(ctr < hi_ - 0.02)) or ext.min() < 0.03 or ext.max() > HOLE + 0.02:
                continue
            dets.append(dict(xy=ctr, box=(xx.min(), yy.min(), xx.max(), yy.max()), kind="foro", qlx=qlx))
        if len(dets) >= 3:                                   # fori col bordo vicino coperto dal vassoio: centro dal bordo lontano
            med = float(np.median([dt["qlx"][1] - dt["qlx"][0] for dt in dets]))
            for dt in dets:
                x0_, x1_, yc_ = dt["qlx"]
                if x1_ - x0_ < med - 0.004:
                    dt["xy"] = local_to_world(base_pose(), x1_ - med / 2, yc_)[:2]
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
# ---------------------------------------------------------------- energia: batteria di sistema 48 V, consumi, ricarica automatica
BAT = {"E": args.soc * args.bat_wh, "cap": args.bat_wh, "P": 0.0, "charging": False, "heater": False, "Pavg": 0.0, "log_t": 0.0}
P_ELEC = 40 + 2 * 4.5 + 5 + 4 + 5 + 6 + 8 + 15         # Jetson, 2 scanner, PNOZ, Gemini, Insta360, LED volto+base, elettronica base [W]
P_ARM_IDLE, K_CU, ETA_DRIVE, P_HEATER, P_CHARGE, CHARGE_X, BREW_X = 10.0, 0.04, 0.85, 1260.0 / 0.92, CHARGE_W, 30.0, 30.0 / 8.0   # inverter 92%
ARM_DOFS = [m.jnt_dofadr[m.actuator_trnid[a_, 0]] for s_ in ("right", "left") for a_ in [m.actuator(f"{s_}_joint{k}_ctrl").id for k in range(1, 8)]]
DRIVE_ACT = [m.actuator("drive_left_vel").id, m.actuator("drive_right_vel").id]


def soc():
    return BAT["E"] / BAT["cap"]


def dock_error():
    """piastra posteriore del robot rispetto ai contatti della stazione, nel frame della stazione: (spazio, scarto laterale, angolo).
    Il robot si aggancia in retromarcia: guarda verso -x della stazione."""
    x, y, th = base_pose()
    c, s_ = math.cos(CHG[2]), math.sin(CHG[2])
    dx, dy = x - CHG[0], y - CHG[1]
    lx, ly = c * dx + s_ * dy, -s_ * dx + c * dy
    gap = DOCK_FACE_X - (lx + DOCK_REAR_X)               # contatti stazione - contatti posteriori del robot (Ranger: spazzole a 0.365 /
                                                         # lamelle a 0.363; rev B: collettore RoboPad a 0.388, gap 0 = posa di aggancio CAD)
    return gap, ly, wrap(th - CHG[2] - math.pi)


def docked_at_charger():
    """contatti chiusi: contatti posteriori sui contatti della stazione (corsa 10 mm), allineati entro 20 mm e 3 gradi
    (tolleranze ASSUNTE: AgileX non le pubblica; RoboPad rev B: da confermare con Roboteq)"""
    gap, ly, dth = dock_error()
    return -0.010 < gap < 0.004 and abs(ly) < 0.020 and abs(dth) < math.radians(3)


def energy_step():
    """consumo istantaneo: motori dei bracci (meccanica + perdite rame), ruote, elettronica, caffettiera; ricarica ai contatti"""
    tau = d.qfrc_actuator[ARM_DOFS] + d.qfrc_applied[ARM_DOFS]
    p_arm = float(np.sum(np.maximum(tau * d.qvel[ARM_DOFS], 0.0)) + K_CU * np.sum(tau ** 2)) + 2 * P_ARM_IDLE
    p_drv = 0.0
    for a_ in DRIVE_ACT:
        p_drv += abs(float(d.actuator_force[a_] * d.qvel[m.jnt_dofadr[m.actuator_trnid[a_, 0]]]))
    p = P_ELEC + p_arm + p_drv / ETA_DRIVE + (P_HEATER if BAT["heater"] else 0.0)
    p_e = p + (P_HEATER * (BREW_X - 1.0) if BAT["heater"] else 0.0)    # erogazione compressa nel video: energia reale (~30 s a 1260 W)
    BAT["charging"] = docked_at_charger()
    e_in = P_CHARGE * 0.92 * CHARGE_X if BAT["charging"] and soc() < 0.995 else 0.0      # tempo di ricarica accelerato nel video
    BAT["E"] = float(np.clip(BAT["E"] + (e_in - p_e) * DT / 3600.0, 0.0, BAT["cap"]))
    BAT["P"] = p; BAT["Pavg"] += 0.002 * (p - BAT["Pavg"])


GRIP = {s: (m.actuator(f"{s}_finger1_ctrl").id if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{s}_finger1_ctrl") >= 0 else None)
        for s in ("right", "left")}
SGN = {"right": -1, "left": 1}
IK = {s: ArmIK(m, s, f"{s}_grasp") for s in ("right", "left")}
YAW_HAND = {"right": math.pi / 2, "left": -math.pi / 2}      # pinza simmetrica: il braccio sinistro usa l'orientazione speculare


def yaw_of(body):
    R = d.body(body).xmat.reshape(3, 3)
    return math.atan2(R[1, 0], R[0, 0])


def base_pose():
    return np.array([d.body("amr").xpos[0], d.body("amr").xpos[1], yaw_of("amr")])


def smooth(u):
    return u * u * u * (10 - 15 * u + 6 * u * u)


STATS_CLASH = {"evitati": 0, "non_risolti": 0}
DEBUG_CLASH = bool(os.environ.get("DEBUG_CLASH"))
OBJ_GEOMS = [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.startswith(("part_", "pz", "cup")) and m.geom_contype[g] + m.geom_conaffinity[g] > 0
             and m.body(m.geom_bodyid[g]).name != "cup_rest"]
ARM_GEOMS = {s_: [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.startswith(f"openarm_{s_}_") and m.geom_contype[g] + m.geom_conaffinity[g] > 0
                  and m.body(m.geom_bodyid[g]).name not in (f"openarm_{s_}_base_link", f"openarm_{s_}_link1")] for s_ in ("right", "left")}


class Seg:
    def __init__(self, kind, qa=None, qb=None, dur=0.5, grip=None, ev=None):
        self.kind, self.qa, self.qb, self.dur, self.grip, self.ev = kind, qa, qb, dur, grip, ev


class Arm:
    def __init__(self, s):
        self.s, self.sg, self.ik = s, SGN[s], IK[s]
        self.q = np.array([d.qpos[a] for a in self.ik.qadr]); self.grip = GRIP_PART[s]
        self.segs, self.i, self.t, self.held, self.target, self.queue = [], 0, 0.0, None, None, []

    def R(self):
        return Rot.from_euler("z", yaw_of("amr") + YAW_HAND[self.s]).as_matrix()

    def solve(self, p, q0):
        qc, _, _ = self.ik.solve1(d.qpos.copy(), q0, np.asarray(p, float), self.R())       # prima: stesso ramo della posa attuale
        pc, Rc = self.ik.fk(d.qpos, qc)
        if np.linalg.norm(pc - p) < 0.002 and np.linalg.norm(self.ik.err(pc, Rc, np.asarray(p, float), self.R())[3:]) < 0.02:
            return qc
        q, ok, ep, er = self.ik.solve(d.qpos.copy(), q0, np.asarray(p, float), self.R())
        if not ok:                                       # secondo tentativo: semi piu' lontani (altro ramo del braccio)
            q2, ok2, ep2, er2 = self.ik.solve(d.qpos.copy(), q0, np.asarray(p, float), self.R(), seeds=96, noise=1.3,
                                              rng=np.random.default_rng(7))
            if ep2 + 0.1 * er2 < ep + 0.1 * er:
                q, ok, ep, er = q2, ok2, ep2, er2
        if not ok:
            print(f"[{self.s}] IK imprecisa su {np.round(p, 3)}: {ep * 1000:.1f} mm", flush=True)
        return q

    def line(self, pa, pb, q0, dur, n=10):
        qs, q, R = [], q0, self.R()
        for u in np.linspace(0, 1, n + 1)[1:]:
            q, _, _ = self.ik.solve1(d.qpos.copy(), q, pa + (pb - pa) * u, R); qs.append(q)
        segs, qp = [], q0
        for qn in qs:
            segs.append(Seg("lin", qp, qn, dur / n)); qp = qn
        return segs, qp

    def _jseg(self, qa, qb):
        return Seg("joint", qa, qb, max(0.7, float(np.max(np.abs(qb - qa))) / 1.4 * 1.9))

    def held_len(self):
        """quanto sporge sotto la pinza l'oggetto tenuto (0 se la pinza e' vuota)"""
        if not self.held:
            return 0.0
        g = m.body(self.held).id
        gs = [k for k in range(m.ngeom) if m.geom_bodyid[k] == g and m.geom_type[k] == mujoco.mjtGeom.mjGEOM_CYLINDER]
        bottom = min(d.geom_xpos[k][2] - m.geom_size[k][1] for k in gs) if gs else d.body(self.held).xpos[2]
        return max(0.0, d.site(f"{self.s}_grasp").xpos[2] - bottom), (max(m.geom_size[k][0] for k in gs) if gs else 0.03)

    def clash(self, qa, qb, n=14, margin=0.012):
        """il percorso in giunti qa->qb tocca un oggetto gia' posato? bracci (geometrie di collisione) e oggetto tenuto"""
        objs = [g for g in OBJ_GEOMS if m.body(m.geom_bodyid[g]).name != self.held]
        if not objs:
            return False
        arm = ARM_GEOMS[self.s]; ik = self.ik; ft = np.zeros(6)
        hl = self.held_len() if self.held else None
        for u in np.linspace(0, 1, n + 1)[1:-1]:
            ps, _ = ik.fk(d.qpos, qa + (qb - qa) * smooth(u))
            for e in objs:
                if hl:                                   # oggetto tenuto: cilindro verticale sotto la pinza
                    L, r = hl; c = ik.d.geom_xpos[e]; re, he = m.geom_size[e][0], m.geom_size[e][1]
                    if np.linalg.norm(ps[:2] - c[:2]) < r + re + margin and ps[2] - L < c[2] + he + margin and ps[2] > c[2] - he:
                        return True
                for g in arm:
                    if np.linalg.norm(ik.d.geom_xpos[g] - ik.d.geom_xpos[e]) < 0.25 and \
                            mujoco.mj_geomDistance(m, ik.d, g, e, margin + 0.01, ft) < margin:
                        return True
        return False

    def jmove(self, qa, qb):
        """movimento in giunti; se spazzerebbe un oggetto gia' posato (col braccio o con l'oggetto in mano) passa sopra"""
        self._alt_end = None
        mg = 0.012
        while mg > 0.002 and (self.clash(qa, qa, n=2, margin=mg) or self.clash(qb, qb, n=2, margin=mg)):
            mg -= 0.004                                  # partenza/arrivo obbligati vicino a un oggetto: margine ridotto
        self._mg = mg
        if not self.clash(qa, qb, margin=mg):
            if DEBUG_CLASH:
                print(f"      [jmove {self.s} t={d.time:.1f}] libero: {np.round(self.ik.fk(d.qpos, qa)[0], 3)} -> {np.round(self.ik.fk(d.qpos, qb)[0], 3)}", flush=True)
            return self._jseg(qa, qb)
        R = self.R()
        objs = [g for g in OBJ_GEOMS if m.body(m.geom_bodyid[g]).name != self.held]
        z_top = max([d.geom_xpos[g][2] + m.geom_size[g][1] for g in objs] + [0.0])
        below = (self.held_len()[0] if self.held else 0.0) + 0.05      # oggetto tenuto + dita
        pa, _ = self.ik.fk(d.qpos, qa); pb, _ = self.ik.fk(d.qpos, qb)
        dist = float(np.linalg.norm(pb - pa))                   # 1) linea retta tra i due punti (entrambi gia' alti)
        mid, qm = self.line(pa, pb, qa, max(0.6, dist / 0.35), n=max(4, int(dist / 0.03)))
        if np.linalg.norm(self.ik.fk(d.qpos, qm)[0] - pb) < 0.01 and all(not self.clash(sg_.qa, sg_.qb, n=3, margin=mg) for sg_ in mid):
            STATS_CLASH["evitati"] += 1
            if self.clash(qm, qb, margin=mg):            # arrivo su un'altra configurazione: chi chiama prosegue da qm (niente ribaltamento)
                self._alt_end = qm
            return mid + [self._jseg(qm, qb)]
        for lift in (0.03, 0.08, 0.14, 0.22):                   # 2) salita, tratto alto, discesa: tutti in linea retta sullo stesso ramo
            zc = z_top + below + lift
            p1 = np.array([pa[0], pa[1], max(pa[2], zc)]); p2 = np.array([pb[0], pb[1], max(pb[2], zc)])
            segs, q = [], qa
            for u_, v_ in ((pa, p1), (p1, p2), (p2, pb)):
                L_ = float(np.linalg.norm(v_ - u_))
                if L_ < 1e-3:
                    continue
                part_, q = self.line(u_, v_, q, max(0.4, L_ / 0.35), n=max(3, int(L_ / 0.03)))
                segs += part_
            err = float(np.linalg.norm(self.ik.fk(d.qpos, q)[0] - pb))
            ok = err < 0.01 and all(not self.clash(sg_.qa, sg_.qb, n=3, margin=mg) for sg_ in segs)
            if DEBUG_CLASH:
                bad = [i_ for i_, sg_ in enumerate(segs) if self.clash(sg_.qa, sg_.qb, n=3, margin=mg)]
                print(f"      [via {lift}] arrivo a {1000 * err:.0f} mm, tratti {len(segs)} urtano {bad} finale {self.clash(q, qb, margin=mg)} mg {mg} | da {np.round(pa, 3)} a {np.round(pb, 3)} tenuto {self.held}", flush=True)
            if ok:
                STATS_CLASH["evitati"] += 1
                if self.clash(q, qb, margin=mg):
                    self._alt_end = q
                return segs + [self._jseg(q, qb)]
        STATS_CLASH["non_risolti"] += 1
        print(f"[{self.s}] percorso vicino a oggetti posati: nessun passaggio alto trovato", flush=True)
        return self._jseg(qa, qb)

    def approach(self, q0, q_t, p_t, p_end):
        """jmove verso q_t (sopra p_end); se si arriva su un'altra configurazione che sa scendere in linea fino a p_end, si resta su quella"""
        mv = self.jmove(q0, q_t)
        alt = getattr(self, "_alt_end", None)
        if isinstance(mv, list) and alt is not None:
            s_, q_ = self.line(p_t, p_end, alt, 1.1)
            _, q_ref = self.line(p_t, p_end, q_t, 1.1)
            e_alt = np.linalg.norm(self.ik.fk(d.qpos, q_)[0] - p_end); e_ref = np.linalg.norm(self.ik.fk(d.qpos, q_ref)[0] - p_end)
            if DEBUG_CLASH:
                print(f"      [arrivo alternativo] discesa {1000 * e_alt:.0f} mm (riferimento {1000 * e_ref:.0f} mm)", flush=True)
            if e_alt < max(0.003, e_ref + 0.002) and not any(self.clash(g_.qa, g_.qb, n=2, margin=0.004) for g_ in s_):
                return mv[:-1], alt
        return (mv if isinstance(mv, list) else [mv]), q_t

    def robot_pt(self, xl, yl, z):
        p = local_to_world(base_pose(), xl, yl)
        return np.array([p[0], p[1], z])

    def plan_pose(self, xl, yl, dz):
        q = self.solve(self.robot_pt(xl, self.sg * yl, Z_GRASP + dz), self.q)
        return [self.jmove(self.q, q)]

    def plan_pose_from(self, q0, xl, yl, dz):
        q = self.solve(self.robot_pt(xl, self.sg * yl, Z_GRASP + dz), q0)
        return [self.jmove(q0, q)]

    def pick(self, a, part, q0, z_base, h=None, down_first=False, wide=None):
        """presa verticale vicino alla sommita' di un oggetto (flacone o bicchiere) il cui fondo e' a z_base"""
        h = PH if h is None else h
        zg = z_base + h - (0.028 if h > 0.1 else 0.03)
        a = np.array([a[0], a[1], zg]); up = np.array([0, 0, 0.12])
        if down_first:                                   # oggetti bassi: prima la posa di presa, poi l'avvicinamento sullo stesso ramo
            q_dn = self.solve(a, q0)
            q_pre, _, _ = self.ik.solve1(d.qpos.copy(), q_dn, a + up, self.R())
        else:
            q_pre = self.solve(a + up, q0)
        if wide is None:
            wide = abs(z_base - BUF_Z) < 1e-6 or h < 0.1
        g_open = (0.785 if self.s == "left" else -0.785) if wide else GRIP_PART[self.s]   # vassoio: apertura piena
        mv, q_pre = self.approach(q0, q_pre, a + up, a)
        segs = [Seg("grip", dur=0.25, grip=g_open)] + mv + [Seg("wait", dur=0.45)]   # assestamento polso
        s1, q_g = self.line(a + up, a, q_pre, 1.1); segs += s1
        pf, _ = self.ik.fk(d.qpos.copy(), q_g)
        if np.linalg.norm(pf - a) > 0.003:
            print(f"    [IK linea] {self.s}: fine discesa a {1000 * np.linalg.norm(pf - a):.0f} mm dal punto di presa", flush=True)
        self.goal = a
        segs += [Seg("grip", dur=0.4, grip=0.0, ev=("grip", part)), Seg("wait", dur=0.15)]
        s2, q_up = self.line(a, a + np.array([0, 0, 0.20]), q_g, 0.8); segs += s2     # alto: sopra i flaconi gia' posati
        return segs, q_up

    def place(self, b, part, q0, z_base, ev, drop=0.0, h=None, down_first=False):
        """deposito: fondo dell'oggetto a z_base + drop, apertura parziale"""
        h = PH if h is None else h
        zg = z_base + drop + h - (0.028 if h > 0.1 else 0.03)
        if self.held == part and part.startswith("pz"):  # pezzo scivolato nella presa: rilascio con il fondo 5 mm sopra il piano (telecamera di polso)
            bp = d.body(part); ax = bp.xmat.reshape(3, 3)[:, 2]
            bottom_z = bp.xpos[2] - abs(ax[2]) * h / 2 - (1 - abs(ax[2])) * SR_
            zg = z_base + 0.005 + (d.site(f"{self.s}_grasp").xpos[2] - bottom_z)
        b = np.array([b[0], b[1], zg]); up = np.array([0, 0, 0.17])
        if self.held == part and part in PARTS:          # posa in mano stimata (telecamera di polso): compenso offset e inclinazione
            bp = d.body(part); ax = bp.xmat.reshape(3, 3)[:, 2]
            bottom = bp.xpos - ax * h / 2
            Rs = d.site(f"{self.s}_grasp").xmat.reshape(3, 3)
            v = Rs.T @ (bottom - d.site(f"{self.s}_grasp").xpos)
            off = (self.R() @ v)[:2]
            b[:2] = np.asarray(b[:2]) - off
            self.inhand_mm = 1000 * np.linalg.norm(off - (self.R() @ np.array([0, 0, -(h - 0.035)]))[:2])
        if down_first:                                   # come nella presa: posa di deposito, poi l'avvicinamento sullo stesso ramo
            q_dn = self.solve(b, q0)
            q_bu, _, _ = self.ik.solve1(d.qpos.copy(), q_dn, b + up, self.R())
        else:
            q_bu = self.solve(b + up, q0)
        mv, q_bu = self.approach(q0, q_bu, b + up, b)
        segs = mv + [Seg("wait", dur=0.45)]
        s3, q_b = self.line(b + up, b, q_bu, 1.1); segs += s3
        pf, _ = self.ik.fk(d.qpos.copy(), q_b)
        if np.linalg.norm(pf - b) > 0.003:
            print(f"    [IK linea] {self.s}: fine discesa (deposito) a {1000 * np.linalg.norm(pf - b):.0f} mm, {np.round(1000 * (pf - b))}", flush=True)
        segs += [Seg("wait", dur=0.15), Seg("grip", dur=0.3, grip=GRIP_PART[self.s], ev=("release", part)), Seg("wait", dur=0.35)]
        s4, q_r = self.line(b, b + up, q_b, 0.5); segs += s4
        segs[-1].ev = (ev, part)
        return segs, q_r

    def start(self, segs):
        flat = []                                        # jmove puo' restituire piu' tratti (passaggio alto sopra gli oggetti)
        for sg_ in segs:
            flat += sg_ if isinstance(sg_, list) else [sg_]
        self.segs, self.i, self.t, self._g0 = flat, 0, 0.0, self.grip

    @property
    def busy(self):
        return bool(self.segs)

    def step(self, dt, k):
        if not self.segs:
            if self.queue:
                self.start(self.queue.pop(0)())
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
        if GRIP[self.s] is not None:
            d.ctrl[GRIP[self.s]] = self.grip


# posa "pronto" (base nell'origine), poi robot agganciato in A
for s_ in ("right", "left"):
    tgt_r = np.array([0.30, SGN[s_] * 0.20, Z_GRASP + 0.30]); R0 = Rot.from_euler("z", YAW_HAND[s_]).as_matrix()   # riposo alto
    best = None
    for sg_ in itertools.product((1, -1), repeat=7):
        sd = np.clip(np.array([-0.59, 2.38, 0.36, 1.63, 0.79, 0.3, 1.19]) * np.array(sg_), IK[s_].lo, IK[s_].hi)
        q, ep, er = IK[s_].solve1(d.qpos.copy(), sd, tgt_r, R0, 150)
        c = ep * 1000 + er * 100 + 0.05 * np.sum(np.abs(q - (IK[s_].lo + IK[s_].hi) / 2))
        if best is None or c < best[0]:
            best = (c, q)
    d.qpos[IK[s_].qadr] = best[1]; d.ctrl[ARM_ACT[s_]] = best[1]
d.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A"][0], DOCK["A"][1], 0.0]
d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(DOCK["A"][2] / 2), 0, 0, math.sin(DOCK["A"][2] / 2)]
mujoco.mj_forward(m, d)
def set_part_xyz(p, pos):
    j = m.body(p).jntadr[0]; qa, va = m.jnt_qposadr[j], m.jnt_dofadr[j]
    d.qpos[qa:qa + 3] = pos; d.qpos[qa + 3:qa + 7] = [1, 0, 0, 0]; d.qvel[va:va + 6] = 0


def reset_cup():
    """bicchiere in cima alla pila sullo zaino, vuoto"""
    p_ = local_to_world(base_pose(), *COF_STACK)
    set_part_xyz("cup", np.array([p_[0], p_[1], CUP_TOP0 + CUP_H / 2 + 0.001]))
    g = m.geom("cup_coffee").id; m.geom_size[g][1] = 0.0005; m.geom_pos[g][2] = -CUP_H / 2 + 0.002
    for i in range(3):
        m.geom_rgba[m.geom(f"cup_steam{i}").id][3] = 0.0
    mujoco.mj_forward(m, d)


reset_cup()
for p_ in PARTS:                                        # all'avvio i flaconi sono nel vassoio di kitting del banco A
    set_part_xyz(p_, a_pocket(p_))
mujoco.mj_forward(m, d)
arms = {s: Arm(s) for s in ("right", "left")}
Q_HOME = {s: a.q.copy() for s, a in arms.items()}

stats = {"inserted": 0, "lost": 0, "loaded": 0, "cycles": 0, "stops": 0, "slows": 0, "vis_err": []}
mission = {"state": "settle", "t": 0.0, "log": [], "route": None}
expr = {"happy_t": -10.0}
FACE = [0, 0.0, 0.0, 0.0, 0.0]


def log(msg):
    print(f"[t={d.time:6.1f}s] {msg}", flush=True)
    mission["log"] = (mission["log"] + [msg])[-4:]


def on_event(a, ev, part):
    if ev == "grip":
        a.held = part
        pp = d.body(part).xpos; gs = d.site(f"{a.s}_grasp").xpos
        g_ = getattr(a, "goal", gs)
        print(f"    [presa] {a.s} {part}: flacone a {1000 * np.linalg.norm(pp[:2] - gs[:2]):.0f} mm dalla pinza; pinza a {1000 * np.linalg.norm(gs - g_):.0f} mm dal comando", flush=True)
    elif ev == "loaded":
        stats["loaded"] += 1; a.held = None
        pp = d.body(part).xpos; k = min(range(N_SLOTS), key=lambda k_: np.linalg.norm(buffer_xy(a.s, k_) - pp[:2]))
        print(f"    [buffer] {a.s} {part}: {1000 * np.linalg.norm(buffer_xy(a.s, k) - pp[:2]):.0f} mm dall'alloggio {k}, z {pp[2]:.3f}", flush=True)
    elif ev == "release" and False:
        pass
    elif ev == "button":
        m.geom_rgba[m.geom("cm_btn1").id] = [1.0, 0.8, 0.4, 1]
    elif ev == "cup_on_grid":
        a.held = None
    elif ev == "inserted":
        p = d.body(part).xpos; tgt = a.target
        err = 1000 * np.linalg.norm(p[:2] - tgt) if tgt is not None else -1
        ok = abs(p[2] - ZC) < 0.012 and err < 6
        stats["inserted" if ok else "lost"] += 1
        if ok:
            expr["happy_t"] = d.time
        log(f"{a.s}: flacone {'INSERITO' if ok else 'NON INSERITO'} ({err:.1f} mm dal centro del foro)")
        a.held = None


# ---------------------------------------------------------------- guida AMR fluida
WL, WR = m.actuator("drive_left_vel").id, m.actuator("drive_right_vel").id
BT = {"p": None}
MOC_BT = m.body("base_target").mocapid[0] if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base_target") >= 0 else -1


def base_target_step():
    """integra v e omega comandati (dalle velocita' ruota, cinematica differenziale) nel bersaglio cinematico della base"""
    if MOC_BT < 0:
        return
    x, y, th = base_pose()
    if BT["p"] is None or np.linalg.norm(BT["p"][:2] - [x, y]) > 0.10:      # avvio o spostamento manuale: riallinea
        BT["p"] = np.array([x, y, th])
    wl, wr = d.ctrl[WL], d.ctrl[WR]
    v = WHEEL_R * (wl + wr) / 2; w = WHEEL_R * (wr - wl) / (2 * B_HALF)
    p_ = BT["p"]; p_[0] += v * math.cos(p_[2]) * DT; p_[1] += v * math.sin(p_[2]) * DT; p_[2] = wrap(p_[2] + w * DT)
    d.mocap_pos[MOC_BT] = [p_[0], p_[1], 0.0]; d.mocap_quat[MOC_BT] = [math.cos(p_[2] / 2), 0, 0, math.sin(p_[2] / 2)]
B_HALF, WHEEL_R = DRIVE_HALF_TRACK, DRIVE_WHEEL_R     # rev B: carreggiata 464 mm, ruote D125; Ranger Mini: 364 mm, D 200 (equivalente)
drive = {"v": 0.0, "w": 0.0}
V_MAX, A_LON, A_LAT, W_MAX, A_ROT = 0.6, 0.25, 0.25, 0.7, 0.7
JERK = 0.6                                           # m/s^3: niente "imbarcate" in frenata


def hermite(p0, h0, p1, h1, n=120, k=None):
    L = np.linalg.norm(np.asarray(p1) - p0) * (k or 1.2)
    t0 = L * np.array([math.cos(h0), math.sin(h0)]); t1 = L * np.array([math.cos(h1), math.sin(h1)])
    u = np.linspace(0, 1, n)[:, None]
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * p0 + h10 * t0 + h01 * p1 + h11 * t1


class Leg:
    """tratto continuo: polilinea con direzione (+1 avanti, -1 retro) e profilo di velocita' (curvatura + rampe)"""

    def __init__(self, pts, direction):
        self.P = np.asarray(pts, float); self.dir = direction
        seg = np.linalg.norm(np.diff(self.P, axis=0), axis=1); self.s = np.r_[0, np.cumsum(seg)]
        hd = np.unwrap(np.arctan2(np.diff(self.P[:, 1]), np.diff(self.P[:, 0])))
        kap = np.r_[np.abs(np.diff(hd)) / np.maximum(seg[1:], 1e-4), 0, 0]
        v = np.minimum(V_MAX if direction > 0 else 0.25, np.sqrt(A_LAT / np.maximum(kap, 1e-3)))
        v[0] = v[-1] = 0.0
        for i in range(1, len(v)):                  # rampa in accelerazione
            v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * A_LON * (self.s[i] - self.s[i - 1])))
        for i in range(len(v) - 2, -1, -1):         # rampa in frenata
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * A_LON * (self.s[i + 1] - self.s[i])))
        self.v = v; self.i = 0

    def command(self, pose):
        x, y, th = pose
        lo = self.i; hi = min(len(self.P), self.i + 40)
        self.i = lo + int(np.argmin(np.linalg.norm(self.P[lo:hi] - [x, y], axis=1)))
        rem = self.s[-1] - self.s[self.i]
        self.rem = rem
        Ld = 0.32
        j = int(np.searchsorted(self.s, self.s[self.i] + Ld)); j = min(j, len(self.P) - 1)
        tgt = self.P[j] if rem > 0.05 else self.P[-1] + (self.P[-1] - self.P[-2]) / max(1e-6, np.linalg.norm(self.P[-1] - self.P[-2])) * 0.3
        th_eff = th if self.dir > 0 else th + math.pi
        alpha = wrap(math.atan2(tgt[1] - y, tgt[0] - x) - th_eff)
        # velocita' dal profilo, con avvicinamento finale dolce fino a fermarsi sul punto
        v_prof = max(self.v[min(self.i + 2, len(self.v) - 1)], min(0.06, math.sqrt(2 * A_LON * max(rem, 0))))
        v = self.dir * min(v_prof, math.sqrt(2 * A_LON * max(rem, 0.0)) + 0.01)
        w = 2 * abs(v) * math.sin(alpha) / Ld
        done = rem < 0.004 or (rem < 0.03 and abs(drive["v"]) < 0.02)
        return v, w, done


class Turn:
    def __init__(self, heading, tol_deg=0.8):
        self.h, self.tol = heading, math.radians(tol_deg)

    def command(self, pose):
        e = wrap(self.h - pose[2])
        w = math.copysign(min(W_MAX, math.sqrt(2 * A_ROT * abs(e)) * 0.9), e)
        w = math.copysign(max(abs(w), 0.06), e) if abs(e) > self.tol else w
        return 0.0, w, abs(e) < self.tol and abs(drive["w"]) < 0.08


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def route(to):
    x, y, th = base_pose()
    back = np.array([x, y]) - 0.75 * np.array([math.cos(th), math.sin(th)])
    legs = [Leg(np.linspace([x, y], back, 30), -1)]
    if to == "B":
        legs.append(Turn(-0.35))
        p0 = back; p1 = np.array([-0.95, 0.0])
        legs.append(Leg(np.vstack([hermite(p0, -0.35, p1, 0.0, k=1.1), np.linspace(p1, DOCK["B"][:2], 30)[1:]]), +1))
        legs.append(Turn(0.0))
    elif to == "A":
        legs.append(Turn(math.pi))
        p0 = back; p1 = np.array([-2.4, 0.5])
        legs.append(Leg(np.vstack([hermite(p0, math.pi, p1, math.pi / 2, k=1.0), np.linspace(p1, DOCK["A"][:2], 30)[1:]]), +1))
        legs.append(Turn(math.pi / 2))
    elif to == "W":                                       # punto di attesa 1,1 m davanti alla baia A
        legs.append(Turn(math.pi))
        p0 = back; p1 = np.array([-2.4, 0.35])
        legs.append(Leg(hermite(p0, math.pi, p1, math.pi / 2, k=1.0), +1))
        legs.append(Turn(math.pi / 2))
    elif to == "C":
        legs.append(Turn(-math.pi / 2))
        p0 = back; p1 = local_to_world(CHG, -0.55, 0.0)
        legs.append(Leg(np.vstack([hermite(p0, -math.pi / 2, p1, CHG[2], k=1.0), np.linspace(p1, CHG[:2], 25)[1:]]), +1))
        legs.append(Turn(CHG[2]))
    return legs


def drive_step(k):
    legs = mission["route"]
    v, w, done = legs[0].command(base_pose())
    if isinstance(legs[0], Leg):
        FIELDS.update(prot=0.45 + 0.5 * abs(drive["v"]), warn=0.85 + 0.6 * abs(drive["v"]))
        if np.linalg.norm(legs[0].P[-1] - base_pose()[:2]) < 0.6 and legs[0].dir > 0:
            FIELDS.update(prot=0.38, warn=0.6)                    # campi di aggancio
    else:
        FIELDS.update(prot=0.4, warn=0.55)
    near_person = any(np.linalg.norm(base_pose()[:2] - pp) < 2.2 for pp in PEOPLE_NAMED.values())
    if args.agent and AG.get("approach") and near_person:   # avvicinamento a una persona: lento + campo stretto (servizio)
        FIELDS.update(prot=0.40, warn=0.9); v = float(np.clip(v, -0.2, 0.2))
    if isinstance(legs[0], Leg):                         # frenata che tiene conto di strappo e ritardo: si arriva gia' fermi
        rem = getattr(legs[0], "rem", 1.0); Ab = 0.8 * A_LON; tau = Ab / (2 * JERK) + 0.4
        vb = Ab * (-tau + math.sqrt(tau * tau + 2 * max(rem, 0.0) / Ab))
        v = math.copysign(min(abs(v), max(vb, 0.008 if rem > 0.004 else 0.0)), v)
    v *= k; w *= k
    a_cmd = float(np.clip((v - drive["v"]) / 0.4, -A_LON, A_LON))           # accelerazione con strappo limitato
    drive["a"] = drive.get("a", 0.0) + float(np.clip(a_cmd - drive.get("a", 0.0), -JERK * DT, JERK * DT))
    dv = drive["a"] * DT
    dw = float(np.clip(w - drive["w"], -A_ROT * DT * 2, A_ROT * DT * 2))
    drive["v"] += dv; drive["w"] += dw
    d.ctrl[WL] = (drive["v"] - drive["w"] * B_HALF) / WHEEL_R
    d.ctrl[WR] = (drive["v"] + drive["w"] * B_HALF) / WHEEL_R
    if done:
        legs.pop(0)
    return not legs


def hold_step():
    """fuori dalle tratte: v, w portati a zero con lo stesso profilo a strappo limitato (niente colpi, niente deriva)"""
    a_cmd = float(np.clip(-drive["v"] / 0.4, -A_LON, A_LON))
    drive["a"] = drive.get("a", 0.0) + float(np.clip(a_cmd - drive.get("a", 0.0), -JERK * DT, JERK * DT))
    drive["v"] += drive["a"] * DT
    drive["w"] += float(np.clip(-drive["w"], -A_ROT * DT * 2, A_ROT * DT * 2))
    if abs(drive["v"]) < 2e-3 and abs(drive["a"]) < 0.02:
        drive["v"] = drive["a"] = 0.0
    d.ctrl[WL] = (drive["v"] - drive["w"] * B_HALF) / WHEEL_R
    d.ctrl[WR] = (drive["v"] + drive["w"] * B_HALF) / WHEEL_R


# ---------------------------------------------------------------- occhi e baffi
EYES = {"l": m.geom("eye_l").id, "r": m.geom("eye_r").id}
MUS = {n: m.geom(n).id for n in ("mus_l", "mus_r")}
MUS_SERVO = True                                         # True = versione con 2 micro-servo (opzionale)
LEDS = [m.geom(f"status_led{k}").id for k in range(4)]
EYE_POS0 = {k: m.geom_pos[g].copy() for k, g in EYES.items()}
MUS0 = {n: (m.geom_pos[g].copy(), m.geom_quat[g].copy()) for n, g in MUS.items()}
EYE_COL = {0: (0.45, 0.85, 1.0), 1: (1.0, 0.72, 0.15), 2: (1.0, 0.18, 0.12)}
eye = {"gaze": np.zeros(2), "next_blink": 2.5, "mus": 0.0}
state = {"k": 1.0, "k_cmd": 1.0, "zone": 0, "clear_t": 0.0, "hits": [], "scan_t": 0.0}


def face_step():
    t = d.time
    cr = d.body("crown"); Rc = cr.xmat.reshape(3, 3)
    near = [np.r_[p.pos, 1.6] for p in people if p.active and np.linalg.norm(p.pos - d.body("amr").xpos[:2]) < 3.0]
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
    coffee = args.agent and AG["mode"] == "caffe"
    for k_, gid in EYES.items():
        m.geom_pos[gid] = EYE_POS0[k_] + [0, 0.011 * eye["gaze"][0], 0.008 * eye["gaze"][1]]
        m.geom_size[gid] = [0.004, 0.0125, 0.017 * (1 - 0.85 * blink)]
        m.geom_rgba[gid] = list((1.0, 0.62, 0.25) if (coffee and state["zone"] == 0) else EYE_COL[state["zone"]]) + [1]
    # baffi: angolo (rad, + = in su) secondo l'espressione
    happy = t - expr["happy_t"] < 1.6
    if state["zone"] == 2:
        target = -0.30                                   # triste: fermo per una persona
    elif happy:
        target = 0.30 + 0.08 * math.sin(t * 30)         # contento: flacone inserito
    elif state["zone"] == 1:
        target = 0.0
    elif mission["state"].startswith("drive"):
        target = 0.12 + 0.08 * math.sin(t * 9)           # saltella mentre guida
    else:
        target = 0.12 + (0.12 * math.sin(t * 22) if (t % 6.0) < 0.5 else 0.0)   # piccolo fremito ogni tanto
    if args.agent and AG["mode"] == "caffe" and state["zone"] != 2:
        target = 0.22 + 0.05 * math.sin(t * 5)          # modalita' barista: baffi su e un po' vivaci
    if not MUS_SERVO:
        target = 0.0                                     # baffi fissi (retroilluminati): esprimono solo con il colore
    target *= 0.42                                       # corsa reale dei micro-servo: circa +-8 gradi
    eye["mus"] += 0.25 * (target - eye["mus"])
    for n, gid in MUS.items():
        p0, q0 = MUS0[n]
        sg = 1 if n.startswith("mus_l") else -1
        piv = np.array([0.094, 0.0, -0.033])             # perno al centro, sotto il naso
        R = Rot.from_rotvec([sg * eye["mus"], 0, 0])     # rotazione nel piano frontale (micro-servo)
        m.geom_pos[gid] = piv + R.apply(p0 - piv)
        qq = (R * Rot.from_quat([q0[1], q0[2], q0[3], q0[0]])).as_quat()
        m.geom_quat[gid] = [qq[3], qq[0], qq[1], qq[2]]
        m.geom_rgba[gid] = m.geom_rgba[EYES["l"]]
    for gid in LEDS:                                     # striscia LED di stato sulla base: verde / giallo / rosso
        m.geom_rgba[gid] = list(((0.2, 1.0, 0.45), (1.0, 0.75, 0.1), (1.0, 0.12, 0.1))[state["zone"]]) + [1]
    if BAT["charging"]:                                  # in carica: la striscia "respira" in verde
        m.geom_rgba[LEDS[0]] = [0.1, 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 2.5)), 0.25, 1]
    # stato del volto a matrice LED (64 x 32): espressione, sguardo, palpebre -> registrato per il render
    code = 0                                             # 0 neutro, 1 contento, 2 caffe', 3 stop, 4 pensa, 5 cuori, 6 attento
    if state["zone"] == 2:
        code = 3
    elif t - expr.get("love_t", -10) < 2.5:
        code = 5
    elif t - expr["happy_t"] < 1.6:
        code = 1
    elif t < AG.get("think_until", -1):
        code = 4
    elif coffee:
        code = 2
    elif state["zone"] == 1:
        code = 6
    if BAT["charging"] and code in (0, 6):
        code = 7
    FACE[:] = [code, float(eye["gaze"][0]), float(eye["gaze"][1]), float(blink), t]


# ---------------------------------------------------------------- missione (ciclo)
TEACH = {"pending": False, "t": 0.0}


def teach_contour():
    """il contorno si apprende solo a base ferma (dopo la rampa di arresto): fino ad allora campi di aggancio stretti"""
    TEACH["pending"] = True; TEACH["t"] = 0.0
    FIELDS.update(prot=0.38, warn=0.6, mode="aggancio")


def teach_step():
    global REF
    if not TEACH["pending"]:
        return
    still = abs(drive["v"]) < 1e-3 and abs(drive["w"]) < 1e-3 and np.linalg.norm(d.qvel[FREE_V:FREE_V + 3]) < 0.003 \
        and abs(d.qvel[FREE_V + 5]) < 0.003
    TEACH["t"] = TEACH["t"] + DT if still else 0.0
    if TEACH["t"] > 0.3:
        REF = [dd.copy() for _, _, dd in scan_once()]
        FIELDS.update(prot=R_PROT, warn=R_WARN, mode="fermo"); TEACH["pending"] = False


def set_state(s_):
    mission["state"], mission["t"] = s_, 0.0


def local_rel(xy, pose=None):
    x, y, th = base_pose() if pose is None else pose
    c, s = math.cos(th), math.sin(th)
    dx, dy = xy[0] - x, xy[1] - y
    return np.array([c * dx + s * dy, -s * dx + c * dy])


def buffer_xy(side, k):
    xl, yl = BUFFER_SLOTS[k]
    return local_to_world(base_pose(), xl, SGN[side] * yl)


def arms_idle():
    return not any(a.busy or a.queue for a in arms.values())


LOAD_ORDER = [0, 1, 2]               # carico: prima l'alloggio interno
UNLOAD_ORDER = [2, 1, 0]             # vassoio: prima l'alloggio esterno (l'avambraccio passa sopra alloggi vuoti)
N_SLOTS = len(BUFFER_SLOTS)


def plan_load(side, dets):
    """coda: per ogni flacone visto sul lato -> presa -> alloggio k del buffer"""
    a = arms[side]
    mine = sorted([dt for dt in dets if np.sign(local_rel(dt["xy"])[1]) == a.sg], key=lambda dt: -abs(local_rel(dt["xy"])[1]))
    jobs = []
    for k, dt in zip(LOAD_ORDER, mine[:6]):
        part = min(PARTS, key=lambda p: np.linalg.norm(d.body(p).xpos[:2] - dt["xy"]))
        dt["err"] = 1000 * np.linalg.norm(d.body(part).xpos[:2] - dt["xy"]); stats["vis_err"].append(dt["err"])

        def job(dt=dt, part=part, a=a):
            s1, q1 = a.pick(dt["xy"], part, a.q, BENCH_Z)
            return s1

        def job2(part=part, k=k, a=a):
            s2, _ = a.place(buffer_xy(a.s, k), part, a.q, BUF_Z, "loaded", drop=0.060 - 0.016 - 0.020)   # rilascio dentro l'imbocco svasato
            return s2
        jobs += [job, job2]
    if len(mine) > len(LOAD_ORDER):              # il quarto resta in mano (trasporto)
        dt = mine[len(LOAD_ORDER)]
        part = min(PARTS, key=lambda p: np.linalg.norm(d.body(p).xpos[:2] - dt["xy"]))
        dt["err"] = 1000 * np.linalg.norm(d.body(part).xpos[:2] - dt["xy"]); stats["vis_err"].append(dt["err"])

        def hold(dt=dt, part=part, a=a):
            s1, q1 = a.pick(dt["xy"], part, a.q, BENCH_Z)
            return s1 + a.plan_pose_from(q1, 0.22, 0.36, 0.26)
        jobs.append(hold)
    else:
        jobs.append(lambda a=a: [a.jmove(a.q, Q_HOME[a.s])])
    a.queue = jobs


def plan_unload(side, holes):
    a = arms[side]
    mine = sorted([h for h in holes if np.sign(local_rel(h["xy"])[1]) == a.sg], key=lambda h: abs(local_rel(h["xy"])[1]))
    jobs = []
    if a.held and mine:
        h0 = mine.pop(0)

        def put_held(h=h0, a=a):
            a.target = h["true"]
            s2, _ = a.place(h["xy"], a.held, a.q, BENCH_Z, "inserted", drop=FIX_H + 0.012)
            return s2
        jobs.append(put_held)
    full = [k for k in UNLOAD_ORDER if any(np.linalg.norm(d.body(p).xpos[:2] - buffer_xy(side, k)) < 0.03 for p in PARTS)]
    for k, h in zip(full, mine):
        part = min(PARTS, key=lambda p: np.linalg.norm(d.body(p).xpos[:2] - buffer_xy(side, k)))

        def job(k=k, part=part, a=a):
            pp = d.body(part).xpos
            s1, q1 = a.pick(pp[:2], part, a.q, BUF_Z)
            return s1

        def job2(h=h, part=part, a=a):
            a.target = h["true"]
            s2, _ = a.place(h["xy"], part, a.q, BENCH_Z, "inserted", drop=FIX_H + 0.012)
            return s2
        jobs += [job, job2]
    jobs.append(lambda a=a: [a.jmove(a.q, Q_HOME[a.s])])
    a.queue = jobs


def onboard_count():
    return sum(any(np.linalg.norm(d.body(p).xpos[:2] - buffer_xy(s_, k)) < 0.03 for s_ in arms for k in range(N_SLOTS)) for p in PARTS)


def table_A_full():
    return sum(np.linalg.norm(local_rel(d.body(p).xpos[:2], DOCK["A"]) - [0.35, 0]) < 0.4 and d.body(p).xpos[2] > ZC - 0.02 for p in PARTS)


OPER = {"phase": "idle", "loaded": 0, "t": 0.0}
PARK = np.array([-5.6, -3.4])                       # ingresso persone: fuori inquadratura
STAND_A = local_to_world(DOCK["A"], 0.05, -0.85)
STAND_B = np.array([1.15, 0.35])
CUP0 = None


def slot_world(side, k, pose):
    xl, yl = BUFFER_SLOTS[k]
    return local_to_world(pose, xl, SGN[side] * yl)


def load_one(i):
    """i = 0..5: per lato (destro poi sinistro) due flaconi negli alloggi, il terzo consegnato nella pinza"""
    side = "right" if i < 4 else "left"; j = i % 4; p = PARTS[i]
    if j < 3:
        xy = slot_world(side, UNLOAD_ORDER[::-1][j], base_pose()); set_part(p, np.array([xy[0], xy[1], BUF_Z + PH / 2 + 0.002]))
    else:                                                # passaggio di mano: l'operatore tiene il flacone finche' la pinza stringe
        HANDOVER[p] = (side, d.time + 0.6)
        a = arms[side]; a.grip = 0.0; a.held = p       # chiusura a bassa forza: ammessa anche con l'operatore vicino


HANDOVER = {}


def handover_step():
    for p, (side, t_end) in list(HANDOVER.items()):
        if d.time > t_end:
            HANDOVER.pop(p); continue
        gs = d.site(f"{side}_grasp").xpos
        j = m.body(p).jntadr[0]; qa, va = m.jnt_qposadr[j], m.jnt_dofadr[j]
        d.qpos[qa:qa + 3] = [gs[0], gs[1], gs[2] - (PH - 0.035) + PH / 2]; d.qpos[qa + 3:qa + 7] = [1, 0, 0, 0]
        d.qvel[va:va + 6] = d.qvel[FREE_V:FREE_V + 6] * 0


def op_walk(op, goal):
    """cammino pianificato (A*) fino a goal; resta fermo all'arrivo"""
    pts = plan_path(op.pos.copy(), np.asarray(goal, float), (), infl=0.30, robot=base_pose()[:2])
    op.path = [op.pos.copy()] + [np.asarray(q, float) for q in pts[1:]] + [np.asarray(goal, float)]
    op.i, op.tw, op.stop_at_end, op.keys = 0, 0.0, True, []
    while op.i != len(op.path) - 1:
        yield


def op_face(op, yaw, t=0.6):
    op.face_yaw = yaw; t0 = d.time
    while d.time - t0 < t:
        yield


def op_hand(op, tgt, T):
    """mano destra verso tgt: prima l'allungamento (r 0->1), poi spostamenti con profilo morbido"""
    tgt = np.asarray(tgt, float)
    if op.reach_tgt is None or op.r_reach < 0.99:
        op.reach_tgt = tgt.copy()
        while op.r_reach < 0.99:
            yield
        return
    p0 = np.asarray(op.reach_tgt, float).copy(); t0 = d.time
    while d.time - t0 < T:
        u_ = (d.time - t0) / T; u_ = u_ * u_ * (3 - 2 * u_)
        op.reach_tgt = p0 + (tgt - p0) * u_
        yield
    op.reach_tgt = tgt.copy()


def crate_slot(op, j):
    c, s_ = math.cos(op.yaw), math.sin(op.yaw)
    f, l = np.array([c, s_, 0]), np.array([-s_, c, 0])
    fx, ly = (-0.04, 0.04)[j % 2], (-0.105, -0.035, 0.035, 0.105)[j // 2]
    return op.crate_c + f * fx + l * ly + np.array([0, 0, -CR_H + 0.008 + PH / 2])


OPS = {"gen": None, "in_crate": {}, "held": None, "rel": None}


def op_sync(op):
    """cassetta e flaconi seguono l'operatore (presi in mano o appoggiati nella cassetta)"""
    tm = m.body_mocapid[m.body("tote").id]
    if op is None or op.crate_c is None or not op.crate:
        d.mocap_pos[tm] = [0, 0, -5]
    else:
        d.mocap_pos[tm] = op.crate_c; d.mocap_quat[tm] = [math.cos(op.yaw / 2), 0, 0, math.sin(op.yaw / 2)]
        for p, j in OPS["in_crate"].items():
            set_part(p, crate_slot(op, j))
    if op is not None and OPS["held"] is not None and op.hand_r is not None:
        c, s_ = math.cos(op.yaw), math.sin(op.yaw); r_ = OPS["rel"]
        set_part(OPS["held"], op.hand_r + np.array([c * r_[0] - s_ * r_[1], s_ * r_[0] + c * r_[1], r_[2]]))


def op_grab(op, p):
    c, s_ = math.cos(op.yaw), math.sin(op.yaw); dv = d.body(p).xpos - op.hand_r
    OPS["rel"] = np.array([c * dv[0] + s_ * dv[1], -s_ * dv[0] + c * dv[1], dv[2]]); OPS["held"] = p
    OPS["in_crate"].pop(p, None)


def op_script():
    """operatore con cassetta: svuota il banco B a mano (Giorgio e' gia' ripartito), porta i flaconi in A e rifornisce il vassoio"""
    while not (mission["state"] in ("drive_BW", "wait_refill") and np.linalg.norm(base_pose()[:2] - DOCK["B"][:2]) > 1.6):
        yield
    op = spawn(0, [PARK, PARK], 1.1, None, look="operatore"); op.crate = True; op.stop_at_end = True
    up = np.array([0, 0, 1.0]); top_off = up * (PH / 2 - 0.035)
    j = 0
    for sy in (1, -1):                                   # due posizioni davanti al banco B: fori a sinistra, poi a destra
        yield from op_walk(op, np.array([-0.08, 0.30 if sy > 0 else -0.02]))
        yield from op_face(op, 0.0)
        mine = [p for p in PARTS if np.sign(d.body(p).xpos[1]) == sy and abs(d.body(p).xpos[0] - 0.345) < 0.1
                and abs(d.body(p).xpos[1]) < 0.25 and d.body(p).xpos[2] < ZC + 0.03]
        for p in sorted(mine, key=lambda q: -abs(d.body(q).xpos[1])):
            pp = d.body(p).xpos.copy()
            yield from op_hand(op, pp + top_off, 0.6)
            op_grab(op, p)
            yield from op_hand(op, pp + top_off + up * 0.20, 0.5)       # sopra i tappi dei vicini
            sl = crate_slot(op, j)
            yield from op_hand(op, sl + top_off + up * 0.14, 0.6)
            yield from op_hand(op, sl + top_off, 0.4)
            OPS["held"] = None; OPS["in_crate"][p] = j; j += 1
        op.reach_tgt = None
        while op.r_reach > 0.02:
            yield
    th = DOCK["A"][2]
    for sy in (1, -1):                                   # baia A (Giorgio aspetta indietro): rimette i flaconi nel vassoio
        yield from op_walk(op, local_to_world(DOCK["A"], -0.08, 0.30 if sy > 0 else -0.02))
        yield from op_face(op, th)
        for p in [q for q in list(OPS["in_crate"]) if np.sign(HOME[q][1]) == sy]:
            yield from op_hand(op, d.body(p).xpos + top_off, 0.5)
            op_grab(op, p)
            yield from op_hand(op, d.body(p).xpos + top_off + up * 0.16, 0.45)
            dst = a_pocket(p)
            yield from op_hand(op, dst + top_off + up * 0.16, 0.7)      # sopra i flaconi gia' rimessi
            yield from op_hand(op, dst + top_off + up * 0.004, 0.45)
            OPS["held"] = None; set_part(p, dst)
        op.reach_tgt = None
        while op.r_reach > 0.02:
            yield
    yield from op_walk(op, PARK)
    people[:] = [q for q in people if q.idx != 0]; OPS["in_crate"] = {}
    while True:
        yield


def operator_step():
    if args.no_humans:
        return
    if OPS["gen"] is None:
        OPS["gen"] = op_script()
    next(OPS["gen"])
    op_sync(next((q for q in people if q.idx == 0), None))
    if mission["state"] == "wait_load" and OPS.get("done_cycle") != stats["cycles"] and stats["cycles"] > 0:
        OPS["gen"] = op_script(); OPS["done_cycle"] = stats["cycles"]


def storage(p):
    i = PARTS.index(p)
    return np.array([-7.0 + 0.1 * (i % 6), 4.0 + 0.1 * (i // 6), ZC + 0.001])


CLIPS = {}      # flaconi trattenuti dalle clip a molla del buffer: posa relativa alla base


def clip(p, on):
    e = m.equality(f"clip_{p}").id
    if on:
        bp, ba = d.body(p), d.body("amr")
        Rp = bp.xmat.reshape(3, 3)
        rel = Rp.T @ (ba.xpos - bp.xpos)
        qi = np.zeros(4); mujoco.mju_negQuat(qi, bp.xquat); qr = np.zeros(4); mujoco.mju_mulQuat(qr, qi, ba.xquat)
        m.eq_data[e][0:3] = 0.0; m.eq_data[e][3:6] = rel; m.eq_data[e][6:10] = qr; m.eq_data[e][10] = 1.0
    d.eq_active[e] = 1 if on else 0
    if on:
        CLIPS[p] = True
    else:
        CLIPS.pop(p, None)


def clip_all():
    for p in PARTS:
        xy = local_rel(d.body(p).xpos[:2])
        if any(np.linalg.norm(xy - np.array([bx, SGN[s_] * by])) < 0.02 for s_ in arms for bx, by in BUFFER_SLOTS):
            clip(p, True)


def clips_step():
    pass


def set_part(p, pos):
    j = m.body(p).jntadr[0]; qa, va = m.jnt_qposadr[j], m.jnt_dofadr[j]
    d.qpos[qa:qa + 7] = list(pos) + [1, 0, 0, 0]; d.qvel[va:va + 6] = 0


def passer_step():
    """passanti in corsia (x = -1.6): partono all'inizio dei tratti di marcia, cosi' incrociano Giorgio"""
    if args.no_humans:
        return
    st = mission["state"]
    if st in ("drive_AB", "drive_BW") and mission["t"] < DT * 1.5:
        idx = 1 if st == "drive_AB" else 2
        y0 = -4.5 if st == "drive_AB" else 4.5
        spawn(idx, [np.array([-1.6, y0]), np.array([-1.6, -y0])], 1.25, (0.85, 0.95, 0.1) if idx == 1 else (0.3, 0.6, 1.0))
    for p in list(people):
        if p.idx in (1, 2) and getattr(p, 'ki', 0) >= 1:
            people.remove(p)


def agent_people():
    for i, (nm_, pp) in enumerate(PEOPLE_NAMED.items()):
        if not any(q.idx == 1 + i for q in people) and not (AG.get("taker") == nm_ and any(q.idx == 3 for q in people)):
            q_ = spawn(1 + i, [pp, pp], 0.5, (0.85, 0.95, 0.1) if i == 0 else (0.9, 0.3, 0.6), look=nm_)
            if AG.get("taker") != nm_:
                q_.yaw = q_.face_yaw = PEOPLE_FACE[nm_]
        elif AG.get("taker") == nm_ and any(q.idx == 3 for q in people):
            people[:] = [q for q in people if q.idx != 1 + i]


def mission_step(k):
    st = mission["state"]
    mission["t"] += DT
    if st == "settle" and mission["t"] > 0.4:
        teach_contour(); set_state("wait_load"); log("Giorgio in baia di carico A: attende l'operatore")
    elif st == "wait_load":
        if args.no_humans and table_A_full() < len(PARTS):
            for p in PARTS:
                set_part(p, a_pocket(p))
        op_near = any(np.linalg.norm(q.pos - base_pose()[:2]) < 1.6 for q in people if q.idx == 0 and q.active)
        if table_A_full() == len(PARTS) and arms_idle() and not op_near and mission["t"] > 1.0:
            set_state("look_A")
    elif st == "look_A" and mission["t"] > 0.5:
        dets = vision.find_bottles()
        log(f"visione: {len(dets)} flaconi sul banco A, errore medio {np.mean([1000 * min(np.linalg.norm(d.body(p).xpos[:2] - dt['xy']) for p in PARTS) for dt in dets]) if dets else 0:.1f} mm")
        for s_ in arms:
            plan_load(s_, dets)
        set_state("load_A")
    elif st == "load_A" and arms_idle() and mission["t"] > 0.5:
        full = onboard_count() + sum(1 for a in arms.values() if a.held)
        if args.agent:
            log(f"a bordo {full} flaconi"); set_state("agente")
        else:
            log(f"a bordo {full} flaconi (6 sul vassoio, 2 in mano): partenza verso il banco B")
            mission["route"] = route("B"); FIELDS["mode"] = "marcia"; set_state("drive_AB")
    elif st == "drive_AB" and drive_step(k):
        for p in list(CLIPS):                          # robot fermo e agganciato: clip del buffer aperte
            clip(p, False)
        teach_contour(); set_state("look_B")
        x, y, th = base_pose(); log(f"AMR agganciato a B: {1000 * x:.0f} / {1000 * y:.0f} mm, {math.degrees(th):.1f} gradi")
    elif st == "look_B" and mission["t"] > 0.5:
        holes = vision.find_holes()
        for h in holes:
            tv = min(HOLES, key=lambda t_: np.linalg.norm(np.array(t_) - h["xy"])); h["true"] = np.array(tv)
            h["err"] = 1000 * np.linalg.norm(h["true"] - h["xy"]); stats["vis_err"].append(h["err"])
        log(f"visione: {len(holes)} fori liberi, errore medio {np.mean([h['err'] for h in holes]) if holes else 0:.1f} mm")
        for s_ in arms:
            plan_unload(s_, holes)
        set_state("unload_B")
    elif st == "unload_B" and arms_idle() and mission["t"] > 0.5 and args.agent:
        stats["cycles"] += 1; set_state("agente")
    elif st == "unload_B" and arms_idle() and mission["t"] > 0.5:
        stats["cycles"] += 1
        mission["route"] = route("W"); FIELDS["mode"] = "marcia"; set_state("drive_BW"); log("AMR: ritorno verso A (attesa del rifornimento)")
    elif st == "drive_BW" and drive_step(k):
        teach_contour(); set_state("wait_refill")
    elif st == "wait_refill":
        op_near = any(np.linalg.norm(q.pos - DOCK["A"][:2]) < 1.3 for q in people if q.idx == 0 and q.active)
        if table_A_full() == len(PARTS) and not op_near and mission["t"] > 1.0:
            log("banco A rifornito, operatore fuori: aggancio in A")
            mission["route"] = [Leg(np.linspace(base_pose()[:2], DOCK["A"][:2], 30), +1), Turn(math.pi / 2)]
            FIELDS["mode"] = "marcia"; set_state("drive_WA")
    elif st == "drive_WA" and drive_step(k):
        teach_contour()
        set_state("done" if stats["cycles"] >= args.cycles else "wait_load")


# ---------------------------------------------------------------- agente (Sistema 1 veloce + Sistema 2 Claude)
import json
import re
import subprocess

AG = {"queue": [], "cur": None, "mode": "lavoro", "chat": [], "pending": [], "say": "", "say_t": -10.0, "busy_llm": False}
PEOPLE_NAMED = {"Marco": np.array([1.6, -1.92]), "Sara": np.array([-4.6, 3.12])}      # in piedi a 35 cm dalla scrivania
PEOPLE_FACE = {"Marco": -math.pi / 2, "Sara": math.pi / 2}                            # rivolti verso la scrivania
DESK = {"Marco": (1.6, -2.55), "Sara": (-4.6, 3.75)}
PEOPLE_IDX = {"Marco": 1, "Sara": 2}
SKILLS_DOC = """Sei il pianificatore di GIORGIO, robot collaborativo (AMR AgileX Tracer 2.0 + 2 braccia Enactic OpenArm 2.0 con pinze,
Orbbec Gemini 336L RGB-D, Insta360 a 360 gradi, 2 laser scanner SICK di sicurezza, macchina a capsule sul retro).
Abilita' disponibili (usa SOLO queste):
- vai_a(target): target = A (baia di carico), B (banco di inserimento), C (stazione di ricarica) oppure il nome di una persona.
- carica(): in A Giorgio carica da solo i flaconi dal vassoio di kitting con la visione (6 sul vassoio frontale, 2 nelle pinze). Va prima in A se serve.
- scarica_e_inserisci(): in B, la visione trova i fori e Giorgio inserisce i flaconi che ha a bordo.
- fai_caffe(): prepara un caffe' con la macchina a capsule integrata sulla schiena (bicchiere -> navetta -> pulsante -> erogazione, ~40 s). Modalita' caffe'.
- porta_caffe(target): va dalla persona con il bicchiere in mano e glielo porge (la persona lo prende).
- ricarica(): va alla stazione C e si mette in carica.
- di(testo): dice una frase breve.
Limiti: non sale scale, porta al massimo 8 flaconi da 0.35 kg (6 sul vassoio + 2 in mano); con un caffe' in mano non carica flaconi, le pinze non sono mani: niente manipolazione fine.
Se la richiesta non e' fattibile, spiegalo in 'say' e restituisci un piano vuoto o parziale sicuro."""
SCHEMA = {"type": "object", "properties": {
    "say": {"type": "string"},
    "plan": {"type": "array", "items": {"type": "object", "properties": {
        "skill": {"type": "string", "enum": ["vai_a", "carica", "scarica_e_inserisci", "fai_caffe", "porta_caffe", "ricarica", "di"]},
        "target": {"type": "string"}, "text": {"type": "string"}}, "required": ["skill"]}}},
    "required": ["say", "plan"]}


def scene_state():
    x, y, th = base_pose()
    return {"giorgio": {"pos": [round(x, 2), round(y, 2)], "a_bordo": onboard_count() + sum(1 for a in arms.values() if a.held),
                        "modalita": AG["mode"]},
            "stazioni": {"A": DOCK["A"][:2].round(2).tolist(), "B": DOCK["B"][:2].round(2).tolist(), "C": CHG[:2].round(2).tolist()},
            "persone": {n: v.round(2).tolist() for n, v in PEOPLE_NAMED.items()},
            "oggetti": ["6 flaconi (magazzino)", "attrezzatura a 8 fori sul banco B", "macchina a capsule (retro di Giorgio)", "tazzine"]}


def system1(text):
    """router veloce (< 1 ms): comandi frequenti senza LLM"""
    t = text.lower()
    who = next((n for n in PEOPLE_NAMED if n.lower() in t), None)
    if re.search(r"\bpoi\b|\bdopo\b|\bdimmi\b|\bse\b|\bquando\b|\bperche\b|\?", t):
        return None                                      # richiesta composta o domanda: decide Claude (Sistema 2)
    if re.search(r"\b(stop|fermati|alt)\b", t):
        return [{"skill": "di", "text": "Mi fermo."}]
    if re.search(r"ricaric|in carica|batteria", t) and not re.search(r"caff", t):
        return [{"skill": "ricarica"}]
    m_ = re.fullmatch(r".*\bvai (?:a|al|alla|in)? ?(?:banco |baia |stazione )?([abc])\b.*", t)
    if m_ and not re.search(r"caff|poi|e poi", t):
        return [{"skill": "vai_a", "target": m_.group(1).upper()}]
    if re.fullmatch(r".*caff.*", t) and who and not re.search(r"poi|dopo|quando|se ", t):
        return [{"skill": "fai_caffe"}, {"skill": "porta_caffe", "target": who}]
    return None


def system2(text):
    """Claude: pianificazione su richieste libere, vincolata alle abilita' reali e alla scena"""
    prompt = f"Scena: {json.dumps(scene_state(), ensure_ascii=False)}\nRichiesta: {text}"
    t0 = time.time()
    try:
        out = subprocess.run(["claude", "-p", "--model", "haiku", "--output-format", "json", "--tools", "", "--system-prompt", SKILLS_DOC,
                              "--json-schema", json.dumps(SCHEMA), prompt], capture_output=True, text=True, timeout=120, cwd="/tmp")
        res = json.loads(out.stdout)
        plan = res.get("structured_output") or {}
    except Exception as e:
        plan = {"say": f"(pianificatore non disponibile: {e})", "plan": []}
    AG["llm_s"] = time.time() - t0
    return plan


def ag_command(text):
    AG["chat"] = (AG["chat"] + [f"> {text}"])[-6:]
    AG["think_until"] = d.time + 1.4                  # volto: "sto pensando"
    t0 = time.perf_counter()
    plan = system1(text)
    if plan is not None:
        AG["chat"] = (AG["chat"] + [f"[Sistema 1, {1000 * (time.perf_counter() - t0):.2f} ms] " + " -> ".join(fmt(s_) for s_ in plan)])[-6:]
    else:
        res = system2(text)
        plan = res.get("plan", [])
        AG["chat"] = (AG["chat"] + [f"[Claude, {AG.get('llm_s', 0):.1f} s] " + " -> ".join(fmt(s_) for s_ in plan)])[-6:]
        if res.get("say"):
            ag_say(res["say"])
    log(f"agente: '{text}' -> {[fmt(s_) for s_ in plan]}")
    AG["queue"] += plan


def fmt(s_):
    return s_["skill"] + (f"({s_.get('target') or s_.get('text', '')})" if (s_.get("target") or s_.get("text")) else "()")


def ag_say(txt):
    AG["say"], AG["say_t"] = txt, d.time


def pose_near(target):
    if target in DOCK:
        return DOCK[target]
    if target == "C":
        return CHG
    if target in PEOPLE_NAMED:                          # 1.15 m davanti alla persona, rivolto verso di lei
        pp = PEOPLE_NAMED[target]; rb = base_pose()[:2]
        best = None
        for a_ in np.linspace(0, 2 * math.pi, 16, endpoint=False):     # punto di servizio libero attorno alla persona
            u = np.array([math.cos(a_), math.sin(a_)])
            p_, app = pp + 1.15 * u, pp + 1.85 * u
            if all(clearance(q) > 0.72 for q in (p_, app)):
                c = np.linalg.norm(app - rb)
                if best is None or c < best[0]:
                    best = (c, np.array([p_[0], p_[1], math.atan2(-u[1], -u[0])]))
        return best[1] if best else None
    return None


VIA = {}
GRID_RES, GX0, GY0, GNX, GNY = 0.1, -6.5, -5.0, 115, 115
OBST = [(0.16, 0.80, -0.85, 0.85), (1.2, 2.0, -2.85, -2.25), (-5.0, -4.2, 3.45, 4.05), (-3.15, -2.85, -3.1, -2.9),   # banco B, scrivanie, colonnina
        (-3.27, -1.53, 1.59, 2.27), (3.34, 4.02, 0.33, 2.07)]                                                             # banco A, banco D
if BASE == "amr_revB":                                   # dock rev B: ingombro piu' largo della colonnina AgileX
    OBST[3] = (-3.26, -2.74, -3.30, -3.02)


def clearance(p_):
    return min(math.hypot(max(x0 - p_[0], p_[0] - x1, 0), max(y0 - p_[1], p_[1] - y1, 0)) for x0, x1, y0, y1 in OBST)


def plan_path(start, goal, avoid_people=(), infl=0.70, robot=None):
    """A* su griglia 10 cm: ostacoli gonfiati della sagoma del robot (0.55 m), persone sedute a 1.0 m"""
    import heapq
    xs = GX0 + GRID_RES * np.arange(GNX); ys = GY0 + GRID_RES * np.arange(GNY)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); blocked = np.zeros((GNX, GNY), bool)
    for x0, x1, y0, y1 in OBST:
        dx = np.maximum(np.maximum(x0 - X, X - x1), 0); dy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
        blocked |= np.hypot(dx, dy) < infl
    for pp in avoid_people:
        blocked |= np.hypot(X - pp[0], Y - pp[1]) < 1.0
    if robot is not None:                               # le persone girano attorno al robot (ingombro + vassoio)
        blocked |= np.hypot(X - robot[0], Y - robot[1]) < 0.75
    idx = lambda p_: (int(round((p_[0] - GX0) / GRID_RES)), int(round((p_[1] - GY0) / GRID_RES)))
    s0, g0 = idx(start), idx(goal); blocked[s0] = blocked[g0] = False
    openl = [(0, s0)]; came = {s0: None}; cost = {s0: 0.0}
    while openl:
        _, c = heapq.heappop(openl)
        if c == g0:
            break
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                n = (c[0] + di, c[1] + dj)
                if (di or dj) and 0 <= n[0] < GNX and 0 <= n[1] < GNY and not blocked[n]:
                    nc = cost[c] + math.hypot(di, dj)
                    if nc < cost.get(n, 1e9):
                        cost[n] = nc; came[n] = c; heapq.heappush(openl, (nc + math.hypot(n[0] - g0[0], n[1] - g0[1]), n))
    if g0 not in came:
        return [np.asarray(start), np.asarray(goal)]
    path, c = [], g0
    while c is not None:
        path.append(np.array([GX0 + GRID_RES * c[0], GY0 + GRID_RES * c[1]])); c = came[c]
    path = path[::-1]
    def free(a_, b_):
        for u in np.linspace(0, 1, 20):
            q = idx(a_ + (b_ - a_) * u)
            if blocked[q]:
                return False
        return True
    out = [path[0]]; i = 0                               # sfoltisco: linea di vista
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not free(path[i], path[j]):
            j -= 1
        out.append(path[j]); i = j
    out[0], out[-1] = np.asarray(start, float), np.asarray(goal, float)
    return out


def route_pose(pose, via=()):
    x, y, th = base_pose()
    docked = min(np.linalg.norm(np.array([x, y]) - st_[:2]) for st_ in (DOCK["A"], DOCK["B"], CHG)) < 0.15
    back = np.array([x, y]) - (0.6 if docked else 0.02) * np.array([math.cos(th), math.sin(th)])   # retro solo per uscire da una stazione
    app = pose[:2] - 0.7 * np.array([math.cos(pose[2]), math.sin(pose[2])])
    seated = [pp for nm_, pp in PEOPLE_NAMED.items() if np.linalg.norm(pp - pose[:2]) > 1.5]
    pts = plan_path(back, app, seated)
    P = np.vstack([pts, [app + 0.25 * np.array([math.cos(pose[2]), math.sin(pose[2])])]])
    for _ in range(4):                                  # Chaikin: angoli arrotondati senza uscire dai segmenti
        Q = [P[0]]
        for i in range(len(P) - 1):
            Q += [0.75 * P[i] + 0.25 * P[i + 1], 0.25 * P[i] + 0.75 * P[i + 1]]
        Q.append(P[-1]); P = np.array(Q)
    dense = [P[0]]
    for i in range(len(P) - 1):
        n_ = max(2, int(np.linalg.norm(P[i + 1] - P[i]) / 0.03))
        dense += list(np.linspace(P[i], P[i + 1], n_)[1:])
    h0 = math.atan2(dense[3][1] - dense[0][1], dense[3][0] - dense[0][0])
    return [Leg(np.linspace([x, y], back, 25), -1), Turn(h0),
            Leg(np.vstack([np.array(dense), np.linspace(dense[-1], pose[:2], 20)[1:]]), +1), Turn(pose[2], 3.0)]


class Skill:
    def __init__(self, spec):
        self.s, self.phase, self.t = spec, 0, 0.0

    def step(self, k):
        sk, tg = self.s["skill"], self.s.get("target", "")
        self.t += DT
        if sk == "di":
            if self.phase == 0:
                ag_say(self.s.get("text", "")); self.phase = 1
            return self.t > 2.0
        if sk == "ricarica":
            return dock_skill(self, k)
        if sk in ("vai_a", "ricarica"):
            tg = "C" if sk == "ricarica" else tg
            if self.phase == 0:
                ps = pose_near(tg)
                if ps is None:
                    ag_say(f"Non conosco '{tg}'."); return True
                mission["route"] = route_pose(ps, VIA.get(tg, ())); FIELDS["mode"] = "marcia"; mission["state"] = "drive_ag"; self.phase = 1
            if self.phase == 1 and drive_step(k):
                teach_contour(); mission["state"] = "agente"; self.phase = 2
                if sk == "ricarica":
                    ag_say("In carica: contatti chiusi, 48 V."); m.geom_rgba[m.geom("charger_led").id] = [0.2, 1.0, 0.4, 1]
                return True
            return False
        if sk == "fai_caffe":
            if self.phase == 0 and self.t <= DT * 1.5 and soc() < 0.20 and not BAT["charging"]:
                ag_say(f"Batteria al {100 * soc():.0f}%: prima mi ricarico, poi faccio il caffe'.")
                AG["queue"][:0] = [{"skill": "ricarica"}, dict(self.s)]
                return True
            return coffee_skill(self, k)
        if sk == "porta_caffe":
            return deliver_skill(self, k, tg)
        if sk == "carica":
            if self.phase == 0:
                if np.linalg.norm(base_pose()[:2] - DOCK["A"][:2]) > 0.08:
                    mission["route"] = route_pose(DOCK["A"]); FIELDS["mode"] = "marcia"; mission["state"] = "drive_ag"; self.phase = 1
                else:
                    self.phase = 2
            if self.phase == 1 and drive_step(k):
                teach_contour(); mission["state"] = "agente"; self.phase = 2
            if self.phase == 2:
                if table_A_full() == 0:
                    ag_say("Il banco A e' vuoto: serve un rifornimento."); return True
                mission["state"] = "look_A"; mission["t"] = 0.0; self.phase = 3; ag_say("Carico i flaconi dal banco A.")
            return self.phase == 3 and mission["state"] == "agente"
        if sk == "scarica_e_inserisci":
            if self.phase == 0:
                mission["state"] = "look_B"; mission["t"] = 0.0; self.phase = 1
            return mission["state"] == "unload_B" and arms_idle() and mission["t"] > 0.5
        return True


def cup_hold_follow():
    """bicchiere in mano alla persona: segue la mano destra; l'offset misurato alla presa converge a una presa naturale"""
    if AG.get("cup_in_hand") is None:
        return
    op = next((q for q in people if q.idx == 3), None)
    if op is None or op.hand_r is None:
        return
    rel = AG.get("cup_rel", np.array([0.035, 0.0, 0.0]))
    if AG.get("hand") not in ("release", "lift"):         # finche' la pinza non si e' ritirata il bicchiere resta fermo nella mano
        rel = rel + 0.01 * (np.array([0.035, 0.0, -0.03]) - rel); AG["cup_rel"] = rel   # impugnato vicino al bordo
    c, s_ = math.cos(op.yaw), math.sin(op.yaw)
    set_part_xyz("cup", op.hand_r + np.array([c * rel[0] - s_ * rel[1], s_ * rel[0] + c * rel[1], rel[2]]))


SHUTTLE = m.actuator("cm_shuttle").id
PLATE_Z = COF_SH + COF_LIFT + 0.006 + 0.004                       # piano della navetta


def coffee_skill(sk_, k):
    """caffe' con la macchina a capsule sullo zaino: bicchiere dalla pila -> navetta -> pulsante -> erogazione -> bicchiere pieno in mano"""
    a = arms["right"]; AG["mode"] = "caffe"
    if sk_.phase == 0 and not a.busy:
        cp = d.body("cup").xpos.copy()
        s1, q1 = a.pick(cp[:2], "cup", a.q, cp[2] - CUP_H / 2, h=CUP_H)
        s2, q2 = a.place(a.robot_pt(COF_X, COF_Y_OUT, 0)[:2], "cup", q1, PLATE_Z, "cup_on_grid", drop=0.004, h=CUP_H, down_first=True)
        btn = a.robot_pt(COF_X + 0.02, -0.105, COF_SH + COF_MH + 0.003 + 0.004)    # pinza chiusa: le dita premono il pulsante
        q3 = a.solve(btn + [0, 0, 0.025], q2)
        s3, q4 = a.line(btn + [0, 0, 0.025], btn - [0, 0, 0.004], q3, 0.6)
        s4, q5 = a.line(btn - [0, 0, 0.004], btn + [0, 0, 0.03], q4, 0.4)
        a.start(s1 + s2 + [Seg("grip", dur=0.3, grip=0.0), a.jmove(q2, q3)] + s3 + [Seg("wait", dur=0.25, ev=("button", "cup"))] + s4)
        sk_.q_after = q5
        sk_.q_wait = q5; sk_.phase = 1; ag_say("Preparo il caffe': bicchiere sulla navetta, premo il pulsante.")
    elif sk_.phase == 1 and not a.busy:
        d.ctrl[SHUTTLE] = COF_Y_IN - COF_Y_OUT; sk_.phase = 2; sk_.t = 0.0
    elif sk_.phase == 2 and sk_.t > 2.2:                     # navetta sotto l'erogatore
        sk_.phase = 3; sk_.t = 0.0
    elif sk_.phase == 3:                                     # erogazione (8 s nel video, ~25 s reali)
        BAT["heater"] = True                                 # resistenza della macchina accesa durante l'erogazione
        u = min(1.0, sk_.t / 8.0)
        g = m.geom("cup_coffee").id; m.geom_size[g][1] = 0.0005 + 0.028 * u; m.geom_pos[g][2] = -CUP_H / 2 + 0.002 + 0.028 * u
        m.geom_rgba[m.geom("cm_stream").id][3] = 1.0 if 0.03 < u < 0.97 else 0.0
        m.geom_rgba[m.geom("cm_btn1").id] = [1.0, 0.55, 0.2, 1] if int(sk_.t * 3) % 2 else [0.35, 0.18, 0.07, 1]
        for i in range(3):
            m.geom_rgba[m.geom(f"cup_steam{i}").id][3] = 0.3 * u * (0.5 + 0.5 * math.sin(sk_.t * 4 + i))
        if u >= 1.0:
            m.geom_rgba[m.geom("cm_btn1").id] = [1.0, 0.55, 0.2, 1]
            d.ctrl[SHUTTLE] = 0.0; sk_.phase = 4; sk_.t = 0.0; BAT["heater"] = False
    elif sk_.phase == 4 and sk_.t > 2.4 and not a.busy:      # navetta fuori: presa dall'alto
        cp = d.body("cup").xpos.copy()
        qv = a.solve(np.array([cp[0], cp[1], cp[2] + 0.30]), a.q)      # passaggio in quota: lontano da pila e busto
        s1, q1 = a.pick(cp[:2], "cup", qv, cp[2] - CUP_H / 2, h=CUP_H)
        s1 = [a.jmove(a.q, qv)] + s1
        qa_ = a.solve(a.robot_pt(COF_X + 0.02, -0.33, 1.06), q1)          # su e fuori dalla navetta
        qb_ = a.solve(a.robot_pt(0.02, -0.40, 1.16), qa_)                   # lungo il fianco, lontano dal vassoio
        a.start(s1 + [a.jmove(q1, qa_), a.jmove(qa_, qb_), a.jmove(qb_, carry_q(a, qb_))])
        sk_.phase = 5; ag_say("Caffe' pronto!")
    elif sk_.phase == 5 and not a.busy:
        return True
    return False


def carry_q(a, q0):
    """posa di trasporto del caffe': di lato e sopra il vassoio dei flaconi (che sta davanti al petto)"""
    return a.solve(a.robot_pt(0.28, -0.34, 1.18), q0)


def deliver_skill(sk_, k, who):
    """porta il bicchiere in mano fino alla persona, si ferma davanti, allunga il braccio e glielo porge"""
    a = arms["right"]
    if sk_.phase == 0:
        ps = pose_near(who)
        mission["route"] = route_pose(ps); FIELDS["mode"] = "marcia"; mission["state"] = "drive_ag"; AG["approach"] = True
        sk_.phase = 1; ag_say(f"Arrivo, {who}!")
    elif sk_.phase == 1 and drive_step(k):
        mission["state"] = "agente"
        FIELDS.update(prot=0.35, warn=0.9, mode="servizio")
        offer = a.robot_pt(0.36, -0.36, 1.15)                       # braccio teso verso la persona, fuori dal vassoio
        a.start([a.jmove(a.q, a.solve(offer, a.q))]); sk_.phase = 2
    elif sk_.phase == 2 and not a.busy:
        cp_ = d.body("cup").xpos[:2]; rb_ = base_pose()[:2]; pp_ = PEOPLE_NAMED[who]
        best_ = None                                          # dove fermarsi: a 44 cm dal bicchiere, lontano da mobili e robot, vicino al posto della persona
        for ang_ in np.linspace(0, 2 * math.pi, 48, endpoint=False):
            g_ = cp_ + 0.44 * np.array([math.cos(ang_), math.sin(ang_)])
            if clearance(g_) < 0.32 or np.linalg.norm(g_ - rb_) < 0.62:
                continue
            c_ = np.linalg.norm(g_ - pp_)
            if best_ is None or c_ < best_[0]:
                best_ = (c_, g_)
        grab = best_[1] if best_ else cp_ + 0.44 * (pp_ - cp_) / max(np.linalg.norm(pp_ - cp_), 1e-6)
        pp = PEOPLE_NAMED[who]
        old = next((q for q in people if q.idx == PEOPLE_IDX[who]), None)
        tk = spawn(3, [pp, grab, grab, pp], 0.7, (0.3, 0.6, 1.0), waits={2: 8.0}, look=who); AG["taker"] = who
        tk.near_ok = True                                 # la persona servita si avvicina apposta (campo di servizio)
        if old is not None:
            tk.yaw = old.yaw
        sk_.phase = 3; sk_.t = 0.0; ag_say(f"Ecco il tuo caffe', {who}.")
    elif sk_.phase == 3:
        op = next((q for q in people if q.idx == 3), None)
        if op is None:
            sk_.phase = 4; return False
        st_ = AG.setdefault("hand", "walk")
        if st_ == "walk" and getattr(op, "ki", 0) == 2:          # davanti al robot: allunga la mano verso il bicchiere
            cp = d.body("cup").xpos; op.reach_tgt = cp.copy()
            op.face_yaw = math.atan2(cp[1] - op.pos[1], cp[0] - op.pos[0]); AG["hand"] = "reach"
        elif st_ == "reach" and op.r_reach > 0.97 and op.hand_r is not None:   # la mano stringe il bicchiere: la pinza si apre
            c_, s2_ = math.cos(op.yaw), math.sin(op.yaw); dv = d.body("cup").xpos - op.hand_r
            AG["cup_rel"] = np.array([c_ * dv[0] + s2_ * dv[1], -s2_ * dv[0] + c_ * dv[1], dv[2]])
            a.start([Seg("wait", dur=0.25), Seg("grip", dur=0.45, grip=-0.785)]); AG["cup_in_hand"] = who; a.held = None
            expr["love_t"] = d.time; ag_say("Ecco a te!"); AG["hand"] = "release"; AG["hand_t"] = d.time
        elif st_ == "release" and d.time - AG["hand_t"] > 0.9 and not a.busy:     # il braccio di Giorgio si ritira
            back = a.robot_pt(0.20, -0.34, 1.20)
            a.start([a.jmove(a.q, a.solve(back, a.q))]); AG["hand"] = "lift"; AG["hand_t"] = d.time
        elif st_ == "lift" and d.time - AG["hand_t"] > 0.6:      # Marco porta a se' il bicchiere...
            op.carry = True; op.carry_from = op.reach_tgt.copy(); op.reach_tgt = None; op.r_reach = 1.0
            AG["hand"] = "sip"; AG["hand_t"] = d.time
        elif st_ == "sip" and d.time - AG["hand_t"] > 1.3 and not getattr(op, "sip", False) and d.time - AG["hand_t"] < 1.4:
            op.sip = True                                        # ...e assaggia
        elif st_ == "sip" and d.time - AG["hand_t"] > 3.2:
            op.sip = False; expr["happy_t"] = d.time; ag_say("Buon caffe', Marco!"); AG["hand"] = "carry"
        elif st_ == "carry" and getattr(op, "ki", 0) == 3 and np.linalg.norm(op.pos - PEOPLE_NAMED[who]) < 0.05:
            dk = DESK.get(who, PEOPLE_NAMED[who]); spot = np.array([dk[0] + 0.12, dk[1] + 0.20, 0.74 + CUP_H / 2 + 0.002])
            op.tw = 4.0; op.face_yaw = math.atan2(spot[1] - op.pos[1], spot[0] - op.pos[0])
            op.carry = False; op.reach_tgt = spot + np.array([0, 0, 0.03]); op.r_reach = 1.0; AG["hand"] = "place"; AG["spot"] = spot
            if not a.busy:
                a.start([a.jmove(a.q, Q_HOME["right"])])
        elif st_ == "place" and op.tw < 2.6:                     # appoggiato sulla scrivania
            AG["cup_in_hand"] = None; AG["cup_done"] = True; set_part_xyz("cup", AG["spot"])
            op.reach_tgt = None; AG["hand"] = "done"
        elif st_ == "done" and op.r_reach < 0.02:
            i_ = PEOPLE_IDX[who]; people[:] = [q for q in people if q.idx != i_]
            op.idx = i_; op.path = [PEOPLE_NAMED[who].copy(), PEOPLE_NAMED[who].copy()]; op.i = 0; op.waits = {}; op.keys = []
            AG["hand"] = "walk"; sk_.phase = 4
        if sk_.t > 60:
            sk_.phase = 4
    elif sk_.phase == 4:
        people[:] = [q for q in people if q.idx != 3]; AG["mode"] = "lavoro"; AG["approach"] = False; AG["taker"] = None
        if AG.get("cup_in_hand"):
            AG["cup_in_hand"] = None
        if not a.busy:
            a.start([a.jmove(a.q, Q_HOME["right"])])
        teach_contour(); mission["state"] = "agente"
        return True
    return False


DOCK_RNG = np.random.default_rng(11)


def dock_sense():
    """riconoscimento della stazione (ICP sul profilo laser della piastra / AprilTag): posa relativa con rumore di misura"""
    gap, ly, dth = dock_error()
    return gap + DOCK_RNG.normal(0, 0.003), ly + DOCK_RNG.normal(0, 0.003), dth + DOCK_RNG.normal(0, math.radians(0.3))


def dock_skill(sk_, k):
    """aggancio alla stazione di ricarica: punto di attesa 60 cm davanti, poi avvicinamento lento in anello chiuso fino a contatti chiusi"""
    if sk_.phase == 0:
        stage = np.array([*(CHG[:2] - 0.60 * np.array([math.cos(CHG[2]), math.sin(CHG[2])])), CHG[2]])   # arriva di fronte alla stazione...
        mission["route"] = route_pose(stage) + [Turn(wrap(CHG[2] + math.pi))]                        # ...poi si gira: retromarcia sui contatti
        FIELDS["mode"] = "marcia"; mission["state"] = "drive_ag"; sk_.phase = 1; sk_.n_ok = 0
        if hasattr(sk_, "gf"):
            del sk_.gf
        ag_say("Vado alla stazione di ricarica.")
    elif sk_.phase == 1 and drive_step(k):
        mission["state"] = "drive_dock"; FIELDS.update(prot=0.30, warn=0.36, mode="aggancio"); sk_.phase = 2; sk_.t = 0.0   # campo di aggancio: la stazione e' esclusa
    elif sk_.phase == 2:                                  # avvicinamento finale (velocita' di aggancio <= 0,08 m/s)
        g_m, ly, dth = dock_sense()
        sk_.gf = g_m if not hasattr(sk_, "gf") else 0.8 * sk_.gf + 0.2 * g_m      # misura filtrata (rumore 3 mm)
        gap = sk_.gf
        v = -float(np.clip(0.9 * (gap + 0.006), 0.012, 0.08)) * k          # retromarcia verso la stazione
        w = float(np.clip(-2.5 * dth - 6.0 * ly, -0.25, 0.25)) * k
        sk_.n_ok = getattr(sk_, "n_ok", 0) + 1 if gap < -0.004 else 0
        if sk_.n_ok >= 10:                                # molla compressa ~5 mm per 10 letture di fila: contatti chiusi, fermo
            v = w = 0.0; sk_.phase = 3; sk_.t = 0.0
        drive["v"], drive["w"] = v, w
        d.ctrl[WL] = (v - w * B_HALF) / WHEEL_R; d.ctrl[WR] = (v + w * B_HALF) / WHEEL_R
        if sk_.t > 25:                                    # non riesce: torna indietro e riprova una volta
            sk_.phase = 0 if not getattr(sk_, "retry", False) else 3; sk_.retry = True
    elif sk_.phase == 3:
        drive["v"] = drive["w"] = 0.0; d.ctrl[WL] = d.ctrl[WR] = 0.0
        if sk_.t > 0.6:
            teach_contour(); mission["state"] = "agente"
            if BAT["charging"]:
                ag_say("In carica: contatti chiusi, 48 V."); m.geom_rgba[m.geom("charger_led").id] = [0.2, 1.0, 0.4, 1]
            else:
                ag_say("Aggancio non riuscito: chiamo assistenza.")
            return True
    return False


def auto_charge():
    """ricarica automatica: sotto il 30% e senza compiti in corso va alla stazione C da solo"""
    if AG["cur"] is None and not AG["queue"] and not BAT["charging"] and soc() < 0.30 and not AG.get("going_charge"):
        AG["queue"].append({"skill": "ricarica"}); AG["going_charge"] = True
        ag_say(f"Batteria al {100 * soc():.0f}%: vado a ricaricarmi.")
    if BAT["charging"]:
        AG["going_charge"] = False


def agent_step(k):
    auto_charge()
    cup_hold_follow()
    if mission["state"] == "settle":
        teach_contour(); mission["state"] = "agente"
    agent_people()
    if AG["cur"] is None and AG["queue"]:
        AG["cur"] = Skill(AG["queue"].pop(0))
    if AG["cur"] is not None and AG["cur"].step(k):
        AG["cur"] = None
    if mission["state"] in ("look_A", "load_A", "look_B", "unload_B"):
        mission_step(k)
    # comandi a tempo (demo)
    while AG["pending"] and d.time >= AG["pending"][0][0] and AG["cur"] is None and not AG["queue"]:
        ag_command(AG["pending"].pop(0)[1])


AMR_H_ = 0.25
if args.agent:
    for chunk in args.agent.split("|"):
        t_, txt = chunk.split(":", 1)
        AG["pending"].append((float(t_), txt.strip()))


def control_step():
    t = d.time
    d.qfrc_applied[GC_DOFS] = np.clip(d.qfrc_bias[GC_DOFS], -GC_TAU, GC_TAU)
    if int(round(t / DT)) % 16 == 0:
        face_step()
    if not args.agent:
        operator_step(); passer_step()
    for p in people:
        p.step(t, DT)
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
            if zone == 1 and state["zone"] == 0:
                stats["slows"] += 1
            state["clear_t"] += 0.03
            if state["clear_t"] > 1.0 or state["k_cmd"] > 0:
                state["k_cmd"] = 0.3 if zone == 1 else 1.0
        state["zone"] = zone
    k, kc = state["k"], state["k_cmd"]
    state["k"] = k = max(kc, k - DT / 0.3) if kc < k else min(kc, k + DT / 0.6)
    if args.agent:
        agent_step(k)
    else:
        mission_step(k)
    if not mission["state"].startswith("drive"):
        hold_step()
    teach_step()
    for a in arms.values():
        a.step(DT, k); a.apply()
    clips_step(); handover_step()
    base_target_step()
    mujoco.mj_step(m, d)
    energy_step()


# ---------------------------------------------------------------- uscite
STATE_TXT = {"settle": "avvio", "wait_load": "baia A: attesa (banco di kitting pieno?)", "look_A": "visione: cerca i flaconi sul banco A",
             "load_A": "carico da solo: 3 per lato sul vassoio + 1 in pinza", "drive_AB": "AMR: trasporto A -> B",
             "look_B": "visione: cerca i fori liberi (banco B)", "unload_B": "scarico: inserimento nei fori (smusso + visione)",
             "drive_BW": "AMR: ritorno verso A (punto di attesa)", "wait_refill": "attesa: l'operatore rifornisce il banco A",
             "drive_WA": "AMR: aggancio in baia A", "done": "ciclo completato", "agente": "agente", "drive_ag": "AMR: in marcia"}
ZN = ["LIBERO", "AVVISO - velocita' 30%", "PROTEZIONE - arresto"]
ZCOL = [(80, 255, 110), (255, 215, 30), (255, 50, 50)]


def onboard():
    return onboard_count() + sum(1 for a in arms.values() if a.held)


def bat_line():
    st_ = "IN CARICA 960 W (tempo x30)" if BAT["charging"] else f"{BAT['P']:.0f} W"
    return f"batteria 48 V LiFePO4: {100 * soc():.0f}%   {st_}"


def hud_lines():
    if args.agent:
        return [f"GIORGIO  //  agente: Sistema 1 (router locale) + Sistema 2 (Claude)   modalita': {AG['mode']}",
                f"abilita' in corso: {fmt(AG['cur'].s) if AG['cur'] else '-'}   in coda: {len(AG['queue'])}",
                f"scanner ({FIELDS['mode']}): {ZN[state['zone']]}   |   " + bat_line()] + AG["chat"][-4:] + ([f'GIORGIO: "{AG["say"]}"'] if d.time - AG["say_t"] < 4 else [])
    return _hud_lines()


def _hud_lines():
    ve = stats["vis_err"]
    return [f"GIORGIO  //  OpenArm 2.0 + AgileX Tracer 2.0 + Gemini 336L + Insta360 X4",
            f"missione: {STATE_TXT.get(mission['state'], mission['state'])}" + (f"   v = {drive['v']:.2f} m/s" if mission['state'].startswith('drive') else ""),
            f"scanner ({FIELDS['mode']}): {ZN[state['zone']]}   campi {FIELDS['prot']:.2f} / {FIELDS['warn']:.2f} m   |   " + bat_line(),
            f"a bordo {onboard()}/{len(PARTS)}   inseriti {stats['inserted']}   falliti {stats['lost']}   arresti {stats['stops']}   rallentamenti {stats['slows']}"
            + (f"   visione {np.mean(ve):.1f} mm" if ve else "")]


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
    if mission["route"] and mission["state"].startswith("drive"):          # traiettoria pianificata
        for lg in mission["route"]:
            if isinstance(lg, Leg):
                for i in range(lg.i, len(lg.P) - 3, 3):
                    line((*lg.P[i], 0.01), (*lg.P[i + 3], 0.01), (0.2, 0.75, 1.0, 0.9), 3.0)
    if mission["state"] in ("look_A", "load_A", "look_B", "unload_B"):
        for dt in vision.dets:
            z = Z_GRASP + 0.05 if dt["kind"] == "flacone" else BENCH_Z + FIX_H + 0.01
            dot((dt["xy"][0], dt["xy"][1], z), (0.2, 1.0, 0.45, 0.9) if dt["kind"] == "flacone" else (0.2, 0.7, 1.0, 0.9))


def finished():
    if args.agent:
        return d.time > args.seconds or (not AG["pending"] and not AG["queue"] and AG["cur"] is None and d.time > 5 and AG.get("end_t", 1e9) < d.time)
    return _finished()


def _finished():
    return (mission["state"] == "done" and not any(q.idx == 0 for q in people) and mission["t"] > 2.0) or d.time > args.seconds


cam = mujoco.MjvCamera(); cam.distance = 3.4; cam.elevation = -28
if args.video:
    import cv2
    import imageio
    W, H = 1600, 900
    r = mujoco.Renderer(m, H, W)
    wr = mujoco.Renderer(m, 108, 190)
    writer = imageio.get_writer(args.video, fps=30, quality=7, macro_block_size=8)
    cam.lookat[:] = [-1.6, 1.0, 0.8]; cam.azimuth = 215
    t_next, wall0 = 0.0, time.time()
    while not finished():
        control_step()
        if d.time >= t_next:
            t_next += args.speedup / 30
            b = d.body("amr").xpos
            if globals().get("CAM_FIXED"):                 # scene dimostrative: inquadratura fissa
                cam.lookat[:], cam.distance, cam.azimuth, cam.elevation = CAM_FIXED
            else:
                cam.lookat[:] = 0.97 * np.array(cam.lookat) + 0.03 * np.array([b[0] * 0.7 - 0.5, b[1] * 0.7 + 0.3, 0.8])
            r.update_scene(d, cam); draw(r.scene)
            img = r.render().copy()
            vis = vision.render_overlay()
            if vis is not None:
                img[20:320, W - 500:W - 20] = cv2.resize(vis, (480, 300))
                cv2.rectangle(img, (W - 502, 18), (W - 18, 322), (60, 220, 120), 2)
            for j, s_ in enumerate(("right", "left")):
                wr.update_scene(d, f"camera_wrist_{s_}"); x0 = W - 500 + j * 245
                img[335:443, x0:x0 + 190] = wr.render()
                cv2.putText(img, f"polso {'dx' if s_ == 'right' else 'sx'}", (x0 + 5, 352), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            for i, txt in enumerate(hud_lines()):
                col = ZCOL[state["zone"]] if i == 2 else (235, 235, 240)
                cv2.putText(img, txt, (22, 38 + 30 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(img, txt, (22, 38 + 30 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.66, col, 2, cv2.LINE_AA)
            for i, txt in enumerate(mission["log"]):
                cv2.putText(img, txt, (22, H - 110 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(img, txt, (22, H - 110 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (250, 250, 250), 1, cv2.LINE_AA)
            big = ["", "RALLENTA - persona vicina", "STOP - persona troppo vicina"][state["zone"]]
            if big:
                col = ZCOL[state["zone"]]; (tw, th_), _ = cv2.getTextSize(big, cv2.FONT_HERSHEY_DUPLEX, 1.4, 3)
                cv2.rectangle(img, ((W - tw) // 2 - 20, H - 170), ((W + tw) // 2 + 20, H - 115), (20, 20, 20), -1)
                cv2.putText(img, big, ((W - tw) // 2, H - 128), cv2.FONT_HERSHEY_DUPLEX, 1.4, col[::-1] if False else col, 3, cv2.LINE_AA)
            if args.speedup > 1:
                cv2.putText(img, f"x{args.speedup}", (W - 90, H - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
            writer.append_data(img)
    writer.close(); print("video:", args.video)
elif args.record:
    import pickle
    geoms = []
    for g in range(m.ngeom):
        nm_ = m.geom(g).name
        if m.geom_group[g] > 2 or (m.geom_rgba[g][3] == 0 and m.geom_matid[g] < 0 and not nm_.startswith(("cup_steam", "cm_stream"))):
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
    ANIM_N = ["eye_l", "eye_r", "mus_l", "mus_r", "cup_coffee", "cup_steam0", "cup_steam1", "cup_steam2", "cm_stream", "cm_btn1",
              "charger_led", "status_led0", "status_led1", "status_led2", "status_led3"]
    ANIM = [m.geom(n).id for n in ANIM_N]
    hum = [m.geom(f"h{h}_{k}_g").id for h in range(NH) for k in range(N_SEG)]
    XP, XQ, ZONE, SIZES, AN, ST, HRGB, FC, EN = [], [], [], [], [], [], [], [], []
    t_next = 0.0
    while not finished():
        control_step()
        if d.time >= t_next:
            t_next += 1 / 30
            XP.append(d.xpos.copy()); XQ.append(d.xquat.copy()); ZONE.append(state["zone"]); ST.append(mission["state"])
            SIZES.append(np.array([m.geom_size[g] for g in hum]) if hum else np.zeros((0, 3)))
            HRGB.append(np.array([m.geom_rgba[g] for g in hum]) if hum else np.zeros((0, 4)))
            FC.append(list(FACE)); EN.append([soc(), float(BAT["charging"]), BAT["P"]])
            AN.append(np.array([np.r_[m.geom_pos[g], m.geom_quat[g], m.geom_size[g],
                                (m.geom_rgba[g] if m.geom_matid[g] < 0 else np.r_[m.mat_rgba[m.geom_matid[g]][:3], m.geom_rgba[g][3]])] for g in ANIM]))
    pickle.dump(dict(geoms=geoms, xpos=np.array(XP), xquat=np.array(XQ), zone=np.array(ZONE), hum=hum, hum_sizes=np.array(SIZES),
                     hum_rgba=np.array(HRGB), n_seg=N_SEG, face=np.array(FC),
                     anim=np.array(AN), anim_names=ANIM_N, states=ST, energy=np.array(EN),
                     body_names=[m.body(i).name for i in range(m.nbody)], r_prot=R_PROT, r_warn=R_WARN, stats=stats), open(args.record, "wb"))
    print(f"registrati {len(XP)} fotogrammi -> {args.record}", flush=True)
else:
    import mujoco.viewer
    with mujoco.viewer.launch_passive(m, d) as v:
        v.cam.lookat[:] = [-1.2, 0.8, 0.9]; v.cam.distance = 4.8; v.cam.azimuth = 215; v.cam.elevation = -32
        last = 0.0
        while v.is_running() and not finished():
            t0 = time.time()
            for _ in range(int((1 / 60) / DT)):
                control_step()
            with v.lock():
                v.user_scn.ngeom = 0
                draw(v.user_scn)
            big = ["", "RALLENTA - persona vicina (30%)", "STOP - persona nel campo di protezione"][state["zone"]]
            v.set_texts([(mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPLEFT, "\n".join(hud_lines()), ""),
                         (mujoco.mjtFontScale.mjFONTSCALE_300, mujoco.mjtGridPos.mjGRID_BOTTOM, big, "")])
            if time.time() - last > 0.2:
                last = time.time()
                vis = vision.render_overlay()
                if vis is not None:
                    v.set_images([(mujoco.MjrRect(v.viewport.width - 650, v.viewport.height - 410, 640, 400), vis)])
            v.sync()
            time.sleep(max(0.0, 1 / 60 - (time.time() - t0)))
print(f"FINE t={d.time:.1f}s: caricati {stats['loaded']}, inseriti {stats['inserted']}, falliti {stats['lost']}, arresti {stats['stops']}, "
      f"rallentamenti {stats['slows']}, visione {np.mean(stats['vis_err']) if stats['vis_err'] else 0:.1f} mm", flush=True)

