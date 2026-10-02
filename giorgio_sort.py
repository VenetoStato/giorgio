"""Smistamento con la visione: pezzi arancioni e blu sparsi sul tavolo -> la Gemini 336L li riconosce (colore + profondita'),
le due pinze OpenArm li mettono nel contenitore giusto. Errori di presa e di deposito misurati.
uso: MUJOCO_GL=egl python giorgio_sort.py --record render/rec_smista.pkl     (oppure --video ..., oppure GUI)
"""
import math
import sys

import numpy as np

argv = sys.argv[1:]
sys.argv = ["giorgio_v5.py", "--no_humans", "--seconds", "80"] + argv
src = open(__file__.replace("giorgio_sort.py", "giorgio_v5.py")).read()
pre, post = src.split("# ---------------------------------------------------------------- uscite")

PROPS = '''
DOCK["D"] = np.array([3.2, 1.2, 0.0])
table("D", DOCK["D"])
SR_, SH_ = 0.021, 0.09                                    # pezzi: cilindri 42 x 90 mm
BINS = {("arancio", -1): (0.29, -0.145), ("blu", -1): (0.29, -0.295), ("arancio", 1): (0.29, 0.145), ("blu", 1): (0.29, 0.295)}
BIN_HX, BIN_HY = 0.051, 0.068                             # contenitori larghi: due posti affiancati, un pezzo non cade mai sull'altro
SLOTS = (0.038, -0.038)                                   # due posti affiancati; si sceglie quello libero piu' lontano dai pezzi ancora sul tavolo
for nm_, (xl, yl) in BINS.items():
    nm_s = f"{nm_[0]}{'d' if nm_[1] < 0 else 's'}"
    col_ = [1.0, 0.45, 0.1, 1] if nm_[0] == "arancio" else [0.15, 0.35, 0.95, 1]
    for k_, (dx, dy, hx, hy) in enumerate(((-BIN_HX + 0.003, 0, 0.003, BIN_HY), (BIN_HX - 0.003, 0, 0.003, BIN_HY), (0, -BIN_HY + 0.003, BIN_HX, 0.003), (0, BIN_HY - 0.003, BIN_HX, 0.003))):
        q_ = local_to_world(DOCK["D"], xl + dx, yl + dy)
        g_ = box(f"bin_{nm_s}_{k_}", (q_[0], q_[1], BENCH_Z + 0.025), (hx, hy, 0.025), "bench")
        g_.material = ""; g_.rgba = col_
    q_ = local_to_world(DOCK["D"], xl, yl)
    g_ = box(f"bin_{nm_s}_f", (q_[0], q_[1], BENCH_Z + 0.003), (BIN_HX, BIN_HY, 0.003), "bench"); g_.material = ""; g_.rgba = [0.9, 0.9, 0.92, 1]
SORT = []
_r = np.random.default_rng(5)
for i_, (xl, yl, c_) in enumerate(((0.40, -0.13, "blu"), (0.40, -0.21, "arancio"), (0.40, -0.29, "blu"),
                                   (0.40, 0.13, "arancio"), (0.40, 0.21, "blu"), (0.40, 0.29, "arancio"))):
    q_ = local_to_world(DOCK["D"], xl + _r.uniform(-0.01, 0.01), yl + _r.uniform(-0.01, 0.01))
    b_ = wb.add_body(name=f"pz{i_}", pos=[q_[0], q_[1], BENCH_Z + SH_ / 2 + 0.001])
    b_.add_freejoint(name=f"pz{i_}_free")
    b_.add_geom(name=f"pz{i_}_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[SR_, SH_ / 2, 0], mass=0.08, friction=[0.8, 0.02, 0.002],
                condim=4, conaffinity=3, group=GROUP_ENV, rgba=[1.0, 0.45, 0.1, 1] if c_ == "arancio" else [0.15, 0.35, 0.95, 1])
    SORT.append((f"pz{i_}", c_))
'''
pre = pre.replace("m = sp.compile()", PROPS + "\nm = sp.compile()", 1)
pre = pre.replace('d.qpos[FREE_Q:FREE_Q + 3] = [DOCK["A"][0], DOCK["A"][1], 0.0]', 'd.qpos[FREE_Q:FREE_Q + 3] = [DOCK["D"][0], DOCK["D"][1], 0.0]')
pre = pre.replace('d.qpos[FREE_Q + 3:FREE_Q + 7] = [math.cos(DOCK["A"][2] / 2), 0, 0, math.sin(DOCK["A"][2] / 2)]',
                  'd.qpos[FREE_Q + 3:FREE_Q + 7] = [1, 0, 0, 0]')
exec(compile(pre, "giorgio_v5", "exec"))
import cv2

mission["state"] = "demo"
teach_contour()
PZ = [p for p, _ in SORT]
DEMO = {"step": 0, "t": 0.0, "dets": [], "res": {}}


def find_parts():
    """Gemini 336L: maschere di colore (arancio / blu) + quota della faccia superiore dalla profondita'"""
    img, depth, Pw = vision.capture()
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(int)
    top = np.abs(Pw[..., 2] - (BENCH_Z + SH_)) < 0.006
    dets = []
    for col, mk in (("arancio", (hsv[..., 0] >= 5) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 110)),
                    ("blu", (hsv[..., 0] >= 100) & (hsv[..., 0] <= 130) & (hsv[..., 1] > 110))):
        lab, n = ndimage.label(mk & top)
        for i in range(1, n + 1):
            yy, xx = np.nonzero(lab == i)
            hh, ww = yy.max() - yy.min() + 1, xx.max() - xx.min() + 1
            if len(yy) < 25 or min(hh, ww) < 6 or max(hh, ww) > 3 * min(hh, ww):     # solo macchie compatte (niente bordi o strisce)
                continue
            P = Pw[yy, xx]
            dets.append(dict(xy=0.5 * (P[:, :2].min(0) + P[:, :2].max(0)), color=col, box=(xx.min(), yy.min(), xx.max(), yy.max()), kind=col))
    vision.dets, vision.title = dets, "VISIONE: pezzi per colore (Gemini 336L)"
    return dets


def plan_sort():
    dets = find_parts()
    for dt in dets:
        part = min(PZ, key=lambda p: np.linalg.norm(d.body(p).xpos[:2] - dt["xy"]))
        dt["part"] = part; dt["err"] = 1000 * np.linalg.norm(d.body(part).xpos[:2] - dt["xy"])
        print(f"    [visione] {dt['color']} {np.round(local_rel(dt['xy']), 3)} -> {part} ({dt['err']:.0f} mm) box {dt['box']}", flush=True)
    log(f"visione: {len(dets)} pezzi ({sum(dt['color'] == 'arancio' for dt in dets)} arancio, {sum(dt['color'] == 'blu' for dt in dets)} blu), "
        f"errore medio {np.mean([dt['err'] for dt in dets]):.1f} mm")
    for s_ in ("right", "left"):
        a = arms[s_]
        mine = sorted([dt for dt in dets if np.sign(local_rel(dt["xy"])[1]) == a.sg], key=lambda dt: -abs(local_rel(dt["xy"])[1]))
        jobs = []
        for dt in mine:
            def pick(dt=dt, a=a):
                s1, _ = a.pick(dt["xy"], dt["part"], a.q, BENCH_Z, h=SH_, down_first=True, wide=False)   # apertura parziale: le dita non entrano nel contenitore
                return s1

            def drop(dt=dt, a=a):
                xl, yl = BINS[(dt["color"], a.sg)]
                cands = [local_to_world(base_pose(), xl, yl + o) for o in SLOTS]
                cands = [c for c in cands if all(np.linalg.norm(d.body(p_).xpos[:2] - c) > 0.03 for p_ in PZ)] or cands   # posti liberi
                todo = [d.body(p_).xpos[:2] for p_ in PZ if p_ != dt["part"] and p_ not in DEMO["res"] and local_rel(d.body(p_).xpos[:2])[0] > 0.36]
                b = max(cands, key=lambda c: min([np.linalg.norm(c - t_) for t_ in todo] + [9.0]))   # lontano dai pezzi ancora da prendere
                a.target = np.array(b); DEMO["cur"] = dt
                s2, _ = a.place(b, dt["part"], a.q, BENCH_Z + 0.006, "sorted", drop=0.025, h=SH_, down_first=True)
                return s2
            jobs += [pick, drop]
        jobs.append(lambda a=a: [a.jmove(a.q, Q_HOME[a.s])])
        a.queue = jobs
    return dets


_on_event = on_event


def on_event(a, ev, part):
    if ev == "sorted":
        a.held = None
        p = d.body(part).xpos; col = next(c for pz, c in SORT if pz == part)
        xl, yl = BINS[(col, a.sg)]; b = local_to_world(base_pose(), xl, yl)
        ok = abs(local_rel(p[:2])[0] - xl) < BIN_HX - 0.024 and abs(local_rel(p[:2])[1] - yl) < BIN_HY - 0.024
        DEMO["res"][part] = ok
        if ok:
            expr["happy_t"] = d.time
        log(f"{a.s}: pezzo {col} {'NEL CONTENITORE GIUSTO' if ok else 'FUORI'} ({1000 * np.linalg.norm(p[:2] - b):.0f} mm dal centro)"
            + ("" if ok else f" pos {np.round(local_rel(p[:2]), 3)} z {p[2]:.3f} contenitore {xl, yl}"))
        return
    return _on_event(a, ev, part)


def demo_step():
    t = d.time
    if DEMO["step"] == 0 and t > 1.5:
        ag_say("Smisto i pezzi per colore."); plan_sort(); DEMO["step"] = 1
    elif DEMO["step"] == 1 and t > 4 and arms_idle():
        n_ok = sum(DEMO["res"].values())
        log(f"smistati {n_ok}/{len(SORT)} nel contenitore giusto"); print(f"RISULTATO smistamento: {n_ok}/{len(SORT)}", flush=True)
        ag_say(f"Fatto: {n_ok} su {len(SORT)}."); DEMO["step"] = 2; DEMO["end"] = t + 2.5


_control_step = control_step


def control_step():
    demo_step()
    _control_step()


def finished():
    return d.time > DEMO.get("end", 1e9) or d.time > args.seconds


CAM_FIXED = ([3.55, 1.2, 1.0], 1.7, 200, -32)
post = post.replace("def finished():", "def _finished_v5():", 1)
exec(compile(post, "giorgio_v5_out", "exec"))

