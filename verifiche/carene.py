"""Verifica: le parti meccaniche del busto (OpenArm body_link0, colonna) stanno dentro le carene?
Per ogni vertice delle mesh 'interne' controlla se e' contenuto in almeno una carena (mesh chiuse, trimesh).
uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/carene.py"""
import sys
import numpy as np
from scipy.spatial import Delaunay
sys.argv = ["x", "--seconds", "0", "--no_humans"]
src = open("giorgio_v5.py").read().split("# ---------------------------------------------------------------- uscite")[0]
exec(compile(src, "v5", "exec"))


def world_mesh(gname):
    g = m.geom(gname).id; mid = m.geom_dataid[g]
    v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
    f = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]]
    R = d.geom_xmat[g].reshape(3, 3); p = d.geom_xpos[g]
    return v @ R.T + p


SHELLS = [n for n in ("shell_torso", "column_cover", "base_cover", "cm_housing", "shell_crown", "crown_shell", "head_shell", "waist_cover", "neck_cover") if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) >= 0]
shells = {n: world_mesh(n) for n in SHELLS}
hulls = {n: Delaunay(v) for n, v in shells.items()}          # carene quasi convesse: test sull'inviluppo convesso
pts = world_mesh("torso_link0")[::3]
inside = np.zeros(len(pts), bool)
for n, h in hulls.items():
    inside |= h.find_simplex(pts) >= 0
out = pts[~inside]
amr = d.body("amr").xpos
print(f"body_link0: {len(pts)} vertici, FUORI dalle carene {len(out)} ({100 * len(out) / len(pts):.1f}%)")
if len(out):
    rel = out - amr
    print("  quota z dei punti fuori: %.3f .. %.3f m; x %.3f..%.3f  y %.3f..%.3f (rispetto alla base)" % (rel[:, 2].min(), rel[:, 2].max(), rel[:, 0].min(), rel[:, 0].max(), rel[:, 1].min(), rel[:, 1].max()))
    zs = np.round(rel[:, 2], 2)
    for z in sorted(set(zs))[:40]:
        sel = rel[zs == z]
        print(f"   z {z:.2f}: {len(sel):4d} punti, |y| max {np.abs(sel[:, 1]).max():.3f}, x {sel[:, 0].min():.3f}..{sel[:, 0].max():.3f}")
