"""Vectorized GPU environment (mujoco_warp + torch): standalone OpenArm 2.0 (official MJCF, right arm + gripper) opens a
cabinet compartment closed by a DRAWER or by a hinged DOOR (hinge left or right). The policy is not told which.

Randomized per episode (standalone scene only):
  mechanism: drawer 50 %, door hinged left 25 %, door hinged right 25 %
  cabinet:  closed-front 0.44-0.56 m in front of the arm base, lateral -0.20..0.05 m, yaw +-20 deg, compartment centre
            0.12-0.26 m above the table; table height -0.40..-0.32 m and front edge 0-0.20 m (as lift v2+)
  handle:   drawer: horizontal bar 50 % (8-16 cm) / vertical bar 25 % (8-11 cm) / knob 25 % (dia 2.4-4.4 cm);
            door (near the free edge): vertical bar 60 % / knob 40 %; bar radius 5-12 mm, standoff 2.5-4.5 cm, friction 0.4-1.0
  drawer:   Coulomb friction 1-15 N, damping 2-40 N s/m, mass 0.5-4 kg, closing spring 0-40 N/m (50 %), initially open 0-5 cm
  door:     Coulomb friction 0.1-1.5 N m, damping 0.1-2 N m s/rad, mass 0.6-2 kg, closing spring 0-1 N m/rad (50 %),
            initially open 0-8 deg
  arm:      kp/kv x0.8-1.2, joint damping x0.7-1.3, gravity compensation 0-100 % (as lift)
  obstacle: low box in front of the base in 50 % of episodes (as lift v2+)
  sensing:  handle point bias +-7.5 mm/axis, noise 3 mm, latency 0-3 steps; panel-normal yaw error +-3 deg;
            handle size error +-2 mm; joint noise, 0-1 step latency; action one step late in 30 % of episodes
Success: drawer >= 15 cm or door >= 60 deg, held >= 0.48 s, within the 10 s episode.
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
import scene_cabinet as sc
from policy_io_cabinet import (ACT_SCALE, CTRL_DT, EP_LEN, OBS_DIM, ACT_DIM, Q_HOME, DRAWER_GOAL, DOOR_GOAL, DRAWER_SUCC,
                               DOOR_SUCC, SUCC_HOLD, G_OPEN, grip_cmd, build_obs_torch)

MECH_P = (0.5, 0.25, 0.25)
Q_NOISE = [0.15, 0.1, 0.2, 0.15, 0.3, 0.3, 0.3]


def yaw_rot(yaw):
    c, s = torch.cos(yaw), torch.sin(yaw)
    z, o = torch.zeros_like(yaw), torch.ones_like(yaw)
    return torch.stack([torch.stack([c, -s, z], -1), torch.stack([s, c, z], -1), torch.stack([z, z, o], -1)], -2)


class OpenArmCabinetEnv:
    def __init__(self, num_envs=4096, device="cuda:0", randomize=True, seed=0, nconmax=64, njmax=400):
        self.N = num_envs
        self.dev = dev = torch.device(device)
        self.randomize = randomize
        self.gen = torch.Generator(device=dev).manual_seed(seed)
        self.p_obst = float(os.environ.get("P_OBST", "0.5"))
        self.mech_p = tuple(float(x) for x in os.environ.get("MECH_P", "0.5,0.25,0.25").split(","))
        sp = sc.build_standalone(obstacle=True)
        for b in sp.bodies:
            if b.name.startswith("openarm_right"):
                b.gravcomp = 0.5
        self.mjm = m = sp.compile()
        mjd = mujoco.MjData(m)
        self.substeps = int(round(CTRL_DT / m.opt.timestep))
        self.dt = CTRL_DT
        self.base_b = m.body(scene.BASE_BODY).id
        self.ee_b = m.body(scene.EE_BODY).id
        self.mb = [m.body(n).id for n in sc.MECHS]
        self.qa = torch.tensor([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS], device=dev)
        self.va = torch.tensor([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS], device=dev)
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        jn = ["drawer_slide", "door_l_hinge", "door_r_hinge"]
        self.mj = [m.joint(j).id for j in jn]
        self.mq = torch.tensor([m.joint(j).qposadr[0] for j in jn], device=dev)
        self.mv = [m.joint(j).dofadr[0] for j in jn]
        self.act_arm = [m.actuator(a).id for a in scene.ARM_ACT]
        self.act_f = m.actuator(scene.FINGER_ACT).id
        self.lo = torch.tensor([m.actuator_ctrlrange[i, 0] for i in self.act_arm], device=dev, dtype=torch.float32)
        self.hi = torch.tensor([m.actuator_ctrlrange[i, 1] for i in self.act_arm], device=dev, dtype=torch.float32)
        self.arm_bodies = [i for i in range(m.nbody) if m.body(i).name.startswith("openarm_right")]
        self.mech_geoms = [[g for g in range(m.ngeom) if m.geom_bodyid[g] == b] for b in self.mb]
        self.hgeoms = [[m.geom(f"{mm}_{h}").id for h in sc.HNAMES] for mm in sc.MECHS]
        self.hc = [torch.tensor(sc.handle_center(mm), device=dev, dtype=torch.float32) for mm in sc.MECHS]
        self.mid_table = int(m.body_mocapid[m.body("table_body").id])
        self.mid_obst = int(m.body_mocapid[m.body("obst_body").id])
        self.mid_cab = int(m.body_mocapid[m.body("cab").id])
        links = {m.body(f"openarm_right_link{k}").id for k in range(1, 7)}
        envb = {"cab", "obst_body", "table_body"} | set(sc.MECHS)
        link_g = torch.zeros(m.ngeom, dtype=torch.bool); env_g = torch.zeros(m.ngeom, dtype=torch.bool)
        for g in range(m.ngeom):
            b = int(m.geom_bodyid[g])
            if b in links and m.geom_contype[g]:
                link_g[g] = True
            if m.body(b).name in envb and (m.geom_contype[g] or m.geom_conaffinity[g]):
                env_g[g] = True
        self.link_g, self.env_g = link_g.to(dev), env_g.to(dev)
        self.inert0 = [torch.tensor(m.body_inertia[b], device=dev, dtype=torch.float32) for b in self.mb]
        self.mass0 = [float(m.body_mass[b]) for b in self.mb]

        with wp.ScopedDevice(device):
            self.wm = mjw.put_model(m)
            self.wd = mjw.put_data(m, mjd, nworld=self.N, nconmax=nconmax, njmax=njmax)
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
        self.m_size, self.m_gpos, self.m_fric = T(self.wm.geom_size), T(self.wm.geom_pos), T(self.wm.geom_friction)
        self.m_mass, self.m_inertia, self.m_gc = T(self.wm.body_mass), T(self.wm.body_inertia), T(self.wm.body_gravcomp)
        self.m_gain, self.m_bias, self.m_damp = T(self.wm.actuator_gainprm), T(self.wm.actuator_biasprm), T(self.wm.dof_damping)
        self.m_floss, self.m_stiff = T(self.wm.dof_frictionloss), T(self.wm.jnt_stiffness)
        self.gain0, self.bias0, self.damp0 = self.m_gain[0].clone(), self.m_bias[0].clone(), self.m_damp[0].clone()
        self.gpos0 = self.m_gpos[0].clone()
        N = self.N
        z = lambda *s: torch.zeros(*s, device=dev)
        self.target, self.gtarget = z(N, 7), z(N)
        self.last_a, self.prev_a = z(N, ACT_DIM), z(N, ACT_DIM)
        self.t = torch.zeros(N, dtype=torch.long, device=dev)
        self.hold = torch.zeros(N, dtype=torch.long, device=dev)
        self.success = torch.zeros(N, dtype=torch.bool, device=dev)
        self.max_prog = z(N)
        self.mech = torch.zeros(N, dtype=torch.long, device=dev)
        self.kind = torch.zeros(N, dtype=torch.long, device=dev)
        self.s_off = torch.full((N,), 0.03, device=dev)
        self.hsize_v = z(N, 3)
        self.yerr_R = torch.eye(3, device=dev).repeat(N, 1, 1)
        self.h0 = z(N, 3)
        self.table_z = z(N)
        self.H = 4
        self.h_hist = z(N, self.H, 3)
        self.h_delay = torch.zeros(N, dtype=torch.long, device=dev)
        self.h_bias = z(N, 3)
        self.prop_hist = z(N, 2, 15)
        self.prop_delay = torch.zeros(N, dtype=torch.long, device=dev)
        self.act_delay = torch.zeros(N, dtype=torch.bool, device=dev)
        self.obs_dim, self.act_dim = OBS_DIM, ACT_DIM
        wp.capture_launch(self.graph_kin)
        self.base_p = self.xpos[0, self.base_b].clone()
        self.base_R = self.xmat[0, self.base_b].reshape(3, 3).clone()

    def _rand(self, n, lo, hi):
        return lo + (hi - lo) * torch.rand(n, device=self.dev, generator=self.gen)

    def _to_base(self, p):
        return (p - self.base_p) @ self.base_R

    def _layout(self, kind, L, r, s, k, hc):
        """vectorized scene_cabinet.handle_layout -> pos (n,5,3), size (n,5,3)"""
        n = len(kind); dev = self.dev
        P = sc.PARK
        z = torch.zeros(n, device=dev)
        x0, y0, z0 = hc[0] + z, hc[1] + z, hc[2] + z
        hb, vb, kb = kind == 0, kind == 1, kind == 2
        pos = torch.zeros(n, 5, 3, device=dev); siz = torch.zeros(n, 5, 3, device=dev)
        pos[:, 0] = torch.stack([x0 - s, y0, z0 + torch.where(hb, z, z + P)], -1); siz[:, 0] = torch.stack([r, L / 2, z], -1)
        pos[:, 1] = torch.stack([x0 - s, y0, z0 + torch.where(vb, z, z + P)], -1); siz[:, 1] = torch.stack([r, L / 2, z], -1)
        pos[:, 2] = torch.stack([x0 - s, y0, z0 + torch.where(kb, z, z + P)], -1); siz[:, 2] = torch.stack([k, z + 0.009, z], -1)
        off = L / 2 - 0.006
        py1 = torch.where(hb, off, z); pz1 = torch.where(vb, off, z)
        py2 = torch.where(hb, -off, z); pz2 = torch.where(vb, -off, torch.where(kb, z + P, z))
        pos[:, 3] = torch.stack([x0 - s / 2, y0 + py1, z0 + pz1], -1); pos[:, 4] = torch.stack([x0 - s / 2, y0 + py2, z0 + pz2], -1)
        pw = torch.where(kb, z + 0.008, z + 0.006)
        siz[:, 3] = torch.stack([s / 2, pw, pw], -1); siz[:, 4] = torch.stack([s / 2, z + 0.006, z + 0.006], -1)
        return pos, siz

    # ------------------------------------------------------------------
    def reset_idx(self, ids):
        n = len(ids)
        if n == 0:
            return
        dev, R = self.dev, self.randomize
        bz = float(self.base_p[2])
        if R:
            dz = self._rand(n, -0.40, -0.32); edge = self._rand(n, 0.0, 0.20); hz = self._rand(n, 0.12, 0.26)
            cx = self._rand(n, 0.44, 0.56); cy = self._rand(n, -0.20, 0.05)
            yaw = self._rand(n, -math.radians(20), math.radians(20))
            u = torch.rand(n, device=dev, generator=self.gen)
            mp_ = self.mech_p
            mech = torch.where(u < mp_[0], 0, torch.where(u < mp_[0] + mp_[1], 1, 2)).long()
            u2 = torch.rand(n, device=dev, generator=self.gen)
            kind_dr = torch.where(u2 < 0.5, 0, torch.where(u2 < 0.75, 1, 2))
            kind_do = torch.where(u2 < 0.6, 1, 2)
            kind = torch.where(mech == 0, kind_dr, kind_do).long()
            L = torch.where(kind == 0, self._rand(n, 0.08, 0.16), self._rand(n, 0.08, 0.11))
            r = self._rand(n, 0.005, 0.012); s = self._rand(n, 0.025, 0.045); k = self._rand(n, 0.012, 0.022)
            open0 = torch.where(mech == 0, self._rand(n, 0.0, 0.05), self._rand(n, 0.0, math.radians(8)))
        else:
            dz = torch.full((n,), scene.TABLE_DZ, device=dev); edge = torch.full((n,), 0.08, device=dev)
            hz = torch.full((n,), 0.18, device=dev); cx = torch.full((n,), 0.50, device=dev); cy = torch.full((n,), -0.10, device=dev)
            yaw = torch.zeros(n, device=dev)
            mech = torch.arange(n, device=dev) % 3
            kind = torch.where(mech == 0, 0, 1).long()
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
            mp[:, self.mid_obst, 0] = self.base_p[0] + ox
            mp[:, self.mid_obst, 1] = self.base_p[1] + oy
            mp[:, self.mid_obst, 2] = torch.where(present, bz + dz + oh - 0.06, torch.full_like(oh, -3.0))
        else:
            mp[:, self.mid_obst, 2] = -3.0
        self.mocap_pos[ids] = mp
        mq = self.mocap_quat[ids]
        mq[:, self.mid_cab] = torch.stack([torch.cos(yaw / 2), 0 * yaw, 0 * yaw, torch.sin(yaw / 2)], -1)
        self.mocap_quat[ids] = mq
        self.mech[ids] = mech; self.kind[ids] = kind; self.s_off[ids] = s
        # geometry: active mechanism + handle, others parked
        gp = self.m_gpos[ids]; gs = self.m_size[ids]
        for mi in range(3):
            act = (mech == mi)
            off = torch.where(act, 0.0, sc.PARK2)[:, None]
            g = self.mech_geoms[mi]
            base = self.gpos0[g][None].repeat(n, 1, 1)
            base[:, :, 2] += off
            gp[:, g] = base
            pos, siz = self._layout(kind, L, r, s, k, self.hc[mi])
            pos[:, :, 2] += off
            gp[:, self.hgeoms[mi]] = pos; gs[:, self.hgeoms[mi]] = siz
        self.m_gpos[ids] = gp; self.m_size[ids] = gs
        if R:
            fr = self.m_fric[ids]
            hf = self._rand(n, 0.4, 1.0)
            for mi in range(3):
                fr[:, self.hgeoms[mi], 0] = hf[:, None]
            self.m_fric[ids] = fr
            fl = self.m_floss[ids]; dm = self.damp0[None].repeat(n, 1) * self._rand(n, 0.7, 1.3)[:, None]
            st = self.m_stiff[ids]; bm = self.m_mass[ids]; bi = self.m_inertia[ids]
            spring_on = torch.rand(n, device=dev, generator=self.gen) < 0.5
            fl[:, self.mv[0]] = self._rand(n, 1.0, 15.0); dm[:, self.mv[0]] = self._rand(n, 2.0, 40.0)
            st[:, self.mj[0]] = torch.where(spring_on, self._rand(n, 0.0, 40.0), torch.zeros(n, device=dev))
            for mi in (1, 2):
                fl[:, self.mv[mi]] = self._rand(n, 0.1, 1.5); dm[:, self.mv[mi]] = self._rand(n, 0.1, 2.0)
                st[:, self.mj[mi]] = torch.where(spring_on, self._rand(n, 0.0, 1.0), torch.zeros(n, device=dev))
            for mi, (lo_, hi_) in enumerate(((0.5, 4.0), (0.6, 2.0), (0.6, 2.0))):
                ms = self._rand(n, lo_, hi_)
                bm[:, self.mb[mi]] = ms; bi[:, self.mb[mi]] = self.inert0[mi][None] * (ms / self.mass0[mi])[:, None]
            self.m_floss[ids] = fl; self.m_damp[ids] = dm; self.m_stiff[ids] = st; self.m_mass[ids] = bm; self.m_inertia[ids] = bi
            kp = self._rand(n * 8, 0.8, 1.2).reshape(n, 8); kv = self._rand(n * 8, 0.8, 1.2).reshape(n, 8)
            g_ = self.gain0[None].repeat(n, 1, 1); b_ = self.bias0[None].repeat(n, 1, 1)
            g_[:, :, 0] *= kp; b_[:, :, 1] *= kp; b_[:, :, 2] *= kv
            self.m_gain[ids], self.m_bias[ids] = g_, b_
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
        self.yerr_R[ids] = yaw_rot(yerr)
        self.hsize_v[ids] = torch.stack([torch.where(kind == 2, 2 * k, L), torch.where(kind == 2, k, r), s], -1) + serr

        q = self.qpos[ids]
        qh = torch.tensor(Q_HOME, device=dev)[None] + (torch.rand(n, 7, device=dev, generator=self.gen) - 0.5) * 2 * \
            torch.tensor(Q_NOISE, device=dev)
        qh = torch.clamp(qh, self.lo, self.hi)
        q[:, self.qa] = qh
        q[:, self.qf[0]] = G_OPEN; q[:, self.qf[1]] = G_OPEN
        for mi in range(3):
            q[:, self.mq[mi]] = torch.where(mech == mi, open0, torch.zeros_like(open0))
        self.qpos[ids] = q
        self.qvel[ids] = 0
        self.qacc_ws[ids] = 0
        c = self.ctrl[ids]
        c[:, self.act_arm] = qh; c[:, self.act_f] = G_OPEN
        self.ctrl[ids] = c
        self.target[ids] = qh; self.gtarget[ids] = G_OPEN
        self.last_a[ids] = 0; self.prev_a[ids] = 0
        self.t[ids] = 0
        self.hold[ids] = 0; self.success[ids] = False; self.max_prog[ids] = 0

    def _post_reset(self, ids):
        """after kinematics: handle start position and perception history"""
        hb, _, _, _ = self._handle()
        n = len(ids)
        self.h0[ids] = hb[ids]
        hv = hb[ids] + self.h_bias[ids]
        self.h_hist[ids] = hv[:, None].expand(n, self.H, 3)
        prop = torch.cat([self.target[ids], torch.zeros(n, 7, device=self.dev), torch.full((n, 1), G_OPEN, device=self.dev)], -1)
        self.prop_hist[ids] = prop[:, None].expand(n, 2, 15)

    def reset(self):
        ids = torch.arange(self.N, device=self.dev)
        self.reset_idx(ids)
        wp.capture_launch(self.graph_kin)
        self._post_reset(ids)
        return self.obs()

    # ------------------------------------------------------------------
    def _handle(self):
        """true handle point, outward panel normal, bar axis (base frame) and progress of the active mechanism"""
        ar = torch.arange(self.N, device=self.dev)
        bids = torch.tensor(self.mb, device=self.dev)[self.mech]
        bp = self.xpos[ar, bids]
        bR = self.xmat[ar, bids].reshape(self.N, 3, 3)
        hc = torch.stack(self.hc)[self.mech]
        loc = hc + torch.stack([-self.s_off, 0 * self.s_off, 0 * self.s_off], -1)
        hw = bp + (bR @ loc[..., None])[..., 0]
        Rb = self.base_R.T @ bR
        normal = -Rb[:, :, 0]
        bar = torch.where((self.kind == 0)[:, None], Rb[:, :, 1],
                          torch.where((self.kind == 1)[:, None], Rb[:, :, 2], torch.zeros_like(normal)))
        qm = self.qpos[ar, self.mq[self.mech]]
        prog = torch.where(self.mech == 0, qm / DRAWER_GOAL, qm / DOOR_GOAL)
        ok = torch.where(self.mech == 0, qm >= DRAWER_SUCC, qm >= DOOR_SUCC)
        return self._to_base(hw), normal, bar, (prog, ok, qm)

    def _grasp(self):
        ee_p = self.xpos[:, self.ee_b]
        ee_R = self.xmat[:, self.ee_b].reshape(self.N, 3, 3)
        grasp_w = ee_p + ee_R @ torch.tensor(scene.GRASP_OFS, device=self.dev, dtype=torch.float32)
        Rb = self.base_R.T @ ee_R
        return self._to_base(grasp_w), -Rb[:, :, 2], Rb[:, :, 1]

    def _push_hist(self, handle_b):
        R = self.randomize
        noise = 0.003 * torch.randn(self.N, 3, device=self.dev, generator=self.gen) if R else 0
        self.h_hist = torch.roll(self.h_hist, 1, 1)
        self.h_hist[:, 0] = handle_b + self.h_bias + noise
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
        grasp_b, appr_b, fing_b = self._grasp()
        _, normal, bar, _ = self._handle()
        normal_v = (self.yerr_R @ normal[..., None])[..., 0]
        bar_v = (self.yerr_R @ bar[..., None])[..., 0]
        o = build_obs_torch(prop[:, :7], prop[:, 7:14], prop[:, 14], self.target, self.gtarget, grasp_b, appr_b, fing_b,
                            hv, normal_v, bar_v, self.hsize_v, hv - (self.h0 + self.h_bias), self.last_a)
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
        handle_b, normal, bar, (prog, ok, qm) = self._handle()
        self._push_hist(handle_b)

        grasp_b, appr_b, fing_b = self._grasp()
        d = torch.norm(grasp_b - handle_b, dim=-1)
        near = 1 - torch.tanh(d / 0.1)
        r_reach = near + 0.5 * (1 - torch.tanh(d / 0.02))
        r_appr = 0.5 * torch.clamp((appr_b * -normal).sum(-1), 0, 1) * near
        r_fing = 0.5 * (1 - torch.abs((fing_b * bar).sum(-1))) * near
        r_open = 8.0 * torch.clamp(prog, 0, 1) + 2.0 * ok.float()
        r_rate = -0.02 * ((action - old_last) ** 2).sum(-1)
        r_vel = -2e-4 * (self.qvel[:, self.va] ** 2).sum(-1)
        r_touch = torch.zeros(self.N, device=self.dev)
        nc = int(self.nacon.item())
        if nc:
            g = self.con_geom[:nc]; w = self.con_wid[:nc]
            bad = (self.link_g[g[:, 0]] & self.env_g[g[:, 1]]) | (self.link_g[g[:, 1]] & self.env_g[g[:, 0]])
            r_touch.index_add_(0, w[bad].long(), torch.ones(int(bad.sum().item()), device=self.dev))
        r_touch = -1.0 * (r_touch > 0).float()
        bad_state = ~torch.isfinite(grasp_b).all(-1) | ~torch.isfinite(qm)
        rew = r_reach + r_appr + r_fing + r_open + r_rate + r_vel + r_touch - 10.0 * bad_state.float()
        rew = torch.nan_to_num(rew, nan=-10.0)

        self.hold = torch.where(ok, self.hold + 1, torch.zeros_like(self.hold))
        self.success |= self.hold >= SUCC_HOLD
        self.max_prog = torch.maximum(self.max_prog, torch.nan_to_num(prog))
        timeout = self.t >= EP_LEN
        done = bad_state | timeout
        info = {"success": self.success.clone(), "max_dz": self.max_prog.clone(), "caduto": bad_state, "d": d,
                "t": self.t.clone(), "touch": (r_touch < 0), "mech": self.mech.clone()}
        ids = done.nonzero(as_tuple=False).squeeze(-1)
        if len(ids):
            self.reset_idx(ids)
            wp.capture_launch(self.graph_kin)
            self._post_reset(ids)
        return self.obs(), rew, done, timeout, info


if __name__ == "__main__":
    import time
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4096
    env = OpenArmCabinetEnv(N)
    o = env.reset()
    print("obs", o.shape, "substeps", env.substeps)
    for i in range(5):
        env.step(torch.zeros(N, ACT_DIM, device=env.dev))
    torch.cuda.synchronize(); t0 = time.time(); T = 60
    for i in range(T):
        o, r, d, to, info = env.step(torch.randn(N, ACT_DIM, device=env.dev) * 0.5)
    torch.cuda.synchronize(); dt = time.time() - t0
    print(f"N={N}: {T*N/dt:.0f} control steps/s, r={r.mean().item():.3f}, obs finite {torch.isfinite(o).all().item()}")
    _, _, _, (prog, ok, qm) = env._handle()
    for mi in range(3):
        sel = env.mech == mi
        print("mech", mi, "n", int(sel.sum()), "q mean", qm[sel].mean().item(), "max", qm[sel].max().item())
