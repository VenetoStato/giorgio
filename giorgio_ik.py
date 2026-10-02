"""IK a 7 giunti per le braccia OpenArm (DLS sullo Jacobiano MuJoCo, limiti di giunto, piu' semi)."""
import mujoco
import numpy as np


class ArmIK:
    def __init__(self, m, side, site):
        self.m, self.d = m, mujoco.MjData(m)
        self.jids = [m.joint(f"openarm_{side}_joint{k}").id for k in range(1, 8)]
        self.qadr = np.array([m.jnt_qposadr[j] for j in self.jids])
        self.dadr = np.array([m.jnt_dofadr[j] for j in self.jids])
        self.lo, self.hi = m.jnt_range[self.jids, 0], m.jnt_range[self.jids, 1]
        self.site = m.site(site).id

    def fk(self, qfull, q):
        self.d.qpos[:] = qfull
        self.d.qpos[self.qadr] = q
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_comPos(self.m, self.d)
        return self.d.site_xpos[self.site].copy(), self.d.site_xmat[self.site].reshape(3, 3).copy()

    def err(self, p, R, pt, Rt):
        e = np.zeros(6)
        e[:3] = pt - p
        q = np.zeros(4); mujoco.mju_mat2Quat(q, (Rt @ R.T).reshape(-1))
        mujoco.mju_quat2Vel(e[3:], q, 1.0)
        return e

    def solve1(self, qfull, q0, pt, Rt, iters=150, wrot=0.6):
        q = np.clip(np.array(q0, float), self.lo, self.hi)
        Jp, Jr = np.zeros((3, self.m.nv)), np.zeros((3, self.m.nv))
        W = np.array([1, 1, 1, wrot, wrot, wrot])
        for _ in range(iters):
            p, R = self.fk(qfull, q)
            e = self.err(p, R, pt, Rt)
            if np.linalg.norm(e[:3]) < 5e-4 and np.linalg.norm(e[3:]) < 5e-3:
                break
            mujoco.mj_jacSite(self.m, self.d, Jp, Jr, self.site)
            J = np.vstack([Jp, Jr])[:, self.dadr] * W[:, None]
            dq = J.T @ np.linalg.solve(J @ J.T + 2e-4 * np.eye(6), e * W)
            q = np.clip(q + np.clip(dq, -0.3, 0.3), self.lo, self.hi)
        p, R = self.fk(qfull, q)
        e = self.err(p, R, pt, Rt)
        return q, float(np.linalg.norm(e[:3])), float(np.linalg.norm(e[3:]))

    def solve(self, qfull, q0, pt, Rt, seeds=16, rng=None):
        rng = rng or np.random.default_rng(0)
        best = None
        for k in range(seeds):
            s = q0 if k == 0 else np.clip(q0 + rng.normal(0, 0.6, 7), self.lo, self.hi)
            q, ep, er = self.solve1(qfull, s, pt, Rt)
            ok = ep < 2e-3 and er < 2e-2
            cost = (0 if ok else 100 + 100 * ep + 10 * er) + float(np.sum(np.abs(q - q0)))
            if best is None or cost < best[0]:
                best = (cost, q, ok, ep, er)
        return best[1], best[2], best[3], best[4]
