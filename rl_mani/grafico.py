"""Curva di apprendimento da runs/<run>/log.csv -> curva_apprendimento.png"""
import sys
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

log = sys.argv[1] if len(sys.argv) > 1 else "runs/r1/log.csv"
out = sys.argv[2] if len(sys.argv) > 2 else "curva_apprendimento.png"
rows = [r for r in csv.DictReader(open(log)) if r["rad_10s"] != ""]
x = np.array([float(r["passi"]) for r in rows]) / 1e6
rp = np.array([float(r["ricompensa_passo"]) for r in rows])
rad = np.array([float(r["rad_10s"]) for r in rows])
cad = np.array([float(r["frac_cadute"]) for r in rows]) * 100


def liscia(y, k=25):
    k = max(1, min(k, len(y) // 5 or 1))
    yp = np.pad(y, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(yp, np.ones(k) / k, mode="valid")


plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 3, figsize=(16, 4.8), facecolor="white")
C1, C2, C3 = "#2a6fdb", "#e07b00", "#c0392b"
ax[0].plot(x, rp, color=C1, alpha=0.2, lw=1)
ax[0].plot(x, liscia(rp), color=C1, lw=2.2)
ax[0].set_title("Ricompensa media per passo")
ax[0].set_ylabel("ricompensa")
ax[1].plot(x, rad, color=C2, alpha=0.2, lw=1)
ax[1].plot(x, liscia(rad), color=C2, lw=2.2)
ax[1].set_title("Rotazione del cubo (episodi conclusi)")
ax[1].set_ylabel("radianti ogni 10 s")
ax[2].plot(x, cad, color=C3, alpha=0.2, lw=1)
ax[2].plot(x, liscia(cad), color=C3, lw=2.2)
ax[2].set_title("Episodi terminati per caduta")
ax[2].set_ylabel("% degli episodi conclusi")
for a in ax:
    a.set_xlabel("passi di ambiente (milioni)")
    a.grid(alpha=0.3)
fig.suptitle("Mano ORCA v2: rotazione in mano di un cubo, PPO su mujoco_warp (4096 ambienti paralleli)",
             fontsize=14)
fig.tight_layout()
fig.savefig(out, dpi=130, facecolor="white")
print("salvato", out)
