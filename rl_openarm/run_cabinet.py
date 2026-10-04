"""'Open the cabinet' (drawer OR hinged door) on CPU (standard MuJoCo), with the trained policy (unchanged) or a
scripted IK baseline, on
  --robot openarm : standalone OpenArm 2.0 (official MJCF, right arm + gripper), training randomization
  --robot giorgio : Giorgio as built (giorgio_model.build) + the same cabinet standing on bench B

Controllers:
  policy           the trained network (policy_io_cabinet.py interface, arm-base frame)
  scripted         IK + gravity feed-forward: pre-grasp 10 cm in front of the perceived handle, approach, close,
                   pull 20 cm straight along the perceived panel normal (the classic scripted drawer opener)
  scripted_follow  same grasp, but during the pull it re-reads the handle and the panel normal from vision every step
                   and keeps pulling along the CURRENT normal with the gripper re-oriented to it (follows a door's arc)
Both scripted controllers get exactly the policy's inputs (same noise, bias, latency) and the same action interface.

usage:
  python run_cabinet.py eval --robot openarm --n 100 --json valutazione/cabinet_openarm.json
  python run_cabinet.py eval --robot openarm --n 100 --controller scripted --json valutazione/cabinet_scripted_openarm.json
  python run_cabinet.py video --robot giorgio --seconds 10 --out cabinet_giorgio.mp4
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
import scene_cabinet as sc
from policy_io_cabinet import (ACT_DIM, ACT_SCALE, CTRL_DT, EP_LEN, Q_HOME, DRAWER_SUCC, DOOR_SUCC, DRAWER_GOAL, DOOR_GOAL,
                               SUCC_HOLD, G_OPEN, build_obs_np, grip_cmd)
from env_cabinet import MECH_P, Q_NOISE

MECH_NAMES = ["drawer", "door_left_hinge", "door_right_hinge"]
KIND_NAMES = ["hbar", "vbar", "knob"]


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


class Runner:
    def __init__(self, robot, policy=None, randomize=True, seed=0, buffer=True, controller="policy", force=None):
        self.robot = robot
        if robot == "openarm":
            sp = sc.build_standalone(obstacle=True)
        else:
            sp, self.bench_z = sc.build_giorgio(buffer=buffer)
        self.m = m = sp.compile()
        # handle/mechanism geoms are moved and resized at runtime: disable the (compile-time) mid-phase BVH
        m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_MIDPHASE
        self.d = d = mujoco.MjData(m)
        self.dik = mujoco.MjData(m)
        self.pol = policy
        self.ctrl_kind = controller
        self.R = randomize
        self.force = force or {}
        self.rng = np.random.default_rng(seed)
        self.sub = int(round(CTRL_DT / m.opt.timestep))
        self.qa = np.array([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS])
        self.va = np.array([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS])
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        jn = ["drawer_slide", "door_l_hinge", "door_r_hinge"]
        self.mj = [m.joint(j).id for j in jn]
        self.mq = [m.joint(j).qposadr[0] for j in jn]
        self.mv = [m.joint(j).dofadr[0] for j in jn]
        self.mb = [m.body(n).id for n in sc.MECHS]
        self.aa = np.array([m.actuator(a).id for a in scene.ARM_ACT])
        self.af = m.actuator(scene.FINGER_ACT).id
        self.lo, self.hi = m.actuator_ctrlrange[self.aa, 0].copy(), m.actuator_ctrlrange[self.aa, 1].copy()
        self.base, self.ee = m.body(scene.BASE_BODY).id, m.body(scene.EE_BODY).id
        self.mid_cab = m.body_mocapid[m.body("cab").id]
        self.mid_table = m.body_mocapid[m.body("table_body").id] if robot == "openarm" else None
        self.mid_obst = m.body_mocapid[m.body("obst_body").id] if robot == "openarm" else None
        self.hg = [[m.geom(f"{mm}_{h}").id for h in sc.HNAMES] for mm in sc.MECHS]
        self.gain0, self.bias0 = m.actuator_gainprm.copy(), m.actuator_biasprm.copy()
        self.mass0 = [float(m.body_mass[b]) for b in self.mb]
        self.in0 = [m.body_inertia[b].copy() for b in self.mb]
        self.gpos0 = m.geom_pos.copy()
        self.rgba0 = m.geom_rgba.copy()
        self.conaff0 = m.geom_conaffinity.copy()
        self.q_init = d.qpos.copy()
        self.kp0 = m.actuator_gainprm[self.aa, 0].copy()
        self.frame_cb = None

    def base_frame(self):
        return self.d.xpos[self.base].copy(), self.d.xmat[self.base].reshape(3, 3).copy()

    def to_base(self, p):
        bp, bR = self.base_frame()
        return (p - bp) @ bR

    def grasp_state(self):
        d = self.d
        R = d.xmat[self.ee].reshape(3, 3)
        bp, bR = d.xpos[self.base], d.xmat[self.base].reshape(3, 3)
        g = (d.xpos[self.ee] + R @ scene.GRASP_OFS - bp) @ bR
        Rb = bR.T @ R
        return g, -Rb[:, 2], Rb[:, 1]

    def handle(self):
        """true handle point, outward normal, bar axis (base frame), mechanism value"""
        b = self.mb[self.mech]
        bR_w = self.d.xmat[b].reshape(3, 3)
        loc = sc.handle_center(sc.MECHS[self.mech]) + np.array([-self.s, 0, 0])
        hw = self.d.xpos[b] + bR_w @ loc
        _, bR = self.base_frame()
        Rb = bR.T @ bR_w
        normal = -Rb[:, 0]
        bar = Rb[:, 1] if self.kind == 0 else (Rb[:, 2] if self.kind == 1 else np.zeros(3))
        return self.to_base(hw), normal, bar, float(self.d.qpos[self.mq[self.mech]])

    def _configure(self, mech, kind, L, r, s, k):
        m = self.m
        sc.configure_cpu(m, mech=sc.MECHS[mech], kind=kind, L=L, r=r, s=s, k=k, geom_pos0=self.gpos0)
        m.geom_rgba[:] = self.rgba0
        m.geom_conaffinity[:] = self.conaff0
        # hide parked geoms in the renders
        for mi, b in enumerate(self.mb):
            for g in range(m.ngeom):
                if m.geom_bodyid[g] == b and (mi != mech or m.geom_pos[g][2] < sc.PARK / 2):
                    m.geom_rgba[g] = [0, 0, 0, 0]
                    m.geom_conaffinity[g] = 0          # parked: no contacts (Giorgio's floor collides)
                    m.geom_pos[g][2] -= 5.0

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
                cx = rng.uniform(0.44, 0.56); cy = rng.uniform(-0.20, 0.05); yaw = rng.uniform(-math.radians(20), math.radians(20))
            else:   # cabinet standing on bench B, plausible placements in front of the right arm
                dz = self.bench_z - bp[2]; edge = 0; hz = rng.uniform(0.16, 0.24)
                cx = rng.uniform(0.46, 0.54); cy = rng.uniform(-0.18, -0.05); yaw = rng.uniform(-math.radians(15), math.radians(15))
            u = rng.random()
            mech = 0 if u < MECH_P[0] else (1 if u < MECH_P[0] + MECH_P[1] else 2)
            mech = self.force.get("mech", mech)
            u2 = rng.random()
            kind = (0 if u2 < 0.5 else (1 if u2 < 0.75 else 2)) if mech == 0 else (1 if u2 < 0.6 else 2)
            L = rng.uniform(0.08, 0.16) if kind == 0 else rng.uniform(0.08, 0.11)
            r = rng.uniform(0.005, 0.012); s = rng.uniform(0.025, 0.045); k = rng.uniform(0.012, 0.022)
            open0 = rng.uniform(0, 0.05) if mech == 0 else rng.uniform(0, math.radians(8))
            hfric = rng.uniform(0.4, 1.0)
            spring_on = rng.random() < 0.5
            if mech == 0:
                floss, damp, mass = rng.uniform(1, 15), rng.uniform(2, 40), rng.uniform(0.5, 4.0)
                stiff = rng.uniform(0, 40) if spring_on else 0.0
            else:
                floss, damp, mass = rng.uniform(0.1, 1.5), rng.uniform(0.1, 2.0), rng.uniform(0.6, 2.0)
                stiff = rng.uniform(0, 1.0) if spring_on else 0.0
            kp = rng.uniform(0.8, 1.2, 8); kv = rng.uniform(0.8, 1.2, 8)
            self.h_delay, self.prop_delay = rng.integers(0, 4), rng.integers(0, 2)
            self.act_delay = rng.random() < 0.3
            self.h_bias = (rng.random(3) - 0.5) * 0.015
            yerr = rng.uniform(-math.radians(3), math.radians(3)); serr = (rng.random(3) - 0.5) * 0.004
            obst = self.robot == "openarm" and rng.random() < 0.5
            ox, oy, oh = rng.uniform(0.12, 0.20), rng.uniform(-0.15, 0.05), rng.uniform(0.04, 0.11)
        else:
            dz = scene.TABLE_DZ if self.robot == "openarm" else self.bench_z - bp[2]
            edge, hz, cx, cy, yaw = 0.08, 0.18 if self.robot == "openarm" else 0.20, 0.50, -0.10, 0.0
            mech, kind, L, r, s, k, open0 = 0, 0, 0.12, 0.008, 0.035, 0.017, 0.0
            hfric = 0.8
            floss, damp, mass, stiff = 6.0, 15.0, 1.5, 0.0
            kp = kv = np.ones(8)
            self.h_delay = self.prop_delay = 0; self.act_delay = False; self.h_bias = np.zeros(3)
            yerr, serr, obst, ox, oy, oh = 0.0, np.zeros(3), False, 0, 0, 0
        if not R:
            mech = self.force.get("mech", mech)
            if mech != 0:
                kind, floss, damp, mass, stiff = 1, 0.5, 0.5, 1.0, 0.0
        self.mech, self.kind, self.s = mech, kind, s
        if self.robot == "openarm":
            d.mocap_pos[self.mid_table] = [bp[0] + edge + 0.34, d.mocap_pos[self.mid_table][1], bp[2] + dz - 0.02]
            d.mocap_pos[self.mid_obst] = [bp[0] + ox, bp[1] + oy, bp[2] + dz + oh - 0.06] if obst else [0, 0, -3]
        cab_b = np.array([cx, cy, dz + hz])
        d.mocap_pos[self.mid_cab] = bp + bR @ cab_b
        d.mocap_quat[self.mid_cab] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
        sc.fit_plinth(m, hz - sc.HZ - 0.006)
        self._configure(mech, kind, L, r, s, k)
        for mi in range(3):
            for g in self.hg[mi]:
                m.geom_friction[g][0] = hfric
        jm = self.mj[mech]; vm = self.mv[mech]; bm = self.mb[mech]
        m.dof_frictionloss[vm] = floss; m.dof_damping[vm] = damp; m.jnt_stiffness[jm] = stiff
        m.body_mass[bm] = mass; m.body_inertia[bm] = self.in0[mech] * mass / self.mass0[mech]
        m.actuator_gainprm[:] = self.gain0; m.actuator_biasprm[:] = self.bias0
        for kk, ai in enumerate(list(self.aa) + [self.af]):
            m.actuator_gainprm[ai, 0] *= kp[kk]; m.actuator_biasprm[ai, 1] *= kp[kk]; m.actuator_biasprm[ai, 2] *= kv[kk]
        self.yerr_R = yaw_R(yerr)
        self.hsize_v = np.array([2 * k if kind == 2 else L, k if kind == 2 else r, s]) + serr
        qh = np.clip(np.array(Q_HOME) + (rng.random(7) - 0.5) * 2 * np.array(Q_NOISE), self.lo, self.hi)
        d.qpos[self.qa] = qh
        d.qpos[self.qf] = G_OPEN
        for mi in range(3):
            d.qpos[self.mq[mi]] = open0 if mi == mech else 0.0
        d.ctrl[:] = 0
        for i in range(m.nu):
            if m.actuator_trntype[i] == mujoco.mjtTrn.mjTRN_JOINT:
                d.ctrl[i] = d.qpos[m.jnt_qposadr[m.actuator_trnid[i, 0]]]
        d.ctrl[self.aa] = qh; d.ctrl[self.af] = G_OPEN
        mujoco.mj_forward(m, d)
        self.target, self.gtarget = qh.copy(), G_OPEN
        self.last_a = np.zeros(ACT_DIM); self.prev_a = np.zeros(ACT_DIM)
        hb, _, _, _ = self.handle()
        self.h0 = hb.copy()
        self.h_hist = [hb + self.h_bias] * 4
        prop = np.r_[qh, np.zeros(7), G_OPEN]
        self.prop_hist = [prop, prop]
        self.hold, self.success, self.t, self.t_success = 0, False, 0, None
        self.max_val = open0
        self.info = dict(mechanism=MECH_NAMES[mech], handle=KIND_NAMES[kind], L=round(L, 3), standoff=round(s, 3),
                         cab_xy_base=[round(cx, 3), round(cy, 3)], handle_z_base=round(dz + hz, 3), yaw_deg=round(math.degrees(yaw), 1),
                         friction=round(floss, 2), damping=round(damp, 2), mass=round(mass, 2), spring=round(stiff, 2),
                         open0=round(open0, 3), obstacle=bool(obst))
        if self.ctrl_kind.startswith("scripted"):
            self.sc_init = False

    def push_hist(self):
        rng = self.rng
        hb, _, _, _ = self.handle()
        noise = 0.003 * rng.standard_normal(3) if self.R else 0
        self.h_hist = [hb + self.h_bias + noise] + self.h_hist[:3]
        d = self.d
        prop = np.r_[d.qpos[self.qa], d.qvel[self.va], d.qpos[self.qf[0]]]
        if self.R:
            prop = prop + np.r_[0.003 * rng.standard_normal(7), 0.05 * rng.standard_normal(7), 0.01 * rng.standard_normal(1)]
        self.prop_hist = [prop, self.prop_hist[0]]

    def perceived(self):
        hv = self.h_hist[self.h_delay]
        _, normal, bar, _ = self.handle()
        return hv, self.yerr_R @ normal, self.yerr_R @ bar

    def obs(self):
        hv, nv, bv = self.perceived()
        prop = self.prop_hist[self.prop_delay]
        g, ap, fi = self.grasp_state()
        return build_obs_np(prop[:7], prop[7:14], prop[14], self.target, self.gtarget, g, ap, fi, hv, nv, bv, self.hsize_v,
                            hv - (self.h0 + self.h_bias), self.last_a)

    # ---------------- scripted IK baselines ----------------
    def _grip_R(self, nrm, bar):
        a = -nrm / np.linalg.norm(nrm)
        if np.linalg.norm(bar) > 0.5 and abs(bar[2]) < 0.5:      # horizontal bar: fingers close vertically
            f = np.array([0, 0, 1.0])
        else:                                                     # vertical bar or knob: fingers close horizontally
            f = np.cross([0, 0, 1.0], a)
        f = f - a * (f @ a); f /= np.linalg.norm(f)
        z = -a; y = f; x = np.cross(y, z)
        Rd = np.stack([x, y, z], 1)
        _, _, fi = self.grasp_state()
        if fi @ f < 0:
            Rd = np.stack([-x, -y, z], 1)
        return Rd

    def ik(self, p_des_b, R_des_b, q0, iters=40):
        m, d = self.m, self.dik
        d.qpos[:] = self.d.qpos; d.mocap_pos[:] = self.d.mocap_pos; d.mocap_quat[:] = self.d.mocap_quat
        q = q0.copy()
        bp, bR = self.base_frame()
        p_des = bp + bR @ p_des_b; R_des = bR @ R_des_b
        jp = np.zeros((3, m.nv)); jr = np.zeros((3, m.nv)); qq = np.zeros(4); er = np.zeros(3)
        for _ in range(iters):
            d.qpos[self.qa] = q
            mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
            R = d.xmat[self.ee].reshape(3, 3)
            p = d.xpos[self.ee] + R @ scene.GRASP_OFS
            ep = p_des - p
            mujoco.mju_mat2Quat(qq, (R_des @ R.T).flatten()); mujoco.mju_quat2Vel(er, qq, 1.0)
            if np.linalg.norm(ep) < 1e-4 and np.linalg.norm(er) < 1e-3:
                break
            mujoco.mj_jac(m, d, jp, jr, p, self.ee)
            J = np.r_[jp[:, self.va], 0.5 * jr[:, self.va]]
            e = np.r_[ep, 0.5 * er]
            dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(6), e)
            q = np.clip(q + np.clip(dq, -0.2, 0.2), self.lo, self.hi)
        return q

    def script_action(self):
        t = self.t * CTRL_DT
        hv, nv, bv = self.perceived()
        nv = nv / np.linalg.norm(nv)
        follow = self.ctrl_kind == "scripted_follow"
        if not self.sc_init:
            self.sc_init = True
            self.sc_R = self._grip_R(nv, bv); self.sc_n = nv.copy(); self.q_ik = self.target.copy()
            self.pull_s = 0.0
        if t < 2.3:                       # track the perceived handle until the gripper closes
            self.sc_h = hv.copy(); self.sc_n = nv.copy(); self.sc_R = self._grip_R(nv, bv)
        h, n = self.sc_h, self.sc_n
        Rg = self.sc_R
        if t < 1.2:
            x, g = h + 0.10 * n, -1.0
        elif t < 2.2:
            x, g = h + 0.10 * n * (1 - (t - 1.2) / 1.0), -1.0
        elif t < 2.8:
            x, g = h, 1.0
        else:
            g = 1.0
            if not follow:
                x = h + n * min(0.20, 0.07 * (t - 2.8))
            else:
                # follow: from the CURRENT perceived handle, step along the CURRENT perceived normal
                Rg = self._grip_R(nv, bv)
                self.pull_s = min(self.pull_s + 0.07 * CTRL_DT, 0.30)
                x = hv + nv * 0.03 if self.pull_s < 0.30 else hv
        q = self.ik(x, Rg, self.q_ik)
        self.q_ik = q
        # gravity feed-forward as a set-point offset (nominal kp): the official MJCF has no gravity compensation
        # (Giorgio already compensates gravity motor-side, so no offset there)
        if self.robot == "openarm":
            q = np.clip(q + self.d.qfrc_bias[self.va] / self.kp0, self.lo, self.hi)
        a = np.zeros(ACT_DIM)
        a[:7] = np.clip((q - self.target) / ACT_SCALE, -1, 1)
        a[7] = g
        return a

    # ------------------------------------------------------
    def step(self):
        if self.ctrl_kind.startswith("scripted"):
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
        v = float(self.d.qpos[self.mq[self.mech]])
        self.max_val = max(self.max_val, v)
        ok = v >= (DRAWER_SUCC if self.mech == 0 else DOOR_SUCC)
        self.hold = self.hold + 1 if ok else 0
        if self.hold >= SUCC_HOLD and not self.success:
            self.success, self.t_success = True, self.t * CTRL_DT
        return v

    def result(self):
        v = float(self.d.qpos[self.mq[self.mech]])
        if self.mech == 0:
            mx, fin = dict(max_open_cm=round(100 * self.max_val, 1)), dict(final_open_cm=round(100 * v, 1))
        else:
            mx, fin = dict(max_open_deg=round(math.degrees(self.max_val), 1)), dict(final_open_deg=round(math.degrees(v), 1))
        return dict(success=bool(self.success), t_success_s=self.t_success, **mx, **fin, **self.info)

    def episode(self, ep_len=EP_LEN):
        self.reset()
        for _ in range(ep_len):
            self.step()
        return self.result()


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 3), round(c + h, 3)]


def evaluate(a):
    pol = load_policy(a.policy) if a.controller == "policy" else None
    torch.set_num_threads(1)
    force = {"mech": a.mech} if a.mech is not None else None
    R = Runner(a.robot, pol, randomize=not a.nominal, seed=a.seed, buffer=not a.no_buffer, controller=a.controller, force=force)
    res = []
    t0 = time.time()
    for i in range(a.n):
        res.append(R.episode())
        if (i + 1) % 10 == 0:
            print(f"  {a.robot}/{a.controller}: {i + 1}/{a.n} successes {sum(x['success'] for x in res)}  ({time.time() - t0:.0f} s)", flush=True)
    k = sum(r["success"] for r in res)
    by_mech, by_handle = {}, {}
    for mn in MECH_NAMES:
        sub = [r for r in res if r["mechanism"] == mn]
        if sub:
            kk = sum(r["success"] for r in sub)
            by_mech[mn] = dict(successes=kk, episodes=len(sub), rate=round(kk / len(sub), 3), wilson95=wilson(kk, len(sub)))
    for hn in KIND_NAMES:
        sub = [r for r in res if r["handle"] == hn]
        if sub:
            by_handle[hn] = f"{sum(r['success'] for r in sub)}/{len(sub)}"
    drw = [r for r in res if r["mechanism"] == "drawer"]; dor = [r for r in res if r["mechanism"] != "drawer"]
    out = dict(task="cabinet (drawer or hinged door, articulation not given)", robot=a.robot, controller=a.controller,
               policy=os.path.basename(a.policy) if a.controller == "policy" else None,
               giorgio_front_tray=(not a.no_buffer) if a.robot == "giorgio" else None, episodes=a.n,
               randomized=not a.nominal, seed=a.seed, success_rate=round(k / a.n, 4), successes=k, wilson95=wilson(k, a.n),
               by_mechanism=by_mech, by_handle=by_handle,
               mean_max_drawer_open_cm=round(float(np.mean([r["max_open_cm"] for r in drw])), 1) if drw else None,
               mean_max_door_open_deg=round(float(np.mean([r["max_open_deg"] for r in dor])), 1) if dor else None,
               mean_time_to_success_s=round(float(np.mean([r["t_success_s"] for r in res if r["success"]])), 2) if k else None,
               criterion=f"drawer opened >= {DRAWER_SUCC * 100:.0f} cm or door >= {math.degrees(DOOR_SUCC):.0f} deg (from fully closed), "
                         f"held >= {SUCC_HOLD * CTRL_DT:.2f} s continuously, within a {EP_LEN * CTRL_DT:.0f} s episode",
               episodes_detail=res)
    print(json.dumps({k_: v for k_, v in out.items() if k_ != "episodes_detail"}, indent=1))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)


def video(a):
    """renders the episodes of seeds a.seed, a.seed+1, ... (or the listed --episodes 'seed:mech' items)"""
    import imageio
    pol = load_policy(a.policy) if a.controller == "policy" else None
    W, H = 1920, 1080
    writer = imageio.get_writer(a.out, fps=30, quality=8, macro_block_size=8)
    nframes = int(a.seconds * 30)
    state = {"n": 0}
    items = [tuple(int(v) for v in it.split(":")) for it in a.episodes.split(",")] if a.episodes else \
        [(a.seed + i, -1) for i in range(50)]
    eps = []
    for seed, mech in items:
        if state["n"] >= nframes:
            break
        force = {"mech": mech} if mech >= 0 else None
        R = Runner(a.robot, pol, randomize=not a.nominal, seed=seed, buffer=not a.no_buffer, controller=a.controller, force=force)
        m, d = R.m, R.d
        ren = mujoco.Renderer(m, H, W)
        cam = mujoco.MjvCamera()
        if a.robot == "openarm":
            cam.lookat[:] = [0.36, -0.08, 0.98]; cam.distance = 1.2; cam.azimuth = 62; cam.elevation = -24
        else:
            cam.lookat[:] = [0.30, -0.12, 1.08]; cam.distance = 1.75; cam.azimuth = 50; cam.elevation = -20
        if a.cam:
            lk = [float(v) for v in a.cam.split(",")]
            cam.lookat[:] = lk[:3]; cam.distance, cam.azimuth, cam.elevation = lk[3], lk[4], lk[5]
        opt = mujoco.MjvOption()
        st = {"tn": 0.0}

        def cb():
            if d.time + 1e-9 >= st["tn"] and state["n"] < nframes:
                st["tn"] += 1 / 30; state["n"] += 1
                ren.update_scene(d, cam, opt)
                writer.append_data(ren.render())
        R.reset(); st["tn"] = d.time
        R.frame_cb = cb
        for _ in range(int(a.ep_seconds / CTRL_DT)):
            R.step()
            if state["n"] >= nframes:
                break
        eps.append(dict(seed=seed, **R.result()))
        print("  episode", eps[-1], flush=True)
    writer.close()
    print("video:", a.out, state["n"], "frames")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["eval", "video"])
    ap.add_argument("--robot", default="openarm", choices=["openarm", "giorgio"])
    ap.add_argument("--controller", default="policy", choices=["policy", "scripted", "scripted_follow"])
    ap.add_argument("--policy", default=os.path.join(QUI, "politica_openarm_cabinet.pt"))
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mech", type=int, default=None, help="force mechanism: 0 drawer, 1 door hinged left, 2 door hinged right")
    ap.add_argument("--nominal", action="store_true", help="no randomization/noise/latency")
    ap.add_argument("--json", default="")
    ap.add_argument("--no_buffer", action="store_true")
    ap.add_argument("--out", default="out.mp4")
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--ep_seconds", type=float, default=5.0)
    ap.add_argument("--episodes", default="", help="comma list of seed:mech (mech -1 = random) to render")
    ap.add_argument("--cam", default="", help="lookat_x,y,z,distance,azimuth,elevation")
    a = ap.parse_args()
    evaluate(a) if a.mode == "eval" else video(a)
