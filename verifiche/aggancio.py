"""Verifica ricarica automatica: partenza casuale con batteria al 25%, il robot va da solo alla stazione e chiude i contatti.
uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/aggancio.py <seme>"""
import sys
seed = int(sys.argv[1])
sys.argv = ["x", "--seconds", "0", "--agent", "999:nulla", "--soc", "0.25"]
import numpy as np, math
src = open("/home/gpitton/giorgio_sim/giorgio_v5.py").read().split("# ---------------------------------------------------------------- uscite")[0]
exec(compile(src, "v5", "exec"))
rng = np.random.default_rng(seed)
# posa di partenza casuale in zona libera
while True:
    p0 = np.array([rng.uniform(-4.5, 1.5), rng.uniform(-2.0, 1.0)])
    if clearance(p0) > 0.9 and np.linalg.norm(p0 - CHG[:2]) > 1.5:
        break
th0 = rng.uniform(-math.pi, math.pi)
d.qpos[FREE_Q:FREE_Q + 3] = [p0[0], p0[1], 0.0]; d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(th0 / 2), 0, 0, math.sin(th0 / 2)]
d.qvel[:] = 0; mujoco.mj_forward(m, d); reset_cup()
soc0 = soc(); t_dock = None; t_end = None
while d.time < 90:
    control_step()
    if AG["cur"] is None and not AG["queue"] and t_end is None and d.time > 3:
        t_end = d.time
    if t_end is not None and d.time > t_end + 3:
        break
gap, ly, dth = dock_error()
ok = docked_at_charger()
print(f"seed {seed} start {np.round(p0,2)} th {math.degrees(th0):.0f} -> {'CONTATTI CHIUSI' if ok else 'CONTATTI APERTI'} in {t_end:.1f} s: spazio {1000*gap:.1f} mm, laterale {1000*ly:.1f} mm, angolo {math.degrees(dth):.2f} gradi, carica {100*soc0:.1f}% -> {100*soc():.1f}%", flush=True)
