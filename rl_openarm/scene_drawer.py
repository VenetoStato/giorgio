"""Drawer-opening scenes: the same OpenArm 2.0 (official MJCF, right arm + gripper) and a benchtop chest of drawers.

build_standalone(): standalone OpenArm (same table/column as scene.py) + cabinet (mocap carcass, pose randomized in
                    training) + optional low obstacle in front of the base (as in lift v2-v5).
build_giorgio():    Giorgio as built (giorgio_model.build, unchanged) + bench "B" (as in scene.py) + the same cabinet
                    placed ON the bench, in front of the right arm.

Cabinet frame ("cab", a mocap body): origin = centre of the CLOSED drawer's front face, x axis pointing INTO the cabinet.
The drawer slides along -x (joint "drawer_slide", value = opening in metres, 0 = closed).
Handle types (all on the drawer body, unused ones are parked 1 m below the drawer, see set_handle):
  0 = horizontal bar, 1 = vertical bar, 2 = round knob.  The grasp target is always the handle point at [-s, 0, 0].
"""
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

import scene
from scene import ARM_Z, TABLE_DZ, BASE_BODY, _openarm_right_only

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

CAB_DEPTH = 0.35          # x extent of the carcass
CAB_HW = 0.23             # half width (outer)
DR_HZ = 0.058             # drawer front half height
DR_HY = 0.198             # drawer front half width
DR_T = 0.018              # drawer front thickness
TOP_H = 0.15              # fixed upper drawer + top above the moving drawer
TRAVEL = 0.30             # drawer slide range
PARK = -1.0               # z (drawer frame) where unused handle geoms are parked
# training-time maxima (geoms are compiled at max size, so broadphase bounds stay conservative when shrunk per world)
L_MAX, R_MAX, S_MAX, K_MAX = 0.16, 0.012, 0.045, 0.022
HANDLE_GEOMS = ["h_hbar", "h_vbar", "h_knob", "h_post1", "h_post2"]


def _mats(sp):
    sp.add_material(name="cab_body", rgba=[0.86, 0.85, 0.82, 1], reflectance=0.05, specular=0.3)
    sp.add_material(name="cab_front", rgba=[0.30, 0.42, 0.52, 1], reflectance=0.1, specular=0.4)
    sp.add_material(name="cab_inner", rgba=[0.72, 0.62, 0.48, 1], reflectance=0.02)
    sp.add_material(name="cab_handle", rgba=[0.75, 0.76, 0.78, 1], reflectance=0.4, specular=0.9, shininess=0.9)


def add_cabinet(wb, pos, yaw=0.0, plinth=0.5, group=0):
    """Adds the carcass (mocap body 'cab') and the sliding drawer. plinth = height of the solid base under the drawer."""
    q = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    cab = wb.add_body(name="cab", pos=list(pos), quat=q, mocap=True)
    B = mujoco.mjtGeom.mjGEOM_BOX

    def cg(name, p, s, mat="cab_body"):
        # carcass: collides with the arm (contype 1 of the arm vs conaffinity 1), not with table/drawer (contype 0)
        return cab.add_geom(name=name, type=B, pos=list(p), size=list(s), material=mat, contype=0, conaffinity=1,
                            group=group, friction=[0.6, 0.01, 0.001])
    D = CAB_DEPTH
    zb = -DR_HZ - 0.007                       # bottom of the drawer cavity
    zt = DR_HZ + 0.007                        # top of the drawer cavity
    cg("cab_side_l", (D / 2, CAB_HW - 0.015, (zt + TOP_H + zb - plinth) / 2), (D / 2, 0.015, (zt + TOP_H - zb + plinth) / 2))
    cg("cab_side_r", (D / 2, -CAB_HW + 0.015, (zt + TOP_H + zb - plinth) / 2), (D / 2, 0.015, (zt + TOP_H - zb + plinth) / 2))
    cg("cab_top", (D / 2, 0, zt + TOP_H / 2), (D / 2, CAB_HW - 0.03, TOP_H / 2))
    cg("cab_plinth", (D / 2, 0, zb - plinth / 2), (D / 2, CAB_HW - 0.03, plinth / 2))
    cg("cab_back", (D - 0.01, 0, 0), (0.01, CAB_HW - 0.03, (zt - zb) / 2))
    # upper fixed drawer front with its own (fixed) bar handle: a realistic obstacle just above the target handle
    cab.add_geom(name="cab_upper_front", type=B, pos=[-0.002, 0, zt + TOP_H / 2], size=[0.004, DR_HY, TOP_H / 2 - 0.012],
                 material="cab_front", contype=0, conaffinity=0, group=group)
    cab.add_geom(name="cab_upper_handle", type=mujoco.mjtGeom.mjGEOM_CAPSULE, pos=[-0.03, 0, zt + TOP_H / 2],
                 quat=[0.7071068, 0.7071068, 0, 0], size=[0.008, 0.05, 0], material="cab_handle", contype=0, conaffinity=1, group=group)
    for yy in (-0.05, 0.05):
        cab.add_geom(type=B, pos=[-0.017, yy, zt + TOP_H / 2], size=[0.015, 0.005, 0.005], material="cab_handle",
                     contype=0, conaffinity=0, group=group)
    # plinth front face (visual)
    cab.add_geom(name="cab_plinth_front", type=B, pos=[-0.002, 0, zb - plinth / 2], size=[0.004, DR_HY, plinth / 2 - 0.006],
                 material="cab_front", contype=0, conaffinity=0, group=group)

    dr = cab.add_body(name="drawer", pos=[0, 0, 0])
    dr.add_joint(name="drawer_slide", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[-1, 0, 0], range=[0, TRAVEL],
                 limited=mujoco.mjtLimited.mjLIMITED_TRUE, damping=10.0, frictionloss=4.0, stiffness=0.0, springref=0.0,
                 armature=0.05)
    dr.explicitinertial = True
    dr.mass = 1.5
    dr.inertia = [0.02, 0.02, 0.03]
    dr.ipos = [0.17, 0, -0.02]

    def dg(name, p, s, mat="cab_inner", typ=B, **kw):
        return dr.add_geom(name=name, type=typ, pos=list(p), size=list(s), material=mat, contype=0, conaffinity=1,
                           group=group, mass=0, **kw)
    dg("dr_front", (DR_T / 2, 0, 0), (DR_T / 2, DR_HY, DR_HZ), mat="cab_front")
    dg("dr_side_l", (0.17, DR_HY - 0.02, -0.008), (0.15, 0.006, DR_HZ - 0.015))
    dg("dr_side_r", (0.17, -DR_HY + 0.02, -0.008), (0.15, 0.006, DR_HZ - 0.015))
    dg("dr_bottom", (0.17, 0, -DR_HZ + 0.01), (0.15, DR_HY - 0.02, 0.004))
    dg("dr_back", (0.315, 0, -0.008), (0.006, DR_HY - 0.02, DR_HZ - 0.015))
    hk = dict(mat="cab_handle", priority=2, friction=[0.8, 0.01, 0.001], condim=4, solref=[0.004, 1])
    C, Y = mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_CYLINDER
    dg("h_hbar", (-0.03, 0, 0), (R_MAX, L_MAX / 2, 0), typ=C, quat=[0.7071068, 0.7071068, 0, 0], **hk)    # along y
    dg("h_vbar", (-0.03, 0, PARK), (R_MAX, L_MAX / 2, 0), typ=C, **hk)                                   # along z
    dg("h_knob", (-0.03, 0, PARK), (K_MAX, 0.009, 0), typ=Y, quat=[0.7071068, 0, 0.7071068, 0], **hk)     # disc, axis x
    dg("h_post1", (-S_MAX / 2, L_MAX / 2, 0), (S_MAX / 2, 0.008, 0.008), **hk)    # compiled at max size (knob stem)
    dg("h_post2", (-S_MAX / 2, -L_MAX / 2, 0), (S_MAX / 2, 0.008, 0.008), **hk)
    return cab, dr


def handle_layout(kind, L, r, s, k):
    """geom pos/size of the 5 handle geoms (drawer frame) for one handle. kind 0 hbar, 1 vbar, 2 knob.
    Returns dict name -> (pos(3), size(3))."""
    P = PARK
    out = {}
    if kind == 0:
        out["h_hbar"] = ((-s, 0, 0), (r, L / 2, 0)); out["h_vbar"] = ((-s, 0, P), (r, L / 2, 0)); out["h_knob"] = ((-s, 0, P), (k, 0.009, 0))
        out["h_post1"] = ((-s / 2, L / 2 - 0.006, 0), (s / 2, 0.006, 0.006)); out["h_post2"] = ((-s / 2, -L / 2 + 0.006, 0), (s / 2, 0.006, 0.006))
    elif kind == 1:
        out["h_hbar"] = ((-s, 0, P), (r, L / 2, 0)); out["h_vbar"] = ((-s, 0, 0), (r, L / 2, 0)); out["h_knob"] = ((-s, 0, P), (k, 0.009, 0))
        out["h_post1"] = ((-s / 2, 0, L / 2 - 0.006), (s / 2, 0.006, 0.006)); out["h_post2"] = ((-s / 2, 0, -L / 2 + 0.006), (s / 2, 0.006, 0.006))
    else:
        out["h_hbar"] = ((-s, 0, P), (r, L / 2, 0)); out["h_vbar"] = ((-s, 0, P), (r, L / 2, 0)); out["h_knob"] = ((-s, 0, 0), (k, 0.009, 0))
        out["h_post1"] = ((-s / 2, 0, 0), (s / 2, 0.008, 0.008)); out["h_post2"] = ((-s / 2, 0, P), (s / 2, 0.006, 0.006))
    return out


def set_handle_cpu(m, kind, L, r, s, k):
    for n, (p, sz) in handle_layout(kind, L, r, s, k).items():
        g = m.geom(n).id
        m.geom_pos[g] = p
        m.geom_size[g] = sz


def _base_scene(sp, light=False):
    sp.compiler.degree = False
    sp.option.timestep = 0.002
    sp.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    sp.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    sp.option.impratio = 10
    sp.visual.global_.offwidth, sp.visual.global_.offheight = 1920, 1080
    sp.visual.quality.shadowsize = 4096


def build_standalone(obstacle=False, plinth=0.5):
    sp = scene.build_standalone(obstacle=False)
    # remove the cube: this task has no cube
    sp.delete(sp.body("cube"))
    _mats(sp)
    wb = sp.worldbody
    # table: contype 2 so it does not collide with the (static) carcass; still collides with the arm (conaffinity 3)
    t = sp.geom("table"); t.contype = 2; t.conaffinity = 3
    if obstacle:
        ob = wb.add_body(name="obst_body", pos=[0.15, -0.05, -3.0], mocap=True)
        ob.add_geom(name="obst", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.035, 0.30, 0.06], rgba=[0.3, 0.3, 0.33, 1],
                    contype=0, conaffinity=1, group=0)
    add_cabinet(wb, [0.46, -0.10, ARM_Z - 0.20], 0.0, plinth=plinth)
    return sp


def build_giorgio(buffer=True, cab_front_x=0.48, cab_y=-0.13, handle_above_bench=0.18, yaw=0.0):
    """Giorgio as built + bench B (as scene.build_giorgio) + the chest of drawers standing on the bench in front of the
    right arm. No change to giorgio_model.py: the fixture is added to the transfer scene only."""
    sys.path.insert(0, str(ROOT))
    from giorgio_model import build, GROUP_ENV
    sp = build("gb", hands="gripper", humans=0, fixed_base=True, base="amr", buffer=buffer, coffee=False)
    _mats(sp)
    wb = sp.worldbody
    BENCH_Z = 0.90

    def box(name, pos, half, material, collide=True):
        g = wb.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material, group=GROUP_ENV)
        if collide:
            g.contype = 2; g.conaffinity = 3
        else:
            g.contype = g.conaffinity = 0
        return g
    box("B_top", (0.48, 0.0, BENCH_Z - 0.02), (0.32, 0.85, 0.02), "bench")
    for xl in (0.19, 0.77):
        for yl in (-0.8, 0.8):
            box(f"B_leg_{xl}_{yl}", (xl, yl, (BENCH_Z - 0.04) / 2), (0.025, 0.025, (BENCH_Z - 0.04) / 2), "steel", collide=False)
    box("B_edge", (0.80, 0.0, BENCH_Z - 0.03), (0.002, 0.85, 0.006), "accent", collide=False)
    zb = -DR_HZ - 0.007
    plinth = handle_above_bench + zb      # from the drawer cavity bottom down to the bench top
    add_cabinet(wb, [cab_front_x, cab_y, BENCH_Z + handle_above_bench], yaw, plinth=plinth, group=GROUP_ENV)
    return sp, BENCH_Z


if __name__ == "__main__":
    for nm, sp in (("standalone", build_standalone(obstacle=True)), ("giorgio", build_giorgio()[0])):
        m = sp.compile(); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
        print(nm, "nq", m.nq, "nv", m.nv, "nu", m.nu, "ngeom", m.ngeom, "base", d.body(BASE_BODY).xpos.round(3),
              "handle", d.geom("h_hbar").xpos.round(3))
        for _ in range(500):
            mujoco.mj_step(m, d)
        print("  ncon after 1 s", d.ncon, "drawer q", d.joint("drawer_slide").qpos)
