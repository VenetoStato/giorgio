"""Ambiente vettorizzato GPU (mujoco_warp + torch): OpenArm 2.0 standalone (MJCF ufficiale, braccio destro + pinza),
prendi il cubo sul tavolo e sollevalo di 10 cm.

Osservazioni (43) tutte nel FRAME BASE DEL BRACCIO (openarm_right_base_link):
  q braccio (7), qd braccio *0.1 (7), q pinza (1), target correnti (8), punto di presa da FK (3),
  posizione cubo "da visione" (3, rumore + bias + latenza), cubo - punto di presa (3), obiettivo (3), ultima azione (8)
Azioni (8): 7 incrementi del target di posizione dei giunti (0.05 rad/passo, 25 Hz) + comando pinza assoluto.
La logica di osservazione/azione e' in policy_io.py ed e' la STESSA usata su CPU (standalone e Giorgio).
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
from policy_io import (ACT_SCALE, CTRL_DT, EP_LEN, GOAL_DZ, OBS_DIM, ACT_DIM, Q_HOME, SUCC_DZ, SUCC_HOLD,
                       grip_cmd, build_obs_torch)


class OpenArmLiftEnv:
    def __init__(self, num_envs=4096, device="cuda:0", randomize=True, seed=0, nconmax=48, njmax=300, v2=True):
        self.N = num_envs
        self.dev = torch.device(device)
        self.randomize = randomize
        self.gen = torch.Generator(device=self.dev).manual_seed(seed)
        self.v2 = v2
        self.p_obst = float(os.environ.get("P_OBST", "0.5"))   # r2-r4: 0.5, r5: 0.75
        sp = scene.build_standalone(obstacle=v2)
        # gravcomp nominale 0.5 solo per abilitare il campo in mujoco_warp: viene randomizzato in [0,1] per ambiente
        for b in sp.bodies:
            if b.name.startswith("openarm_right"):
                b.gravcomp = 0.5
        self.mjm = m = sp.compile()
        mjd = mujoco.MjData(m)
        self.substeps = int(round(CTRL_DT / m.opt.timestep))
        self.dt = CTRL_DT
        self.base_b = m.body(scene.BASE_BODY).id
        self.ee_b = m.body(scene.EE_BODY).id
        self.cube_b = m.body("cube").id
        self.cube_g = m.geom("cube_g").id
        self.table_g = m.geom("table").id
        self.qa = torch.tensor([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS], device=self.dev)
        self.va = torch.tensor([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS], device=self.dev)
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        self.qc = m.joint("cube_free").qposadr[0]
        self.vc = m.joint("cube_free").dofadr[0]
        self.act_arm = [m.actuator(a).id for a in scene.ARM_ACT]
        self.act_f = m.actuator(scene.FINGER_ACT).id
        self.lo = torch.tensor([m.actuator_ctrlrange[i, 0] for i in self.act_arm], device=self.dev, dtype=torch.float32)
        self.hi = torch.tensor([m.actuator_ctrlrange[i, 1] for i in self.act_arm], device=self.dev, dtype=torch.float32)
        self.arm_bodies = [i for i in range(m.nbody) if m.body(i).name.startswith("openarm_right")]
        self.half0 = float(m.geom_size[self.cube_g][0])
        self.mid_table = int(m.body_mocapid[m.body("table_body").id])
        # v2: contatti vietati = segmenti del braccio (non le dita) col tavolo, qualsiasi parte del braccio con l'ostacolo
        fingers = {m.body("openarm_right_ee_inner_finger").id, m.body("openarm_right_ee_outer_finger").id}
        arm_g = torch.zeros(m.ngeom, dtype=torch.bool); link_g = torch.zeros(m.ngeom, dtype=torch.bool)
        for g in range(m.ngeom):
            b = int(m.geom_bodyid[g])
            if m.body(b).name.startswith("openarm_right") and m.geom_contype[g]:
                arm_g[g] = True
                if b not in fingers:
                    link_g[g] = True
        self.arm_g, self.link_g = arm_g.to(self.dev), link_g.to(self.dev)
        self.is_table = torch.zeros(m.ngeom, dtype=torch.bool, device=self.dev); self.is_table[self.table_g] = True
        self.is_obst = torch.zeros(m.ngeom, dtype=torch.bool, device=self.dev)
        if v2:
            self.mid_obst = int(m.body_mocapid[m.body("obst_body").id])
            self.is_obst[m.geom("obst").id] = True
        self.table_pos0 = m.geom_pos[self.table_g].copy()
        self.base_z = None

        with wp.ScopedDevice(device):
            self.wm = mjw.put_model(m)
            self.wd = mjw.put_data(m, mjd, nworld=self.N, nconmax=nconmax, njmax=njmax)
            if randomize:
                from mjlab.sim.randomization import expand_model_fields
                expand_model_fields(self.wm, self.N, ["geom_size", "geom_rbound", "geom_aabb", "geom_friction",
                                                      "body_mass", "body_inertia", "body_gravcomp", "actuator_gainprm",
                                                      "actuator_biasprm", "dof_damping"])
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
        self.mocap_pos = T(self.wd.mocap_pos)
        self.nacon = T(self.wd.nacon)
        self.con_geom, self.con_wid = T(self.wd.contact.geom), T(self.wd.contact.worldid)
        self.act_ = T(self.wd.act) if m.na else None
        if randomize:
            self.m_size, self.m_rbound, self.m_aabb = T(self.wm.geom_size), T(self.wm.geom_rbound), T(self.wm.geom_aabb)
            self.m_fric = T(self.wm.geom_friction)
            self.m_mass, self.m_inertia, self.m_gc = T(self.wm.body_mass), T(self.wm.body_inertia), T(self.wm.body_gravcomp)
            self.m_gain, self.m_bias, self.m_damp = T(self.wm.actuator_gainprm), T(self.wm.actuator_biasprm), T(self.wm.dof_damping)
            self.gain0, self.bias0, self.damp0 = self.m_gain[0].clone(), self.m_bias[0].clone(), self.m_damp[0].clone()
            self.rbound0, self.aabb0 = float(self.m_rbound[0, self.cube_g]), self.m_aabb[0, self.cube_g].clone()
        N, d = self.N, self.dev
        self.target = torch.zeros(N, 7, device=d)
        self.gtarget = torch.zeros(N, device=d)
        self.last_a = torch.zeros(N, ACT_DIM, device=d)
        self.prev_a = torch.zeros(N, ACT_DIM, device=d)
        self.t = torch.zeros(N, dtype=torch.long, device=d)
        self.z0 = torch.zeros(N, device=d)               # quota iniziale del cubo (frame base)
        self.goal = torch.zeros(N, 3, device=d)
        self.table_z = torch.zeros(N, device=d)
        self.hold = torch.zeros(N, dtype=torch.long, device=d)
        self.success = torch.zeros(N, dtype=torch.bool, device=d)
        self.max_dz = torch.zeros(N, device=d)
        # latenze e rumore
        self.H = 4
        self.cube_hist = torch.zeros(N, self.H, 3, device=d)
        self.cube_delay = torch.zeros(N, dtype=torch.long, device=d)
        self.cube_bias = torch.zeros(N, 3, device=d)
        self.prop_hist = torch.zeros(N, 2, 15, device=d)       # q(7), qd(7), qf(1)
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

    # ------------------------------------------------------------------
    def reset_idx(self, ids):
        n = len(ids)
        if n == 0:
            return
        R = self.randomize
        bz = float(self.base_p[2])
        if R:
            half = self._rand(n, 0.02, 0.03)
            s = half / self.half0
            self.m_size[ids, self.cube_g] = half[:, None].expand(n, 3)
            self.m_rbound[ids, self.cube_g] = self.rbound0 * s
            self.m_aabb[ids, self.cube_g] = self.aabb0 * s[:, None, None]
            mass = self._rand(n, 0.03, 0.25)
            self.m_mass[ids, self.cube_b] = mass
            self.m_inertia[ids, self.cube_b] = (mass * (2 * half) ** 2 / 6)[:, None].expand(n, 3)
            fr = self.m_fric[ids]
            fr[:, self.cube_g, 0] = self._rand(n, 0.5, 1.2)
            self.m_fric[ids] = fr
            dz = self._rand(n, -0.40, -0.32)
            mp = self.mocap_pos[ids]
            mp[:, self.mid_table, 2] = bz + dz - 0.02
            if self.v2:
                edge = self._rand(n, 0.0, 0.20)                       # bordo anteriore del tavolo (frame base)
                mp[:, self.mid_table, 0] = self.base_p[0] + edge + 0.34
                ox = self._rand(n, 0.12, 0.20); oy = self._rand(n, -0.15, 0.05); oh = self._rand(n, 0.04, 0.11)
                present = torch.rand(n, device=self.dev, generator=self.gen) < self.p_obst
                mp[:, self.mid_obst, 0] = self.base_p[0] + ox
                mp[:, self.mid_obst, 1] = self.base_p[1] + oy
                mp[:, self.mid_obst, 2] = torch.where(present, bz + dz + oh - 0.06, torch.full_like(oh, -3.0))
            self.mocap_pos[ids] = mp
            kp = self._rand(n * 8, 0.8, 1.2).reshape(n, 8)
            kv = self._rand(n * 8, 0.8, 1.2).reshape(n, 8)
            g = self.gain0[None].repeat(n, 1, 1); b = self.bias0[None].repeat(n, 1, 1)
            g[:, :, 0] *= kp; b[:, :, 1] *= kp; b[:, :, 2] *= kv
            self.m_gain[ids], self.m_bias[ids] = g, b
            self.m_damp[ids] = self.damp0 * self._rand(n, 0.7, 1.3)[:, None]
            gc = self.m_gc[ids]
            gc[:, self.arm_bodies] = self._rand(n, 0.0, 1.0)[:, None]
            self.m_gc[ids] = gc
            self.cube_delay[ids] = torch.randint(0, 4, (n,), device=self.dev, generator=self.gen)
            self.prop_delay[ids] = torch.randint(0, 2, (n,), device=self.dev, generator=self.gen)
            self.act_delay[ids] = torch.rand(n, device=self.dev, generator=self.gen) < 0.3
            self.cube_bias[ids] = (torch.rand(n, 3, device=self.dev, generator=self.gen) - 0.5) * 0.01
        else:
            half = torch.full((n,), self.half0, device=self.dev)
            dz = torch.full((n,), scene.TABLE_DZ, device=self.dev)
            self.cube_delay[ids] = 0; self.prop_delay[ids] = 0; self.act_delay[ids] = False; self.cube_bias[ids] = 0
        self.table_z[ids] = dz
        q = self.qpos[ids]
        qh = torch.tensor(Q_HOME, device=self.dev)[None] + (torch.rand(n, 7, device=self.dev, generator=self.gen) - 0.5) * 2 * \
            torch.tensor([0.25, 0.15, 0.3, 0.3, 0.3, 0.3, 0.3], device=self.dev)
        qh = torch.clamp(qh, self.lo, self.hi)
        q[:, self.qa] = qh
        q[:, self.qf[0]] = -0.7854; q[:, self.qf[1]] = -0.7854
        # cubo: posizione casuale nel frame base -> mondo (base standalone: nessuna rotazione)
        cx = self._rand(n, 0.25, 0.40); cy = self._rand(n, -0.22, 0.0)
        if R and self.v2:     # l'ostacolo non deve compenetrare il cubo
            mp = self.mocap_pos[ids]
            mp[:, self.mid_obst, 0] = torch.minimum(mp[:, self.mid_obst, 0], self.base_p[0] + cx - half - 0.04)
            self.mocap_pos[ids] = mp
        cz = dz + half + 0.001
        pb = torch.stack([cx, cy, cz], -1)
        pw = pb @ self.base_R.T + self.base_p
        yaw = self._rand(n, -math.pi, math.pi)
        q[:, self.qc:self.qc + 3] = pw
        q[:, self.qc + 3:self.qc + 7] = torch.stack([torch.cos(yaw / 2), 0 * yaw, 0 * yaw, torch.sin(yaw / 2)], -1)
        self.qpos[ids] = q
        self.qvel[ids] = 0
        self.qacc_ws[ids] = 0
        c = self.ctrl[ids]
        c[:, self.act_arm] = qh
        c[:, self.act_f] = -0.7854
        self.ctrl[ids] = c
        self.target[ids] = qh
        self.gtarget[ids] = -0.7854
        self.last_a[ids] = 0; self.prev_a[ids] = 0
        self.t[ids] = 0
        self.z0[ids] = cz
        self.goal[ids] = pb + torch.tensor([0, 0, GOAL_DZ], device=self.dev)
        self.hold[ids] = 0; self.success[ids] = False; self.max_dz[ids] = 0
        pv = pb + self.cube_bias[ids]
        self.cube_hist[ids] = pv[:, None].expand(n, self.H, 3)
        prop = torch.cat([qh, torch.zeros_like(qh), torch.full((n, 1), -0.7854, device=self.dev)], -1)
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
        cube_b = self._to_base(self.qpos[:, self.qc:self.qc + 3])
        return grasp_b, cube_b

    def _push_hist(self):
        _, cube_b = self._state()
        noise = 0.003 * torch.randn(self.N, 3, device=self.dev, generator=self.gen) if self.randomize else 0
        self.cube_hist = torch.roll(self.cube_hist, 1, 1)
        self.cube_hist[:, 0] = cube_b + self.cube_bias + noise
        prop = torch.cat([self.qpos[:, self.qa], self.qvel[:, self.va], self.qpos[:, self.qf[0]:self.qf[0] + 1]], -1)
        if self.randomize:
            prop = prop + torch.cat([0.003 * torch.randn(self.N, 7, device=self.dev, generator=self.gen),
                                     0.05 * torch.randn(self.N, 7, device=self.dev, generator=self.gen),
                                     0.01 * torch.randn(self.N, 1, device=self.dev, generator=self.gen)], -1)
        self.prop_hist = torch.roll(self.prop_hist, 1, 1)
        self.prop_hist[:, 0] = prop

    def obs(self):
        ar = torch.arange(self.N, device=self.dev)
        cube_v = self.cube_hist[ar, self.cube_delay]
        prop = self.prop_hist[ar, self.prop_delay]
        grasp_b, _ = self._state()
        o = build_obs_torch(prop[:, :7], prop[:, 7:14], prop[:, 14], self.target, self.gtarget, grasp_b, cube_v, self.goal, self.last_a)
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

        grasp_b, cube_b = self._state()
        d = torch.norm(grasp_b - cube_b, dim=-1)
        dz = cube_b[:, 2] - self.z0
        near = (d < 0.035).float()
        r_reach = (1 - torch.tanh(d / 0.1)) + 0.5 * (1 - torch.tanh(d / 0.02))
        # v3/v4: oltre i 16 cm la ricompensa di sollevamento scende (la v2 portava il cubo a ~50 cm; v3 coeff. 8, v4 coeff. 25)
        r_lift = (4.0 * torch.clamp(dz / GOAL_DZ, 0, 1) - 25.0 * torch.clamp(dz - 0.16, 0, 0.5)) * near
        lifted = (dz > 0.02).float()
        r_goal = 4.0 * (1 - torch.tanh(torch.abs(dz - GOAL_DZ) / 0.05)) * lifted * near
        r_rate = -0.02 * ((action - old_last) ** 2).sum(-1)
        r_vel = -2e-4 * (self.qvel[:, self.va] ** 2).sum(-1)
        r_touch = torch.zeros(self.N, device=self.dev)
        if self.v2:
            nc = int(self.nacon.item())
            if nc:
                g = self.con_geom[:nc]; w = self.con_wid[:nc]
                bad = (self.link_g[g[:, 0]] & self.is_table[g[:, 1]]) | (self.link_g[g[:, 1]] & self.is_table[g[:, 0]]) | \
                      (self.arm_g[g[:, 0]] & self.is_obst[g[:, 1]]) | (self.arm_g[g[:, 1]] & self.is_obst[g[:, 0]])
                r_touch.index_add_(0, w[bad].long(), torch.ones(int(bad.sum().item()), device=self.dev))
            r_touch = -1.5 * (r_touch > 0).float()
        caduto = (cube_b[:, 2] < self.table_z - 0.05) | (torch.norm(cube_b[:, :2], dim=-1) > 0.9) | ~torch.isfinite(cube_b).all(-1)
        rew = r_reach + r_lift + r_goal + r_rate + r_vel + r_touch - 10.0 * caduto.float()
        rew = torch.nan_to_num(rew, nan=-10.0)

        ok = (dz >= SUCC_DZ) & (d < 0.05)
        self.hold = torch.where(ok, self.hold + 1, torch.zeros_like(self.hold))
        self.success |= self.hold >= SUCC_HOLD
        self.max_dz = torch.maximum(self.max_dz, torch.where(d < 0.05, dz, torch.zeros_like(dz)))
        timeout = self.t >= EP_LEN
        done = caduto | timeout
        info = {"success": self.success.clone(), "max_dz": self.max_dz.clone(), "caduto": caduto, "d": d, "t": self.t.clone(), "touch": (r_touch < 0)}
        ids = done.nonzero(as_tuple=False).squeeze(-1)
        if len(ids):
            self.reset_idx(ids)
            wp.capture_launch(self.graph_kin)
        return self.obs(), rew, done, timeout, info


if __name__ == "__main__":
    import time
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4096
    env = OpenArmLiftEnv(N)
    o = env.reset()
    print("obs", o.shape, "substeps", env.substeps)
    torch.cuda.synchronize(); t0 = time.time(); T = 60
    for i in range(T):
        o, r, d, to, info = env.step(torch.randn(N, ACT_DIM, device=env.dev) * 0.5)
    torch.cuda.synchronize(); dt = time.time() - t0
    print(f"N={N}: {T*N/dt:.0f} passi controllo/s, r={r.mean().item():.3f}, obs finite {torch.isfinite(o).all().item()}")
    print("mem GPU MB", torch.cuda.max_memory_allocated() / 1e6)
    print("ncon max", wp.to_torch(env.wd.nacon).max().item() if hasattr(env.wd, 'nacon') else '?')
