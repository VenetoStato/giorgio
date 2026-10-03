"""Esporta dal modello MuJoCo (sola lettura) quello che serve al CAD:

  data/sim_static.json      quote chiave (spalle, busto, corona, massa e baricentro della sim)
  data/arm_meshes/*.stl     mesh visive di ogni corpo dei bracci OpenArm nel frame del corpo (mm)
  data/arm_traj.npz         pose dei corpi dei bracci RELATIVE alla base (frame "amr"), mm, campionate
                            dalle registrazioni reali delle missioni (render/*_v9.npz) + pose IK di riferimento
Frame del robot: origine a terra al centro della Tracer, x avanti, y sinistra, z su.

Uso:  cd ~/giorgio_sim && cad/.env/bin/python cad/sim_export.py
"""
import json
import sys
from pathlib import Path

import mujoco
import numpy as np
import trimesh

CAD = Path(__file__).resolve().parent
ROOT = CAD.parent
sys.path.insert(0, str(ROOT))
import giorgio_model as gm  # noqa: E402

OUT = CAD / "data"
RECS = ["logistica_v9", "caffe_v9", "espr_v9"]   # registrazioni delle missioni (base libera, colonna a 0)
STEP = 10                                        # un fotogramma ogni 10 (~0.3 s)


def quat2mat(q):
    m = np.zeros(9)
    mujoco.mju_quat2Mat(m, np.asarray(q, float))
    return m.reshape(3, 3)


def T(pos, R):
    t = np.eye(4)
    t[:3, :3] = R
    t[:3, 3] = pos
    return t


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "arm_meshes").mkdir(exist_ok=True)
    sp = gm.build("gb", hands="gripper", humans=0, fixed_base=True, base="amr", buffer=True, coffee=True)
    m = sp.compile()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    amr = m.body("amr").id
    arm_bodies = [m.body(i).name for i in range(m.nbody) if m.body(i).name.startswith("openarm_")]
    # ------------------------------------------------ mesh per corpo (solo geom visivi gruppo 2, frame del corpo, mm)
    for bn in arm_bodies:
        bid = m.body(bn).id
        parts = []
        for g in range(m.ngeom):
            if m.geom_bodyid[g] != bid or m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
                continue
            if m.geom_contype[g] or m.geom_conaffinity[g]:      # collisioni: escluse (doppioni)
                continue
            mid = m.geom_dataid[g]
            va, nv = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
            fa, nf = m.mesh_faceadr[mid], m.mesh_facenum[mid]
            V = m.mesh_vert[va:va + nv].astype(float)
            F = m.mesh_face[fa:fa + nf].astype(int)
            R = quat2mat(m.geom_quat[g])
            V = V @ R.T + m.geom_pos[g]
            parts.append(trimesh.Trimesh(V * 1000.0, F, process=False))
        if parts:
            tm = trimesh.util.concatenate(parts)
            tm.export(OUT / "arm_meshes" / f"{bn}.stl")
    # ------------------------------------------------ quote statiche (colonna a 0, posa iniziale della sim)
    def rel(bn):
        R0 = d.xmat[amr].reshape(3, 3); p0 = d.xpos[amr]
        return ((d.xpos[m.body(bn).id] - p0) @ R0 * 1000).round(2).tolist()
    st = {
        "note": "posizioni in mm nel frame base (amr), colonna (lift) = 0, qpos iniziale",
        "torso_origin": rel("torso"), "column_origin": rel("column"), "crown": rel("crown"),
        "left_link2": rel("openarm_left_link2"), "right_link2": rel("openarm_right_link2"),
        "left_base_link": rel("openarm_left_base_link"), "right_base_link": rel("openarm_right_base_link"),
        "sim_robot_mass_kg": float(m.body_subtreemass[amr]),
        "sim_robot_com_mm": (d.subtree_com[amr] * 1000).round(1).tolist(),
        "arm_mass_kg": {s: float(sum(m.body_mass[m.body(b).id] for b in arm_bodies if f"_{s}_" in b)) for s in ("left", "right")},
        "arm_bodies": arm_bodies,
    }
    # masse dei singoli corpi (per il bilancio masse) e baricentro di ogni corpo braccio in posa iniziale
    st["arm_body_mass_com"] = {b: [float(m.body_mass[m.body(b).id])] + (d.xipos[m.body(b).id] * 1000).round(1).tolist() for b in arm_bodies}
    (OUT / "sim_static.json").write_text(json.dumps(st, indent=1))
    print("statico:", json.dumps({k: v for k, v in st.items() if k not in ("arm_bodies", "arm_body_mass_com")}))
    # ------------------------------------------------ traiettorie registrate -> pose relative alla base
    traj = {bn: [] for bn in arm_bodies}
    src, shuttle = [], []
    for rec in RECS:
        f = ROOT / "render" / f"{rec}.npz"
        jf = ROOT / "render" / f"{rec}.json"
        if not f.exists():
            print("manca", f); continue
        z = np.load(f, allow_pickle=True)
        names = json.load(open(jf))["body_names"]
        ia = names.index("amr")
        xp, xq = z["xpos"], z["xquat"]
        for k in range(0, xp.shape[0], STEP):
            Ra = quat2mat(xq[k, ia]); pa = xp[k, ia]
            for bn in arm_bodies:
                ib = names.index(bn)
                Rb = quat2mat(xq[k, ib])
                traj[bn].append(T(Ra.T @ (xp[k, ib] - pa) * 1000.0, Ra.T @ Rb))
            src.append(rec)
            if "cm_shuttle" in names:
                ish = names.index("cm_shuttle")
                shuttle.append((Ra.T @ (xp[k, ish] - pa) * 1000.0))
            else:
                shuttle.append([np.nan] * 3)
        print(rec, xp.shape[0], "fotogrammi")
    # posa iniziale del modello (bracci in posa di partenza)
    for bn in arm_bodies:
        i = m.body(bn).id
        traj[bn].append(T((d.xpos[i] - d.xpos[amr]) * 1000.0, d.xmat[i].reshape(3, 3)))
    src.append("home")
    shuttle.append([np.nan] * 3)
    np.savez_compressed(OUT / "arm_traj.npz", bodies=np.array(arm_bodies), src=np.array(src),
                        shuttle=np.array(shuttle, float), **{bn: np.array(v) for bn, v in traj.items()})
    print("pose:", len(src))


if __name__ == "__main__":
    main()
