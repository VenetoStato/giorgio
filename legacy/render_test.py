import sys, mujoco, numpy as np, imageio
from giorgio_model import build
look = sys.argv[1] if len(sys.argv) > 1 else "eva"
m = build(look).compile(); d = mujoco.MjData(m)
mujoco.mj_resetData(m, d)
# posa "pronto": gomiti piegati
for s, sg in (("left", 1), ("right", -1)):
    d.joint(f"openarm_{s}_joint4").qpos = 1.6
    d.joint(f"openarm_{s}_joint2").qpos = -0.15 * sg
d.joint("lift").qpos = 0.0
mujoco.mj_forward(m, d)
r = mujoco.Renderer(m, 900, 1600)
cam = mujoco.MjvCamera(); cam.lookat[:] = [0.1, 0, 1.0]; cam.distance = 2.4; cam.azimuth = 215; cam.elevation = -12
r.update_scene(d, cam); img = r.render()
r2 = mujoco.Renderer(m, 360, 640); r2.update_scene(d, "head_d435i"); hi = r2.render()
img[20:380, 940:1580] = hi
imageio.imwrite(sys.argv[2], img)
print("massa totale", m.body_subtreemass[m.body("amr").id])
