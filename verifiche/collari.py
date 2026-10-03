"""Distanza minima braccia/mani dai colletti (waist_cover, neck_cover) e dal guscio del busto sulle pose registrate.
uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/collari.py render/rec_caffe_v9.pkl [...]"""
import pickle, sys
import numpy as np
recs = sys.argv[1:]
sys.argv = ["x", "--seconds", "0", "--no_humans"]
src = open("giorgio_v5.py").read().split("# ---------------------------------------------------------------- uscite")[0]
exec(compile(src, "v5", "exec"))
targets = [m.geom(n).id for n in ("waist_cover", "neck_cover", "shell_torso")]
arm = [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.startswith(("openarm_left_link", "openarm_right_link", "openarm_left_ee", "openarm_right_ee"))
       and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH and m.body(m.geom_bodyid[g]).name not in ("openarm_left_link1", "openarm_right_link1")]
ft = np.zeros(6); qadr = np.r_[arms["right"].ik.qadr, arms["left"].ik.qadr]
d2 = mujoco.MjData(m)
for r in recs:
    D = pickle.load(open(r, "rb")); bn = D["body_names"]
    if "qarm" not in D:
        print(r, ": registrazione senza giunti dei bracci, uso le posizioni dei corpi"); 
    worst = {t: (9.0, None) for t in targets}
    XQ, XP = D["xquat"], D["xpos"]
    ib = {m.body(i).name: i for i in range(m.nbody)}
    for f in range(0, len(XP), 10):
        for i, n in enumerate(bn):
            if n in ib:
                d2.xpos[ib[n]] = XP[f, i]; d2.xquat[ib[n]] = XQ[f, i]
        for i in range(m.nbody):
            mujoco.mju_quat2Mat(d2.xmat[i], d2.xquat[i])
        for g in range(m.ngeom):
            b = m.geom_bodyid[g]
            mujoco.mju_mulMatVec(d2.geom_xpos[g], d2.xmat[b].reshape(3, 3), m.geom_pos[g]); d2.geom_xpos[g] += d2.xpos[b]
            q = np.zeros(4); mujoco.mju_mulQuat(q, d2.xquat[b], m.geom_quat[g]); mujoco.mju_quat2Mat(d2.geom_xmat[g], q)
        for t in targets:
            for g in arm:
                if np.linalg.norm(d2.geom_xpos[g] - d2.geom_xpos[t]) > 0.6:
                    continue
                dist = mujoco.mj_geomDistance(m, d2, g, t, 0.2, ft)
                if dist < worst[t][0]:
                    worst[t] = (dist, (f, m.body(m.geom_bodyid[g]).name))
    for t, (dd, w) in worst.items():
        print(f"{r}: {m.geom(t).name:12s} distanza minima dai bracci {1000 * dd:7.1f} mm  (fotogramma/parte {w})")
