"""Verifica v14 (scatole) sulle pose registrate: distanza minima VERA (superfici delle mesh, non inviluppi convessi) tra
 - braccia/pinze (mesh visive OpenArm, link2..pinza) e: gusci del robot (busto, testa, visiera, carter di vita, colonna, base),
   vassoio frontale, rastrelliera posteriore, Gemini/Insta360, piani dei banchi A2/B2
 - scatole e cassetta (anche quando sono in mano) e i gusci del robot
La spalla (base_link, link1) sta dentro il busto per progetto ed e' esclusa, come in gusci_reali.py.
Un vertice ogni 12 delle mesh dei bracci; oltre 60 mm dalla scatola d'ingombro di un guscio la distanza e' riportata come ">= 60 mm".
uso: python verifiche/scatole_v14.py render/rec_scatole_v14.pkl [passo]"""
import pickle
import sys

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation as Rot

rec = sys.argv[1]; STEP = int(sys.argv[2]) if len(sys.argv) > 2 else 5
D = pickle.load(open(rec, "rb")); G = D["geoms"]; bn = D["body_names"]; XP, XQ = D["xpos"], D["xquat"]
SHELL_MESH = ("shell_torso", "head_shell", "face_glass", "waist_cover", "column_cover", "base_cover")
ROBOT_BOX = ("btray_plate", "btray_mat", "btray_lip0", "btray_lip1", "btray_rail-1", "btray_rail1",
             "rrack_plate", "rrack_mat", "rrack_lip0", "rrack_lip1", "rrack_rail-1", "rrack_rail1", "rrack_post-1", "rrack_post1",
             "gemini_body", "insta360")
FURN = ("A2_top", "B2_top")
gi = {e["name"]: e for e in G}


def wq(q):                                                   # MuJoCo (w x y z) -> scipy
    return Rot.from_quat([q[1], q[2], q[3], q[0]])


def gpose(e, f):
    b = e["body"]; Rb = wq(XQ[f, b]); return XP[f, b] + Rb.apply(e["pos"]), Rb * wq(e["quat"])


def box_sd(pts, e, f):
    """distanza con segno punto-box (negativa dentro)"""
    p, R = gpose(e, f); loc = R.inv().apply(pts - p); h = np.asarray(e["size"][:3])
    q = np.abs(loc) - h
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)


def box_pts(e, n=5):
    h = np.asarray(e["size"][:3]); g = np.linspace(-1, 1, n)
    P = np.array([[x, y, z] for x in g for y in g for z in g]); P = P[np.abs(P).max(1) > 0.999]   # superficie
    return P * h


meshes = {n: trimesh.Trimesh(gi[n]["vert"], gi[n]["face"], process=False) for n in SHELL_MESH if n in gi}
ARM = {s: [e for e in G if e["body_name"].startswith(f"openarm_{s}_") and "vert" in e
           and not e["body_name"].endswith(("base_link", "link1")) or (e["body_name"] == f"openarm_{s}_ee_base_link" and "vert" in e)]
       for s in ("right", "left")}
BOXG = [e for e in G if e["name"] in ("box_s_r_g", "box_s_l_g") or (e["name"].startswith("box_big_") and e["type"] == 6 and "w" in e["name"] or e["name"] == "box_big_g")]
best = {}


def note(k, dist, f, who):
    if dist < best.get(k, (9.0,))[0]:
        best[k] = (dist, f, who)


for f in range(0, len(XP), STEP):
    for s, geoms in ARM.items():
        for e in geoms:
            p, R = gpose(e, f); w = R.apply(e["vert"][::12]) + p
            for n, tm in meshes.items():
                ps, Rs = gpose(gi[n], f); loc = Rs.inv().apply(w - ps)
                lo, hi = tm.bounds[0] - 0.06, tm.bounds[1] + 0.06
                near = loc[np.all((loc > lo) & (loc < hi), 1)]
                if len(near):
                    _, dist, _ = trimesh.proximity.closest_point(tm, near)
                    note((s, n), float(dist.min()), f, e["body_name"])
                else:
                    note((s, n), 0.06, f, "(oltre 60 mm)")
            for n in ROBOT_BOX + FURN:
                if n in gi:
                    note((s, n if n in FURN else n.split("_")[0]), float(box_sd(w, gi[n], f).min()), f, e["body_name"])
    for e in BOXG:                                           # scatole/cassetta contro i gusci del robot
        p, R = gpose(e, f); w = R.apply(box_pts(e)) + p
        for n, tm in meshes.items():
            ps, Rs = gpose(gi[n], f); loc = Rs.inv().apply(w - ps)
            lo, hi = tm.bounds[0] - 0.06, tm.bounds[1] + 0.06
            near = loc[np.all((loc > lo) & (loc < hi), 1)]
            if len(near):
                _, dist, _ = trimesh.proximity.closest_point(tm, near)
                note(("scatole", n), float(dist.min()), f, e["name"])
print(f"{rec}: {len(range(0, len(XP), STEP))} pose (una ogni {STEP} fotogrammi = {STEP / 30:.2f} s)")
for k in sorted(best):
    dist, f, who = best[k]
    print(f"  {k[0]:7s} vs {k[1]:13s}: minimo {1000 * dist:7.1f} mm  (fotogramma {f}, t={f / 30:.1f} s, {who})")
