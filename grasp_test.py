"""prova di presa della mano Inspire su cilindro (mano su mocap), per tarare la posa di presa"""
import sys, mujoco, numpy as np
from giorgio_model import _hand_spec, _q
side = sys.argv[1] if len(sys.argv) > 1 else "right"
R_PART, H_PART, M_PART = float(sys.argv[2]) if len(sys.argv) > 2 else 0.025, 0.16, 0.35
off = np.array([float(v) for v in sys.argv[3].split(",")]) if len(sys.argv) > 3 else np.array([0.165, 0.045, 0.0])
TH2 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
sgn = 1 if side == "right" else -1
sp = mujoco.MjSpec(); sp.option.timestep = 0.002; sp.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC; sp.option.impratio = 10
sp.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
wb = sp.worldbody
wb.add_geom(type=mujoco.mjtGeom.mjGEOM_PLANE, size=[0, 0, 0.05])
wb.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.43], size=[0.3, 0.3, 0.02])
pb = wb.add_body(name="part", pos=[0, 0, 0.45 + H_PART / 2]); pb.add_freejoint()
SHAPE = sys.argv[5] if len(sys.argv) > 5 else "cyl"
FF = float(sys.argv[6]) if len(sys.argv) > 6 else 0.8
if SHAPE == "box":
    pb.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[R_PART, R_PART, H_PART / 2], mass=M_PART, friction=[1.0, 0.02, 0.002], condim=4)
else:
    pb.add_geom(type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[R_PART, H_PART / 2, 0], mass=M_PART, friction=[1.0, 0.02, 0.002], condim=4)
# mano: x dita = +x mondo, palmo verso il pezzo, pollice in alto
Rh = np.eye(3)   # dita +x, pollice +z; palmo: destra +y, sinistra -y
off = off * [1, sgn, 1]
hp = -Rh @ off + np.array([0, 0, 0.45 + H_PART / 2 + 0.0])
mb = wb.add_body(name="mocap", pos=list(hp - [0, sgn * 0.08, 0]), quat=list(_q(Rh)))
for k, ax in enumerate(("x", "y", "z")):
    a = [0, 0, 0]; a[k] = 1
    mb.add_joint(name=f"s{ax}", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=a, armature=1.0)
    sp.add_actuator(name=f"a{ax}", target=f"s{ax}", trntype=mujoco.mjtTrn.mjTRN_JOINT, gainprm=[3e4] + [0] * 9,
                    biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -3e4, -1e3] + [0] * 7)
mb.add_geom(type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.01, 0, 0], mass=0.5, contype=0, conaffinity=0)
hs, mimic = _hand_spec(side)
for g in hs.geoms:
    g.friction = [1.2, 0.02, 0.002]; g.solref = [0.004, 1]; g.priority = 1; g.condim = 4
    g.contype, g.conaffinity = 2, 1   # niente autocollisioni nella mano
for j in hs.joints:
    j.limited = 1
mb.add_frame().attach_body(hs.body(f"{side}_wrist_yaw_link"), "", "")
for s_, m_, k in mimic:
    sp.add_equality(type=mujoco.mjtEq.mjEQ_JOINT, name1=s_, name2=m_, data=[0, float(k)] + [0] * 9, solref=[0.005, 1])
act = {}
for jn, fr in (("thumb_1", 0.6), ("thumb_2", 1.2), ("index_1", FF), ("middle_1", FF), ("ring_1", FF), ("little_1", FF)):
    j = f"{side}_{jn}_joint"; sp.joint(j).damping = [0.05, 0, 0]
    sp.add_actuator(name=jn, target=j, trntype=mujoco.mjtTrn.mjTRN_JOINT, gainprm=[8.0] + [0] * 9,
                    biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -8.0, -0.2] + [0] * 7, ctrlrange=sp.joint(j).range,
                    ctrllimited=1, forcerange=[-fr, fr], forcelimited=1)
for b in sp.bodies:
    if b.name.startswith(side): b.gravcomp = 1.0
m = sp.compile(); d = mujoco.MjData(m)
mujoco.mj_forward(m, d)
def run(T, f=None):
    for _ in range(int(T / m.opt.timestep)):
        if f: f(d.time)
        mujoco.mj_step(m, d)
P0 = np.array(m.body('mocap').pos)
class _MP:
    def __getitem__(self, i): return P0 + d.ctrl[[m.actuator('ax').id, m.actuator('ay').id, m.actuator('az').id]]
    def __setitem__(self, i, v): d.ctrl[[m.actuator('ax').id, m.actuator('ay').id, m.actuator('az').id]] = np.asarray(v) - P0
MP = _MP()
p0 = MP[0].copy()
d.ctrl[m.actuator("thumb_1").id] = 1.1   # pre-orientamento del pollice
import imageio
_r = mujoco.Renderer(m, 480, 640); _c = mujoco.MjvCamera(); _c.lookat[:] = [0, 0, 0.5]; _c.distance = 0.5; _c.azimuth = 90; _c.elevation = -10
def snap(n):
    _r.update_scene(d, _c); imageio.imwrite(f"/tmp/claude-1000/-home-gpitton/73890d0e-b4dc-4184-b008-e491487358ce/scratchpad/g_{n}.png", _r.render())
mujoco.mj_forward(m, d); snap(0)
run(0.5)
snap(1)
def approach(t, t0=0.5):
    u = min(1, (t - t0) / 1.0); MP[0] = p0 + [0, sgn * 0.08 * u * u * (3 - 2 * u), 0]
run(1.0, approach)
snap(2)
run(0.2)
print("  dopo avvicinamento: incl", round(float(np.degrees(np.arccos(abs(d.body("part").xmat[8])))),1))
def ramp(acts, v, T):
    c0 = {a: d.ctrl[m.actuator(a).id] for a in acts}
    t0 = d.time
    def f(t):
        u = min(1.0, (t - t0) / T)
        for a in acts: d.ctrl[m.actuator(a).id] = c0[a] + (v - c0[a]) * u
    run(T, f)
def inc(tag): print(f"  {tag}: incl {np.degrees(np.arccos(min(1,abs(d.body('part').xmat[8])))):.1f}, pos {np.round(d.body('part').xpos,3)}, ncon {d.ncon}")
inc("prima pollice")
ramp(["thumb_2"], TH2, 0.4)
inc("dopo pollice")
ramp(["index_1", "middle_1", "ring_1", "little_1"], 1.35, 0.6)
inc("dopo dita")
def forces():
    pid = m.body("part").id; tot = 0; out = []
    for i in range(d.ncon):
        c = d.contact[i]; b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
        if pid in (b1, b2):
            f = np.zeros(6); mujoco.mj_contactForce(m, d, i, f)
            other = m.body(b2 if b1 == pid else b1).name
            out.append((other.replace(side + "_", ""), round(f[0], 1))); tot += f[0]
    print("  forze normali sul pezzo [N]:", out)
forces()
run(0.3)
snap(3)
import imageio
r = mujoco.Renderer(m, 480, 640); cam = mujoco.MjvCamera(); cam.lookat[:] = d.body("part").xpos; cam.distance = 0.45; cam.azimuth = 200; cam.elevation = -35
r.update_scene(d, cam); imageio.imwrite(f"/tmp/claude-1000/-home-gpitton/73890d0e-b4dc-4184-b008-e491487358ce/scratchpad/grasp_{side}.png", r.render())
z0 = d.body("part").xpos[2]
pc = MP[0].copy()
def lift(t, t0=d.time):
    u = min(1, (t - t0) / 1.0); MP[0] = pc + [0, 0, 0.15 * u * u * (3 - 2 * u)]
    if int(round((t - t0) / m.opt.timestep)) % 50 == 0:
        print(f"    t={t-t0:.2f} hand z {MP[0][2]:.3f} part {np.round(d.body('part').xpos,3)} ncon {d.ncon}")
run(1.2, lift)
snap(4)
print('  mocap z', MP[0], 'qpos dita', np.round([d.joint(f'{side}_{j}_joint').qpos[0] for j in ('index_1','middle_1','thumb_1','thumb_2')],2))
run(1.0)
dz = d.body("part").xpos[2] - z0
rel = d.body("part").xpos - d.body("mocap").xpos
print(f"{side} off={off} sollevato {dz*1000:.0f} mm su 150, ncon {d.ncon}, incl {np.degrees(np.arccos(abs(d.body('part').xmat[8]))):.1f} gradi")
# scuoti: accelerazione laterale 3 m/s^2
pc = MP[0].copy()
def shake(t, t0=d.time):
    MP[0] = pc + [0.05 * np.sin(2 * np.pi * 1.2 * (t - t0)), 0, 0]
run(2.0, shake)
rel2 = d.body("part").xpos - d.body("mocap").xpos
print(f"  dopo scuotimento (+-5 cm @1.2 Hz, ~2.8 m/s^2): deriva {np.linalg.norm(rel2-rel)*1000:.1f} mm, quota {d.body('part').xpos[2]:.3f}")
