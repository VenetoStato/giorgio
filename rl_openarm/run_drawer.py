"""Drawer task on CPU (standard MuJoCo): the trained policy (unchanged) or a scripted IK baseline, on
  --robot openarm : the standalone OpenArm 2.0 (official MJCF, right arm + gripper), same randomization as training
  --robot giorgio : Giorgio as built (giorgio_model.build) + the same chest of drawers standing on bench B

Observation and action go through policy_io_drawer.py and are expressed in the frame of 'openarm_right_base_link',
read from the simulator at every step (on the robot: TF base_link -> openarm_right_base_link).

usage:
  python run_drawer.py eval  --robot openarm --n 100 --policy politica_openarm_drawer.pt --json valutazione/drawer_openarm.json
  python run_drawer.py eval  --robot openarm --n 100 --controller scripted --json valutazione/drawer_scripted_openarm.json
  python run_drawer.py video --robot giorgio --seconds 10 --out drawer_giorgio.mp4
"""
import argparse
import json
import math
import os
import sys
import time

import mujoco
import numpy as np
import torch

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import scene
import scene_drawer as sd
from policy_io_drawer import (ACT_DIM, ACT_SCALE, CTRL_DT, EP_LEN, Q_HOME, SUCC_OPEN, SUCC_HOLD, G_OPEN, G_CLOSE,
                              build_obs_np, grip_cmd)
from env_drawer import HANDLE_P, Q_NOISE


def load_policy(path):
    from train import AttoreCritico
    ck = torch.load(path, map_location="cpu")
    ac = AttoreCritico(ck["obs_dim"], ck["act_dim"])
    ac.load_state_dict(ck["modello"])
    ac.eval()
    return ac


def yaw_R(y):
    c, s = math.cos(y), math.sin(y)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def fit_plinth(m, plinth):
    """resize the carcass so that its solid base reaches exactly 'plinth' below the drawer cavity (visual + collision)"""
    D = sd.CAB_DEPTH; zb = -sd.DR_HZ - 0.007; zt = sd.DR_HZ + 0.007
    for n in ("cab_side_l", "cab_side_r"):
        g = m.geom(n).id
        m.geom_pos[g][2] = (zt + sd.TOP_H + zb - plinth) / 2; m.geom_size[g][2] = (zt + sd.TOP_H - zb + plinth) / 2
    g = m.geom("cab_plinth").id; m.geom_pos[g][2] = zb - plinth / 2; m.geom_size[g][2] = plinth / 2
    g = m.geom("cab_plinth_front").id; m.geom_pos[g][2] = zb - plinth / 2; m.geom_size[g][2] = max(plinth / 2 - 0.006, 0.001)


class Runner:
    def __init__(self, robot, policy=None, randomize=True, seed=0, buffer=True, controller="policy"):
        self.robot = robot
        if robot == "openarm":
            sp = sd.build_standalone(obstacle=True)
        else:
            sp, self.bench_z = sd.build_giorgio(buffer=buffer)
        self.m = m = sp.compile()
        # handle geoms are moved/resized at runtime: the compile-time mid-phase BVH would be stale, so disable mid-phase
        # (narrow phase still uses the per-geom bounding spheres at their current positions)
        m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_MIDPHASE
        self.d = d = mujoco.MjData(m)
        self.dik = mujoco.MjData(m)
        self.pol = policy
        self.ctrl_kind = controller
        self.R = randomize
        self.rng = np.random.default_rng(seed)
        self.sub = int(round(CTRL_DT / m.opt.timestep))
        self.qa = np.array([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS])
        self.va = np.array([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS])
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        self.jd = m.joint("drawer_slide").id
        self.qd_ = m.joint("drawer_slide").qposadr[0]; self.vd_ = m.joint("drawer_slide").dofadr[0]
        self.aa = np.array([m.actuator(a).id for a in scene.ARM_ACT])
        self.af = m.actuator(scene.FINGER_ACT).id
        self.lo, self.hi = m.actuator_ctrlrange[self.aa, 0].copy(), m.actuator_ctrlrange[self.aa, 1].copy()
        self.base, self.ee, self.dr = m.body(scene.BASE_BODY).id, m.body(scene.EE_BODY).id, m.body("drawer").id
        self.mid_cab = m.body_mocapid[m.body("cab").id]
        self.mid_table = m.body_mocapid[m.body("table_body").id] if robot == "openarm" else None
        self.mid_obst = m.body_mocapid[m.body("obst_body").id] if robot == "openarm" else None
        self.hg = [m.geom(n).id for n in sd.HANDLE_GEOMS]
        self.gain0, self.bias0 = m.actuator_gainprm.copy(), m.actuator_biasprm.copy()
        self.dr_mass0, self.dr_in0 = float(m.body_mass[self.dr]), m.body_inertia[self.dr].copy()
        self.q_init = d.qpos.copy()
        self.kp0 = m.actuator_gainprm[self.aa, 0].copy()
        self.frame_cb = None

    def base_frame(self):
        return self.d.xpos[self.base].copy(), self.d.xmat[self.base].reshape(3, 3).copy()

    def to_base(self, p):
        bp, bR = self.base_frame()
        return (p - bp) @ bR

    def grasp_state(self, d=None):
        d = d or self.d
        R = d.xmat[self.ee].reshape(3, 3)
        bp, bR = d.xpos[self.base], d.xmat[self.base].reshape(3, 3)
        g = (d.xpos[self.ee] + R @ scene.GRASP_OFS - bp) @ bR
        Rb = bR.T @ R
        return g, -Rb[:, 2], Rb[:, 1]

    def handle_b(self):
        Rd = self.d.xmat[self.dr].reshape(3, 3)
        return self.to_base(self.d.xpos[self.dr] - Rd[:, 0] * self.s)

    def reset(self):
        m, d, rng, R = self.m, self.d, self.rng, self.R
        mujoco.mj_resetData(m, d)
        d.qpos[:] = self.q_init
        if self.robot == "giorgio":
            for k, v in enumerate([0.0, 0.0, 0.0, 2.3, 0.0, 0.0, 0.0]):
                d.joint(f"openarm_left_joint{k + 1}").qpos = v
        mujoco.mj_kinematics(m, d)
        bp, bR = self.base_frame()
        if R:
            if self.robot == "openarm":
                dz = rng.uniform(-0.40, -0.32); edge = rng.uniform(0, 0.20); hz = rng.uniform(0.12, 0.26)
                cx = rng.uniform(0.40, 0.54); cy = rng.uniform(-0.25, 0.05); yaw = rng.uniform(-math.radians(20), math.radians(20))
            else:   # cabinet on bench B, plausible placements in front of the right arm
                dz = self.bench_z - bp[2]; hz = rng.uniform(0.14, 0.22)
                cx = rng.uniform(0.44, 0.52); cy = rng.uniform(-0.20, -0.05); yaw = rng.uniform(-math.radians(15), math.radians(15))
            u = rng.random()
            pk = HANDLE_P[2]; ph = HANDLE_P[0] / (HANDLE_P[0] + HANDLE_P[1]) * (1 - pk)
            kind = 0 if u < ph else (1 if u < 1 - pk else 2)
            L = rng.uniform(0.08, 0.16) if kind == 0 else rng.uniform(0.08, 0.11)
            r = rng.uniform(0.005, 0.012); s = rng.uniform(0.025, 0.045); k = rng.uniform(0.012, 0.022)
            open0 = rng.uniform(0, 0.05)
            hfric = rng.uniform(0.4, 1.0); floss = rng.uniform(1, 15); damp = rng.uniform(2, 40); mass = rng.uniform(0.5, 4.0)
            stiff = rng.uniform(0, 40) if rng.random() < 0.5 else 0.0
            kp = rng.uniform(0.8, 1.2, 8); kv = rng.uniform(0.8, 1.2, 8)
            self.h_delay, self.prop_delay = rng.integers(0, 4), rng.integers(0, 2)
            self.act_delay = rng.random() < 0.3
            self.h_bias = (rng.random(3) - 0.5) * 0.015
            yerr = rng.uniform(-math.radians(3), math.radians(3)); serr = (rng.random(3) - 0.5) * 0.004
            obst = self.robot == "openarm" and rng.random() < 0.5
            ox, oy, oh = rng.uniform(0.12, 0.20), rng.uniform(-0.15, 0.05), rng.uniform(0.04, 0.11)
        else:
            dz = scene.TABLE_DZ if self.robot == "openarm" else self.bench_z - bp[2]
            edge, hz, cx, cy, yaw = 0.08, 0.18, 0.47 if self.robot == "openarm" else 0.48, -0.10, 0.0
            kind, L, r, s, k, open0 = 0, 0.12, 0.008, 0.035, 0.017, 0.0
            hfric, floss, damp, mass, stiff = 0.8, 6.0, 15.0, 1.5, 0.0
            kp = kv = np.ones(8)
            self.h_delay = self.prop_delay = 0; self.act_delay = False; self.h_bias = np.zeros(3)
            yerr, serr, obst = 0.0, np.zeros(3), False
            ox = oy = oh = 0
        self.kind, self.s = kind, s
        if self.robot == "openarm":
            d.mocap_pos[self.mid_table] = [bp[0] + edge + 0.34, d.mocap_pos[self.mid_table][1], bp[2] + dz - 0.02]
            ox = min(ox, cx - 0.22)
            d.mocap_pos[self.mid_obst] = [bp[0] + ox, bp[1] + oy, bp[2] + dz + oh - 0.06] if obst else [0, 0, -3]
        cab_b = np.array([cx, cy, dz + hz])
        d.mocap_pos[self.mid_cab] = bp + bR @ cab_b
        Rc = yaw_R(yaw)
        d.mocap_quat[self.mid_cab] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
        fit_plinth(m, hz + (-sd.DR_HZ - 0.007))          # carcass stands on the table / bench
        sd.set_handle_cpu(m, kind, L, r, s, k)
        for g in self.hg:
            m.geom_friction[g][0] = hfric
        m.dof_frictionloss[self.vd_] = floss; m.dof_damping[self.vd_] = damp; m.jnt_stiffness[self.jd] = stiff
        m.body_mass[self.dr] = mass; m.body_inertia[self.dr] = self.dr_in0 * mass / self.dr_mass0
        m.actuator_gainprm[:] = self.gain0; m.actuator_biasprm[:] = self.bias0
        for kk, ai in enumerate(list(self.aa) + [self.af]):
            m.actuator_gainprm[ai, 0] *= kp[kk]; m.actuator_biasprm[ai, 1] *= kp[kk]; m.actuator_biasprm[ai, 2] *= kv[kk]
        self.pull_t = -(bR.T @ Rc)[:, 0]          # base frame (cabinet yaw is about the vertical, base is upright)
        bar = Rc[:, 1] if kind == 0 else (np.array([0, 0, 1.0]) if kind == 1 else np.zeros(3))
        Re = yaw_R(yerr)
        self.pull_v = Re @ self.pull_t
        self.bar_v = Re @ (bR.T @ bar)
        self.hsize_v = np.array([2 * k if kind == 2 else L, k if kind == 2 else r, s]) + serr
        qh = np.clip(np.array(Q_HOME) + (rng.random(7) - 0.5) * 2 * np.array(Q_NOISE), self.lo, self.hi)
        d.qpos[self.qa] = qh
        d.qpos[self.qf] = G_OPEN
        d.qpos[self.qd_] = open0
        d.ctrl[:] = 0
        for i in range(m.nu):
            if m.actuator_trntype[i] == mujoco.mjtTrn.mjTRN_JOINT:
                d.ctrl[i] = d.qpos[m.jnt_qposadr[m.actuator_trnid[i, 0]]]
        d.ctrl[self.aa] = qh; d.ctrl[self.af] = G_OPEN
        mujoco.mj_forward(m, d)
        self.target, self.gtarget = qh.copy(), G_OPEN
        self.last_a = np.zeros(ACT_DIM); self.prev_a = np.zeros(ACT_DIM)
        hv = np.r_[self.handle_b() + self.h_bias, open0]
        self.h_hist = [hv] * 4
        prop = np.r_[qh, np.zeros(7), G_OPEN]
        self.prop_hist = [prop, prop]
        self.hold, self.success, self.t, self.t_success = 0, False, 0, None
        self.open0, self.max_open = open0, open0
        self.info = dict(kind=["hbar", "vbar", "knob"][kind], L=round(L, 3), standoff=round(s, 3), cab_xy_base=[round(cx, 3), round(cy, 3)],
                         handle_z_base=round(dz + hz, 3), yaw_deg=round(math.degrees(yaw), 1), friction_N=round(floss, 1),
                         damping=round(damp, 1), mass=round(mass, 2), spring=round(stiff, 1), open0_cm=round(100 * open0, 1),
                         obstacle=bool(obst))
        if self.ctrl_kind == "scripted":
            self.script_init()

    def push_hist(self):
        rng = self.rng
        noise = 0.003 * rng.standard_normal(4) if self.R else 0
        self.h_hist = [np.r_[self.handle_b() + self.h_bias, self.d.qpos[self.qd_]] + noise] + self.h_hist[:3]
        d = self.d
        prop = np.r_[d.qpos[self.qa], d.qvel[self.va], d.qpos[self.qf[0]]]
        if self.R:
            prop = prop + np.r_[0.003 * rng.standard_normal(7), 0.05 * rng.standard_normal(7), 0.01 * rng.standard_normal(1)]
        self.prop_hist = [prop, self.prop_hist[0]]

    def obs(self):
        hv = self.h_hist[self.h_delay]
        prop = self.prop_hist[self.prop_delay]
        g, ap, fi = self.grasp_state()
        return build_obs_np(prop[:7], prop[7:14], prop[14], self.target, self.gtarget, g, ap, fi, hv[:3], self.pull_v,
                            self.bar_v, self.hsize_v, hv[3], self.last_a)

    # ---------------- scripted IK baseline ----------------
    def script_init(self):
        p = self.pull_v / np.linalg.norm(self.pull_v)
        a = -p
        if self.kind == 0:
            f = np.array([0, 0, 1.0])
        else:
            f = np.cross([0, 0, 1.0], a); f /= np.linalg.norm(f)
        f = f - a * (f @ a); f /= np.linalg.norm(f)
        z = -a; y = f; x = np.cross(y, z)
        Rd = np.stack([x, y, z], 1)
        # choose the finger-axis sign that needs the smaller wrist rotation
        _, _, fi = self.grasp_state()
        if fi @ f < 0:
            Rd = np.stack([-x, -y, z], 1)
        self.sc_R = Rd
        self.sc_p = p
        self.sc_off = np.zeros(3)

    def ik(self, p_des_b, R_des_b, q0, iters=40):
        m, d = self.m, self.dik
        d.qpos[:] = self.d.qpos; d.mocap_pos[:] = self.d.mocap_pos; d.mocap_quat[:] = self.d.mocap_quat
        q = q0.copy()
        bp, bR = self.base_frame()
        p_des = bp + bR @ p_des_b; R_des = bR @ R_des_b
        jp = np.zeros((3, m.nv)); jr = np.zeros((3, m.nv))
        for _ in range(iters):
            d.qpos[self.qa] = q
            mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
            R = d.xmat[self.ee].reshape(3, 3)
            p = d.xpos[self.ee] + R @ scene.GRASP_OFS
            ep = p_des - p
            er = np.zeros(3); mujoco.mju_mat2Quat(qq := np.zeros(4), (R_des @ R.T).flatten()); mujoco.mju_quat2Vel(er, qq, 1.0)
            mujoco.mj_jac(m, d, jp, jr, p, self.ee)
            J = np.r_[jp[:, self.va], 0.5 * jr[:, self.va]]
            e = np.r_[ep, 0.5 * er]
            if np.linalg.norm(ep) < 1e-4 and np.linalg.norm(er) < 1e-3:
                break
            dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(6), e)
            q = np.clip(q + np.clip(dq, -0.2, 0.2), self.lo, self.hi)
        return q

    def script_action(self):
        """pregrasp 10 cm in front of the perceived handle -> approach -> close -> pull 20 cm along the perceived axis.
        Perception (with the same bias/noise/latency as the policy) is re-read at every step until the gripper closes."""
        t = self.t * CTRL_DT
        hv = self.h_hist[self.h_delay]
        p = self.sc_p
        depth = -float(os.environ.get("SC_DEPTH", "0.0"))      # >0: grasp point beyond the perceived handle centre
        if t < 2.3:
            self.sc_h = hv[:3].copy()
        h = self.sc_h + p * depth
        if t < 1.2:
            x, g = h + 0.10 * p, -1.0
        elif t < 2.2:
            x, g = h + 0.10 * p * (1 - (t - 1.2) / 1.0), -1.0
        elif t < 2.8:
            x, g = h, 1.0
        else:
            x, g = h + p * min(0.20, 0.07 * (t - 2.8)), 1.0
        # gravity feed-forward as a set-point offset (nominal kp, the true per-episode gains are unknown to the script):
        # the official MJCF has no gravity compensation, so plain position servos sag by 2-3 cm.
        q = self.ik(x, self.sc_R, self.q_ik if hasattr(self, "q_ik") and self.t > 1 else self.target)
        self.q_ik = q
        q = np.clip(q + self.d.qfrc_bias[self.va] / self.kp0, self.lo, self.hi)
        a = np.zeros(ACT_DIM)
        a[:7] = np.clip((q - self.target) / ACT_SCALE, -1, 1)
        a[7] = g
        return a

    # ------------------------------------------------------
    def step(self):
        if self.ctrl_kind == "scripted":
            a = self.script_action()
        else:
            o = torch.from_numpy(self.obs())[None]
            a = np.clip(self.pol.act_det(o)[0].numpy(), -1, 1)
        a_eff = self.prev_a if self.act_delay else a
        self.prev_a = a.copy(); self.last_a = a.copy()
        self.target = np.clip(self.target + ACT_SCALE * a_eff[:7], self.lo, self.hi)
        self.gtarget = grip_cmd(a_eff[7])
        self.d.ctrl[self.aa] = self.target
        self.d.ctrl[self.af] = self.gtarget
        for _ in range(self.sub):
            mujoco.mj_step(self.m, self.d)
            if self.frame_cb:
                self.frame_cb()
        self.t += 1
        self.push_hist()
        op = float(self.d.qpos[self.qd_])
        self.max_open = max(self.max_open, op)
        self.hold = self.hold + 1 if op >= SUCC_OPEN else 0
        if self.hold >= SUCC_HOLD and not self.success:
            self.success, self.t_success = True, self.t * CTRL_DT
        return op

    def episode(self, ep_len=EP_LEN):
        self.reset()
        for _ in range(ep_len):
            self.step()
        return dict(success=bool(self.success), max_open_cm=round(100 * self.max_open, 1),
                    final_open_cm=round(100 * float(self.d.qpos[self.qd_]), 1), t_success_s=self.t_success, **self.info)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 3), round(c + h, 3)]


def evaluate(a):
    pol = load_policy(a.policy) if a.controller == "policy" else None
    torch.set_num_threads(1)
    R = Runner(a.robot, pol, randomize=not a.nominal, seed=a.seed, buffer=not a.no_buffer, controller=a.controller)
    res = []
    t0 = time.time()
    for i in range(a.n):
        res.append(R.episode())
        if (i + 1) % 10 == 0:
            print(f"  {a.robot}/{a.controller}: {i + 1}/{a.n} successes {sum(x['success'] for x in res)}  ({time.time() - t0:.0f} s)", flush=True)
    k = sum(r["success"] for r in res)
    by = {}
    for kind in ("hbar", "vbar", "knob"):
        sub = [r for r in res if r["kind"] == kind]
        if sub:
            by[kind] = f"{sum(r['success'] for r in sub)}/{len(sub)}"
    out = dict(task="drawer", robot=a.robot, controller=a.controller,
               policy=os.path.basename(a.policy) if a.controller == "policy" else None,
               giorgio_front_tray=(not a.no_buffer) if a.robot == "giorgio" else None, episodes=a.n,
               randomized=not a.nominal, seed=a.seed, success_rate=round(k / a.n, 4), successes=k, wilson95=wilson(k, a.n),
               success_by_handle=by, mean_max_opening_cm=round(float(np.mean([r["max_open_cm"] for r in res])), 1),
               mean_time_to_success_s=round(float(np.mean([r["t_success_s"] for r in res if r["success"]])), 2) if k else None,
               criterion=f"drawer opened >= {SUCC_OPEN * 100:.0f} cm (from fully closed) for >= {SUCC_HOLD * CTRL_DT:.2f} s "
                         f"continuously, within a {EP_LEN * CTRL_DT:.0f} s episode",
               episodes_detail=res)
    print(json.dumps({k_: v for k_, v in out.items() if k_ != "episodes_detail"}, indent=1))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)


def video(a):
    import imageio
    pol = load_policy(a.policy) if a.controller == "policy" else None
    R = Runner(a.robot, pol, randomize=not a.nominal, seed=a.seed, buffer=not a.no_buffer, controller=a.controller)
    m, d = R.m, R.d
    W, H = 1920, 1080
    ren = mujoco.Renderer(m, H, W)
    opt = mujoco.MjvOption()
    cam = mujoco.MjvCamera()
    lk = [float(v) for v in a.cam.split(",")] if a.cam else None
    if a.robot == "openarm":
        cam.lookat[:] = [0.30, -0.12, scene.ARM_Z - 0.17]; cam.distance = 1.35; cam.azimuth = 235; cam.elevation = -18
    else:
        cam.lookat[:] = [0.30, -0.14, 1.06]; cam.distance = 1.55; cam.azimuth = 228; cam.elevation = -16
    if lk:
        cam.lookat[:] = lk[:3]; cam.distance, cam.azimuth, cam.elevation = lk[3], lk[4], lk[5]
    writer = imageio.get_writer(a.out, fps=30, quality=8, macro_block_size=8)
    state = {"tn": 0.0, "n": 0}
    nframes = int(a.seconds * 30)

    def cb():
        if d.time + 1e-9 >= state["tn"] and state["n"] < nframes:
            state["tn"] += 1 / 30; state["n"] += 1
            ren.update_scene(d, cam, opt)
            writer.append_data(ren.render())
    eps = []
    skip = [int(x) for x in a.skip.split(",")] if a.skip else []
    while state["n"] < nframes:
        R.frame_cb = None
        R.reset()
        if len(eps) + len([1 for _ in []]) in skip or (a.only_fail and False):
            pass
        R.frame_cb = cb; state["tn"] = d.time
        for _ in range(int(a.ep_seconds / CTRL_DT)):
            R.step()
            if state["n"] >= nframes:
                break
        eps.append(dict(success=R.success, max_open_cm=round(100 * R.max_open, 1), **R.info))
        print("  episode", len(eps), eps[-1], flush=True)
    writer.close()
    print("video:", a.out, state["n"], "frames")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["eval", "video"])
    ap.add_argument("--robot", default="openarm", choices=["openarm", "giorgio"])
    ap.add_argument("--controller", default="policy", choices=["policy", "scripted"])
    ap.add_argument("--policy", default=os.path.join(QUI, "politica_openarm_drawer.pt"))
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--nominal", action="store_true", help="no randomization/noise/latency")
    ap.add_argument("--json", default="")
    ap.add_argument("--no_buffer", action="store_true")
    ap.add_argument("--out", default="out.mp4")
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--ep_seconds", type=float, default=5.0)
    ap.add_argument("--cam", default="", help="lookat_x,y,z,distance,azimuth,elevation")
    ap.add_argument("--skip", default="")
    ap.add_argument("--only_fail", action="store_true")
    a = ap.parse_args()
    evaluate(a) if a.mode == "eval" else video(a)
