"""Registrazione di una posa "prodotto" per i render (robot al centro dello studio, braccio destro con il caffe', sinistro rilassato).
uso: MUJOCO_GL=egl python pose_record.py render/rec_pose.pkl
"""
import math
import sys

import numpy as np

out = sys.argv[1] if len(sys.argv) > 1 else "render/rec_pose.pkl"
MODE = sys.argv[2] if len(sys.argv) > 2 else "lavoro"
EXPR = MODE == "espressioni"                     # sequenza di espressioni per il primo piano dei baffi
HANDS = sys.argv[3] if len(sys.argv) > 3 else "gripper"   # configurazione delle mani: gripper | orca | amazing
sys.argv = ["giorgio_v5.py", "--record", out, "--seconds", "13.0" if MODE == "espressioni" else "3.0", "--no_humans", "--hands", HANDS]
src = open(__file__.replace("pose_record.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")
exec(compile(pre, "giorgio_v5", "exec"))

# robot al centro dello studio (luci puntate su 0.2, 0, 1.0), rivolto verso +x
d.qpos[FREE_Q:FREE_Q + 3] = [0.0, 0.0, 0.0]
d.qpos[FREE_Q + 3:FREE_Q + 7] = [1, 0, 0, 0]
d.qvel[:] = 0
for p_ in PARTS:                                      # flaconi fuori scena
    set_part_xyz(p_, storage(p_))
mujoco.mj_forward(m, d)
mission["state"] = "posa"
teach_contour()
targets = {"right": (0.34, -0.24, 1.12), "left": (0.16, 0.34, 1.02)}
import itertools
for s_, (xl, yl, z) in targets.items():
    a = arms[s_]; best = None
    for sg_ in itertools.product((1, -1), repeat=7):
        sd = np.clip(np.array([-0.59, 2.38, 0.36, 1.63, 0.79, 0.3, 1.19]) * np.array(sg_), a.ik.lo, a.ik.hi)
        q, ep, er = a.ik.solve1(d.qpos.copy(), sd, a.robot_pt(xl, yl, z), a.R(), 200)
        if ep > 0.004 or er > 0.03:
            continue
        qf = d.qpos.copy(); qf[a.ik.qadr] = q; d2 = mujoco.MjData(m); d2.qpos[:] = qf; mujoco.mj_kinematics(m, d2)
        el = d2.body(f"openarm_{s_}_link4").xpos
        cost = el[2] - 1.5 * abs(el[1])                  # gomito basso e in fuori: niente braccio davanti al viso
        if best is None or cost < best[0]:
            best = (cost, q)
    q = best[1] if best else a.solve(a.robot_pt(xl, yl, z), a.q)
    print(s_, "posa", "ok" if best else "IK di riserva")
    a.q = q; d.qpos[a.ik.qadr] = q
mujoco.mj_forward(m, d)
if HANDS != "gripper":
    # mani articolate: posa di presentazione. Avambracci in avanti all'altezza della vita, mani ai lati del busto
    # (non davanti al petto), dita in avanti e un po' in basso, palmi rivolti verso l'interno.
    from scipy.spatial.transform import Rotation as _R
    yaw_b = base_pose()[2]
    for s_, a in arms.items():
        sg = a.sg
        fwd = np.array([1.0, 0.0, -0.35]); fwd /= np.linalg.norm(fwd)
        inward = np.array([0.0, -sg, 0.25]); inward -= (inward @ fwd) * fwd; inward /= np.linalg.norm(inward)
        Rb = _R.from_euler("z", yaw_b).as_matrix()
        gl = m.site_pos[m.site(f"{s_}_grasp").id].copy()          # centro presa nel frame del polso: dice da che parte e' il palmo
        palm_l = np.array([gl[0], gl[1], 0.0]); palm_l /= np.linalg.norm(palm_l) + 1e-9
        best = None
        for roll in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            z_ee = -fwd                                         # la mano cresce lungo -z del polso
            x0 = np.cross([0, 0, 1.0], z_ee); x0 /= np.linalg.norm(x0); y0 = np.cross(z_ee, x0)
            x_ee = math.cos(roll) * x0 + math.sin(roll) * y0; y_ee = np.cross(z_ee, x_ee)
            R_ee = np.stack([x_ee, y_ee, z_ee], 1)
            palm_w = R_ee @ palm_l
            score = palm_w @ inward
            if best is None or score > best[0]:
                best = (score, Rb @ R_ee)
        Rt = best[1] @ m.site(f"{s_}_grasp").id * 0 if False else best[1]
        tgt = a.robot_pt(0.36, sg * 0.30, 0.98)
        cand = None
        for sg_ in itertools.product((1, -1), repeat=7):
            sd = np.clip(np.array([-0.59, 2.38, 0.36, 1.63, 0.79, 0.3, 1.19]) * np.array(sg_), a.ik.lo, a.ik.hi)
            q, ep, er = a.ik.solve1(d.qpos.copy(), sd, tgt, Rt, 250)
            if ep > 0.01 or er > 0.08:
                continue
            qf = d.qpos.copy(); qf[a.ik.qadr] = q; d2 = mujoco.MjData(m); d2.qpos[:] = qf; mujoco.mj_kinematics(m, d2)
            el = d2.body(f"openarm_{s_}_link4").xpos
            cost = el[2] - 2.0 * abs(el[1]) + 0.2 * er
            if cand is None or cost < cand[0]:
                cand = (cost, q, ep, er)
        if cand:
            a.q = cand[1]; d.qpos[a.ik.qadr] = cand[1]
            print(s_, f"posa mani: errore {1000 * cand[2]:.0f} mm, {math.degrees(cand[3]):.0f} gradi, palmo {best[0]:.2f}")
        else:
            print(s_, "posa mani: nessuna soluzione")
    mujoco.mj_forward(m, d)
# caffe' pieno nella pinza destra
gs = d.site("right_grasp").xpos.copy()
if HANDS == "gripper":
    set_part_xyz("cup", gs + np.array([0, 0, -(CUP_H - 0.03) + CUP_H / 2]))
else:
    set_part_xyz("cup", np.array([-7.0, 4.5, 0.05]))          # mani articolate: bicchiere fuori scena
g = m.geom("cup_coffee").id; m.geom_size[g][1] = 0.028; m.geom_pos[g][2] = -CUP_H / 2 + 0.03
for i in range(3):
    m.geom_rgba[m.geom(f"cup_steam{i}").id][3] = 0.25
arms["right"].grip = 0.0
arms["left"].grip = 0.6
AG["mode"] = "lavoro" if EXPR else MODE
mujoco.mj_forward(m, d)
if EXPR:
    args.agent = "espressioni"; AG["pending"] = []
    _safety = safety

    def safety():
        z, h = _safety()
        t = d.time
        zf = 2 if 7.5 <= t < 10.0 else 0                   # stop: una persona troppo vicina
        AG["mode"] = "caffe" if 4.5 <= t < 7.5 else "lavoro"
        if 2.2 <= t < 2.3 or 10.2 <= t < 10.3:
            expr["happy_t"] = t
        return zf, h

    def agent_step(k):
        pass
exec(compile(post, "giorgio_v5_out", "exec"))
