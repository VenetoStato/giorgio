"""'Open the cabinet' scenes: a benchtop cabinet whose target compartment is closed EITHER by a drawer OR by a hinged
door (hinge on the left or on the right). The articulation is not told to the policy.

Cabinet frame ("cab", mocap body): origin = centre of the closed front face of the target compartment, x axis INTO the
cabinet. Three mechanism bodies share the compartment; in each episode one is active and the other two are parked
PARK2 m below (geoms moved, so they never collide):
  "drawer"  slide joint "drawer_slide" along -x (value = opening, m)
  "door_l"  hinge on the robot's LEFT edge  (y = +HW), joint "door_l_hinge" (value = opening angle, rad, > 0 opens)
  "door_r"  hinge on the robot's RIGHT edge (y = -HW), joint "door_r_hinge"
Handles (on every mechanism body, unused handle geoms parked like the bodies): 0 horizontal bar, 1 vertical bar, 2 knob.
Drawers: handle centred. Doors: handle near the free edge (vertical bar or knob).
"""
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

import scene
from scene import ARM_Z, TABLE_DZ, BASE_BODY

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

CAB_DEPTH = 0.33
HW = 0.15                 # half width of the compartment front
HZ = 0.09                 # half height of the compartment front
T = 0.018                 # front thickness
WALL = 0.02
TOP_H = 0.12              # fixed upper drawer above the compartment
PARK = -1.0               # unused handle geoms: z offset in the mechanism frame
PARK2 = -2.0              # unused mechanism bodies: all geoms z offset
DOOR_EDGE = 0.035         # door handle centre distance from the free edge
L_MAX, R_MAX, S_MAX, K_MAX = 0.16, 0.012, 0.045, 0.022
MECHS = ["drawer", "door_l", "door_r"]
HNAMES = ["hbar", "vbar", "knob", "post1", "post2"]


def _mats(sp):
    sp.add_material(name="cab_body", rgba=[0.86, 0.85, 0.82, 1], reflectance=0.05, specular=0.3)
    sp.add_material(name="cab_front", rgba=[0.30, 0.42, 0.52, 1], reflectance=0.1, specular=0.4)
    sp.add_material(name="cab_inner", rgba=[0.72, 0.62, 0.48, 1], reflectance=0.02)
    sp.add_material(name="cab_handle", rgba=[0.75, 0.76, 0.78, 1], reflectance=0.4, specular=0.9, shininess=0.9)


def handle_center(mech):
    """handle centre (before the standoff) in the mechanism body frame"""
    if mech == "drawer":
        return np.array([0.0, 0.0, 0.0])
    if mech == "door_l":     # body origin on the hinge (y=+HW): free edge at y = -2HW
        return np.array([0.0, -2 * HW + DOOR_EDGE, 0.0])
    return np.array([0.0, 2 * HW - DOOR_EDGE, 0.0])


def mech_origin(mech):
    return {"drawer": [0, 0, 0], "door_l": [0, HW, 0], "door_r": [0, -HW, 0]}[mech]


def add_cabinet(wb, pos, yaw=0.0, plinth=0.5, group=0):
    q = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    cab = wb.add_body(name="cab", pos=list(pos), quat=q, mocap=True)
    B = mujoco.mjtGeom.mjGEOM_BOX
    C, Y = mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_CYLINDER

    def cg(name, p, s, mat="cab_body", collide=True):
        return cab.add_geom(name=name, type=B, pos=list(p), size=list(s), material=mat, contype=0,
                            conaffinity=1 if collide else 0, group=group, friction=[0.6, 0.01, 0.001])
    D = CAB_DEPTH
    zb, zt = -HZ - 0.006, HZ + 0.006
    OW = HW + 0.006 + WALL
    cg("cab_side_l", (D / 2, OW - WALL / 2, (zt + TOP_H + zb - plinth) / 2), (D / 2, WALL / 2, (zt + TOP_H - zb + plinth) / 2))
    cg("cab_side_r", (D / 2, -OW + WALL / 2, (zt + TOP_H + zb - plinth) / 2), (D / 2, WALL / 2, (zt + TOP_H - zb + plinth) / 2))
    cg("cab_top", (D / 2, 0, zt + TOP_H / 2), (D / 2, OW - WALL, TOP_H / 2))
    cg("cab_plinth", (D / 2, 0, zb - plinth / 2), (D / 2, OW - WALL, plinth / 2))
    cg("cab_back", (D - 0.01, 0, 0), (0.01, OW - WALL, (zt - zb) / 2))
    cg("cab_upper_front", (-0.002, 0, zt + TOP_H / 2), (0.004, HW, TOP_H / 2 - 0.01), mat="cab_front", collide=False)
    cab.add_geom(name="cab_upper_handle", type=C, pos=[-0.03, 0, zt + TOP_H / 2], quat=[0.7071068, 0.7071068, 0, 0],
                 size=[0.008, 0.045, 0], material="cab_handle", contype=0, conaffinity=1, group=group)
    for yy in (-0.04, 0.04):
        cab.add_geom(type=B, pos=[-0.017, yy, zt + TOP_H / 2], size=[0.015, 0.005, 0.005], material="cab_handle",
                     contype=0, conaffinity=0, group=group)
    cg("cab_plinth_front", (-0.002, 0, zb - plinth / 2), (0.004, HW, plinth / 2 - 0.006), mat="cab_front", collide=False)

    hk = dict(mat="cab_handle", priority=2, friction=[0.8, 0.01, 0.001], condim=4, solref=[0.004, 1])
    bodies = {}
    for mech in MECHS:
        o = mech_origin(mech)
        b = cab.add_body(name=mech, pos=list(o))
        if mech == "drawer":
            b.add_joint(name="drawer_slide", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[-1, 0, 0], range=[0, 0.28],
                        limited=mujoco.mjtLimited.mjLIMITED_TRUE, damping=10.0, frictionloss=4.0, armature=0.05)
            b.explicitinertial = True; b.mass = 1.5; b.inertia = [0.02, 0.02, 0.03]; b.ipos = [0.16, 0, -0.02]
        else:
            ax = [0, 0, -1] if mech == "door_l" else [0, 0, 1]
            b.add_joint(name=f"{mech}_hinge", type=mujoco.mjtJoint.mjJNT_HINGE, axis=ax, range=[0, math.radians(110)],
                        limited=mujoco.mjtLimited.mjLIMITED_TRUE, damping=0.5, frictionloss=0.5, armature=0.01)
            b.explicitinertial = True; b.mass = 1.0
            b.ipos = [T / 2, -HW if mech == "door_l" else HW, 0]; b.inertia = [0.004, 0.008, 0.01]

        def dg(name, p, s, mat="cab_inner", typ=B, **kw):
            return b.add_geom(name=f"{mech}_{name}", type=typ, pos=list(p), size=list(s), material=mat, contype=0,
                              conaffinity=1, group=group, mass=0, **kw)
        if mech == "drawer":
            dg("front", (T / 2, 0, 0), (T / 2, HW - 0.002, HZ), mat="cab_front")
            dg("side_l", (0.16, HW - 0.02, -0.01), (0.14, 0.006, HZ - 0.02))
            dg("side_r", (0.16, -HW + 0.02, -0.01), (0.14, 0.006, HZ - 0.02))
            dg("bottom", (0.16, 0, -HZ + 0.012), (0.14, HW - 0.02, 0.004))
            dg("back", (0.295, 0, -0.01), (0.006, HW - 0.02, HZ - 0.02))
        else:
            yc = -HW if mech == "door_l" else HW
            dg("front", (T / 2, yc, 0), (T / 2, HW - 0.003, HZ), mat="cab_front")
            # hinge knuckles (visual)
            for zz in (-HZ + 0.02, HZ - 0.02):
                b.add_geom(type=Y, pos=[-0.004, 0, zz], size=[0.006, 0.015, 0], material="cab_handle", contype=0,
                           conaffinity=0, group=group, mass=0)
        hc = handle_center(mech)
        dg("hbar", (-0.03 + hc[0], hc[1], hc[2]), (R_MAX, L_MAX / 2, 0), typ=C, quat=[0.7071068, 0.7071068, 0, 0], **hk)
        dg("vbar", (-0.03 + hc[0], hc[1], PARK), (R_MAX, L_MAX / 2, 0), typ=C, **hk)
        dg("knob", (-0.03 + hc[0], hc[1], PARK), (K_MAX, 0.009, 0), typ=Y, quat=[0.7071068, 0, 0.7071068, 0], **hk)
        dg("post1", (-S_MAX / 2, hc[1] + L_MAX / 2, 0), (S_MAX / 2, 0.008, 0.008), **hk)
        dg("post2", (-S_MAX / 2, hc[1] - L_MAX / 2, 0), (S_MAX / 2, 0.008, 0.008), **hk)
        bodies[mech] = b
    return cab, bodies


def handle_layout(kind, L, r, s, k, hc):
    """pos/size of the 5 handle geoms (mechanism body frame) for one handle centred at hc. kind 0 hbar, 1 vbar, 2 knob."""
    P = PARK
    x, y, z = hc
    out = {}
    out["hbar"] = ((x - s, y, z + (0 if kind == 0 else P)), (r, L / 2, 0))
    out["vbar"] = ((x - s, y, z + (0 if kind == 1 else P)), (r, L / 2, 0))
    out["knob"] = ((x - s, y, z + (0 if kind == 2 else P)), (k, 0.009, 0))
    if kind == 0:
        out["post1"] = ((x - s / 2, y + L / 2 - 0.006, z), (s / 2, 0.006, 0.006)); out["post2"] = ((x - s / 2, y - L / 2 + 0.006, z), (s / 2, 0.006, 0.006))
    elif kind == 1:
        out["post1"] = ((x - s / 2, y, z + L / 2 - 0.006), (s / 2, 0.006, 0.006)); out["post2"] = ((x - s / 2, y, z - L / 2 + 0.006), (s / 2, 0.006, 0.006))
    else:
        out["post1"] = ((x - s / 2, y, z), (s / 2, 0.008, 0.008)); out["post2"] = ((x - s / 2, y, z + P), (s / 2, 0.006, 0.006))
    return out


def configure_cpu(m, mech, kind, L, r, s, k, geom_pos0):
    """CPU: activate one mechanism (+ its handle), park the others. geom_pos0 = m.geom_pos copy at load."""
    for mm in MECHS:
        bid = m.body(mm).id
        for g in range(m.ngeom):
            if m.geom_bodyid[g] == bid:
                m.geom_pos[g] = geom_pos0[g] + ([0, 0, 0] if mm == mech else [0, 0, PARK2])
        if mm == mech:
            for n, (p, sz) in handle_layout(kind, L, r, s, k, handle_center(mm)).items():
                g = m.geom(f"{mm}_{n}").id
                m.geom_pos[g] = p; m.geom_size[g] = sz


def fit_plinth(m, plinth):
    D = CAB_DEPTH; zb, zt = -HZ - 0.006, HZ + 0.006
    for n in ("cab_side_l", "cab_side_r"):
        g = m.geom(n).id
        m.geom_pos[g][2] = (zt + TOP_H + zb - plinth) / 2; m.geom_size[g][2] = (zt + TOP_H - zb + plinth) / 2
    g = m.geom("cab_plinth").id; m.geom_pos[g][2] = zb - plinth / 2; m.geom_size[g][2] = plinth / 2
    g = m.geom("cab_plinth_front").id; m.geom_pos[g][2] = zb - plinth / 2; m.geom_size[g][2] = max(plinth / 2 - 0.006, 0.001)


def build_standalone(obstacle=False, plinth=0.5):
    sp = scene.build_standalone(obstacle=False)
    sp.delete(sp.body("cube"))
    _mats(sp)
    wb = sp.worldbody
    t = sp.geom("table"); t.contype = 2; t.conaffinity = 3
    if obstacle:
        ob = wb.add_body(name="obst_body", pos=[0.15, -0.05, -3.0], mocap=True)
        ob.add_geom(name="obst", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.035, 0.30, 0.06], rgba=[0.3, 0.3, 0.33, 1],
                    contype=0, conaffinity=1, group=0)
    add_cabinet(wb, [0.50, -0.10, ARM_Z - 0.20], 0.0, plinth=plinth)
    return sp


def build_giorgio(buffer=True, cab_front_x=0.50, cab_y=-0.13, handle_above_bench=0.20, yaw=0.0):
    """Giorgio as built + bench B + the same cabinet standing on the bench in front of the right arm (transfer scene
    only; giorgio_model.py is not modified)."""
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
    plinth = handle_above_bench - HZ - 0.006
    add_cabinet(wb, [cab_front_x, cab_y, BENCH_Z + handle_above_bench], yaw, plinth=plinth, group=GROUP_ENV)
    return sp, BENCH_Z


if __name__ == "__main__":
    for nm, sp in (("standalone", build_standalone(obstacle=True)), ("giorgio", build_giorgio()[0])):
        m = sp.compile(); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
        print(nm, "nq", m.nq, "nv", m.nv, "nu", m.nu, "ngeom", m.ngeom, "base", d.body(BASE_BODY).xpos.round(3))
        for _ in range(500):
            mujoco.mj_step(m, d)
        print("  ncon", d.ncon, "q", d.qpos[-3:])
