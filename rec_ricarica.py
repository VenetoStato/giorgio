"""Scena per il video: batteria al 25%, Giorgio va da solo alla stazione, si aggancia e si ricarica (48 V).
uso: MUJOCO_GL=egl python rec_ricarica.py --record render/rec_ricarica.pkl   (oppure --video ...)"""
import math
import sys

argv = sys.argv[1:]
sys.argv = ["giorgio_v5.py", "--no_humans", "--agent", "999:nulla", "--soc", "0.25", "--seconds", "60"] + argv
src = open(__file__.replace("rec_ricarica.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")
exec(compile(pre, "giorgio_v5", "exec"))
p0, th0 = (-1.6, -0.9), math.pi * 0.85                  # nel corridoio, di spalle alla stazione
d.qpos[FREE_Q:FREE_Q + 3] = [p0[0], p0[1], 0.0]; d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(th0 / 2), 0, 0, math.sin(th0 / 2)]
d.qvel[:] = 0; mujoco.mj_forward(m, d); reset_cup(); teach_contour()
for p_ in PARTS:
    set_part_xyz(p_, storage(p_))
END = {"t": None}


def finished():
    if END["t"] is None and BAT["charging"] and AG["cur"] is None:
        END["t"] = d.time + 6.0
        print(f"agganciato a t={d.time:.1f}s, carica {100 * soc():.1f}%", flush=True)
    return (END["t"] is not None and d.time > END["t"]) or d.time > args.seconds


post = post.replace("def finished():", "def _finished_v5():", 1)
exec(compile(post, "giorgio_v5_out", "exec"))
