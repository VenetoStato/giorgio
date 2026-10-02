"""Verifica urti: braccio/pinza (e oggetto in mano) contro oggetti gia' posati (flaconi, pezzi, tazzina).
Non conta le dita sull'oggetto che stanno afferrando (entro 3 cm dal punto di presa).
uso: MUJOCO_GL=egl PYTHONPATH=. python verifiche/urti.py logistica [secondi] | smista | caffe [secondi]"""
import sys
mode = sys.argv[1]; T = float(sys.argv[2]) if len(sys.argv) > 2 else 175
G = "/home/gpitton/giorgio_sim/"
HOOK = '''
import collections as _co
_ARMB = {s_: {i for i in range(m.nbody) if m.body(i).name.startswith(f"openarm_{s_}")} for s_ in ("right", "left")}
_OBJB = {i: m.body(i).name for i in range(m.nbody) if m.body(i).name.startswith(("part_", "pz", "cup"))}
HITS = _co.OrderedDict()
_ALLOBJ = set(_OBJB)
def _check():
    for c_ in d.contact[:d.ncon]:
        b1, b2 = m.geom_bodyid[c_.geom1], m.geom_bodyid[c_.geom2]
        for ba, bo in ((b1, b2), (b2, b1)):
            if bo in _OBJB:
                for s_, bs in _ARMB.items():
                    if (ba in bs or (ba in _OBJB and arms[s_].held == _OBJB[ba])) and arms[s_].held != _OBJB[bo] and c_.dist < 0.0005 \
                            and not (ba in bs and np.linalg.norm(d.body(int(bo)).xpos[:2] - d.site(f"{s_}_grasp").xpos[:2]) < 0.03):
                        k_ = (s_, m.body(ba).name, _OBJB[bo], round(d.time))
                        HITS[k_] = min(HITS.get(k_, 0), round(1000 * c_.dist, 1))
'''
if mode == "smista":
    src = open(G + "giorgio_sort.py").read()
    src = src.replace('mission["state"] = "demo"', HOOK + '\nmission["state"] = "demo"')
    src = src.replace("def control_step():\n    demo_step()", "def control_step():\n    _check()\n    demo_step()")
    src = src.replace('__file__.replace("giorgio_sort.py", "giorgio_v5.py")', repr(G + "giorgio_v5.py"))
    sys.argv = ["giorgio_sort.py", "--seconds", "80"]
    src = src.replace("exec(compile(post, \"giorgio_v5_out\", \"exec\"))", "while not finished():\n    control_step()")
    exec(compile(src, "sort", "exec"))
else:
    sys.argv = ["x", "--seconds", "0"] + (["--agent", "1:Giorgio, fammi un caffe e portalo a Marco"] if mode == "caffe" else [])
    src = open(G + "giorgio_v5.py").read().split("# ---------------------------------------------------------------- uscite")[0]
    exec(compile(src + HOOK, "v5", "exec"))
    while d.time < T and mission["state"] != "done":
        control_step(); _check()
for k, v in HITS.items():
    print("URTO", k, v, "mm")
print("TOT urti", len(HITS), "| passaggi alti", STATS_CLASH, "| stato", mission["state"])
