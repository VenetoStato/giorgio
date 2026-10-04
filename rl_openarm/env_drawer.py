"""Vectorized GPU environment (mujoco_warp + torch): standalone OpenArm 2.0 (official MJCF, right arm + gripper) opens a
drawer of a benchtop chest of drawers by its handle.

Randomized per episode (standalone scene only):
  cabinet: closed-front position 0.40-0.54 m in front of the arm base, lateral -0.25..0.05 m, yaw +-20 deg,
           handle height 0.12-0.26 m above the table; table height -0.40..-0.32 m and front edge 0-0.20 m (as lift v2+)
  handle:  horizontal bar 50 % (length 8-16 cm), vertical bar 25 % (8-11 cm), round knob 25 % (dia 2.4-4.4 cm);
           bar radius 5-12 mm, standoff 2.5-4.5 cm, friction 0.4-1.0
  drawer:  Coulomb friction 1-15 N, viscous damping 2-40 N s/m, mass 0.5-4 kg, soft-close spring 0-40 N/m (50 %),
           initial opening 0-5 cm
  arm:     kp/kv x0.8-1.2, joint damping x0.7-1.3, gravity compensation 0-100 % (as lift)
  obstacle: low box in front of the base in 50 % of episodes (as lift v2+)
  sensing: handle point bias +-7.5 mm/axis, noise 3 mm, latency 0-3 steps; pull-axis yaw error +-3 deg;
           handle size error +-2 mm; joint noise and 0-1 step latency; action applied one step late in 30 % of episodes
Success: drawer opening >= 15 cm for >= 0.48 s continuously within the 8 s episode.
"""
import math
import os
import sys

import mujoco
import numpy as np
import torch
import warp as wp
import mujoco_warp as mjw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene
import scene_drawer as sd
from policy_io_drawer import (ACT_SCALE, CTRL_DT, EP_LEN, OBS_DIM, ACT_DIM, Q_HOME, OPEN_GOAL, SUCC_OPEN, SUCC_HOLD,
                              G_OPEN, grip_cmd, build_obs_torch)

HANDLE_P = (0.5, 0.25, 0.25)      # hbar, vbar, knob
Q_NOISE = [0.15, 0.1, 0.2, 0.15, 0.3, 0.3, 0.3]


def yaw_rot(yaw):
    c, s = torch.cos(yaw), torch.sin(yaw)
    z, o = torch.zeros_like(yaw), torch.ones_like(yaw)
    return torch.stack([torch.stack([c, -s, z], -1), torch.stack([s, c, z], -1), torch.stack([z, z, o], -1)], -2)


class OpenArmDrawerEnv:
    def __init__(self, num_envs=4096, device="cuda:0", randomize=True, seed=0, nconmax=64, njmax=400):
        self.N = num_envs
        self.dev = torch.device(device)
        self.randomize = randomize
        self.gen = torch.Generator(device=self.dev).manual_seed(seed)
        self.p_obst = float(os.environ.get("P_OBST", "0.5"))
        self.knob_p = float(os.environ.get("KNOB_P", str(HANDLE_P[2])))
        sp = sd.build_standalone(obstacle=True)
        for b in sp.bodies:
            if b.name.startswith("openarm_right"):
                b.gravcomp = 0.5
        self.mjm = m = sp.compile()
        mjd = mujoco.MjData(m)
        self.substeps = int(round(CTRL_DT / m.opt.timestep))
        self.dt = CTRL_DT
        self.base_b = m.body(scene.BASE_BODY).id
        self.ee_b = m.body(scene.EE_BODY).id
        self.dr_b = m.body("drawer").id
        self.qa = torch.tensor([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS], device=self.dev)
        self.va = torch.tensor([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS], device=self.dev)
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        self.jd = m.joint("drawer_slide").id
        self.qd_ = m.joint("drawer_slide").qposadr[0]
        self.vd_ = m.joint("drawer_slide").dofadr[0]
        self.act_arm = [m.actuator(a).id for a in scene.ARM_ACT]
        self.act_f = m.actuator(scene.FINGER_ACT).id
        self.lo = torch.tensor([m.actuator_ctrlrange[i, 0] for i in self.act_arm], device=self.dev, dtype=torch.float32)
        self.hi = torch.tensor([m.actuator_ctrlrange[i, 1] for i in self.act_arm], device=self.dev, dtype=torch.float32)
        self.arm_bodies = [i for i in range(m.nbody) if m.body(i).name.startswith("openarm_right")]
        self.hg = [m.geom(n).id for n in sd.HANDLE_GEOMS]
        self.mid_table = int(m.body_mocapid[m.body("table_body").id])
        self.mid_obst = int(m.body_mocapid[m.body("obst_body").id])
        self.mid_cab = int(m.body_mocapid[m.body("cab").id])
        links = {m.body(f"openarm_right_link{k}").id for k in range(1, 7)}
        link_g = torch.zeros(m.ngeom, dtype=torch.bool); env_g = torch.zeros(m.ngeom, dtype=torch.bool)
        for g in range(m.ngeom):
            b = int(m.geom_bodyid[g]); bn = m.body(b).name
            if b in links and m.geom_contype[g]:
                link_g[g] = True
            if (bn in ("cab", "drawer", "obst_body", "table_body")) and (m.geom_contype[g] or m.geom_conaffinity[g]):
                env_g[g] = True
        self.link_g, self.env_g = link_g.to(self.dev), env_g.to(self.dev)

        with wp.ScopedDevice(device):
            self.wm = mjw.put_model(m)
            self.wd = mjw.put_data(m, mjd, nworld=self.N, nconmax=nconmax, njmax=njmax)
            if randomize:
                from mjlab.sim.randomization import expand_model_fields
                expand_model_fields(self.wm, self.N, ["geom_size", "geom_pos", "geom_friction", "body_mass", "body_inertia",
                                                      "body_gravcomp", "actuator_gainprm", "actuator_biasprm", "dof_damping",
                                                      "dof_frictionloss", "jnt_stiffness"])
            mjw.forward(self.wm, self.wd)
            with wp.ScopedCapture() as cap:
                for _ in range(self.substeps):
                    mjw.step(self.wm, self.wd)
            self.graph = cap.graph
            with wp.ScopedCapture() as cap1:
                mjw.kinematics(self.wm, self.wd)
            self.graph_kin = cap1.graph
        T = wp.to_torch
        self.qpos, self.qvel, self.ctrl = T(self.wd.qpos), T(self.wd.qvel), T(self.wd.ctrl)
        self.qacc_ws = T(self.wd.qacc_warmstart)
        self.xpos, self.xmat = T(self.wd.xpos), T(self.wd.xmat)
        self.mocap_pos, self.mocap_quat = T(self.wd.mocap_pos), T(self.wd.mocap_quat)
        self.nacon = T(self.wd.nacon)
        self.con_geom, self.con_wid = T(self.wd.contact.geom), T(self.wd.contact.worldid)
        if randomize:
            self.m_size, self.m_gpos, self.m_fric = T(self.wm.geom_size), T(self.wm.geom_pos), T(self.wm.geom_friction)
            self.m_mass, self.m_inertia, self.m_gc = T(self.wm.body_mass), T(self.wm.body_inertia), T(self.wm.body_gravcomp)
            self.m_gain, self.m_bias, self.m_damp = T(self.wm.actuator_gainprm), T(self.wm.actuator_biasprm), T(self.wm.dof_damping)
            self.m_floss, self.m_stiff = T(self.wm.dof_frictionloss), T(self.wm.jnt_stiffness)
            self.gain0, self.bias0, self.damp0 = self.m_gain[0].clone(), self.m_bias[0].clone(), self.m_damp[0].clone()
            self.floss0 = self.m_floss[0].clone()
            self.dr_inertia0 = self.m_inertia[0, self.dr_b].clone(); self.dr_mass0 = float(self.m_mass[0, self.dr_b])
        N, d = self.N, self.dev
        self.target = torch.zeros(N, 7, device=d)
        self.gtarget = torch.zeros(N, device=d)
        self.last_a = torch.zeros(N, ACT_DIM, device=d)
        self.prev_a = torch.zeros(N, ACT_DIM, device=d)
        self.t = torch.zeros(N, dtype=torch.long, device=d)
        self.hold = torch.zeros(N, dtype=torch.long, device=d)
        self.success = torch.zeros(N, dtype=torch.bool, device=d)
        self.max_open = torch.zeros(N, device=d)
        self.open0 = torch.zeros(N, device=d)
        self.kind = torch.zeros(N, dtype=torch.long, device=d)
        self.s_off = torch.full((N,), 0.03, device=d)
        self.hsize_v = torch.zeros(N, 3, device=d)
        self.pull_v = torch.zeros(N, 3, device=d)       # perceived (with yaw error), base frame
        self.bar_v = torch.zeros(N, 3, device=d)
        self.pull_t = torch.zeros(N, 3, device=d)       # true, base frame
        self.bar_t = torch.zeros(N, 3, device=d)
        self.table_z = torch.zeros(N, device=d)
        self.H = 4
        self.h_hist = torch.zeros(N, self.H, 4, device=d)     # handle xyz + opening
        self.h_delay = torch.zeros(N, dtype=torch.long, device=d)
        self.h_bias = torch.zeros(N, 3, device=d)
        self.prop_hist = torch.zeros(N, 2, 15, device=d)
        self.prop_delay = torch.zeros(N, dtype=torch.long, device=d)
        self.act_delay = torch.zeros(N, dtype=torch.bool, device=d)
        self.obs_dim, self.act_dim = OBS_DIM, ACT_DIM
        wp.capture_launch(self.graph_kin)
        self.base_p = self.xpos[0, self.base_b].clone()
        self.base_R = self.xmat[0, self.base_b].reshape(3, 3).clone()

    def _rand(self, n, lo, hi):
        return lo + (hi - lo) * torch.rand(n, device=self.dev, generator=self.gen)

    def _to_base(self, p):
        return (p - self.base_p) @ self.base_R

    def _set_handles(self, ids, kind, L, r, s, k):
        """vectorized scene_drawer.handle_layout"""
        n = len(ids)
        P = sd.PARK
        z = torch.zeros(n, device=self.dev)
        pos = torch.zeros(n, 5, 3, device=self.dev); siz = torch.zeros(n, 5, 3, device=self.dev)
        hb, vb, kb = kind == 0, kind == 1, kind == 2
        pos[:, 0] = torch.stack([-s, z, torch.where(hb, z, z + P)], -1); siz[:, 0] = torch.stack([r, L / 2, z], -1)
        pos[:, 1] = torch.stack([-s, z, torch.where(vb, z, z + P)], -1); siz[:, 1] = torch.stack([r, L / 2, z], -1)
        pos[:, 2] = torch.stack([-s, z, torch.where(kb, z, z + P)], -1); siz[:, 2] = torch.stack([k, z + 0.009, z], -1)
        off = L / 2 - 0.006
        py1 = torch.where(hb, off, z); pz1 = torch.where(vb, off, z)
        py2 = torch.where(hb, -off, z); pz2 = torch.where(vb, -off, torch.where(kb, z + P, z))
        pos[:, 3] = torch.stack([-s / 2, py1, pz1], -1); pos[:, 4] = torch.stack([-s / 2, py2, pz2], -1)
        pw = torch.where(kb, z + 0.008, z + 0.006)
        siz[:, 3] = torch.stack([s / 2, pw, pw], -1); siz[:, 4] = torch.stack([s / 2, z + 0.006, z + 0.006], -1)
        gp = self.m_gpos[ids]; gs = self.m_size[ids]
        gp[:, self.hg] = pos; gs[:, self.hg] = siz
        self.m_gpos[ids] = gp; self.m_size[ids] = gs

    # ------------------------------------------------------------------
    def reset_idx(self, ids):
        n = len(ids)
        if n == 0:
            return
        dev, R = self.dev, self.randomize
        bz = float(self.base_p[2])
        if R:
            dz = self._rand(n, -0.40, -0.32)
            edge = self._rand(n, 0.0, 0.20)
            hz = self._rand(n, 0.12, 0.26)
            cx = self._rand(n, 0.40, 0.54); cy = self._rand(n, -0.25, 0.05)
            yaw = self._rand(n, -math.radians(20), math.radians(20))
            u = torch.rand(n, device=dev, generator=self.gen)
            pk = self.knob_p; ph = HANDLE_P[0] / (HANDLE_P[0] + HANDLE_P[1]) * (1 - pk)
            kind = torch.where(u < ph, 0, torch.where(u < 1 - pk, 1, 2)).long()
            L = torch.where(kind == 0, self._rand(n, 0.08, 0.16), self._rand(n, 0.08, 0.11))
            r = self._rand(n, 0.005, 0.012); s = self._rand(n, 0.025, 0.045); k = self._rand(n, 0.012, 0.022)
            open0 = self._rand(n, 0.0, 0.05)
        else:
            dz = torch.full((n,), scene.TABLE_DZ, device=dev); edge = torch.full((n,), 0.08, device=dev)
            hz = torch.full((n,), 0.18, device=dev); cx = torch.full((n,), 0.47, device=dev); cy = torch.full((n,), -0.10, device=dev)
            yaw = torch.zeros(n, device=dev); kind = torch.zeros(n, dtype=torch.long, device=dev)
            L = torch.full((n,), 0.12, device=dev); r = torch.full((n,), 0.008, device=dev); s = torch.full((n,), 0.035, device=dev)
            k = torch.full((n,), 0.017, device=dev); open0 = torch.zeros(n, device=dev)
        self.table_z[ids] = dz
        mp = self.mocap_pos[ids]
        mp[:, self.mid_table, 2] = bz + dz - 0.02
        mp[:, self.mid_table, 0] = self.base_p[0] + edge + 0.34
        cab_b = torch.stack([cx, cy, dz + hz], -1)
        mp[:, self.mid_cab] = cab_b @ self.base_R.T + self.base_p
        if R:
            ox = self._rand(n, 0.12, 0.20); oy = self._rand(n, -0.15, 0.05); oh = self._rand(n, 0.04, 0.11)
            present = torch.rand(n, device=dev, generator=self.gen) < self.p_obst
            # the obstacle must stay below the handle and away from the open drawer path
            ox = torch.minimum(ox, cx - 0.18 - 0.04)
            mp[:, self.mid_obst, 0] = self.base_p[0] + ox
            mp[:, self.mid_obst, 1] = self.base_p[1] + oy
            mp[:, self.mid_obst, 2] = torch.where(present, bz + dz + oh - 0.06, torch.full_like(oh, -3.0))
        else:
            mp[:, self.mid_obst, 2] = -3.0
        self.mocap_pos[ids] = mp
        mq = self.mocap_quat[ids]
        mq[:, self.mid_cab] = torch.stack([torch.cos(yaw / 2), 0 * yaw, 0 * yaw, torch.sin(yaw / 2)], -1)   # base frame = world rot
        self.mocap_quat[ids] = mq
        Rc = yaw_rot(yaw)
        self.pull_t[ids] = -Rc[:, :, 0]
        bar = torch.where((kind == 0)[:, None], Rc[:, :, 1], torch.where((kind == 1)[:, None],
                          torch.tensor([0., 0., 1.], device=dev).expand(n, 3), torch.zeros(n, 3, device=dev)))
        self.bar_t[ids] = bar
        self.kind[ids] = kind
        self.s_off[ids] = s
        if R:
            self._set_handles(ids, kind, L, r, s, k)
            fr = self.m_fric[ids]
            fr[:, self.hg, 0] = self._rand(n, 0.4, 1.0)[:, None]
            self.m_fric[ids] = fr
            # drawer dynamics
            fl = self.m_floss[ids]; fl[:, self.vd_] = self._rand(n, 1.0, 15.0); self.m_floss[ids] = fl
            dm = self.damp0[None].repeat(n, 1) * self._rand(n, 0.7, 1.3)[:, None]
            dm[:, self.vd_] = self._rand(n, 2.0, 40.0)
            self.m_damp[ids] = dm
            mass = self._rand(n, 0.5, 4.0)
            bm = self.m_mass[ids]; bm[:, self.dr_b] = mass; self.m_mass[ids] = bm
            bi = self.m_inertia[ids]; bi[:, self.dr_b] = self.dr_inertia0[None] * (mass / self.dr_mass0)[:, None]; self.m_inertia[ids] = bi
            st = self.m_stiff[ids]
            st[:, self.jd] = torch.where(torch.rand(n, device=dev, generator=self.gen) < 0.5, self._rand(n, 0.0, 40.0), torch.zeros(n, device=dev))
            self.m_stiff[ids] = st
            kp = self._rand(n * 8, 0.8, 1.2).reshape(n, 8); kv = self._rand(n * 8, 0.8, 1.2).reshape(n, 8)
            g = self.gain0[None].repeat(n, 1, 1); b = self.bias0[None].repeat(n, 1, 1)
            g[:, :, 0] *= kp; b[:, :, 1] *= kp; b[:, :, 2] *= kv
            self.m_gain[ids], self.m_bias[ids] = g, b
            gc = self.m_gc[ids]; gc[:, self.arm_bodies] = self._rand(n, 0.0, 1.0)[:, None]; self.m_gc[ids] = gc
            self.h_delay[ids] = torch.randint(0, 4, (n,), device=dev, generator=self.gen)
            self.prop_delay[ids] = torch.randint(0, 2, (n,), device=dev, generator=self.gen)
            self.act_delay[ids] = torch.rand(n, device=dev, generator=self.gen) < 0.3
            self.h_bias[ids] = (torch.rand(n, 3, device=dev, generator=self.gen) - 0.5) * 0.015
            yerr = self._rand(n, -math.radians(3), math.radians(3))
            serr = (torch.rand(n, 3, device=dev, generator=self.gen) - 0.5) * 0.004
        else:
            self.h_delay[ids] = 0; self.prop_delay[ids] = 0; self.act_delay[ids] = False; self.h_bias[ids] = 0
            yerr = torch.zeros(n, device=dev); serr = torch.zeros(n, 3, device=dev)
        Re = yaw_rot(yerr)
        self.pull_v[ids] = (Re @ self.pull_t[ids][..., None])[..., 0]
        self.bar_v[ids] = (Re @ bar[..., None])[..., 0]
        size1 = torch.where(kind == 2, 2 * k, L)
        size2 = torch.where(kind == 2, k, r)
        self.hsize_v[ids] = torch.stack([size1, size2, s], -1) + serr

        q = self.qpos[ids]
        qh = torch.tensor(Q_HOME, device=dev)[None] + (torch.rand(n, 7, device=dev, generator=self.gen) - 0.5) * 2 * \
            torch.tensor(Q_NOISE, device=dev)
        qh = torch.clamp(qh, self.lo, self.hi)
        q[:, self.qa] = qh
        q[:, self.qf[0]] = G_OPEN; q[:, self.qf[1]] = G_OPEN
        q[:, self.qd_] = open0
        self.qpos[ids] = q
        self.qvel[ids] = 0
        self.qacc_ws[ids] = 0
        c = self.ctrl[ids]
        c[:, self.act_arm] = qh
        c[:, self.act_f] = G_OPEN
        self.ctrl[ids] = c
        self.target[ids] = qh
        self.gtarget[ids] = G_OPEN
        self.last_a[ids] = 0; self.prev_a[ids] = 0
        self.t[ids] = 0
        self.hold[ids] = 0; self.success[ids] = False; self.max_open[ids] = open0; self.open0[ids] = open0
        # true handle point (base frame) at reset
        hb = cab_b + (Rc @ torch.stack([-s, 0 * s, 0 * s], -1)[..., None])[..., 0] + self.pull_t[ids] * open0[:, None]
        hv = torch.cat([hb + self.h_bias[ids], open0[:, None]], -1)
        self.h_hist[ids] = hv[:, None].expand(n, self.H, 4)
        prop = torch.cat([qh, torch.zeros_like(qh), torch.full((n, 1), G_OPEN, device=dev)], -1)
        self.prop_hist[ids] = prop[:, None].expand(n, 2, 15)

    def reset(self):
        self.reset_idx(torch.arange(self.N, device=self.dev))
        wp.capture_launch(self.graph_kin)
        return self.obs()

    # ------------------------------------------------------------------
    def _state(self):
        ee_p = self.xpos[:, self.ee_b]
        ee_R = self.xmat[:, self.ee_b].reshape(self.N, 3, 3)
        grasp_w = ee_p + ee_R @ torch.tensor(scene.GRASP_OFS, device=self.dev, dtype=torch.float32)
        grasp_b = self._to_base(grasp_w)
        Rb = self.base_R.T @ ee_R
        appr_b, fing_b = -Rb[:, :, 2], Rb[:, :, 1]
        dr_p = self.xpos[:, self.dr_b]
        dr_R = self.xmat[:, self.dr_b].reshape(self.N, 3, 3)
        hw = dr_p - dr_R[:, :, 0] * self.s_off[:, None]
        handle_b = self._to_base(hw)
        opening = self.qpos[:, self.qd_]
        return grasp_b, appr_b, fing_b, handle_b, opening

    def _push_hist(self):
        _, _, _, handle_b, opening = self._state()
        R = self.randomize
        noise = 0.003 * torch.randn(self.N, 4, device=self.dev, generator=self.gen) if R else 0
        self.h_hist = torch.roll(self.h_hist, 1, 1)
        self.h_hist[:, 0] = torch.cat([handle_b + self.h_bias, opening[:, None]], -1) + noise
        prop = torch.cat([self.qpos[:, self.qa], self.qvel[:, self.va], self.qpos[:, self.qf[0]:self.qf[0] + 1]], -1)
        if R:
            prop = prop + torch.cat([0.003 * torch.randn(self.N, 7, device=self.dev, generator=self.gen),
                                     0.05 * torch.randn(self.N, 7, device=self.dev, generator=self.gen),
                                     0.01 * torch.randn(self.N, 1, device=self.dev, generator=self.gen)], -1)
        self.prop_hist = torch.roll(self.prop_hist, 1, 1)
        self.prop_hist[:, 0] = prop

    def obs(self):
        ar = torch.arange(self.N, device=self.dev)
        hv = self.h_hist[ar, self.h_delay]
        prop = self.prop_hist[ar, self.prop_delay]
        grasp_b, appr_b, fing_b, _, _ = self._state()
        o = build_obs_torch(prop[:, :7], prop[:, 7:14], prop[:, 14], self.target, self.gtarget, grasp_b, appr_b, fing_b,
                            hv[:, :3], self.pull_v, self.bar_v, self.hsize_v, hv[:, 3], self.last_a)
        return torch.nan_to_num(o).clamp(-10, 10)

    def step(self, action):
        action = action.clamp(-1, 1)
        a_eff = torch.where(self.act_delay[:, None], self.prev_a, action)
        self.prev_a = action.clone()
        old_last = self.last_a
        self.last_a = action.clone()
        self.target = torch.clamp(self.target + ACT_SCALE * a_eff[:, :7], self.lo, self.hi)
        self.gtarget = grip_cmd(a_eff[:, 7])
        c = self.ctrl
        c[:, self.act_arm] = self.target
        c[:, self.act_f] = self.gtarget
        wp.capture_launch(self.graph)
        self.t += 1
        self._push_hist()

        grasp_b, appr_b, fing_b, handle_b, opening = self._state()
        d = torch.norm(grasp_b - handle_b, dim=-1)
        near = 1 - torch.tanh(d / 0.1)
        r_reach = near + 0.5 * (1 - torch.tanh(d / 0.02))
        r_appr = 0.5 * torch.clamp((appr_b * -self.pull_t).sum(-1), 0, 1) * near
        r_fing = 0.5 * (1 - torch.abs((fing_b * self.bar_t).sum(-1))) * near
        r_open = 8.0 * torch.clamp(opening / OPEN_GOAL, 0, 1) + 2.0 * (opening >= SUCC_OPEN).float()
        r_rate = -0.02 * ((action - old_last) ** 2).sum(-1)
        r_vel = -2e-4 * (self.qvel[:, self.va] ** 2).sum(-1)
        r_touch = torch.zeros(self.N, device=self.dev)
        nc = int(self.nacon.item())
        if nc:
            g = self.con_geom[:nc]; w = self.con_wid[:nc]
            bad = (self.link_g[g[:, 0]] & self.env_g[g[:, 1]]) | (self.link_g[g[:, 1]] & self.env_g[g[:, 0]])
            r_touch.index_add_(0, w[bad].long(), torch.ones(int(bad.sum().item()), device=self.dev))
        r_touch = -1.0 * (r_touch > 0).float()
        bad_state = ~torch.isfinite(grasp_b).all(-1) | ~torch.isfinite(opening)
        rew = r_reach + r_appr + r_fing + r_open + r_rate + r_vel + r_touch - 10.0 * bad_state.float()
        rew = torch.nan_to_num(rew, nan=-10.0)

        ok = opening >= SUCC_OPEN
        self.hold = torch.where(ok, self.hold + 1, torch.zeros_like(self.hold))
        self.success |= self.hold >= SUCC_HOLD
        self.max_open = torch.maximum(self.max_open, torch.nan_to_num(opening))
        timeout = self.t >= EP_LEN
        done = bad_state | timeout
        # train.py logs: success, max_dz (here: max opening), caduto (here: numerical blow-up), t
        info = {"success": self.success.clone(), "max_dz": self.max_open.clone(), "caduto": bad_state, "d": d,
                "t": self.t.clone(), "touch": (r_touch < 0)}
        ids = done.nonzero(as_tuple=False).squeeze(-1)
        if len(ids):
            self.reset_idx(ids)
            wp.capture_launch(self.graph_kin)
        return self.obs(), rew, done, timeout, info


if __name__ == "__main__":
    import time
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4096
    env = OpenArmDrawerEnv(N)
    o = env.reset()
    print("obs", o.shape, "substeps", env.substeps)
    torch.cuda.synchronize(); t0 = time.time(); T = 60
    for i in range(T):
        o, r, d, to, info = env.step(torch.randn(N, ACT_DIM, device=env.dev) * 0.5)
    torch.cuda.synchronize(); dt = time.time() - t0
    print(f"N={N}: {T*N/dt:.0f} control steps/s, r={r.mean().item():.3f}, obs finite {torch.isfinite(o).all().item()}")
    print("mem GPU MB", torch.cuda.max_memory_allocated() / 1e6, "ncon max", int(env.nacon.max().item()))
    op = env.qpos[:, env.qd_]
    print("opening mean/max", op.mean().item(), op.max().item())
