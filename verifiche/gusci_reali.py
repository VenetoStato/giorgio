"""Distanza vera (superficie con aperture, non inviluppo convesso) tra i link delle braccia e il guscio del busto,
sulle pose registrate. uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/gusci_reali.py render/rec_*.pkl"""
import pickle, sys
import numpy as np
import trimesh
recs = sys.argv[1:]
sys.argv = ["x", "--seconds", "0", "--no_humans"]
src = open("giorgio_v5.py").read().split("# ---------------------------------------------------------------- uscite")[0]
exec(compile(src, "v5", "exec"))
sh = trimesh.load("assets/shells/torso.obj", process=False)
gs = m.geom("shell_torso").id
links = [g for g in range(m.ngeom) if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH and
         m.body(m.geom_bodyid[g]).name.startswith(("openarm_left_link", "openarm_right_link")) and
         m.body(m.geom_bodyid[g]).name[-1] in "234567" and m.geom_contype[g] + m.geom_conaffinity[g] == 0]
def mverts(g):
    mid = m.geom_dataid[g]; return m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]][::4]
V = {g: mverts(g) for g in links}
ib = {m.body(i).name: i for i in range(m.nbody)}
def pose(XP, XQ, bn, f, bname, gpos, gquat):
    i = bn.index(bname); R = np.zeros(9); mujoco.mju_quat2Mat(R, XQ[f, i]); R = R.reshape(3, 3)
    q = np.zeros(4); mujoco.mju_mulQuat(q, XQ[f, i], gquat); Rg = np.zeros(9); mujoco.mju_quat2Mat(Rg, q)
    return XP[f, i] + R @ gpos, Rg.reshape(3, 3)
for r in recs:
    D = pickle.load(open(r, "rb")); bn = D["body_names"]; XP, XQ = D["xpos"], D["xquat"]
    best = (9, None)
    for f in range(0, len(XP), 15):
        ps, Rs = pose(XP, XQ, bn, f, "torso", m.geom_pos[gs], m.geom_quat[gs])
        for g in links:
            pg, Rg = pose(XP, XQ, bn, f, m.body(m.geom_bodyid[g]).name, m.geom_pos[g], m.geom_quat[g])
            w = V[g] @ Rg.T + pg
            loc = (w - ps) @ Rs                                   # nel frame del guscio
            near = loc[np.abs(loc).max(1) < 0.40]
            if not len(near):
                continue
            _, dist, _ = trimesh.proximity.closest_point(sh, near)
            if dist.min() < best[0]:
                best = (dist.min(), (f, m.body(m.geom_bodyid[g]).name))
    print(f"{r}: distanza minima braccia - guscio busto (superficie reale) {1000 * best[0]:.1f} mm  {best[1]}", flush=True)
