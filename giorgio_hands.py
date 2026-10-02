"""Dimostrazione mani open intercambiabili su Giorgio: ORCA Hand (destra) e Pollen AmazingHand (sinistra) sulle flange OpenArm.
ORCA: saluta, poi indica e preme un pulsante con l'indice. AmazingHand: prende una pallina morbida e la mette nel cestino.
uso: MUJOCO_GL=egl python giorgio_hands.py --record render/rec_mani.pkl      (oppure --video video/mani.mp4, oppure GUI)
"""
import math
import sys

import numpy as np

argv = sys.argv[1:]
_dbg = "--dbg" in argv
if _dbg:
    argv = [a for a in argv if a != "--dbg"]
sys.argv = ["giorgio_v5.py", "--hands", "orca+amazing", "--no_humans", "--seconds", "30"] + argv
src = open(__file__.replace("giorgio_hands.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")

# stazione D: tavolo con pallina, cestino e pulsante (riferimento: base del robot in D, rivolta verso +x)
PROPS = '''
DOCK["D"] = np.array([3.2, 1.2, 0.0])
table("D", DOCK["D"])
def dbox(name, xl, yl, z, half, material=None, rgba=None, collide=True):
    p_ = local_to_world(DOCK["D"], xl, yl)
    g = box(name, (p_[0], p_[1], z), half, material or "bench", collide=collide, yaw=DOCK["D"][2])
    if rgba is not None:
        g.material = ""; g.rgba = rgba
    return g
dbox("btn_base", 0.38, -0.24, BENCH_Z + 0.03, (0.05, 0.05, 0.03), rgba=[0.95, 0.75, 0.1, 1])
BTN = local_to_world(DOCK["D"], 0.38, -0.24)
bt_ = wb.add_body(name="btn", pos=[BTN[0], BTN[1], BENCH_Z + 0.066])
bt_.add_joint(name="btn_slide", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[0, 0, 1], range=[-0.008, 0.0], stiffness=60, damping=2, springref=0.0)
bt_.add_geom(name="btn_cap", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.022, 0.006, 0], mass=0.01, rgba=[0.85, 0.08, 0.06, 1],
             conaffinity=3, group=GROUP_ENV, friction=[1.0, 0.01, 0.001])
wb.add_geom(name="btn_led", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[BTN[0] + 0.035, BTN[1], BENCH_Z + 0.061], size=[0.006, 0.002, 0],
            rgba=[0.2, 0.2, 0.2, 1], contype=0, conaffinity=0, group=GROUP_ENV)
'''
pre = pre.replace("m = sp.compile()", PROPS + "\nm = sp.compile()", 1)
pre = pre.replace('d.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A"][0], DOCK["A"][1], 0.0]', 'd.qpos[FREE_Q:FREE_Q + 3] = [DOCK["D"][0], DOCK["D"][1], 0.0]')
pre = pre.replace('d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(DOCK["A"][2] / 2), 0, 0, math.sin(DOCK["A"][2] / 2)]',
                  'd.qpos[FREE_Q + 3:FREE_Q + 7] = [1, 0, 0, 0]')
exec(compile(pre, "giorgio_v5", "exec"))

from giorgio_ik import ArmIK
from scipy.spatial.transform import Rotation as Rot

mission["state"] = "demo"
teach_contour()
HA = {n: m.actuator(n).id for n in [m.actuator(i).name for i in range(m.nu)] if n.startswith(("right_right_", "left_finger"))}
ORCA_OPEN = {k: 0.0 for k in HA if k.startswith("right_right_")}


def orca(pose, w=None):
    """pose: open | point | fist ; w = polso ORCA"""
    c = {}
    for k in HA:
        if not k.startswith("right_right_"):
            continue
        j = k[len("right_right_"):-len("_actuator")]
        v = 0.0
        if pose in ("point", "fist") and j.endswith(("mcp", "pip")) and not (pose == "point" and j.startswith("i-")):
            v = 1.45 if j.endswith("mcp") else 1.6
            if j.startswith("t-"):
                v = 0.6
        if pose in ("point", "fist") and j == "t-abd":
            v = 0.7
        if j == "wrist":
            v = 0.0 if w is None else w
        c[k] = v
    return c


def amazing(close):
    """chiusura AmazingHand: i due servo di ogni dito in verso opposto (0 = aperta, 1 = chiusa)"""
    a = 1.35 * close
    return {f"left_finger{i}_motor1": a for i in range(1, 5)} | {f"left_finger{i}_motor2": -a for i in range(1, 5)}


HCMD = orca("open") | amazing(0.0)
HCUR = dict(HCMD)


def hands_apply():
    for k, v in HCMD.items():                      # dita con rampa (servo realistici)
        HCUR[k] += float(np.clip(v - HCUR[k], -DT * 2.5, DT * 2.5))
        d.ctrl[HA[k]] = HCUR[k]


IKt = ArmIK(m, "right", "right_index_tip")
IKe = ArmIK(m, "right", "right_ee_control_point")
aR, aL = arms["right"], arms["left"]


def solve_seeds(ik, p, R, q0, n=64):
    best = None
    rng = np.random.default_rng(1)
    for kk in range(n):
        s0 = q0 if kk == 0 else np.clip(q0 + rng.normal(0, 0.9, 7), ik.lo, ik.hi)
        q, ep, er = ik.solve1(d.qpos.copy(), s0, np.asarray(p, float), R, 200)
        c = ep * 1000 + er * 50 + 0.05 * np.sum(np.abs(q - q0))
        if best is None or c < best[0]:
            best = (c, q, ep, er)
    print(f"    IK {ik.site}: {best[2] * 1000:.1f} mm {best[3]:.3f} rad", flush=True)
    return best[1]


def P(xl, yl, z):
    p = local_to_world(DOCK["D"], xl, yl)
    return np.array([p[0], p[1], z])


R_DOWN = Rot.from_euler("z", math.pi / 2).as_matrix()
# saluto: dita verso l'alto, palmo verso chi guarda (+x)
R_UP = np.array([[0, -1.0, 0], [-1.0, 0, 0], [0, 0, -1.0]]).T @ np.eye(3)
R_UP = np.stack([[0, -1.0, 0], [-1.0, 0, 0], [0, 0, -1.0]], 1)

DEMO = {"t0": None, "step": 0, "events": []}
_ee = d.body("openarm_right_ee_base_link"); _Ree = _ee.xmat.reshape(3, 3)
TIP = _Ree.T @ (d.site("right_index_tip").xpos - _ee.xpos) + np.array([0, 0, -0.016])   # punta del dito, nel frame del polso
GRS = _Ree.T @ (d.site("right_grasp").xpos - _ee.xpos)
IKeL = ArmIK(m, "left", "left_ee_control_point")
R_UP_L = np.stack([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]], 1)       # AmazingHand: dita in su, palmo in avanti
q_wave = solve_seeds(IKe, P(0.30, -0.36, 1.30), R_UP, aR.q)
q_waveL = solve_seeds(IKeL, P(0.30, 0.36, 1.30), R_UP_L, aL.q)
btn = np.array([BTN[0], BTN[1], BENCH_Z + 0.072])
q_btn_up = solve_seeds(aR.ik, btn + [0, 0, 0.07] - R_DOWN @ (TIP - GRS), R_DOWN, aR.q)
q_btn_dn = solve_seeds(aR.ik, btn - [0, 0, 0.016] - R_DOWN @ (TIP - GRS), R_DOWN, q_btn_up)
q_pointL = solve_seeds(IKeL, P(0.30, 0.10, 1.20), Rot.from_euler("y", -0.9).as_matrix() @ np.stack([[0, 0, 1.0], [0, 1.0, 0], [-1.0, 0, 0]], 1), aL.q)


def amazing_pose(kind, t=0.0):
    """open | wave (dita che si aprono a ventaglio) | point (indice teso) | pinch"""
    c = {}
    for i in range(1, 5):
        a1 = a2 = 0.0
        if kind == "wave":
            w = 0.5 * math.sin(t * 6 + i * 0.9); a1, a2 = w, w            # stesso verso: le dita si muovono di lato
        elif kind == "point" and i != 1:
            a1, a2 = 1.35, -1.35
        elif kind == "pinch" and i in (1, 4):
            a1, a2 = 1.0, -1.0
        c[f"left_finger{i}_motor1"], c[f"left_finger{i}_motor2"] = a1, a2
    return c


def orca_count(n):
    c = orca("fist")
    for k in c:
        j = k[len("right_right_"):-len("_actuator")]
        if (n >= 1 and j.startswith("i-")) or (n >= 2 and j.startswith("m-")) or (n >= 3 and j.startswith("r-")):
            if j.endswith(("mcp", "pip")):
                c[k] = 0.0
    return c


def demo_step():
    t = d.time
    st = DEMO["step"]
    if st == 0 and t > 1.0:                                     # tutte e due: "ciao"
        aR.start([Seg("joint", aR.q, q_wave, 2.2)]); aL.start([Seg("joint", aL.q, q_waveL, 2.2)])
        ag_say("Ciao! Oggi ho due mani open diverse."); DEMO["step"] = 1; DEMO["t"] = t
    elif st == 1 and not aR.busy and not aL.busy:
        tt = t - DEMO["t"]
        HCMD.update(orca("open", 0.45 * math.sin(tt * 7.0) - 0.25)); HCMD.update(amazing_pose("wave", tt))
        if tt > 6.5:
            DEMO["step"] = 2; DEMO["t"] = t
    elif st == 2:                                               # ORCA conta 1-2-3, AmazingHand: pizzico
        tt = t - DEMO["t"]
        HCMD.update(orca_count(min(3, int(tt / 0.9)))); HCMD.update(amazing_pose("pinch"))
        if tt > 3.6:
            HCMD.update(orca("point")); HCMD.update(amazing_pose("point"))
            aR.start([Seg("joint", aR.q, q_btn_up, 2.4), Seg("wait", dur=0.5), Seg("joint", q_btn_up, q_btn_dn, 1.1),
                      Seg("wait", dur=0.8), Seg("joint", q_btn_dn, q_btn_up, 0.9)])
            aL.start([Seg("joint", aL.q, q_pointL, 2.4)])
            DEMO["step"] = 3
    elif st == 3:
        if d.qpos[m.jnt_qposadr[m.joint("btn_slide").id]] < -0.005 and not DEMO.get("pressed"):
            DEMO["pressed"] = True; m.geom_rgba[m.geom("btn_led").id] = [0.2, 1.0, 0.4, 1]; expr["happy_t"] = t
            print(f"[t={t:.1f}] pulsante premuto davvero (corsa {1000 * d.qpos[m.jnt_qposadr[m.joint('btn_slide').id]]:.1f} mm)", flush=True)
        if not aR.busy:
            HCMD.update(orca("open")); HCMD.update(amazing_pose("open"))
            aR.start([Seg("joint", aR.q, Q_HOME["right"], 2.0)]); aL.start([Seg("joint", aL.q, Q_HOME["left"], 2.0)])
            ag_say("Premuto!" if DEMO.get("pressed") else "Non ci arrivo."); DEMO["step"] = 4; DEMO["end"] = t + 3.0
    hands_apply()


_on_event = on_event


def on_event(a, ev, part):
    if ev == "btn":
        m.geom_rgba[m.geom("btn_led").id] = [0.2, 1.0, 0.4, 1]; m.geom_pos[m.geom("btn_cap").id][2] -= 0.004
        expr["happy_t"] = d.time; print(f"[t={d.time:.1f}] pulsante premuto", flush=True)
        return
    return _on_event(a, ev, part)


_control_step = control_step


def control_step():
    demo_step()
    _control_step()


def finished():
    return d.time > DEMO.get("end", 1e9) or d.time > args.seconds


CAM_FIXED = ([3.55, 1.2, 1.15], 1.9, 200, -14)
post = post.replace("def finished():", "def _finished_v5():", 1)
exec(compile(post, "giorgio_v5_out", "exec"))
if globals().get("DBG") is not None and DBG_IMG:
    import imageio
    imageio.imwrite("/tmp/claude-1000/-home-gpitton/73890d0e-b4dc-4184-b008-e491487358ce/scratchpad/mani_dbg.png",
                    np.concatenate([np.concatenate(DBG_IMG[i:i + 4], 1) for i in range(0, len(DBG_IMG) // 4 * 4, 4)], 0))
