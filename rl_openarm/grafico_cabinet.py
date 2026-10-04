"""Learning curve for the cabinet task (dark style, same look as grafico.py / learning_curve_dark.png).
usage: python grafico_cabinet.py learning_curve_cabinet_dark.png runs/c1/log.csv[:N] [runs/c2/log.csv ...]
Right panel: mean of the best opening reached per episode, in % of the reward goal (18 cm drawer / 70 deg door);
doors often swing past 70 deg, so it can exceed 100.
Optional: BASELINE=0.36,0.71 draws the scripted baselines' success rates as horizontal reference lines."""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = sys.argv[1]
X, SC, PR = [], [], []
off = 0.0
BOUNDS = []
for spec in sys.argv[2:]:
    if off > 0:
        BOUNDS.append(off / 1e6)
    path, _, lim = spec.partition(":")
    rows = list(csv.DictReader(open(path)))
    if lim:
        rows = [r for r in rows if int(r["iter"]) <= int(lim)]
    for r in rows:
        if r["successo"] != "":
            X.append(off + float(r["passi"])); SC.append(float(r["successo"])); PR.append(float(r["max_dz_cm"]))
    off += float(rows[-1]["passi"])
x = np.array(X) / 1e6
sc = np.array(SC) * 100
pr = np.array(PR)          # logged as max progress * 100


def liscia(y, k=25):
    k = max(1, min(k, len(y) // 5 or 1))
    yp = np.pad(y, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(yp, np.ones(k) / k, mode="valid")


BG, OR, WH, GR = "#060608", "#ff7a1a", "#f2f2f2", "#9a9a9a"
plt.rcParams.update({"font.family": "DejaVu Sans Mono", "font.size": 15, "text.color": WH, "axes.labelcolor": GR,
                     "xtick.color": GR, "ytick.color": GR, "axes.edgecolor": "#3a3a3a", "axes.facecolor": BG,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(19.2, 7.2), facecolor=BG)
for a, y, c, title, yl in ((ax[0], sc, OR, "DRAWER / DOOR OPENING SUCCESS", "% of episodes"),
                           (ax[1], pr, WH, "BEST OPENING PER EPISODE", "% of goal (18 cm drawer / 70 deg door)")):
    a.plot(x, y, color=c, alpha=0.25, lw=1)
    a.plot(x, liscia(y), color=c, lw=3.2)
    a.set_title(title, loc="left", fontsize=21, pad=18, color=WH)
    a.set_ylabel(yl, fontsize=15)
    a.set_xlabel("SIMULATED STEPS (MILLIONS)", fontsize=16)
    a.grid(color="#262626", lw=1)
    a.tick_params(labelsize=15, length=0)
    for b in BOUNDS:
        a.axvline(b, color=GR, lw=1, ls=":", alpha=0.6)
bl = os.environ.get("BASELINE", "")
if bl:
    names = ["scripted IK, straight pull", "scripted IK, follows panel"]
    for k, v in enumerate(bl.split(",")):
        yv = float(v) * 100
        ax[0].axhline(yv, color=GR, lw=1.4, ls="--", alpha=0.8)
        ax[0].text(x[-1], yv + 1.5, names[k] if k < len(names) else "", color=GR, fontsize=12, ha="right", va="bottom")
ax[0].set_ylim(-3, 103)
ax[1].axhline(100, color=GR, lw=1.4, ls="--", alpha=0.8)
ax[1].text(x[-1], 102, "goal", color=GR, fontsize=12, ha="right", va="bottom")
fig.subplots_adjust(left=0.07, right=0.96, top=0.8, bottom=0.14, wspace=0.18)
fig.savefig(out, dpi=100, facecolor=BG)
print("saved", out)
