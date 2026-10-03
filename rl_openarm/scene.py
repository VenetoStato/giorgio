"""Scene per OpenArm 2.0 (MJCF ufficiale Enactic, Apache-2.0) + cubo.

build_standalone(): UN braccio OpenArm 2.0 (il destro del MJCF ufficiale, pinza ufficiale), base fissa su una colonna
                    davanti a un tavolo. Nessun pezzo di Giorgio.
build_giorgio():    Giorgio completo (giorgio_model.build, pinze OpenArm) + banco come in giorgio_v5 + lo stesso cubo.

Convenzioni comuni (usate dalla politica):
  - frame base del braccio = body "openarm_right_base_link" (radice della catena destra, identico nei due modelli)
  - punto di presa = ee_base_link + R_ee @ GRASP_OFS (centro dei polpastrelli)
  - attuatori: right_joint1..7_ctrl, right_finger1_ctrl (nomi ufficiali)
"""
import math
import os
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OA = ROOT / "third_party/openarm_mujoco/v2"

BASE_BODY = "openarm_right_base_link"
EE_BODY = "openarm_right_ee_base_link"
ARM_JOINTS = [f"openarm_right_joint{k}" for k in range(1, 8)]
FINGER_JOINT = "openarm_right_finger_joint1"
ARM_ACT = [f"right_joint{k}_ctrl" for k in range(1, 8)]
FINGER_ACT = "right_finger1_ctrl"
GRASP_OFS = np.array([0.0, 0.0, -0.14])       # dal frame ee_base_link: centro dei polpastrelli (verificato in check_scene.py)
CUBE_HALF = 0.025
ARM_Z = 1.20                                   # standalone: quota della base del braccio sopra il pavimento
TABLE_DZ = -0.36                               # standalone nominale: piano del tavolo rispetto alla base del braccio


def _openarm_right_only():
    """MJCF ufficiale bimanuale -> solo il braccio destro (si eliminano braccio sinistro, suo attuatore e mimic)."""
    oa = mujoco.MjSpec.from_file(str(OA / "openarm_bimanual.xml"))
    for a in list(oa.actuators):
        if a.name.startswith("left_"):
            oa.delete(a)
    for e in list(oa.equalities):
        if "left" in e.name:
            oa.delete(e)
    oa.delete(oa.body("openarm_left_base_link"))
    return oa


def add_cube(wb, pos, light=True):
    b = wb.add_body(name="cube", pos=list(pos))
    b.add_freejoint(name="cube_free")
    b.add_geom(name="cube_g", type=mujoco.mjtGeom.mjGEOM_BOX, size=[CUBE_HALF] * 3, mass=0.08,
               rgba=[1.0, 0.48, 0.1, 1], friction=[0.9, 0.01, 0.001], condim=4, priority=2,
               contype=1, conaffinity=3, solref=[0.005, 1], group=0)
    return b


def build_standalone(obstacle=False):
    sp = mujoco.MjSpec()
    sp.compiler.degree = False
    sp.option.timestep = 0.002
    sp.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    sp.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    sp.option.impratio = 10
    sp.visual.global_.offwidth, sp.visual.global_.offheight = 1920, 1080
    sp.visual.quality.shadowsize = 4096
    sp.visual.headlight.ambient = [0.3, 0.3, 0.32]
    sp.visual.headlight.diffuse = [0.5, 0.5, 0.52]
    sp.add_texture(name="sky", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX, builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                   rgb1=[0.16, 0.17, 0.19], rgb2=[0.02, 0.02, 0.03], width=256, height=256)
    sp.add_texture(name="floor", type=mujoco.mjtTexture.mjTEXTURE_2D, builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                   rgb1=[0.12, 0.12, 0.13], rgb2=[0.15, 0.15, 0.16], mark=mujoco.mjtMark.mjMARK_EDGE,
                   markrgb=[0.25, 0.25, 0.27], width=256, height=256)
    mf = sp.add_material(name="floor", texrepeat=[6, 6], reflectance=0.1)
    mf.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "floor"
    sp.add_material(name="table", rgba=[0.78, 0.77, 0.74, 1], reflectance=0.05)
    sp.add_material(name="post", rgba=[0.2, 0.2, 0.22, 1], reflectance=0.2)
    wb = sp.worldbody
    wb.add_light(pos=[0.5, -0.6, 2.6], dir=[-0.1, 0.25, -1], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL, diffuse=[0.75, 0.75, 0.75], castshadow=True)
    wb.add_light(pos=[1.5, 1.0, 2.0], dir=[-0.5, -0.4, -1], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL, diffuse=[0.25, 0.25, 0.27], castshadow=False)
    wb.add_geom(name="floor", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[0, 0, 0.05], material="floor", contype=0, conaffinity=0)
    # tavolo: lastra (unico geom che collide); la sua quota viene randomizzata in addestramento (mocap_pos)
    tb = wb.add_body(name="table_body", pos=[0.42, -0.10, ARM_Z + TABLE_DZ - 0.02], mocap=True)   # mocap: quota randomizzabile per mondo
    tb.add_geom(name="table", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.34, 0.45, 0.02],
                rgba=[0.62, 0.61, 0.58, 1], contype=1, conaffinity=3, friction=[0.8, 0.01, 0.001], group=0)
    for x_ in (0.12, 0.72):
        for y_ in (-0.5, 0.3):
            wb.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, pos=[x_, y_, (ARM_Z + TABLE_DZ - 0.04) / 2],
                        size=[0.02, 0.02, (ARM_Z + TABLE_DZ - 0.04) / 2], material="post", contype=0, conaffinity=0)
    # colonna di fissaggio dietro al tavolo (solo visiva): la base del braccio e' fissa
    wb.add_geom(name="post", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.07, 0.0, ARM_Z / 2 + 0.02], size=[0.04, 0.04, ARM_Z / 2 + 0.02],
                material="post", contype=0, conaffinity=0)
    wb.add_geom(name="post_plate", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.02, -0.015, ARM_Z], size=[0.035, 0.03, 0.05],
                material="post", contype=0, conaffinity=0)
    oa = _openarm_right_only()
    fr = wb.add_frame(pos=[0, 0, ARM_Z])
    sp.attach(oa, frame=fr, prefix="")
    if obstacle:      # solo addestramento v2: ostacolo basso davanti alla base (posizione/altezza randomizzate, spesso assente)
        ob = wb.add_body(name="obst_body", pos=[0.15, -0.05, -3.0], mocap=True)
        ob.add_geom(name="obst", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.035, 0.30, 0.06], rgba=[0.3, 0.3, 0.33, 1],
                    contype=1, conaffinity=3, group=0)
    add_cube(wb, [0.35, -0.12, ARM_Z + TABLE_DZ + CUBE_HALF])
    wb.add_camera(name="side", pos=[1.35, -1.25, 1.55], xyaxes=[0.68, 0.73, 0, -0.25, 0.23, 0.94], fovy=40)
    return sp


def build_giorgio(look="gb", buffer=True):
    """Giorgio (modello completo, pinze OpenArm ufficiali, base fissa, braccio destro libero) + banco 'B' di giorgio_v5."""
    sys.path.insert(0, str(ROOT))
    from giorgio_model import build, GROUP_ENV
    sp = build(look, hands="gripper", humans=0, fixed_base=True, base="amr", buffer=buffer, coffee=False)
    wb = sp.worldbody
    BENCH_Z = 0.90                                                  # come giorgio_v5
    def box(name, pos, half, material, collide=True):
        g = wb.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material, group=GROUP_ENV)
        if collide:
            g.conaffinity = 3
        else:
            g.contype = g.conaffinity = 0
        return g
    # stesso banco di giorgio_v5 table("B", (0,0,0))
    box("B_top", (0.48, 0.0, BENCH_Z - 0.02), (0.32, 0.85, 0.02), "bench")
    for xl in (0.19, 0.77):
        for yl in (-0.8, 0.8):
            box(f"B_leg_{xl}_{yl}", (xl, yl, (BENCH_Z - 0.04) / 2), (0.025, 0.025, (BENCH_Z - 0.04) / 2), "steel", collide=False)
    box("B_edge", (0.80, 0.0, BENCH_Z - 0.03), (0.002, 0.85, 0.006), "accent", collide=False)
    add_cube(wb, [0.35, -0.15, BENCH_Z + CUBE_HALF])
    wb.add_camera(name="side", pos=[1.25, -1.15, 1.62], xyaxes=[0.68, 0.73, 0, -0.27, 0.25, 0.93], fovy=42)
    return sp, BENCH_Z


if __name__ == "__main__":
    for nm, sp in (("standalone", build_standalone()), ("giorgio", build_giorgio()[0])):
        m = sp.compile()
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        print(nm, "nq", m.nq, "nv", m.nv, "nu", m.nu, "ngeom", m.ngeom, "neq", m.neq,
              "base", d.body(BASE_BODY).xpos.round(3), "dt", m.opt.timestep)
        print("  act", [m.actuator(i).name for i in range(m.nu)])
