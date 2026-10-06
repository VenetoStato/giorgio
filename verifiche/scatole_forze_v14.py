"""Misure sullo scenario v14 (stessa simulazione deterministica di giorgio_scatole.py): forza normale delle dita sulla
scatola/cassetta mentre e' in mano, scivolamento in mano (presa -> deposito), carico per braccio.
uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/scatole_forze_v14.py"""
import sys

import numpy as np

sys.argv = ["giorgio_scatole.py", "--headless"]
import os
__file__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "giorgio_scatole.py")
src = open(__file__).read().split("post = _sub(post")[0]
exec(compile(src, "scatole", "exec"))
F6 = np.zeros(6)
LOG = {}                                    # (scatola, lato) -> forze normali (N) campionate mentre e' in mano
REL0, SLIP = {}, {}


def rel(s, b):
    R = d.site(f"{s}_grasp").xmat.reshape(3, 3)
    return R.T @ (d.body(b).xpos - d.site(f"{s}_grasp").xpos)


while d.time < 194.0:
    control_step()
    if int(round(d.time / DT)) % 10:
        continue
    for s in ("right", "left"):
        if s not in HOLD:
            continue
        mk = [x_ for x_ in MARKS if x_[2] == s]
        b = mk[-1][3].split(" ")[0] if mk else None
        if b is None:
            continue
        bid = m.body(b).id; fn = 0.0
        for i, c in enumerate(d.contact[:d.ncon]):
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            o = b2 if b1 == bid else b1 if b2 == bid else None
            if o is not None and m.body(o).name.startswith(f"openarm_{s}_ee"):
                mujoco.mj_contactForce(m, d, i, F6); fn += F6[0]
        ng = sum(1 for x_ in mk if x_[3].endswith((" presa", " stretta")))
        LOG.setdefault((b, s, ng), []).append(fn)
        k = (b, s, ng)
        if k not in REL0:
            REL0[k] = rel(s, b)
        SLIP[k] = 1000 * np.linalg.norm(rel(s, b) - REL0[k])
print("forza normale totale delle dita sull'oggetto in mano (N): media / minimo, e scivolamento in mano (mm) a fine trasporto")
for (b, s, n), v in LOG.items():
    v = np.array(v[5:]) if len(v) > 10 else np.array(v)
    print(f"  {b:8s} {s:5s} (presa {n:2d}): {v.mean():6.1f} / {v.min():6.1f} N   scivolamento {SLIP[(b, s, n)]:.1f} mm   campioni {len(v)}")
