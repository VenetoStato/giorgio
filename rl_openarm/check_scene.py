"""Verifiche rapide: punto di presa (centro polpastrelli), apertura pinza, posa iniziale, still di controllo."""
import sys
import mujoco
import numpy as np
from scene import *

sp = build_standalone(); m = sp.compile(); d = mujoco.MjData(m)
Q0 = np.array([0.0, 0.0, 0.0, 1.5708, 0.0, 0.0, 0.0])
for q0 in ([0, 0, 0, 1.5708, 0, 0, 0], [0.4, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0], [-0.3,0.0,0,2.2,0,0.6,0]):
    for g in (-0.7854, 0.0):
        for k, j in enumerate(ARM_JOINTS):
            d.joint(j).qpos = q0[k]
        d.joint(FINGER_JOINT).qpos = g; d.joint("openarm_right_finger_joint2").qpos = g
        mujoco.mj_forward(m, d)
        ee = d.body(EE_BODY); R = ee.xmat.reshape(3, 3)
        tips = []
        for b in ("openarm_right_ee_inner_finger", "openarm_right_ee_outer_finger"):
            bid = m.body(b).id
            gs = [i for i in range(m.ngeom) if m.geom_bodyid[i] == bid and m.geom_contype[i]]
            # punto piu' lontano dal polso tra i vertici delle mesh di collisione
            pts = []
            for gi in gs:
                mid = m.geom_dataid[gi]; v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
                pts.append(d.geom_xpos[gi] + v @ d.geom_xmat[gi].reshape(3, 3).T)
            P = np.concatenate(pts); Pl = (P - ee.xpos) @ R
            tips.append(Pl)
        a, b = tips
        print("q", q0, "grip", g, "inner z-range", a[:, 2].min().round(3), "y-range inner", a[:, 1].min().round(3), a[:, 1].max().round(3),
              "outer y", b[:, 1].min().round(3), b[:, 1].max().round(3), "x", a[:,0].min().round(3), a[:,0].max().round(3))
        base = d.body(BASE_BODY); Rb = base.xmat.reshape(3, 3)
        gp = ee.xpos + R @ GRASP_OFS
        print("   grasp pt in base frame", ((gp - base.xpos) @ Rb).round(3), "ee z axis world", R[:, 2].round(2))
