"""Registrazione di una posa "prodotto" per i render (robot al centro dello studio, braccio destro con il caffe', sinistro rilassato).
uso: MUJOCO_GL=egl python pose_record.py render/rec_pose.pkl
"""
import math
import sys

import numpy as np

out = sys.argv[1] if len(sys.argv) > 1 else "render/rec_pose.pkl"
MODE = sys.argv[2] if len(sys.argv) > 2 else "lavoro"
sys.argv = ["giorgio_v5.py", "--record", out, "--seconds", "3.0", "--no_humans"]
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
# caffe' pieno nella pinza destra
gs = d.site("right_grasp").xpos.copy()
set_part_xyz("cup", gs + np.array([0, 0, -(CUP_H - 0.03) + CUP_H / 2]))
g = m.geom("cup_coffee").id; m.geom_size[g][1] = 0.028; m.geom_pos[g][2] = -CUP_H / 2 + 0.03
for i in range(3):
    m.geom_rgba[m.geom(f"cup_steam{i}").id][3] = 0.25
arms["right"].grip = 0.0
arms["left"].grip = 0.6
AG["mode"] = MODE
mujoco.mj_forward(m, d)
exec(compile(post, "giorgio_v5_out", "exec"))
