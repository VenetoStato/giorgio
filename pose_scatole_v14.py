"""Pose "prodotto" per le foto delle varianti di carico v14 (robot al centro dello studio, braccia in posa pronta).
Le scatole vengono posate 3 mm sopra gli alloggi e si assestano per fisica (1.5 s) prima della registrazione.
uso: MUJOCO_GL=egl python pose_scatole_v14.py render/rec_cfg_front_v14.pkl front|rear|both
  front: vassoio frontale con 3 scatole (zaino caffe' tolto)
  rear:  rastrelliera posteriore con 2 scatole al posto dello zaino caffe' (davanti resta il vassoio flaconi di serie)
  both:  vassoio frontale (3 scatole) + rastrelliera posteriore (2 scatole)
"""
import math
import sys

import numpy as np

out = sys.argv[1]
VAR = sys.argv[2]
sys.argv = ["giorgio_v5.py", "--record", out, "--seconds", "2.0", "--no_humans"]
src = open(__file__.replace("pose_scatole_v14.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")
opts = {"front": "buffer=False, coffee=False, box_tray=True, rear_rack=False",
        "rear": "buffer=True, coffee=False, box_tray=False, rear_rack=True",
        "both": "buffer=False, coffee=False, box_tray=True, rear_rack=True"}[VAR]
pre = pre.replace('sp = build(args.look, hands=args.hands, base="amr", fixed_base=False, buffer=True, coffee=True)',
                  f'sp = build(args.look, hands=args.hands, base="amr", fixed_base=False, {opts})', 1)
pre = pre.replace('SHUTTLE = m.actuator("cm_shuttle").id',
                  'SHUTTLE = m.actuator("cm_shuttle").id if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, "cm_shuttle") >= 0 else -1', 1)
from giorgio_model import BT_Z, RR_Z
SB = (0.08, 0.05, 0.05)
SLOTS = []
if VAR in ("front", "both"):
    SLOTS += [(0.205, y, BT_Z, 0.0) for y in (-0.145, 0.0, 0.145)]          # lato lungo in avanti, passo 145 mm
if VAR in ("rear", "both"):
    SLOTS += [(-0.265, y, RR_Z, math.pi / 2) for y in (-0.11, 0.11)]       # ruotate di 90 gradi
PROPS = "\n".join(f'''
_b = wb.add_body(name="box_{i}", pos=[{x}, {y}, {z + SB[2] + 0.003}], quat=[{math.cos(yw / 2)}, 0, 0, {math.sin(yw / 2)}])
_b.add_freejoint(name="box_{i}_free")
_b.add_geom(name="box_{i}_g", type=mujoco.mjtGeom.mjGEOM_BOX, size={list(SB)}, mass=1.2, rgba=[0.70, 0.52, 0.33, 1], friction=[0.7, 0.01, 0.001], condim=4, conaffinity=3, group=GROUP_ENV)
_b.add_geom(name="box_{i}_tape", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, {SB[2] + 0.0004}], size=[{SB[0] + 0.0004}, 0.024, 0.0005], rgba=[0.58, 0.42, 0.26, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
for _sx in (-1, 1):
    _b.add_geom(name=f"box_{i}_label{{_sx}}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[_sx * {SB[0] + 0.0004}, 0, 0.006], size=[0.0005, 0.03, 0.03], rgba=[0.95, 0.95, 0.93, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
    _b.add_geom(name=f"box_{i}_stripe{{_sx}}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[_sx * {SB[0] + 0.0008}, 0, 0.0285], size=[0.0005, 0.03, 0.0035], rgba=[1.0, 0.55, 0.2, 1], contype=0, conaffinity=0, group=GROUP_ENV, mass=0)
''' for i, (x, y, z, yw) in enumerate(SLOTS))
pre = pre.replace("m = sp.compile()", PROPS + "\nm = sp.compile()", 1)
exec(compile(pre, "giorgio_v5", "exec"))
d.qpos[FREE_Q:FREE_Q + 3] = [0.0, 0.0, 0.0]
d.qpos[FREE_Q + 3:FREE_Q + 7] = [1, 0, 0, 0]
d.qvel[:] = 0
for p_ in PARTS:
    set_part_xyz(p_, storage(p_))
set_part_xyz("cup", np.array([-7.0, 4.6, CUP_H / 2 + 0.001]))
mujoco.mj_forward(m, d)
mission["state"] = "posa"
teach_contour()
print("massa robot", round(float(m.body_subtreemass[m.body("amr").id]), 2), "kg; scatole", len(SLOTS), flush=True)
post = post.replace("    ANIM = [m.geom(n).id for n in ANIM_N]",
                    "    ANIM_N = [n for n in ANIM_N if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) >= 0]\n    ANIM = [m.geom(n).id for n in ANIM_N]", 1)
exec(compile(post, "giorgio_v5_out", "exec"))
for i in range(len(SLOTS)):
    p = d.body(f"box_{i}").xpos; R = d.body(f"box_{i}").xmat.reshape(3, 3)
    print(f"box_{i}: {np.round(p, 3)} inclinazione {math.degrees(math.acos(min(1.0, R[2, 2]))):.2f} gradi", flush=True)
