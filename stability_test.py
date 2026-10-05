"""Stabilita' al ribaltamento di Giorgio-P (multibody completo, base libera su 4 appoggi).

Metodo: nel riferimento della base, una frenata/accelerazione 'a' equivale a inclinare la gravita':
g_eff = (-a_x, -a_y, -9.81). Aumento 'a' a passi e guardo quando una coppia di appoggi perde contatto
(forza normale ~0) = inizio ribaltamento. Le braccia tengono la posa con i loro motori (limiti di coppia reali).
Stesso test = pendenza massima (a = g * tan(theta)).
"""
import math

import mujoco
import numpy as np

from giorgio_model import BASE as AMR_BASE, FOOT_X, FOOT_Y, SUPPORT_X, SUPPORT_Y, build
from giorgio_ik import ArmIK

G = 9.81
import sys as _s
BASE = _s.argv[1] if len(_s.argv) > 1 else "cart"       # cart | amr (la base scelta in giorgio_model.BASE)
QUICK = "quick" in _s.argv[2:]                           # solo il caso di lavoro
if BASE == "amr" and AMR_BASE != "amr_revB":
    raise SystemExit("stability_test: base 'amr' supportata solo con giorgio_model.BASE = 'amr_revB' (il Ranger segue un bersaglio cinematico)")
sp = build("gb", hands="gripper", fixed_base=False, base=BASE, **({"support": True} if BASE == "amr" else {}))
sp.worldbody.add_site(name="dummy", pos=[0, 0, 0])
m = sp.compile()
# niente gravcomp "magica" (con base libera sarebbe una forza esterna): la compensazione la fanno i motori,
# come sul robot vero: coppia di gravita' calcolata (qfrc_bias) e limitata alla coppia massima del giunto
m.body_gravcomp[:] = 0
ARM_DOFS = [m.jnt_dofadr[j] for j in range(m.njnt) if m.jnt_type[j] in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE)]
TAU_MAX = np.array([m.jnt_actfrcrange[m.dof_jntid[k]][1] if m.jnt_actfrclimited[m.dof_jntid[k]] else 2000.0 for k in ARM_DOFS])


def step(d):
    d.qfrc_applied[ARM_DOFS] = np.clip(d.qfrc_bias[ARM_DOFS], -TAU_MAX, TAU_MAX)
    mujoco.mj_step(m, d)


WHEELS = [i for i in range(m.ngeom) if (m.geom(i).name or "").startswith("wheel_")]   # appoggi a terra (rev B: 4 piroette + 2 ruote)
ACT = {s: [m.actuator(f"{s}_joint{k}_ctrl").id for k in range(1, 8)] for s in ("right", "left")}


def pose(d, lift, reach, payload):
    """reach: 'pronto' (mani sopra il banco) | 'distese' (braccia orizzontali in avanti, massimo braccio di leva)"""
    mujoco.mj_resetData(m, d)
    d.qpos[m.jnt_qposadr[m.joint("lift").id]] = lift
    d.ctrl[m.actuator("lift_ctrl").id] = lift
    mujoco.mj_forward(m, d)
    for s, sg in (("right", -1), ("left", 1)):
        ik = ArmIK(m, s, f"{s}_grasp")
        z_sh = d.body(f"openarm_{s}_link1").xpos[2]
        if reach == "pronto":
            tgt = np.array([0.30, sg * 0.20, z_sh - 0.25])
        else:
            tgt = np.array([0.60, sg * 0.16, z_sh - 0.05])
        Rd = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
        q, ok, ep, er = ik.solve(d.qpos.copy(), np.array([0.5 * -sg, 0.3 * -sg, 0, 1.0, 0, 0, 0]), tgt, Rd, seeds=24)
        d.qpos[ik.qadr] = q
        d.ctrl[ACT[s]] = q
    for s in ("right", "left"):                         # carico appeso alla pinza (oltre alla massa della pinza)
        m.body_mass[m.body(f"openarm_{s}_ee_base_link").id] = BASE_EE[s] + payload
    mujoco.mj_forward(m, d)
    return {s: d.site(f"{s}_grasp").xpos.copy() for s in ("right", "left")}


BASE_EE = {s: float(m.body_mass[m.body(f"openarm_{s}_ee_base_link").id]) for s in ("right", "left")}


def wheel_loads(d):
    f = np.zeros(len(WHEELS))
    for i in range(d.ncon):
        c = d.contact[i]
        for k, w in enumerate(WHEELS):
            if w in (c.geom1, c.geom2):
                ff = np.zeros(6); mujoco.mj_contactForce(m, d, i, ff); f[k] += ff[0]
    return f


def tip_accel(lift, reach, payload, direction):
    """massima decelerazione/accelerazione orizzontale [m/s^2] prima del sollevamento di una coppia di appoggi"""
    d = mujoco.MjData(m)
    ux, uy = direction
    last_ok = 0.0
    for a in np.arange(0.0, 9.01, 0.25):
        pose(d, lift, reach, payload)
        m.opt.gravity[:] = [-a * ux, -a * uy, -G]
        for _ in range(int(1.0 / m.opt.timestep)):
            step(d)
        f = wheel_loads(d)
        tilt = math.degrees(math.acos(min(1.0, d.body("amr").xmat[8])))
        if f.min() < 1.0 or tilt > 1.0:
            m.opt.gravity[:] = [0, 0, -G]
            return last_ok, a, f
        last_ok = a
    m.opt.gravity[:] = [0, 0, -G]
    return last_ok, None, f


def com_info(lift, reach, payload):
    d = mujoco.MjData(m)
    hands = pose(d, lift, reach, payload)
    r = m.body("amr").id
    return float(m.body_mass[r:].sum()), d.subtree_com[r].copy(), hands


if __name__ == "__main__":
    sx, sy = (FOOT_X, FOOT_Y) if BASE == "cart" else (SUPPORT_X, SUPPORT_Y)
    print(f"base {BASE}: poligono di appoggio x +-{sx:.3f} m, y +-{sy:.3f} m")
    cases = [("lavoro: colonna giu', mani sul banco, 0.35 kg", 0.0, "pronto", 0.35),
             ("peggiore: colonna +0.40 m, braccia distese, 4.1 kg per braccio", 0.40, "distese", 4.1)][:1 if QUICK else 2]
    for name, lift, reach, pay in cases:
        M, com, hands = com_info(lift, reach, pay)
        a_fw = G * (sx - com[0]) / com[2]
        a_bw = G * (sx + com[0]) / com[2]
        a_lat = G * (sy - abs(com[1])) / com[2]
        print(f"\n== {name}")
        print(f"   massa {M:.1f} kg, baricentro {np.round(com, 3)}; mani a x = {hands['right'][0]:.2f} m, z = {hands['right'][2]:.2f} m")
        print(f"   statico (rigido): avanti {a_fw:.1f} m/s^2, indietro {a_bw:.1f}, laterale {a_lat:.1f}  ->  pendenza max laterale {math.degrees(math.atan(a_lat / G)):.0f} gradi")
        for lbl, dirv in (("frenata andando avanti (spinta in avanti)", (-1, 0)), ("frenata in retro", (1, 0)), ("laterale (curva/urto)", (0, 1))):
            ok, tip, f = tip_accel(lift, reach, pay, dirv)
            print(f"   dinamico {lbl}: stabile fino a {ok:.2f} m/s^2" + (f", ribalta da {tip:.2f}" if tip else " (oltre 9 m/s^2)"))
    # spinta laterale di una persona: forza equivalente a quota spalle
    M, com, _ = com_info(0.0, "pronto", 0.35)
    h_push = 1.25
    F_tip = M * G * sy / h_push
    print(f"\nspinta orizzontale a {h_push:.2f} m per ribaltare (statico): {F_tip:.0f} N (~{F_tip / G:.0f} kgf)")
    print(f"frenata di emergenza Tracer 2.0 (2 m/s in 0.9 m): {2.0 ** 2 / (2 * 0.9):.1f} m/s^2")
