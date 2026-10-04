"""Giorgio v14 - scatole: vassoio frontale + rastrelliera posteriore (al posto dello zaino caffe').

Banco A2: 2 scatole piccole (160 x 100 x 100 mm, 1.2 kg) e 1 scatola grande (180 x 300 x 140 mm, 3.0 kg).
 1. le due braccia prendono le scatole piccole (pinza, presa per attrito) e le posano sulla rastrelliera posteriore
    (pinza inclinata di 30 gradi verso l'esterno; durante il trasferimento la mano ruota di 180 gradi attorno alla verticale:
    la scatola resta orizzontale)
 2. presa bimanuale della scatola grande (le due mani la stringono dai fianchi: forza dal controllo di posizione cedevole,
    nessun vincolo) -> vassoio frontale
 3. marcia fino al banco B2
 4. scarico: scatola grande (bimanuale) e le due piccole dalla rastrelliera -> banco B2
Fisica vera: nessun oggetto viene spostato a mano o saldato; le scatole stanno sul vassoio/rastrelliera per attrito.
uso: MUJOCO_GL=egl python giorgio_scatole.py --record render/rec_scatole_v14.pkl     (oppure --video ..., oppure GUI)
"""
import math
import sys

import numpy as np

argv = sys.argv[1:]
HEADLESS = "--headless" in argv
argv = [a_ for a_ in argv if a_ != "--headless"]
sys.argv = ["giorgio_v5.py", "--no_humans", "--seconds", "260"] + argv
src = open(__file__.replace("giorgio_scatole.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")


def _sub(s, a, b):
    assert a in s, a[:60]
    return s.replace(a, b, 1)


pre = _sub(pre, 'sp = build(args.look, hands=args.hands, base="amr", fixed_base=False, buffer=True, coffee=True)',
           'sp = build(args.look, hands=args.hands, base="amr", fixed_base=False, buffer=False, coffee=False, box_tray=True, rear_rack=True)')
pre = _sub(pre, 'SHUTTLE = m.actuator("cm_shuttle").id',
           'SHUTTLE = m.actuator("cm_shuttle").id if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, "cm_shuttle") >= 0 else -1')
PROPS = '''
DOCK["A2"] = np.array([2.6, -1.3, 0.0]); DOCK["B2"] = np.array([2.6, 1.5, 0.0])
BENCH_OFF = 0.17                                   # banchi 17 cm piu' lontani: il bordo e' a 0.33 m, oltre il vassoio frontale (0.315 m)
for nm_ in ("A2", "B2"):
    c_ = local_to_world(DOCK[nm_], BENCH_OFF, 0.0)
    table(nm_, np.array([c_[0], c_[1], DOCK[nm_][2]]))
SBOX = (0.08, 0.05, 0.05)                           # scatola piccola: semiassi 160 x 100 x 100 mm
TOTE = (0.12, 0.18, 0.07, 0.006)                    # cassetta aperta: 240 (x) x 360 (y) x 140 mm, pareti 6 mm
BOXES = {"box_s_r": (SBOX, 1.2, (0.42, -0.31)), "box_s_l": (SBOX, 1.2, (0.42, 0.31)), "box_big": (None, 1.0, (0.455, 0.0))}
# cassetta (PP, 1.0 kg) con 6 flaconi da 0.35 kg (quelli della logistica): contenuto modellato come massa rigida nella cassetta
p_ = local_to_world(DOCK["A2"], 0.455, 0.0)
tb_ = wb.add_body(name="box_big", pos=[p_[0], p_[1], BENCH_Z + TOTE[2] + 0.0005])
tb_.add_freejoint(name="box_big_free")
hx_, hy_, hz_, tw_ = TOTE
for nm_, ps_, sz_ in (("box_big_g", (0, 0, -hz_ + 0.003), (hx_, hy_, 0.003)),
                      ("box_big_wx0", (hx_ - tw_ / 2, 0, 0.003), (tw_ / 2, hy_, hz_ - 0.003)), ("box_big_wx1", (-hx_ + tw_ / 2, 0, 0.003), (tw_ / 2, hy_, hz_ - 0.003)),
                      ("box_big_wy0", (0, hy_ - tw_ / 2, 0.003), (hx_ - tw_, tw_ / 2, hz_ - 0.003)), ("box_big_wy1", (0, -hy_ + tw_ / 2, 0.003), (hx_ - tw_, tw_ / 2, hz_ - 0.003))):
    tb_.add_geom(name=nm_, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(ps_), size=list(sz_), mass=0.2, rgba=[0.16, 0.36, 0.62, 1],
                 friction=[0.8, 0.01, 0.001], condim=4, conaffinity=3, group=GROUP_ENV)
for k_, (bx_, by_) in enumerate([(x_, y_) for x_ in (-0.05, 0.05) for y_ in (-0.07, 0.0, 0.07)]):
    tb_.add_geom(name=f"box_big_fl{k_}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[bx_, by_, -hz_ + 0.006 + 0.08], size=[0.025, 0.08, 0],
                 material="part", mass=0.35, contype=0, conaffinity=0, group=GROUP_ENV)
    tb_.add_geom(name=f"box_big_cap{k_}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[bx_, by_, -hz_ + 0.006 + 0.166], size=[0.012, 0.006, 0],
                 material="accent", mass=0.0, contype=0, conaffinity=0, group=GROUP_ENV)
for nm_, (hs_, ms_, (xl_, yl_)) in BOXES.items():
    if hs_ is None:
        continue
    p_ = local_to_world(DOCK["A2"], xl_, yl_)
    b_ = wb.add_body(name=nm_, pos=[p_[0], p_[1], BENCH_Z + hs_[2] + 0.0005])
    b_.add_freejoint(name=nm_ + "_free")
    b_.add_geom(name=nm_ + "_g", type=mujoco.mjtGeom.mjGEOM_BOX, size=list(hs_), mass=ms_, rgba=[0.70, 0.52, 0.33, 1],
                friction=[0.7, 0.01, 0.001], condim=4, conaffinity=3, group=GROUP_ENV)       # cartone
    b_.add_geom(name=nm_ + "_tape", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, hs_[2] + 0.0004], size=[hs_[0] + 0.0004, 0.024, 0.0005],
                rgba=[0.58, 0.42, 0.26, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)   # nastro
    for sx_ in (-1, 1):                                                                      # etichette sulle due testate
        b_.add_geom(name=f"{nm_}_label{sx_}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[sx_ * (hs_[0] + 0.0004), 0, 0.006],
                    size=[0.0005, min(0.045, 0.6 * hs_[1]), 0.6 * hs_[2]], rgba=[0.95, 0.95, 0.93, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
        b_.add_geom(name=f"{nm_}_stripe{sx_}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[sx_ * (hs_[0] + 0.0008), 0, 0.006 + 0.45 * hs_[2]],
                    size=[0.0005, min(0.045, 0.6 * hs_[1]), 0.07 * hs_[2]], rgba=[1.0, 0.55, 0.2, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
for s_ in ("right", "left"):                         # sonde invisibili: scatola tenuta in mano, per le verifiche di distanza in pianificazione
    pb_ = wb.add_body(name=f"probe_{s_}", mocap=True, pos=[0, 0, -3])
    pb_.add_geom(name=f"probe_{s_}_g", type=mujoco.mjtGeom.mjGEOM_BOX, size=list(SBOX), contype=0, conaffinity=0, group=3, rgba=[1, 0, 0, 0.3])
'''
pre = _sub(pre, "m = sp.compile()", PROPS + "\nm = sp.compile()")
pre = _sub(pre, 'd.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A"][0], DOCK["A"][1], 0.0]', 'd.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A2"][0], DOCK["A2"][1], 0.0]')
pre = _sub(pre, 'd.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(DOCK["A"][2] / 2), 0, 0, math.sin(DOCK["A"][2] / 2)]', 'd.qpos[FREE_Q + 3:FREE_Q + 7] = [1, 0, 0, 0]')
exec(compile(pre, "giorgio_v5", "exec"))
from scipy.spatial.transform import Slerp
import itertools
from giorgio_model import BT_X0, BT_X1, BT_Z, RR_X0, RR_X1, RR_Z

set_part_xyz("cup", np.array([-7.0, 4.6, CUP_H / 2 + 0.001]))     # niente zaino caffe': bicchiere fuori scena
for p_ in PARTS:
    set_part_xyz(p_, storage(p_))
mujoco.mj_forward(m, d)
mission["state"] = "demo"
teach_contour()
print(f"modello scatole: massa robot {m.body_subtreemass[m.body('amr').id]:.2f} kg", flush=True)

OPEN = {"right": -0.785, "left": 0.785}            # pinza tutta aperta (punte a 134 mm)
PINCH = {"right": 0.35, "left": -0.35}            # chiusura oltre il contatto: le dita stringono la parete (~4 Nm al giunto)
SG = {"right": -1, "left": 1}
BOX_NAMES = list(BOXES)
BOX_G = {b: m.geom(b + "_g").id for b in BOX_NAMES}
BOX_GEOMS = {b: [g_ for g_ in range(m.ngeom) if m.geom_bodyid[g_] == m.body(b).id and m.geom_contype[g_] + m.geom_conaffinity[g_] > 0] for b in BOX_NAMES}
MARKS, RES = [], {}
ALLOW = set()                                      # contatti voluti mano/scatola nella fase corrente: (lato, scatola)


def W(xl, yl, z, pose=None):
    q_ = local_to_world(base_pose() if pose is None else pose, xl, yl)
    return np.array([q_[0], q_[1], z])


def Rh(psi_l, p, ax="y"):
    """orientazione della pinza: imbardata psi_l rispetto alla base, poi beccheggio p attorno all'asse di chiusura (ax='y')
    o all'asse x della mano (ax='x'). Con p costante una scatola stretta resta orizzontale qualunque sia l'imbardata."""
    return Rot.from_euler("z", base_pose()[2] + psi_l).as_matrix() @ Rot.from_euler(ax, p).as_matrix()


def box_local(b):
    """posa della scatola nel riferimento della base: x, y, z (centro), imbardata relativa"""
    xy = local_rel(d.body(b).xpos[:2]); R = d.body(b).xmat.reshape(3, 3)
    return np.array([xy[0], xy[1], d.body(b).xpos[2], wrap(math.atan2(R[1, 0], R[0, 0]) - base_pose()[2])])


def solve_ns(a, q0, pt, Rt, q_bias, iters=150, k_ns=0.3):
    """IK a minimi quadrati smorzati con termine nel nullo (7 giunti, compito 6D): tende verso q_bias senza muovere la pinza"""
    ik = a.ik; q = np.clip(np.array(q0, float), ik.lo, ik.hi)
    Jp, Jr = np.zeros((3, m.nv)), np.zeros((3, m.nv)); Wt = np.array([1, 1, 1, 0.6, 0.6, 0.6])
    for it in range(iters):
        p_, R_ = ik.fk(d.qpos, q); e = ik.err(p_, R_, pt, Rt)
        mujoco.mj_jacSite(m, ik.d, Jp, Jr, ik.site)
        J = np.vstack([Jp, Jr])[:, ik.dadr] * Wt[:, None]
        JJ = J @ J.T + 2e-4 * np.eye(6); Jp_ = J.T @ np.linalg.solve(JJ, np.eye(6))
        dq = Jp_ @ (e * Wt) + (np.eye(7) - Jp_ @ J) @ (k_ns * (q_bias - q))
        q = np.clip(q + np.clip(dq, -0.2, 0.2), ik.lo, ik.hi)
        if np.linalg.norm(e[:3]) < 3e-4 and np.linalg.norm(e[3:]) < 3e-3 and it > 4:
            break
    p_, R_ = ik.fk(d.qpos, q); e = ik.err(p_, R_, pt, Rt)
    return q, float(np.linalg.norm(e[:3])), float(np.linalg.norm(e[3:]))


class Path_:
    """traiettoria cartesiana (posizione + orientazione) di un braccio, campionata e risolta con l'IK in sequenza (stesso ramo)"""

    def __init__(self, a, q=None):
        self.a, self.q, self.segs, self.err = a, (a.q if q is None else q).copy(), [], 0.0
        self.p, self.R = a.ik.fk(d.qpos, self.q)

    def joint(self, qb, dur):
        self.segs.append(Seg("joint", self.q.copy(), qb.copy(), dur)); self.q = qb.copy()
        self.p, self.R = self.a.ik.fk(d.qpos, self.q)
        return self

    def run(self, wps):
        """waypoint: (p, R, dur) oppure ("grip", g, dur, ev) oppure ("wait", dur, ev)"""
        for w_ in wps:
            if isinstance(w_[0], str) and w_[0] == "grip":
                self.grip(w_[1], w_[2], w_[3] if len(w_) > 3 else None)
            elif isinstance(w_[0], str):
                self.wait(w_[1], w_[2] if len(w_) > 2 else None)
            else:
                self.to(w_[0], w_[1], w_[2], w_[3] if len(w_) > 3 else None, w_[4] if len(w_) > 4 else None)
        return self

    def to(self, p, R, dur, n=None, q_goal=None):
        p = np.asarray(p, float)
        n = n or self.nfor(p, R)
        sl = Slerp([0, 1], Rot.from_matrix(np.stack([self.R, R])))
        q, q_s = self.q, self.q.copy()
        for k in range(1, n + 1):
            u = smooth(k / n)
            if q_goal is not None:                     # ridondanza (7 giunti): il ramo scivola verso la configurazione di arrivo
                qn, ep, er = solve_ns(self.a, q, self.p + (p - self.p) * u, sl(u).as_matrix(), q_s + (q_goal - q_s) * u)
            else:
                qn, ep, er = self.a.ik.solve1(d.qpos.copy(), q, self.p + (p - self.p) * u, sl(u).as_matrix(), 80)
            self.err = max(self.err, ep)
            self.segs.append(Seg("lin", q, qn, dur / n)); q = qn
        self.p, self.R, self.q = p, R, q
        return self

    def nfor(self, p, R):
        ang = np.linalg.norm(Rot.from_matrix(R @ self.R.T).as_rotvec())
        return max(4, int(np.linalg.norm(np.asarray(p) - self.p) / 0.012 + ang / 0.05))

    def grip(self, g, dur, ev=None):
        self.segs.append(Seg("grip", dur=dur, grip=g, ev=ev)); return self

    def wait(self, dur, ev=None):
        self.segs.append(Seg("wait", dur=dur, ev=ev)); return self


_rs = np.random.default_rng(11)
SEEDS0 = [np.array([-0.59, 2.38, 0.36, 1.63, 0.79, 0.3, 1.19]) * np.array(sg_) for sg_ in itertools.product((1, -1), repeat=7)][::5]


def ik_candidates(a, p, R, q_ref, k=16):
    """soluzioni IK distinte per una posa difficile, ordinate per margine dai finecorsa e vicinanza a q_ref"""
    ck = (a.s, tuple(np.round(p, 3)), tuple(np.round(np.asarray(R).ravel(), 3)))
    if ck in _IKC:
        return _IKC[ck]
    sols = []
    rs_ = np.random.default_rng(int(1000 * abs(p[0]) + 7919 * abs(p[1]) + 104729 * abs(p[2])) % (2 ** 32))   # semi deterministici
    seeds = [q_ref] + [np.clip(s_, a.ik.lo, a.ik.hi) for s_ in SEEDS0] + [rs_.uniform(a.ik.lo, a.ik.hi) for _ in range(64)]
    for sd in seeds:
        q, ep, er = a.ik.solve1(d.qpos.copy(), sd, np.asarray(p, float), R, 120)
        if ep < 0.0015 and er < 0.015 and not any(np.linalg.norm(q - s_) < 0.15 for s_ in sols):
            sols.append(q)
    mg = lambda q: min(np.min(q - a.ik.lo), np.min(a.ik.hi - q))
    _IKC[ck] = sorted(sols, key=lambda q: -min(mg(q), 0.25) + 0.05 * np.linalg.norm(q - q_ref))[:k]
    return _IKC[ck]


_IKC = {}


def wp_n(wps, p0, R0):
    """numero di campioni per tratto, deciso dai waypoint cartesiani (uguale per le due braccia a specchio)"""
    out, p_, R_ = [], np.asarray(p0, float), R0
    for w_ in wps:
        if isinstance(w_[0], str):
            out.append(w_); continue
        ang = np.linalg.norm(Rot.from_matrix(w_[1] @ R_.T).as_rotvec())
        n = max(4, int(np.linalg.norm(np.asarray(w_[0]) - p_) / 0.012 + ang / 0.05))
        out.append((w_[0], w_[1], w_[2], n * (3 if len(w_) > 4 else 1)) + tuple(w_[4:])); p_, R_ = np.asarray(w_[0], float), w_[1]
    return out


SHELL_G = [m.geom(n_).id for n_ in ("shell_torso", "head_shell", "waist_cover", "face_glass", "gemini_body", "insta360", "column_cover", "crown_neck")]


from scipy.spatial import ConvexHull
_HULL, _VERT, _FT = {}, {}, np.zeros(6)


def _geom_vp(g):
    """vertici e piani (n.p + b <= 0 dentro) del convesso del geom, nel suo frame locale"""
    if g not in _HULL:
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[g]; v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]].astype(float)
            eq = ConvexHull(v).equations
        else:                                        # box (o approssimato col suo box)
            h = m.geom_size[g].copy()
            if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_CYLINDER:
                h = np.array([h[0], h[0], h[1]])
            v = np.array([[sx * h[0], sy * h[1], sz * h[2]] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
            eq = np.array([[1, 0, 0, -h[0]], [-1, 0, 0, -h[0]], [0, 1, 0, -h[1]], [0, -1, 0, -h[1]], [0, 0, 1, -h[2]], [0, 0, -1, -h[2]]], float)
        _VERT[g], _HULL[g] = v, eq
    return _VERT[g], _HULL[g]


def gdist(dd, g1, g2, distmax):
    """mj_geomDistance; se torna 0.0 con segmento incoerente (succede con mesh/box in questa versione) stima conservativa dai
    piani dei due convessi (vertici dell'uno contro le facce dell'altro, nei due versi)"""
    r = mujoco.mj_geomDistance(m, dd, g1, g2, distmax, _FT)
    if r != 0.0 or np.linalg.norm(_FT[:3] - _FT[3:]) < 1e-4:
        return r
    out = []
    for a_, b_ in ((g1, g2), (g2, g1)):
        va, _ = _geom_vp(a_); _, eqb = _geom_vp(b_)
        w = va @ dd.geom_xmat[a_].reshape(3, 3).T + dd.geom_xpos[a_]
        loc = (w - dd.geom_xpos[b_]) @ dd.geom_xmat[b_].reshape(3, 3)
        out.append(float((loc @ eqb[:, :3].T + eqb[:, 3]).max(1).min()))
    return min(min(out), distmax)


CLQ = {}
SHELL_HULL_SKIP = {m.geom("shell_torso").id, m.geom("head_shell").id}   # spalla vs busto/testa: verificata sulla superficie vera (verifiche/gusci_reali.py)


def clear_q(a, q, probe=None, other=None):
    """distanza minima (convessi, MuJoCo) tra il braccio a in configurazione q (+ scatola tenuta) e gusci/vassoio/rastrelliera;
    other = (lato, q) dell'altro braccio per la distanza braccio-braccio"""
    ik = a.ik; ik.fk(d.qpos, q)
    if other is not None:
        ik.d.qpos[arms[other[0]].ik.qadr] = other[1]; mujoco.mj_kinematics(m, ik.d)
    gl = [g_ for g_ in ARM_COLL[a.s] if not m.body(m.geom_bodyid[g_]).name.endswith(("base_link", "link1"))]   # spalla: dentro il busto per progetto
    if probe is not None:
        off_p, off_R = probe; ps, Rs = ik.d.site_xpos[ik.site], ik.d.site_xmat[ik.site].reshape(3, 3)
        mid = m.body_mocapid[m.body(f"probe_{a.s}").id]
        ik.d.mocap_pos[mid] = ps + Rs @ off_p; qq = np.zeros(4); mujoco.mju_mat2Quat(qq, (Rs @ off_R).reshape(-1)); ik.d.mocap_quat[mid] = qq
        mujoco.mj_kinematics(m, ik.d); gl.append(m.geom(f"probe_{a.s}_g").id)
    ft = np.zeros(6); best = 9.0
    targets = SHELL_G + ROBOT_FIX + FURN + [g_ for b_ in BOX_NAMES if b_ != CARRY.get(a.s) for g_ in BOX_GEOMS[b_]] + ([g_ for g_ in ARM_COLL[other[0]] if not m.body(m.geom_bodyid[g_]).name.endswith(('base_link', 'link1'))] if other is not None else [])
    for g in gl:
        upper = m.body(m.geom_bodyid[g]).name.endswith(("link2", "link3"))
        for t_ in targets:
            if np.linalg.norm(ik.d.geom_xpos[g] - ik.d.geom_xpos[t_]) > 0.55 or (upper and t_ in SHELL_HULL_SKIP):
                continue
            dd_ = gdist(ik.d, g, t_, 0.2)
            if dd_ < best:
                best = dd_; CLQ["pair"] = (m.geom(g).name, m.geom(t_).name)
    if probe is not None:
        ik.d.mocap_pos[m.body_mocapid[m.body(f"probe_{a.s}").id]] = [0, 0, -3]
    return best


DBG = bool(os.environ.get('DBG_SC'))
CARRY = {}                                          # scatola in mano (esclusa dagli ostacoli nella pianificazione)


def q_ok(a, q, probe, margin=0.012):
    margin = MARG["m"]
    if np.any(q < a.ik.lo + 0.01) or np.any(q > a.ik.hi - 0.01):
        return False
    _, Rq = a.ik.fk(d.qpos, q)
    if Rq[2, 2] < 0.30:                              # dita entro ~70 gradi dalla verticale: la scatola resta sotto la pinza
        return False
    return clear_q(a, q, probe) > margin


def rrt_connect(a, qa, qb, probe=None, iters=2500, step=0.22, seed=0):
    """RRT-Connect nei giunti (braccio + scatola tenuta contro gusci/vassoio/rastrelliera/banchi/altre scatole), poi scorciatoie.
    Margine 30 mm; se gli estremi stessi sono piu' vicini (presa/deposito appena fatti) si riprova con 15 mm."""
    MARG["m"] = 0.030
    if not (q_ok(a, qa, probe) and q_ok(a, qb, probe)):
        MARG["m"] = 0.015
    try:
        return _rrt_connect(a, qa, qb, probe, iters, step, seed)
    finally:
        MARG["m"] = 0.030


MARG = {"m": 0.030}


def _rrt_connect(a, qa, qb, probe=None, iters=2500, step=0.22, seed=0):
    rg = np.random.default_rng(seed)
    def edge_ok(q1, q2):
        n_ = max(2, int(np.max(np.abs(q2 - q1)) / 0.05))
        return all(q_ok(a, q1 + (q2 - q1) * u, probe) for u in np.linspace(0, 1, n_ + 1)[1:])
    if edge_ok(qa, qb):
        return [qa, qb]
    TA, TB = [(qa, -1)], [(qb, -1)]
    def extend(T, qt):
        i_ = min(range(len(T)), key=lambda k_: np.linalg.norm(T[k_][0] - qt))
        qn = T[i_][0]; dv = qt - qn; L_ = np.linalg.norm(dv)
        qnew = qt if L_ <= step else qn + dv / L_ * step
        if edge_ok(qn, qnew):
            T.append((qnew, i_)); return len(T) - 1
        return None
    def path(T, i_):
        out = []
        while i_ >= 0:
            out.append(T[i_][0]); i_ = T[i_][1]
        return out
    for it in range(iters):
        qr = rg.uniform(a.ik.lo, a.ik.hi) if rg.random() > 0.1 else TB[-1][0]
        ia = extend(TA, qr)
        if ia is None:
            TA, TB = TB, TA; continue
        # connetti l'altro albero
        while True:
            ib = extend(TB, TA[ia][0])
            if ib is None:
                break
            if np.linalg.norm(TB[ib][0] - TA[ia][0]) < 1e-9:
                pa, pb = path(TA, ia), path(TB, ib)
                P_ = pa[::-1] + pb[1:]
                if np.linalg.norm(P_[0] - qa) > 1e-9:
                    P_ = P_[::-1]
                for _ in range(200):                   # scorciatoie
                    if len(P_) < 3:
                        break
                    i1, i2 = sorted(rg.choice(len(P_), 2, replace=False))
                    if i2 - i1 > 1 and edge_ok(P_[i1], P_[i2]):
                        P_ = P_[:i1 + 1] + P_[i2:]
                Lp = lambda pp: sum(np.max(np.abs(pp[k_ + 1] - pp[k_])) for k_ in range(len(pp) - 1))
                best_ = P_
                for k_ in range(1, len(P_) - 1):       # percorso a un solo nodo intermedio, se libero e piu' corto
                    for f_ in (0.0, 0.25, 0.5):
                        qm = P_[k_] + f_ * ((qa + qb) / 2 - P_[k_])
                        if q_ok(a, qm, probe) and edge_ok(qa, qm) and edge_ok(qm, qb) and Lp([qa, qm, qb]) < Lp(best_):
                            best_ = [qa, qm, qb]
                return best_
        TA, TB = TB, TA
    return None


def path_segs(qs, vmax=0.7, tmin=1.5):
    """percorso nei giunti -> tratti 'lin' ricampionati con profilo di velocita' morbido sull'intero percorso"""
    qs = [np.asarray(q_) for q_ in qs]
    L = np.r_[0, np.cumsum([np.max(np.abs(qs[i + 1] - qs[i])) for i in range(len(qs) - 1)])]
    T = max(tmin, L[-1] / vmax * 1.3); N = max(8, int(T / 0.05))
    out, qp = [], qs[0]
    for k in range(1, N + 1):
        sv = smooth(k / N) * L[-1]
        j = min(int(np.searchsorted(L, sv, side="right")) - 1, len(qs) - 2)
        u = 0.0 if L[j + 1] - L[j] < 1e-12 else (sv - L[j]) / (L[j + 1] - L[j])
        qn = qs[j] + (qs[j + 1] - qs[j]) * u
        out.append(Seg("lin", qp, qn, T / N)); qp = qn
    return out, T


def joint_clear(a, qa, qb, probe=None, n=14):
    return min(clear_q(a, qa + (qb - qa) * smooth(u), probe) for u in np.linspace(0, 1, n + 1))


def jdur(qa, qb):
    return max(1.2, float(np.max(np.abs(qb - qa))) / 0.8)


def branch_set(a, key, pre, post_wps, q_ref, k=8, n=10):
    """rami validi per una posa chiave: (q_pre, discesa pre->key, tratti successivi in linea retta)"""
    out, cs = [], ik_candidates(a, key[0], key[1], q_ref, k=k)
    for qk in cs:
        B = Path_(a, qk).to(pre[0], pre[1], 1.0, n)
        if B.err > 0.002:                            # ripiego: posa di avvicinamento risolta vicino a qk, tratto nei giunti quasi rettilineo
            q_pre = None
            for sd_ in [B.q, qk] + [qk + np.random.default_rng(j_).normal(0, 0.25, 7) for j_ in range(8)]:
                qq, ep_, er_ = a.ik.solve1(d.qpos.copy(), np.clip(sd_, a.ik.lo, a.ik.hi), np.asarray(pre[0], float), pre[1], 150)
                if ep_ < 0.0015 and er_ < 0.015 and np.max(np.abs(qq - qk)) < 0.8:
                    dev = max(np.linalg.norm(a.ik.fk(d.qpos, qk + (qq - qk) * u_)[0] - (key[0] + (np.asarray(pre[0]) - key[0]) * u_)) for u_ in np.linspace(0, 1, 11))
                    if dev < 0.004:
                        q_pre = qq; break
            if q_pre is None:
                if DBG: print(f"    [ramo] {a.s} avvicinamento {1000 * B.err:.0f} mm", flush=True)
                continue
            D = Path_(a, q_pre)
            for k_ in range(1, n + 1):
                qn = q_pre + (qk - q_pre) * smooth(k_ / n); D.segs.append(Seg("lin", D.q, qn, 1.0 / n)); D.q = qn
            D.p, D.R = a.ik.fk(d.qpos, D.q)
            F = Path_(a, D.q)
            errs = []
            for w_ in post_wps:
                e0 = F.err; F.err = 0.0; F.run([w_]); errs.append(round(1000 * F.err, 1)); F.err = max(e0, F.err)
            if F.err < 0.002:
                out.append((q_pre, D, F))
            elif DBG:
                print(f"    [ramo] {a.s} (giunti) tratti {errs}", flush=True)
            continue
        D = Path_(a, B.q).to(key[0], key[1], 1.0, n)
        F = Path_(a, D.q)
        errs = []
        for w_ in post_wps:
            e0 = F.err; F.err = 0.0; F.run([w_]); errs.append(round(1000 * F.err, 1)); F.err = max(e0, F.err)
        if max(D.err, F.err) < 0.002:
            out.append((B.q, D, F))
        elif DBG:
            print(f"    [ramo] {a.s} discesa {1000 * D.err:.0f} mm, tratti {errs}", flush=True)
    if DBG: print(f"    [ramo] {a.s}: {len(cs)} soluzioni IK, {len(out)} rami validi", flush=True)
    return out


def both_to(P, tg, dur):
    """stessi tempi e stesso numero di passi per le due braccia (presa bimanuale sincrona)"""
    n = max(P[s].nfor(*tg[s]) for s in P)
    for s in P:
        P[s].to(tg[s][0], tg[s][1], dur, n)


HOME_P = {}
for s_, a_ in arms.items():
    HOME_P[s_] = a_.ik.fk(d.qpos, Q_HOME[s_])


def mark(lbl):
    return ("mark", lbl)


_on_event = on_event


def on_event(a, ev, part):
    if ev == "mark":
        MARKS.append((round(d.time, 2), int(round(d.time * 30)), a.s, part))
        print(f"[t={d.time:6.2f}s f{int(round(d.time * 30)):5d}] {a.s}: {part}", flush=True)
        return
    return _on_event(a, ev, part)


# ---------------------------------------------------------------- abilita'
P_PITCH = math.radians(30)                         # scatole piccole: pinza inclinata di 30 gradi verso l'esterno (portata)
P_TOTE = math.radians(40)                          # cassetta: dita inclinate di 40 gradi in avanti
RACK_SLOT = {"right": (-0.265, -0.14), "left": (-0.265, 0.14)}
Z_RACK_G = RR_Z + 0.10 - 0.03                      # presa 30 mm sotto il bordo superiore


def small_transfer(s, box, src, dst, opts):
    """scatola piccola: presa per attrito con la pinza, trasferimento, deposito. src/dst = (x, y, quota del piano), riferimento base.
    Banco: dita inclinate di 30 gradi in avanti; rastrelliera: 30 gradi all'indietro. Avvicinamento, presa, sollevamento e deposito
    in linea retta; i trasferimenti in aria sono pianificati nei giunti (RRT-Connect) con verifica di distanza di braccio e scatola
    da gusci, vassoio, rastrelliera, banchi e altre scatole (>= 12 mm, convessi MuJoCo)."""
    a = arms[s]
    (xs, ys, zs_pl), (xd, yd, zd_pl) = src, dst
    zg = zs_pl + 0.10 - 0.03                        # presa 30 mm sotto il bordo superiore
    zpl = zd_pl + 0.10 - 0.03 - 0.004               # comando 4 mm sotto il contatto (il braccio carico resta ~1 cm piu' alto)
    Rz180 = Rot.from_euler("z", math.pi).as_matrix()
    for R_s, R_d in opts:                            # opzioni (presa, deposito) con lo stesso beccheggio: scatola orizzontale
        for v_ in (0, 1):                            # pinza simmetrica: stessa presa ruotata di 180 gradi attorno all'asse delle dita
            Rs_v, Rd_v = (R_s, R_d) if v_ == 0 else (R_s @ Rz180, R_d @ Rz180)
            res = _small_transfer(a, s, box, xs, ys, zg, xd, yd, zpl, Rs_v, Rd_v)
            if res:
                return res
    return []


def _small_transfer(a, s, box, xs, ys, zg, xd, yd, zpl, R_s, R_d):
    up = np.array([0, 0, 1.0])
    ax_s, ax_d = R_s @ up, R_d @ up                  # asse della pinza (verso il polso): avvicinamento lungo le dita oppure verticale
    src_set = dst_set = []
    for h_ in (0.12, 0.09, 0.06):
        for dir_ in (up, ax_s):
            src_set = branch_set(a, (W(xs, ys, zg), R_s), (W(xs, ys, zg) + h_ * dir_, R_s), [(W(xs, ys, zg + min(h_, 0.10)), R_s, 0.9, 10)], a.q)
            if src_set:
                break
        if src_set:
            break
    for h_ in (0.12, 0.09, 0.06):
        for dir_ in (up, ax_d):
            dst_set = branch_set(a, (W(xd, yd, zpl), R_d), (W(xd, yd, zpl) + h_ * dir_, R_d), [(W(xd, yd, zpl) + h_ * dir_, R_d, 0.7, 10)], a.q)
            if dst_set:
                break
        if dst_set:
            break
    if not src_set or not dst_set:
        print(f"  [IK] {s} {box}: rami presa {len(src_set)}, deposito {len(dst_set)}", flush=True)
        return []
    bp, bR = d.body(box).xpos.copy(), d.body(box).xmat.reshape(3, 3).copy()
    probe = (R_s.T @ (bp - W(xs, ys, zg)), R_s.T @ bR)
    CARRY[s] = box
    plan = None
    for qs_pre, Ds, Ls in src_set[:4]:
        p1 = rrt_connect(a, a.q, qs_pre)
        if p1 is None:
            continue
        for qd_pre, Dd, Ud in dst_set[:4]:
            p2 = None
            if np.allclose(R_s, R_d, atol=1e-6):        # stessa orientazione (banco -> vassoio): trasporto in linea retta,
                C = Path_(a, Ls.q)                       # la ridondanza porta il braccio verso la configurazione di deposito
                p_up = np.asarray(C.p) + [0, 0, 0.04]
                C.to(p_up, R_s, 0.6, 6).to(a.ik.fk(d.qpos, qd_pre)[0], R_d, 2.0, 40, qd_pre)
                if C.err < 0.002 and np.max(np.abs(C.q - qd_pre)) < 0.05 and \
                        all(clear_q(a, sg_.qb, probe) > 0.02 for sg_ in C.segs[::3] if sg_.qb is not None):
                    C.segs.append(Seg("lin", C.q, qd_pre, 0.2)); p2 = C.segs
            if p2 is None:
                p2 = rrt_connect(a, Ls.q, qd_pre, probe)
            if p2 is None:
                continue
            CARRY.pop(s, None)
            p3 = rrt_connect(a, Ud.q, Q_HOME[s])
            CARRY[s] = box
            if p3 is not None:
                plan = (p1, Ds, Ls, p2, Dd, Ud, p3); break
        if plan:
            break
    CARRY.pop(s, None)
    if plan is None:
        print(f"  [piano] {s} {box}: NESSUN percorso libero trovato", flush=True)
        return []
    p1, Ds, Ls, p2, Dd, Ud, p3 = plan
    CARRY[s] = box
    qs2 = [sg_.qb for sg_ in p2 if sg_.qb is not None][::3] if isinstance(p2[0], Seg) else p2
    c2, wq = min((clear_q(a, q_, probe), i_) for i_, q_ in enumerate(qs2)); clear_q(a, qs2[wq], probe)
    CARRY.pop(s, None)
    print(f"  [piano] {s} {box}: percorsi {len(p1)}/{len(p2)}/{len(p3)} nodi, distanza minima ai nodi con scatola {1000 * c2:.0f} mm "
          f"(nodo {wq}, {CLQ.get('pair')})", flush=True)
    sg1, _ = path_segs(p1, vmax=0.6); sg2 = p2 if isinstance(p2[0], Seg) else path_segs(p2, vmax=0.45)[0]; sg3, _ = path_segs(p3, vmax=0.6)
    P = Path_(a).grip(OPEN[s], 0.3)
    P.segs += sg1; P.wait(0.6)                       # assestamento sopra la scatola prima della discesa
    P.segs += Ds.segs; P.q = Ds.q
    P.grip(0.0, 0.5).wait(0.3, mark(f"{box} presa"))
    P.segs += Ls.segs; P.q = Ls.q
    P.wait(0.1, mark(f"{box} sollevata"))
    P.segs += sg2; P.wait(0.5)
    P.segs += Dd.segs; P.q = Dd.q
    P.wait(0.5, mark(f"{box} sopra il piano")).grip(OPEN[s], 0.4).wait(0.35, mark(f"{box} rilasciata"))
    P.segs += Ud.segs + sg3; P.q = Q_HOME[s]
    return P.segs


def bimanual(box, xy, bottom, mode):
    """presa bimanuale della cassetta: ogni pinza afferra il bordo di una parete laterale (dito interno dentro la cassetta, esterno fuori)
    e stringe con la forza dei motori delle dita; le due braccia sollevano insieme. Tratti con la cassetta in mano in linea retta e
    sincroni, orientazione costante (dita inclinate di 30 gradi in avanti): la cassetta resta orizzontale.
    mode 'pick': avvicinamento, presa, sollevamento di CARRY_DZ (posa di trasporto); 'place': discesa, apertura, ritorno."""
    R = {"right": Rh(math.pi, P_TOTE), "left": Rh(math.pi, P_TOTE)}
    hx, hy, hz, tw = TOTE
    zg = bottom + 2 * hz - 0.018                    # pinza 18 mm sotto il bordo della parete
    x0, y0 = xy[0] - 0.025, xy[1]                    # presa 25 mm verso il robot rispetto al centro della parete
    cand, nref = {}, None
    for s in ("right", "left"):
        a, sg, Rs = arms[s], SG[s], R[s]
        yw = sg * (hy - tw / 2)                      # asse della parete
        if mode == "pick":
            key, pre = (W(x0, y0 + yw, zg), Rs), (W(x0, y0 + yw, zg + 0.12), Rs)
            after = [("grip", PINCH[s], 0.6), ("wait", 0.4, mark(f"{box} stretta")),
                     (W(x0, y0 + yw, zg + 0.03), Rs, 0.9), ("wait", 0.3, mark(f"{box} staccata")),
                     (W(x0, y0 + yw, zg + CARRY_DZ), Rs, 1.0), ("wait", 0.2, mark(f"{box} sollevata"))]
        else:
            key, pre = (W(x0, y0 + yw, zg + 0.006), Rs), (W(x0, y0 + yw, zg + CARRY_DZ), Rs)
            after = [("wait", 0.2, mark(f"{box} sopra il piano")), ("grip", GRIP_PART[s], 0.5), ("wait", 0.2, mark(f"{box} rilasciata")),
                     (W(x0, y0 + yw, zg + 0.20), Rs, 1.0)]
        after = wp_n(after, key[0], key[1])
        if nref is None:
            nref = after
        else:                                        # stessi campioni del destro: movimento sincrono
            after = [(w_[0], w_[1], w_[2], nr_[3]) + tuple(w_[4:]) if not isinstance(w_[0], str) else w_ for w_, nr_ in zip(after, nref)]
        if mode == "place":                          # la discesa parte dalla posa di trasporto attuale, sullo stesso ramo (niente salti)
            F = Path_(a).to(pre[0], pre[1], 0.4, 6).to(key[0], key[1], 1.1, 14).run(after)
            bs = [(a.q.copy(), Path_(a), F)] if F.err < 0.003 else []
            if not bs:
                print(f"  [IK] {s} {box}: deposito dalla posa di trasporto, errore {1000 * F.err:.1f} mm", flush=True)
        else:
            bs = branch_set(a, key, pre, after, a.q, n=14)
        if not bs:
            print(f"  [IK] {s} {box}: nessun ramo per la presa bimanuale ({mode})", flush=True)
            return None
        sc = []
        for b_ in bs[:6]:
            pth = rrt_connect(a, a.q, b_[0]) if mode == "pick" else rrt_connect(a, b_[2].q, Q_HOME[s])
            if pth is not None:
                sc.append((min(clear_q(a, q_) for q_ in pth), b_, pth))
        if not sc:
            print(f"  [piano] {s} {box}: nessun percorso libero ({mode})", flush=True)
            return None
        cand[s] = max(sc, key=lambda x_: x_[0])
        print(f"  [piano] {s} {box} bimanuale {mode}: distanza minima nel movimento in aria {1000 * cand[s][0]:.0f} mm", flush=True)
    segs = {}
    T = max(path_segs(cand[s][2])[1] for s in cand)
    for s in cand:
        q_pre, D, F = cand[s][1]
        sg_, _ = path_segs(cand[s][2], tmin=T)
        if mode == "pick":
            P = Path_(arms[s]).grip(GRIP_PART[s], 0.3)
            P.segs += sg_; P.wait(0.6)
            P.segs += D.segs + F.segs
        else:
            P = Path_(arms[s])
            P.segs += F.segs + sg_
        segs[s] = P.segs
    if len(segs["right"]) != len(segs["left"]) or any(abs(x_.dur - y_.dur) > 1e-9 for x_, y_ in zip(segs["right"], segs["left"])):
        print("  [bimanuale] ATTENZIONE: tempi diversi tra le due braccia", flush=True)
    return segs


CARRY_DZ = 0.12


PLAN_CLEAR = []


def run_arms(segs):
    for s, sg_ in segs.items():
        arms[s].start(sg_)
    while any(a.busy for a in arms.values()):
        yield


def wait_t(T):
    t0 = d.time
    while d.time - t0 < T:
        yield


def placed(box, tgt_local, kind):
    """errore di posizionamento (centro scatola vs bersaglio, imbardata) dopo l'assestamento"""
    bl = box_local(box)
    e = 1000 * np.linalg.norm(bl[:2] - np.asarray(tgt_local[:2]))
    dyaw = abs(math.degrees(wrap(bl[3] - 0.0))) % 90.0
    dyaw = min(dyaw, 90.0 - dyaw)                    # scatola simmetrica; sulla rastrelliera e' ruotata di 90 gradi
    up = d.body(box).xmat.reshape(3, 3)[2, 2]
    RES[f"{box}@{kind}"] = dict(err_mm=round(e, 1), yaw_deg=round(dyaw, 2), tilt_deg=round(math.degrees(math.acos(min(1.0, up))), 2),
                                z=round(float(bl[2]), 4), t=round(d.time, 2))
    log(f"{box} -> {kind}: {e:.1f} mm dal bersaglio, imbardata {dyaw:.1f} gradi, inclinazione {math.degrees(math.acos(min(1.0, up))):.1f}")
    if e < 15:
        expr["happy_t"] = d.time


def hand_slip_monitor():
    pass


FRONT_SLOT = {"right": (0.205, -0.145), "left": (0.205, 0.145)}
RACK_SLOT = {"right": (-0.265, -0.11), "left": (-0.265, 0.11)}      # scatole ruotate di 90 gradi: lato lungo trasversale
OPT_FRONT = lambda: [(Rh(math.pi, P_PITCH), Rh(math.pi, P_PITCH))]                  # banco -> vassoio: dita 30 gradi in avanti
OPT_REAR = lambda s: [(Rh(0.0, -P_PITCH), Rh(-SG[s] * math.pi / 2, -P_PITCH))]     # banco -> rastrelliera: la mano ruota di 90 gradi
OPT_REAR_BACK = lambda s: [(Rh(-SG[s] * math.pi / 2, -P_PITCH), Rh(0.0, -P_PITCH))]
DEST = {"box_s_r": (0.42, -0.31), "box_s_l": (0.42, 0.31), "box_big": (0.475, 0.0)}


def script():
    T0 = d.time
    yield from wait_t(1.0)
    # 1) braccio destro: scatola piccola -> rastrelliera posteriore; braccio sinistro: scatola piccola -> vassoio frontale
    log("scatole piccole: destra -> rastrelliera posteriore, sinistra -> vassoio frontale")
    ALLOW.clear(); ALLOW.update({("right", "box_s_r"), ("left", "box_s_l")})
    STATS["t_phase1"] = d.time
    bl_r = box_local("box_s_r")                      # una alla volta: i percorsi di un braccio sono pianificati con l'altro fermo
    yield from run_arms({"right": small_transfer("right", "box_s_r", (bl_r[0], bl_r[1], BENCH_Z), (*RACK_SLOT["right"], RR_Z), OPT_REAR("right"))})
    STATS["t_rear_loaded"] = d.time
    bl_l = box_local("box_s_l")
    yield from run_arms({"left": small_transfer("left", "box_s_l", (bl_l[0], bl_l[1], BENCH_Z), (*FRONT_SLOT["left"], BT_Z), OPT_FRONT())})
    yield from wait_t(0.5)
    placed("box_s_r", RACK_SLOT["right"], "rastrelliera")
    placed("box_s_l", FRONT_SLOT["left"], "vassoio")
    # 2) scatola grande: presa bimanuale, sollevata in posa di trasporto
    log("scatola grande: presa bimanuale")
    ALLOW.clear(); ALLOW.update({("right", "box_big"), ("left", "box_big")})
    STATS["t_phase2"] = d.time
    bl = box_local("box_big")
    sg2 = bimanual("box_big", bl[:2], BENCH_Z, "pick")
    if sg2:
        yield from run_arms(sg2)
    STATS["t_loaded"] = d.time
    # 3) marcia A2 -> B2 con la scatola grande in braccio
    log("a bordo: scatola grande in braccio, 1 piccola sul vassoio, 1 sulla rastrelliera -> banco B2")
    x, y, th = base_pose()
    back = np.array([x, y]) - 0.6 * np.array([math.cos(th), math.sin(th)])
    p1 = DOCK["B2"][:2] - np.array([0.6, 0.0])
    mission["route"] = [Leg(np.linspace([x, y], back, 30), -1), Turn(math.pi / 2),
                        Leg(np.vstack([hermite(back, math.pi / 2, p1, 0.0, k=1.0), np.linspace(p1, DOCK["B2"][:2], 30)[1:]]), +1),
                        Turn(0.0)]
    FIELDS["mode"] = "marcia"; set_state("drive_scatole")
    STATS["t_drive0"] = d.time; path = 0.0; pp = base_pose()[:2].copy(); vmax = 0.0
    BL0 = {b: box_local(b) for b in BOX_NAMES}
    while not drive_step(state["k"]):
        path += np.linalg.norm(base_pose()[:2] - pp); pp = base_pose()[:2].copy(); vmax = max(vmax, abs(drive["v"]))
        yield
    set_state("demo"); teach_contour()
    yield from wait_t(0.6)
    STATS["t_drive1"] = d.time; STATS["drive_m"] = round(float(path), 2); STATS["drive_vmax"] = round(vmax, 2)
    x, y, th = base_pose()
    STATS["dock_err_mm"] = round(1000 * float(np.hypot(x - DOCK["B2"][0], y - DOCK["B2"][1])), 1)
    STATS["dock_err_deg"] = round(math.degrees(wrap(th - DOCK["B2"][2])), 2)
    STATS["shift_in_drive_mm"] = {b: round(1000 * float(np.linalg.norm(box_local(b)[:3] - BL0[b][:3])), 1) for b in BOX_NAMES}
    log(f"agganciato a B2: {STATS['dock_err_mm']} mm, {STATS['dock_err_deg']} gradi; spostamento scatole in marcia {STATS['shift_in_drive_mm']} mm")
    # 4) scarico: scatola grande (bimanuale) -> banco B2, poi le piccole (vassoio e rastrelliera) -> banco B2
    STATS["t_phase4"] = d.time
    tl = box_local("box_big"); DEST["box_big"] = (float(tl[0]), float(tl[1]))      # si posa sotto le mani: il banco B2 e' davanti
    sg4 = bimanual("box_big", DEST["box_big"], BENCH_Z, "place")
    if sg4:
        yield from run_arms(sg4)
    yield from wait_t(0.5)
    placed("box_big", DEST["box_big"], "banco B2")
    ALLOW.clear(); ALLOW.update({("right", "box_s_r"), ("left", "box_s_l")})
    STATS["t_phase5"] = d.time
    bl_l = box_local("box_s_l")
    yield from run_arms({"left": small_transfer("left", "box_s_l", (bl_l[0], bl_l[1], BT_Z), (*DEST["box_s_l"], BENCH_Z), OPT_FRONT())})
    bl_r = box_local("box_s_r")
    yield from run_arms({"right": small_transfer("right", "box_s_r", (bl_r[0], bl_r[1], RR_Z), (*DEST["box_s_r"], BENCH_Z), OPT_REAR_BACK("right"))})
    yield from wait_t(0.5)
    for b in ("box_s_r", "box_s_l"):
        placed(b, DEST[b], "banco B2")
    STATS["t_end"] = d.time; STATS["cycle_s"] = round(d.time - T0, 1)
    log(f"ciclo completo in {d.time - T0:.1f} s")
    DEMO["end"] = d.time + 1.5
    while True:
        yield


STATS = {}
DEMO = {"gen": None}

# ---------------------------------------------------------------- verifiche durante la simulazione
ARM_BODIES = {s: {i for i in range(m.nbody) if m.body(i).name.startswith(f"openarm_{s}_")} for s in ("right", "left")}
HAND_BODIES = {s: {i for i in ARM_BODIES[s] if "_ee_" in m.body(i).name} for s in ARM_BODIES}
ARM_COLL = {s: [g for g in range(m.ngeom) if m.geom_bodyid[g] in ARM_BODIES[s] and m.geom_contype[g] + m.geom_conaffinity[g] > 0] for s in ARM_BODIES}
BOX_BODY = {m.body(b).id: b for b in BOX_NAMES}
AMR_ID = m.body("amr").id
FURN = [g for g in range(m.ngeom) if m.geom_bodyid[g] == 0 and m.geom(g).name.startswith(("A2_", "B2_"))]
ROBOT_FIX = [g for g in range(m.ngeom) if m.geom_bodyid[g] == AMR_ID and m.geom(g).name.startswith(("btray_", "rrack_")) and m.geom_contype[g] + m.geom_conaffinity[g] > 0]
CHK = {"contacts": {}, "clear": {}, "slip": {}, "tau": {}}
TAU_LIM = {s: np.array([40, 40, 27, 27, 7, 7, 7.0]) for s in ("right", "left")}


def _note_contact(kind, dist):
    k_ = kind
    c_ = CHK["contacts"].setdefault(k_, {"n": 0, "min_mm": 0.0, "t0": round(d.time, 2)})
    c_["n"] += 1; c_["min_mm"] = min(c_["min_mm"], round(1000 * dist, 2))


def monitor():
    step = int(round(d.time / DT))
    if step % 5 == 0:
        for c_ in d.contact[:d.ncon]:
            if c_.dist > 0.0005:
                continue
            b1, b2 = m.geom_bodyid[c_.geom1], m.geom_bodyid[c_.geom2]
            sides = {s for s in ARM_BODIES for b in (b1, b2) if b in ARM_BODIES[s]}
            if len(sides) == 2:
                _note_contact("braccio-braccio", c_.dist); continue
            if sides:
                s = sides.pop(); other = b2 if b1 in ARM_BODIES[s] else b1; me = b1 if other == b2 else b2
                if other in BOX_BODY:
                    if (s, BOX_BODY[other]) in ALLOW and me in HAND_BODIES[s]:
                        continue
                    _note_contact(f"braccio {s} ({m.body(me).name[8:]})-scatola {BOX_BODY[other]} NON voluto", c_.dist)
                elif other == AMR_ID:
                    _note_contact(f"braccio {s}-robot ({m.geom(c_.geom1 if b1 == AMR_ID else c_.geom2).name})", c_.dist)
                elif other == 0:
                    _note_contact(f"braccio {s}-arredo ({m.geom(c_.geom1 if b1 == 0 else c_.geom2).name})", c_.dist)
                continue
            if b1 in BOX_BODY and b2 in BOX_BODY:
                _note_contact("scatola-scatola", c_.dist)
            for bx, ot, g_ot in ((b1, b2, c_.geom2), (b2, b1, c_.geom1)):
                if bx in BOX_BODY and ot == AMR_ID and not m.geom(g_ot).name.endswith(("_mat",)):
                    _note_contact(f"scatola-robot ({m.geom(g_ot).name})", c_.dist)
    if step % 25 == 0:                                   # distanze minime bracci <-> arredo / vassoio / rastrelliera / scatole non prese
        ft = np.zeros(6)
        for s in ARM_COLL:
            for g in ARM_COLL[s]:
                pg = d.geom_xpos[g]
                for grp, targets in (("arredo (banchi)", FURN), ("vassoio+rastrelliera", ROBOT_FIX),
                                     ("scatole non prese", [g_ for b in BOX_NAMES if (s, b) not in ALLOW for g_ in BOX_GEOMS[b]])):
                    for t_ in targets:
                        if np.linalg.norm(d.geom_xpos[t_] - pg) > 0.45:
                            continue
                        dist = gdist(d, g, t_, 0.10)
                        k_ = (s, grp)
                        if dist < CHK["clear"].get(k_, (9.0,))[0]:
                            CHK["clear"][k_] = (dist, m.geom(g).name, m.geom(t_).name, round(d.time, 2))
        for s, a in arms.items():                         # coppie ai giunti (limiti dei motori Damiao) mentre i bracci lavorano
            tau = np.abs(d.actuator_force[ARM_ACT[s]] + d.qfrc_applied[a.ik.dadr])   # motore: posizione + compensazioni (gravita', carico)
            r_ = tau / TAU_LIM[s]
            CHK["tau"][s] = np.maximum(CHK["tau"].get(s, np.zeros(7)), r_)


HOLD = {}                                            # carico in mano (massa per braccio): compensazione in avanti come su un controllore reale


def _hold_from_marks(a, part):
    for key_, m_ in (("presa", None), ("stretta", None)):
        pass


_on_event2 = on_event


def on_event(a, ev, part):
    if ev == "mark":
        b_ = part.split(" ")[0]
        if part.endswith((" presa", " stretta")):
            HOLD[a.s] = float(m.body_subtreemass[m.body(b_).id]) / (2.0 if b_ == "box_big" else 1.0)
        elif part.endswith(" sopra il piano"):
            HOLD.pop(a.s, None)
    return _on_event2(a, ev, part)


_bts = base_target_step
_Jp = np.zeros((3, m.nv))


def base_target_step():
    for s_, mass_ in HOLD.items():                   # J^T m g al sito di presa, entro i limiti dei motori (sommata al resto sotto)
        mujoco.mj_jacSite(m, d, _Jp, None, m.site(f"{s_}_grasp").id)
        dofs = arms[s_].ik.dadr
        d.qfrc_applied[dofs] += _Jp[:, dofs].T @ np.array([0, 0, mass_ * 9.81])
    _bts()


_control_step = control_step


def control_step():
    if DEMO["gen"] is None:
        DEMO["gen"] = script()
    next(DEMO["gen"])
    _control_step()
    monitor()


def finished():
    return d.time > DEMO.get("end", 1e9) or d.time > args.seconds


def report():
    print("==== RISULTATI scatole v14 ====", flush=True)
    print("STATS", {k: v for k, v in STATS.items()}, flush=True)
    for k, v in RES.items():
        print("POSA", k, v, flush=True)
    for k, v in sorted(CHK["contacts"].items()):
        print("CONTATTO", k, v, flush=True)
    for (s, grp), (dist, g, t_, tt) in sorted(CHK["clear"].items()):
        print(f"DISTANZA MIN {s:5s} vs {grp:22s}: {1000 * dist:6.1f} mm ({g} - {t_}, t={tt})", flush=True)
    for s, r_ in CHK["tau"].items():
        print(f"COPPIA MAX/limite {s}: " + " ".join(f"j{i + 1} {100 * v:.0f}%" for i, v in enumerate(r_)), flush=True)
    print("MARKS", MARKS, flush=True)


post = _sub(post, "def finished():", "def _finished_v5():")
post = _sub(post, "    ANIM = [m.geom(n).id for n in ANIM_N]",
            "    ANIM_N = [n for n in ANIM_N if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) >= 0]\n    ANIM = [m.geom(n).id for n in ANIM_N]")
post = _sub(post, "stats=stats), open(args.record, \"wb\"))", "stats=stats, v14=dict(STATS=STATS, RES=RES, MARKS=MARKS)), open(args.record, \"wb\"))")
CAM_FIXED = ([2.9, -1.3, 1.0], 2.2, 160, -25)
if HEADLESS:
    while not finished():
        control_step()
else:
    exec(compile(post, "giorgio_v5_out", "exec"))
report()
