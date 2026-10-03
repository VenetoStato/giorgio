"""Esecuzione su CPU (MuJoCo standard) della politica addestrata, SENZA modifiche, su:
  --robot openarm  : OpenArm 2.0 standalone (MJCF ufficiale, braccio destro + pinza, gravcomp assente come nel file ufficiale)
  --robot giorgio  : braccio destro di Giorgio (giorgio_model.build, pinze OpenArm, gravcomp attiva come in Giorgio) sul banco

Unica cosa che cambia tra i due: da dove si leggono i dati. Osservazione e azione passano per policy_io.py e sono
espresse nel frame del body 'openarm_right_base_link' (ricavato a ogni passo da MuJoCo, come farebbe la TF del robot).

uso:
  python run_cpu.py eval  --robot giorgio --n 100 --policy politica_openarm_lift.pt --json valutazione/giorgio.json
  python run_cpu.py video --robot openarm --seconds 10 --out openarm_standalone.mp4
  python run_cpu.py video --robot giorgio --seconds 10 --out giorgio_transfer.mp4 --record giorgio_transfer.pkl
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
from policy_io import (ACT_DIM, ACT_SCALE, CTRL_DT, EP_LEN, GOAL_DZ, OBS_DIM, Q_HOME, SUCC_DZ, SUCC_HOLD, G_OPEN,
                       build_obs_np, grip_cmd)


def load_policy(path):
    from train import AttoreCritico
    ck = torch.load(path, map_location="cpu")
    ac = AttoreCritico(ck["obs_dim"], ck["act_dim"])
    ac.load_state_dict(ck["modello"])
    ac.eval()
    return ac


class Runner:
    def __init__(self, robot, policy, randomize=True, seed=0, ext=None, buffer=True):
        self.robot = robot
        if robot == "openarm":
            sp = scene.build_standalone()
        else:
            sp, self.bench_z = scene.build_giorgio(buffer=buffer)
        if ext:
            ext(sp)
        self.m = m = sp.compile()
        self.d = d = mujoco.MjData(m)
        self.pol = policy
        self.R = randomize
        self.rng = np.random.default_rng(seed)
        self.sub = int(round(CTRL_DT / m.opt.timestep))
        self.qa = np.array([m.joint(j).qposadr[0] for j in scene.ARM_JOINTS])
        self.va = np.array([m.joint(j).dofadr[0] for j in scene.ARM_JOINTS])
        self.qf = [m.joint(scene.FINGER_JOINT).qposadr[0], m.joint("openarm_right_finger_joint2").qposadr[0]]
        self.qc = m.joint("cube_free").qposadr[0]
        self.aa = np.array([m.actuator(a).id for a in scene.ARM_ACT])
        self.af = m.actuator(scene.FINGER_ACT).id
        self.lo, self.hi = m.actuator_ctrlrange[self.aa, 0].copy(), m.actuator_ctrlrange[self.aa, 1].copy()
        self.cg, self.cb = m.geom("cube_g").id, m.body("cube").id
        self.base, self.ee = m.body(scene.BASE_BODY).id, m.body(scene.EE_BODY).id
        self.gain0, self.bias0 = m.actuator_gainprm.copy(), m.actuator_biasprm.copy()
        self.half0, self.rb0, self.aabb0 = float(m.geom_size[self.cg][0]), float(m.geom_rbound[self.cg]), m.geom_aabb[self.cg].copy()
        self.q_init = d.qpos.copy()
        if robot == "openarm":
            self.table_top_w = scene.ARM_Z + scene.TABLE_DZ
        else:
            self.table_top_w = self.bench_z
        self.frame_cb = None

    # frame base del braccio, letto dal simulatore (sul robot reale: TF base_link -> openarm_right_base_link)
    def base_frame(self):
        return self.d.xpos[self.base].copy(), self.d.xmat[self.base].reshape(3, 3).copy()

    def to_base(self, p):
        bp, bR = self.base_frame()
        return (p - bp) @ bR

    def grasp_b(self):
        R = self.d.xmat[self.ee].reshape(3, 3)
        return self.to_base(self.d.xpos[self.ee] + R @ scene.GRASP_OFS)

    def reset(self):
        m, d, rng = self.m, self.d, self.rng
        mujoco.mj_resetData(m, d)
        d.qpos[:] = self.q_init
        if self.robot == "giorgio":                       # braccio sinistro a riposo, fuori dal banco
            for k, v in enumerate([0.0, 0.0, 0.0, 2.3, 0.0, 0.0, 0.0]):
                d.joint(f"openarm_left_joint{k + 1}").qpos = v
        if self.R:
            half = rng.uniform(0.02, 0.03); mass = rng.uniform(0.03, 0.25); fr = rng.uniform(0.5, 1.2)
            kp = rng.uniform(0.8, 1.2, 8); kv = rng.uniform(0.8, 1.2, 8)
            self.cube_delay, self.prop_delay = rng.integers(0, 4), rng.integers(0, 2)
            self.act_delay = rng.random() < 0.3
            self.cube_bias = (rng.random(3) - 0.5) * 0.01
        else:
            half, mass, fr = self.half0, 0.08, 0.9
            kp = kv = np.ones(8)
            self.cube_delay = self.prop_delay = 0; self.act_delay = False; self.cube_bias = np.zeros(3)
        s = half / self.half0
        m.geom_size[self.cg] = half; m.geom_rbound[self.cg] = self.rb0 * s; m.geom_aabb[self.cg] = self.aabb0 * s
        m.body_mass[self.cb] = mass; m.body_inertia[self.cb] = mass * (2 * half) ** 2 / 6
        m.geom_friction[self.cg][0] = fr
        m.actuator_gainprm[:] = self.gain0; m.actuator_biasprm[:] = self.bias0
        for k, ai in enumerate(list(self.aa) + [self.af]):
            m.actuator_gainprm[ai, 0] *= kp[k]; m.actuator_biasprm[ai, 1] *= kp[k]; m.actuator_biasprm[ai, 2] *= kv[k]
        qh = np.clip(np.array(Q_HOME) + (rng.random(7) - 0.5) * 2 * np.array([0.25, 0.15, 0.3, 0.3, 0.3, 0.3, 0.3]), self.lo, self.hi)
        d.qpos[self.qa] = qh
        d.qpos[self.qf] = G_OPEN
        mujoco.mj_kinematics(m, d)
        # cubo: posizione casuale nel frame base (stessa distribuzione dell'addestramento), appoggiato sul piano
        bp, bR = self.base_frame()
        pb = np.array([rng.uniform(0.25, 0.40), rng.uniform(-0.22, 0.0), 0.0])
        pw = bp + bR @ pb
        pw[2] = self.table_top_w + half + 0.001
        yaw = rng.uniform(-math.pi, math.pi)
        d.qpos[self.qc:self.qc + 3] = pw
        d.qpos[self.qc + 3:self.qc + 7] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
        d.ctrl[:] = 0
        for i in range(m.nu):                              # tutti gli altri attuatori tengono la posa attuale
            if m.actuator_trntype[i] == mujoco.mjtTrn.mjTRN_JOINT:
                d.ctrl[i] = d.qpos[m.jnt_qposadr[m.actuator_trnid[i, 0]]]
        d.ctrl[self.aa] = qh; d.ctrl[self.af] = G_OPEN
        mujoco.mj_forward(m, d)
        self.target, self.gtarget = qh.copy(), G_OPEN
        self.last_a = np.zeros(ACT_DIM); self.prev_a = np.zeros(ACT_DIM)
        cube_b = self.to_base(d.qpos[self.qc:self.qc + 3].copy())
        self.z0 = cube_b[2]
        self.goal = cube_b + [0, 0, GOAL_DZ]
        self.cube_hist = [cube_b + self.cube_bias] * 4
        prop = np.r_[qh, np.zeros(7), G_OPEN]
        self.prop_hist = [prop, prop]
        self.hold, self.success, self.max_dz, self.t = 0, False, 0.0, 0
        self.t_success = None

    def push_hist(self):
        d, rng = self.d, self.rng
        cube_b = self.to_base(d.qpos[self.qc:self.qc + 3].copy())
        noise = 0.003 * rng.standard_normal(3) if self.R else 0
        self.cube_hist = [cube_b + self.cube_bias + noise] + self.cube_hist[:3]
        prop = np.r_[d.qpos[self.qa], d.qvel[self.va], d.qpos[self.qf[0]]]
        if self.R:
            prop = prop + np.r_[0.003 * rng.standard_normal(7), 0.05 * rng.standard_normal(7), 0.01 * rng.standard_normal(1)]
        self.prop_hist = [prop, self.prop_hist[0]]

    def obs(self):
        cube_v = self.cube_hist[self.cube_delay]
        prop = self.prop_hist[self.prop_delay]
        return build_obs_np(prop[:7], prop[7:14], prop[14], self.target, self.gtarget, self.grasp_b(), cube_v, self.goal, self.last_a)

    def step(self):
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
        cube_b = self.to_base(self.d.qpos[self.qc:self.qc + 3].copy())
        dist = np.linalg.norm(self.grasp_b() - cube_b)
        dz = cube_b[2] - self.z0
        self.hold = self.hold + 1 if (dz >= SUCC_DZ and dist < 0.05) else 0
        if self.hold >= SUCC_HOLD and not self.success:
            self.success, self.t_success = True, self.t * CTRL_DT
        if dist < 0.05:
            self.max_dz = max(self.max_dz, dz)
        return dz, dist

    def episode(self, ep_len=EP_LEN):
        self.reset()
        for _ in range(ep_len):
            self.step()
        return dict(success=bool(self.success), max_dz_cm=round(100 * self.max_dz, 2),
                    t_success_s=self.t_success, cube_xy_base=[round(float(v), 3) for v in self.goal[:2]])


def table_ext(a):
    """solo standalone, per le diagnosi: sposta il bordo anteriore del tavolo (frame base) e/o la sua quota"""
    if a.table_dz is not None:
        scene.TABLE_DZ = a.table_dz
    if a.table_edge is None:
        return None
    def ext(sp):
        tb, g = sp.body("table_body"), sp.geom("table")
        x1 = 0.80
        tb.pos = [(a.table_edge + x1) / 2, tb.pos[1], tb.pos[2]]; g.size = [(x1 - a.table_edge) / 2, g.size[1], g.size[2]]
    return ext


def evaluate(a):
    pol = load_policy(a.policy)
    torch.set_num_threads(1)
    R = Runner(a.robot, pol, randomize=not a.nominal, seed=a.seed, buffer=not a.no_buffer, ext=table_ext(a))
    res = []
    t0 = time.time()
    for i in range(a.n):
        r = R.episode()
        res.append(r)
        if (i + 1) % 10 == 0:
            print(f"  {a.robot}: {i + 1}/{a.n} successi {sum(x['success'] for x in res)}  ({time.time() - t0:.0f} s)", flush=True)
    sr = float(np.mean([r["success"] for r in res]))
    k = sum(r["success"] for r in res)
    # intervallo di confidenza di Wilson al 95%
    z, n = 1.96, a.n
    c = (sr + z * z / (2 * n)) / (1 + z * z / n); h = z * math.sqrt(sr * (1 - sr) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    out = dict(robot=a.robot, table_edge_x=a.table_edge, table_dz=a.table_dz, giorgio_front_tray=(not a.no_buffer) if a.robot == "giorgio" else None, policy=os.path.basename(a.policy), episodes=a.n, randomized=not a.nominal, seed=a.seed,
               success_rate=round(sr, 4), successes=k, wilson95=[round(c - h, 3), round(c + h, 3)],
               mean_max_lift_cm=round(float(np.mean([r["max_dz_cm"] for r in res])), 2),
               mean_time_to_success_s=round(float(np.mean([r["t_success_s"] for r in res if r["success"]])), 2) if k else None,
               criterion=f"cube raised >= {SUCC_DZ * 100:.0f} cm above its initial height, within 5 cm of the gripper centre, "
                         f"for >= {SUCC_HOLD * CTRL_DT:.1f} s continuously, within a {EP_LEN * CTRL_DT:.0f} s episode",
               episodes_detail=res)
    print(json.dumps({k_: v for k_, v in out.items() if k_ != "episodes_detail"}, indent=1))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)


def video(a):
    import imageio
    pol = load_policy(a.policy)
    R = Runner(a.robot, pol, randomize=not a.nominal, seed=a.seed, buffer=not a.no_buffer)
    m, d = R.m, R.d
    W, H = 1920, 1080
    ren = mujoco.Renderer(m, H, W)
    opt = mujoco.MjvOption()
    cam = mujoco.MjvCamera()
    if a.robot == "openarm":
        cam.lookat[:] = [0.15, -0.12, scene.ARM_Z - 0.11]; cam.distance = 1.05; cam.azimuth = 214; cam.elevation = -17
    else:
        cam.lookat[:] = [0.16, -0.14, 1.14]; cam.distance = 1.2; cam.azimuth = 208; cam.elevation = -15
    writer = imageio.get_writer(a.out, fps=30, quality=8, macro_block_size=8)
    rec = dict(XP=[], XQ=[])
    state = {"tn": 0.0, "n": 0}
    nframes = int(a.seconds * 30)

    def cb():
        if d.time + 1e-9 >= state["tn"] and state["n"] < nframes:
            state["tn"] += 1 / 30; state["n"] += 1
            ren.update_scene(d, cam, opt)
            writer.append_data(ren.render())
            if a.record:
                rec["XP"].append(d.xpos.copy()); rec["XQ"].append(d.xquat.copy())
    R.frame_cb = cb
    eps = []
    while state["n"] < nframes:
        R.reset(); state["tn"] = d.time   # d.time ripartito da 0 a ogni reset
        steps = int(a.ep_seconds / CTRL_DT)
        for _ in range(steps):
            R.step()
            if state["n"] >= nframes:
                break
        eps.append(dict(success=R.success, max_dz_cm=round(100 * R.max_dz, 1)))
        print("  episodio", len(eps), eps[-1], flush=True)
    writer.close()
    print("video:", a.out, state["n"], "fotogrammi", eps)
    if a.record:
        save_record(m, rec, a.record, eps)


def save_record(m, rec, path, eps):
    """stesso formato di giorgio_v5.py --record (leggibile da render/to_npz.py e blender_render.py)"""
    import pickle
    geoms = []
    for g in range(m.ngeom):
        if m.geom_group[g] > 2 or (m.geom_rgba[g][3] == 0 and m.geom_matid[g] < 0):
            continue
        mat = m.material(m.geom_matid[g]).name if m.geom_matid[g] >= 0 else ""
        rgba = m.mat_rgba[m.geom_matid[g]] if m.geom_matid[g] >= 0 else m.geom_rgba[g]
        e = dict(name=m.geom(g).name, type=int(m.geom_type[g]), size=m.geom_size[g].copy(), body=int(m.geom_bodyid[g]),
                 pos=m.geom_pos[g].copy(), quat=m.geom_quat[g].copy(), mat=mat, rgba=np.array(rgba).copy(), body_name=m.body(m.geom_bodyid[g]).name)
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[g]
            e["vert"] = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]].copy()
            e["face"] = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]].copy()
        geoms.append(e)
    F = len(rec["XP"])
    anim_n = [n for n in ("eye_l", "eye_r", "mus_l", "mus_r") if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) >= 0]
    an = np.array([np.r_[m.geom_pos[m.geom(n).id], m.geom_quat[m.geom(n).id], m.geom_size[m.geom(n).id], m.geom_rgba[m.geom(n).id]] for n in anim_n])
    pickle.dump(dict(geoms=geoms, xpos=np.array(rec["XP"]), xquat=np.array(rec["XQ"]), zone=np.zeros(F, int), hum=[],
                     hum_sizes=np.zeros((F, 0, 3)), hum_rgba=np.zeros((F, 0, 4)), n_seg=7, face=np.zeros((F, 5)),
                     anim=np.repeat(an[None], F, 0) if len(anim_n) else np.zeros((F, 0, 14)), anim_names=anim_n,
                     states=["rl_policy"] * F, energy=np.zeros((F, 3)), body_names=[m.body(i).name for i in range(m.nbody)],
                     r_prot=0.0, r_warn=0.0, stats=dict(episodes=eps)), open(path, "wb"))
    print("registrazione:", path, F, "fotogrammi")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["eval", "video"])
    ap.add_argument("--robot", default="openarm", choices=["openarm", "giorgio"])
    ap.add_argument("--policy", default=os.path.join(QUI, "politica_openarm_lift.pt"))
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--nominal", action="store_true", help="senza randomizzazione/rumore/latenza")
    ap.add_argument("--json", default="")
    ap.add_argument("--table_edge", type=float, default=None, help="standalone: bordo anteriore tavolo [m, frame base]")
    ap.add_argument("--table_dz", type=float, default=None, help="standalone: quota piano tavolo [m, frame base]")
    ap.add_argument("--no_buffer", action="store_true", help="Giorgio senza il vassoio-buffer frontale (ostacolo davanti al busto)")
    ap.add_argument("--out", default="out.mp4")
    ap.add_argument("--record", default="")
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--ep_seconds", type=float, default=3.4)
    a = ap.parse_args()
    evaluate(a) if a.mode == "eval" else video(a)
