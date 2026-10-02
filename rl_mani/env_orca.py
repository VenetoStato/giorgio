"""Ambiente vettorizzato GPU (mujoco_warp): mano ORCA v2 palmo in su ruota un cubo
attorno all'asse verticale (+z, senso antiorario visto dall'alto).

Tutto lo stato vive su GPU (torch <-> warp senza copie)."""
import os
import math
import numpy as np
import torch
import mujoco
import warp as wp
import mujoco_warp as mjw

QUI = os.path.dirname(os.path.abspath(__file__))
XML = os.path.join(QUI, "orca_cubo_rl.xml")

# centro palmo (frame mondo) e quota superficie palmo, da build_model.py
PALMO = (0.004, -0.145)
Z_PALMO = 0.272


def quat_mul(a, b):
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack([aw * bw - ax * bx - ay * by - az * bz,
                        aw * bx + ax * bw + ay * bz - az * by,
                        aw * by - ax * bz + ay * bw + az * bx,
                        aw * bz + ax * by - ay * bx + az * bw], -1)


def quat_conj(q):
    return torch.cat([q[..., :1], -q[..., 1:]], -1)


def quat_to_mat6(q):
    """prime due colonne della matrice di rotazione (rappresentazione 6D)."""
    w, x, y, z = q.unbind(-1)
    c0 = torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)], -1)
    c1 = torch.stack([2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)], -1)
    return torch.cat([c0, c1], -1)


def quat_axis_z(q):
    """asse z locale del cubo espresso nel mondo (non usato per simmetria cubo)."""
    w, x, y, z = q.unbind(-1)
    return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], -1)


class OrcaCubeEnv:
    def __init__(self, num_envs=4096, device="cuda:0", substeps=8, ep_len=400,
                 action_scale=0.10, randomize=True, seed=0, registra=False, spinte=None):
        self.N = num_envs
        self.dev = torch.device(device)
        self.substeps = substeps
        self.ep_len = ep_len
        self.action_scale = action_scale
        self.randomize = randomize
        self.spinte = randomize if spinte is None else spinte
        self.registra = registra
        self.frames = []  # qpos a ogni passo fisico (solo se registra)
        self.gen = torch.Generator(device=self.dev).manual_seed(seed)

        wp.init()
        self.mjm = mujoco.MjModel.from_xml_path(XML)
        mjd = mujoco.MjData(self.mjm)
        m = self.mjm
        self.nu = m.nu
        self.dt = m.opt.timestep * substeps
        self.cube_body = m.body("cubo").id
        self.cube_geom = m.geom("cubo_col").id
        self.qadr_cube = m.jnt_qposadr[m.joint("cubo_libero").id]
        self.vadr_cube = m.jnt_dofadr[m.joint("cubo_libero").id]
        self.hand_qadr = torch.tensor([m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)], device=self.dev)
        self.hand_vadr = torch.tensor([m.jnt_dofadr[m.actuator_trnid[i, 0]] for i in range(m.nu)], device=self.dev)
        self.lo = torch.tensor(m.actuator_ctrlrange[:, 0], device=self.dev, dtype=torch.float32)
        self.hi = torch.tensor(m.actuator_ctrlrange[:, 1], device=self.dev, dtype=torch.float32)
        self.col_geoms = torch.tensor([g for g in range(m.ngeom) if m.geom_contype[g] and g != self.cube_geom], device=self.dev)
        # posa iniziale dita: leggermente flesse, pollice aperto
        q0 = np.zeros(m.nu, dtype=np.float32)
        names = [m.actuator(i).name for i in range(m.nu)]
        for i, n in enumerate(names):
            if "mcp" in n:
                q0[i] = 0.25
            if "pip" in n:
                q0[i] = 0.25
            if "t-abd" in n:
                q0[i] = 0.3
        self.q0 = torch.tensor(np.clip(q0, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]), device=self.dev, dtype=torch.float32)
        self.cube_half0 = float(m.geom_size[self.cube_geom][0])
        self.cube_mass0 = float(m.body_mass[self.cube_body])
        self.cube_inertia0 = m.body_inertia[self.cube_body].copy()
        self.kp0 = float(m.actuator_gainprm[0, 0])

        with wp.ScopedDevice(device):
            self.wm = mjw.put_model(m)
            self.wd = mjw.put_data(m, mjd, nworld=self.N, nconmax=48, njmax=220)
            if randomize:
                self._expand(["geom_size", "geom_rbound", "geom_aabb", "geom_friction", "body_mass",
                              "body_inertia", "actuator_gainprm", "actuator_biasprm", "dof_damping"])
            # grafo CUDA: 'substeps' passi fisici in un'unica cattura
            with wp.ScopedCapture() as cap:
                for _ in range(substeps):
                    mjw.step(self.wm, self.wd)
            self.graph = cap.graph
            if registra:
                with wp.ScopedCapture() as cap1:
                    mjw.step(self.wm, self.wd)
                self.graph1 = cap1.graph

        T = wp.to_torch
        self.qpos = T(self.wd.qpos)
        self.qvel = T(self.wd.qvel)
        self.ctrl = T(self.wd.ctrl)
        self.qacc_ws = T(self.wd.qacc_warmstart)
        self.xfrc = T(self.wd.xfrc_applied)
        self.qfrc_act = T(self.wd.qfrc_actuator)
        if randomize:
            self.m_size = T(self.wm.geom_size)
            self.m_rbound = T(self.wm.geom_rbound)
            self.m_aabb = T(self.wm.geom_aabb)
            self.m_fric = T(self.wm.geom_friction)
            self.m_mass = T(self.wm.body_mass)
            self.m_inertia = T(self.wm.body_inertia)
            self.m_gain = T(self.wm.actuator_gainprm)
            self.m_bias = T(self.wm.actuator_biasprm)
            self.m_damp = T(self.wm.dof_damping)
            self.damp0 = self.m_damp[0].clone()
            self.rbound0 = float(self.m_rbound[0, self.cube_geom])
            self.aabb0 = self.m_aabb[0, self.cube_geom].clone()

        N, d = self.N, self.dev
        self.target = torch.zeros(N, self.nu, device=d)
        self.prev_quat = torch.zeros(N, 4, device=d)
        self.t = torch.zeros(N, dtype=torch.long, device=d)
        self.rot_acc = torch.zeros(N, device=d)  # rotazione cumulata episodio [rad]
        self.last_rate = torch.zeros(N, device=d)
        self.palmo = torch.tensor([PALMO[0], PALMO[1], Z_PALMO], device=d)
        self.obs_dim = 16 * 3 + 3 + 6 + 3 + 3 + 1
        self.act_dim = self.nu
        self.ext_force = torch.zeros(N, 3, device=d)

    def _expand(self, fields):
        from mjlab.sim.randomization import expand_model_fields
        expand_model_fields(self.wm, self.N, fields)

    def _rand(self, n, lo, hi):
        return lo + (hi - lo) * torch.rand(n, device=self.dev, generator=self.gen)

    # ------------------------------------------------------------------
    def reset_idx(self, ids):
        n = len(ids)
        if n == 0:
            return
        m = self.mjm
        # randomizzazione di dominio
        if self.randomize:
            s = self._rand(n, 0.025, 0.030) / self.cube_half0          # lato 5.0-6.0 cm
            self.m_size[ids, self.cube_geom] = self.cube_half0 * s[:, None]
            self.m_rbound[ids, self.cube_geom] = self.rbound0 * s
            self.m_aabb[ids, self.cube_geom] = self.aabb0 * s[:, None, None]
            mass = self._rand(n, 0.03, 0.12)
            self.m_mass[ids, self.cube_body] = mass
            # inerzia cubo pieno: m*(2a)^2/6
            side = 2 * self.cube_half0 * s
            self.m_inertia[ids, self.cube_body] = (mass * side ** 2 / 6)[:, None].expand(n, 3)
            f = self._rand(n, 0.5, 1.2)
            fr = self.m_fric[ids]
            fr[:, :, 0] = f[:, None]
            self.m_fric[ids] = fr
            kp = self.kp0 * self._rand(n, 0.75, 1.25)
            g = self.m_gain[ids]
            g[:, :, 0] = kp[:, None]
            self.m_gain[ids] = g
            b = self.m_bias[ids]
            b[:, :, 1] = -kp[:, None]
            self.m_bias[ids] = b
            self.m_damp[ids] = self.damp0 * self._rand(n, 0.7, 1.4)[:, None]
            half = self.cube_half0 * s
        else:
            half = torch.full((n,), self.cube_half0, device=self.dev)
        q = self.qpos[ids]
        qd = torch.zeros_like(self.qvel[ids])
        qh = self.q0 + 0.08 * (torch.rand(n, self.nu, device=self.dev, generator=self.gen) - 0.5) * 2
        qh = torch.clamp(qh, self.lo, self.hi)
        q[:, self.hand_qadr] = qh
        a = self.qadr_cube
        q[:, a + 0] = PALMO[0] + self._rand(n, -0.01, 0.01)
        q[:, a + 1] = PALMO[1] + self._rand(n, -0.01, 0.01)
        q[:, a + 2] = Z_PALMO + half + 0.004
        yaw = self._rand(n, -math.pi, math.pi)
        quat = torch.stack([torch.cos(yaw / 2), torch.zeros_like(yaw), torch.zeros_like(yaw), torch.sin(yaw / 2)], -1)
        q[:, a + 3:a + 7] = quat
        self.qpos[ids] = q
        self.qvel[ids] = qd
        self.qacc_ws[ids] = 0
        self.ctrl[ids] = qh
        self.target[ids] = qh
        self.prev_quat[ids] = quat
        self.t[ids] = 0
        self.rot_acc[ids] = 0
        self.last_rate[ids] = 0
        self.ext_force[ids] = 0

    def reset(self):
        self.reset_idx(torch.arange(self.N, device=self.dev))
        return self.obs()

    # ------------------------------------------------------------------
    def obs(self):
        a, v = self.qadr_cube, self.vadr_cube
        qh = self.qpos[:, self.hand_qadr]
        qn = 2 * (qh - self.lo) / (self.hi - self.lo) - 1
        tn = 2 * (self.target - self.lo) / (self.hi - self.lo) - 1
        qdh = self.qvel[:, self.hand_vadr] * 0.1
        pos = (self.qpos[:, a:a + 3] - self.palmo) * 10
        quat = self.qpos[:, a + 3:a + 7]
        r6 = quat_to_mat6(quat)
        lin = self.qvel[:, v:v + 3] * 2
        ang = self.qvel[:, v + 3:v + 6] * 0.3
        o = torch.cat([qn, tn, qdh, pos, r6, lin, ang, self.last_rate[:, None] * 0.5], -1)
        if self.randomize:
            o = o + 0.01 * torch.randn(o.shape, device=self.dev, generator=self.gen)
        return torch.nan_to_num(o).clamp(-10, 10)

    def step(self, action):
        action = action.clamp(-1, 1)
        old_target = self.target.clone()
        self.target = torch.clamp(self.target + self.action_scale * action, self.lo, self.hi)
        self.ctrl[:] = self.target
        # spinte casuali sul cubo (robustezza)
        if self.spinte:
            kick = torch.rand(self.N, device=self.dev, generator=self.gen) < 0.02
            newf = torch.randn(self.N, 3, device=self.dev, generator=self.gen) * 0.10
            self.ext_force = torch.where(kick[:, None], newf, self.ext_force * 0.9)
            self.xfrc[:, self.cube_body, :3] = self.ext_force
        if self.registra:
            for _ in range(self.substeps):
                wp.capture_launch(self.graph1)
                self.frames.append(self.qpos.clone())
        else:
            wp.capture_launch(self.graph)
        self.t += 1

        a, v = self.qadr_cube, self.vadr_cube
        quat = self.qpos[:, a + 3:a + 7]
        # rotazione attorno a z mondo nel passo (componente twist)
        qrel = quat_mul(quat, quat_conj(self.prev_quat))
        qrel = torch.where(qrel[:, :1] < 0, -qrel, qrel)
        dyaw = 2 * torch.atan2(qrel[:, 3], qrel[:, 0])
        rate = dyaw / self.dt
        self.prev_quat = quat.clone()
        self.last_rate = rate
        self.rot_acc += dyaw

        pos = self.qpos[:, a:a + 3]
        dxy = torch.norm(pos[:, :2] - self.palmo[:2], dim=-1)
        dz = pos[:, 2] - Z_PALMO
        caduto = (dz < 0.0) | (dxy > 0.075) | ~torch.isfinite(pos).all(-1)
        angv = self.qvel[:, v + 3:v + 6]
        linv = self.qvel[:, v:v + 3]

        r_rot = torch.clamp(rate, -0.5, 1.2)
        r_pos = -2.0 * dxy
        r_tilt = -0.05 * torch.norm(angv[:, :2], dim=-1).clamp(max=10)
        r_lin = -0.3 * torch.norm(linv, dim=-1).clamp(max=5)
        r_act = -0.02 * ((self.target - old_target) ** 2).sum(-1) / self.action_scale ** 2 / self.nu
        tau = self.qfrc_act[:, self.hand_vadr]
        r_tau = -0.05 * (tau ** 2).sum(-1)
        r_drop = -20.0 * caduto.float()
        rew = r_rot + r_pos + r_tilt + r_lin + r_act + r_tau + r_drop
        rew = torch.nan_to_num(rew, nan=-20.0)

        timeout = self.t >= self.ep_len
        done = caduto | timeout
        info = {"rate": rate, "caduto": caduto, "timeout": timeout,
                "rot_acc": self.rot_acc.clone(), "t": self.t.clone()}
        ids = done.nonzero(as_tuple=False).squeeze(-1)
        if len(ids):
            self.reset_idx(ids)
        return self.obs(), rew, done, timeout, info


if __name__ == "__main__":
    import time
    import sys
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4096
    env = OrcaCubeEnv(N)
    o = env.reset()
    print("obs", o.shape)
    torch.cuda.synchronize()
    t0 = time.time()
    T = 100
    nd = 0
    for i in range(T):
        o, r, d, to, info = env.step(torch.randn(N, env.nu, device=env.dev) * 0.5)
        nd += d.sum().item()
    torch.cuda.synchronize()
    dt = time.time() - t0
    print(f"N={N}: {T*N/dt:.0f} passi controllo/s, {T*N*env.substeps/dt:.0f} passi fisici/s, done={nd}, r={r.mean().item():.3f}")
    print("mem GPU MB", torch.cuda.max_memory_allocated() / 1e6)
