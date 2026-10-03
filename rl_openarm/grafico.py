"""Curva di apprendimento (stile scuro come render/stills_v10/rl_curva_dark.png).
uso: python grafico.py learning_curve_dark.png runs/r2/log.csv:450 runs/r3/log.csv runs/r4/log.csv
(le fasi successive, riprese con --resume, vengono accodate sommando i passi; ':N' = usa solo le prime N iterazioni)"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = sys.argv[1]
X, SC, DR = [], [], []
off = 0.0
BOUNDS = []
LABELS = ["reward v3", "reward v4", "obstacle 75%"]     # fasi r3, r4, r5 (vedi README)
for spec in sys.argv[2:]:
    if off > 0:
        BOUNDS.append(off / 1e6)
    path, _, lim = spec.partition(":")
    rows = list(csv.DictReader(open(path)))
    if lim:
        rows = [r for r in rows if int(r["iter"]) <= int(lim)]
    for r in rows:
        if r["successo"] != "":
            X.append(off + float(r["passi"])); SC.append(float(r["successo"])); DR.append(float(r["frac_cadute"]))
    off += float(rows[-1]["passi"])
x = np.array(X) / 1e6
sc = np.array(SC) * 100
dz = np.array(DR) * 100


def liscia(y, k=25):
    k = max(1, min(k, len(y) // 5 or 1))
    yp = np.pad(y, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(yp, np.ones(k) / k, mode="valid")


BG, OR, WH, GR = "#060608", "#ff7a1a", "#f2f2f2", "#9a9a9a"
plt.rcParams.update({"font.family": "DejaVu Sans Mono", "font.size": 15, "text.color": WH, "axes.labelcolor": GR,
                     "xtick.color": GR, "ytick.color": GR, "axes.edgecolor": "#3a3a3a", "axes.facecolor": BG,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(19.2, 7.2), facecolor=BG)
for a, y, c, title, yl in ((ax[0], sc, OR, "GRASP-AND-LIFT SUCCESS", "% of episodes"),
                           (ax[1], dz, WH, "EPISODES ENDING IN A DROP", "%")):
    a.plot(x, y, color=c, alpha=0.25, lw=1)
    a.plot(x, liscia(y), color=c, lw=3.2)
    a.set_title(title, loc="left", fontsize=21, pad=18, color=WH)
    a.set_ylabel(yl, fontsize=15)
    a.set_xlabel("SIMULATED STEPS (MILLIONS)", fontsize=16)
    a.grid(color="#262626", lw=1)
    a.tick_params(labelsize=15, length=0)
    for k, b in enumerate(BOUNDS):                    # ripresa con ricompensa modificata (vedi README)
        a.axvline(b, color=GR, lw=1, ls=":", alpha=0.6)
        a.text(b, 1.01, LABELS[k] if k < len(LABELS) else "", transform=a.get_xaxis_transform(), color=GR, fontsize=11, ha="center", va="bottom")
fig.subplots_adjust(left=0.07, right=0.96, top=0.8, bottom=0.14, wspace=0.18)
fig.savefig(out, dpi=100, facecolor=BG)
print("salvato", out)
