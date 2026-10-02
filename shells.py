"""Gusci di design di Giorgio-P (rework estetico), generati come superellissoidi e salvati in OBJ.
Le stesse mesh vanno nella simulazione MuJoCo (solo visive, senza massa) e nel render Blender.
Produzione reale: stampa SLS PA12 + verniciatura soft-touch, oppure termoformatura ABS per la serie.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "assets/shells"


def _sgn_pow(x, p):
    return np.sign(x) * np.abs(x) ** p


def superellipsoid(a, b, c, e1=0.35, e2=0.35, nu=48, nv=96, taper=None, z0=0.0):
    """a,b,c semiassi; e1 (verticale), e2 (orizzontale): 1 = ellissoide, ->0 = scatola con spigoli arrotondati.
    taper(t) con t in [-1,1] (basso->alto) scala x,y lungo l'altezza."""
    u = np.linspace(-np.pi / 2, np.pi / 2, nu)
    v = np.linspace(-np.pi, np.pi, nv, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    cu, su = np.cos(U), np.sin(U)
    x = a * _sgn_pow(cu, e1) * _sgn_pow(np.cos(V), e2)
    y = b * _sgn_pow(cu, e1) * _sgn_pow(np.sin(V), e2)
    z = c * _sgn_pow(su, e1)
    if taper is not None:
        s = taper(z / c)
        x, y = x * s, y * s
    P = np.stack([x, y, z + z0], -1).reshape(-1, 3)
    F = []
    for i in range(nu - 1):
        for j in range(nv):
            a0, a1 = i * nv + j, i * nv + (j + 1) % nv
            b0, b1 = (i + 1) * nv + j, (i + 1) * nv + (j + 1) % nv
            F += [(a0, b0, b1), (a0, b1, a1)]
    return P, np.array(F)


def save_obj(name, P, F):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{name}.obj", "w") as f:
        for p in P:
            f.write(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\n")
        for t in F:
            f.write(f"f {t[0] + 1} {t[1] + 1} {t[2] + 1}\n")
    return str(OUT / f"{name}.obj")


def moustache(side=1, n=60, m=16):
    """meta' di baffo a manubrio: tubo spazzato lungo una curva nel piano del volto (y, z), spesso al centro,
    assottigliato, punta arricciata verso l'alto; leggermente schiacciato in x (profondita')"""
    t = np.linspace(0, 1, n)
    y = 0.003 + 0.050 * t
    z = -0.004 * np.sin(np.pi * np.minimum(t / 0.7, 1.0)) + 0.016 * np.clip((t - 0.7) / 0.3, 0, 1) ** 2
    y = y - 0.006 * np.clip((t - 0.85) / 0.15, 0, 1) ** 2            # ricciolo: la punta torna un po' indietro
    r = 0.0016 + 0.0062 * (1 - t) ** 0.7
    C = np.stack([np.zeros(n), side * y, z], 1)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    X = np.array([1.0, 0, 0])
    P, F = [], []
    for i in range(n):
        b = np.cross(T[i], X); b /= np.linalg.norm(b)
        for j in range(m):
            a = 2 * np.pi * j / m
            P.append(C[i] + r[i] * (0.55 * np.cos(a) * X + np.sin(a) * b))
    for i in range(n - 1):
        for j in range(m):
            a0, a1, b0, b1 = i * m + j, i * m + (j + 1) % m, (i + 1) * m + j, (i + 1) * m + (j + 1) % m
            F += [(a0, b0, b1), (a0, b1, a1)] if side > 0 else [(a0, b1, b0), (a0, a1, b1)]
    P.append(C[0]); P.append(C[-1]); c0, c1 = len(P) - 2, len(P) - 1
    for j in range(m):
        F.append((c0, (j + 1) % m, j) if side > 0 else (c0, j, (j + 1) % m))
        F.append((c1, (n - 1) * m + j, (n - 1) * m + (j + 1) % m) if side > 0 else (c1, (n - 1) * m + (j + 1) % m, (n - 1) * m + j))
    return np.array(P), np.array(F)


SHELLS = {
    "moustache_l": lambda: moustache(1),
    "moustache_r": lambda: moustache(-1),
    # busto a V: vita stretta, petto largo, profilo morbido (centro a meta' altezza)
    "torso": lambda: superellipsoid(0.105, 0.17, 0.20, e1=0.45, e2=0.5, taper=lambda t: 0.72 + 0.28 * np.clip((t + 1) / 1.6, 0, 1) ** 0.8),
    # corona sensori: fascia bassa e larga che ospita la Gemini 336L (vetro scuro davanti)
    "crown": lambda: superellipsoid(0.07, 0.095, 0.045, e1=0.4, e2=0.45),
    "crown_glass": lambda: superellipsoid(0.02, 0.085, 0.026, e1=0.3, e2=0.3),
    # testa "cute": quasi sfera, leggermente larga; frontale nero ovale; occhi = display rotondi da 1.28" (ovali luminosi)
    "head": lambda: superellipsoid(0.085, 0.095, 0.082, e1=0.85, e2=0.9),
    "face": lambda: superellipsoid(0.03, 0.078, 0.058, e1=0.7, e2=0.7),
    "eye": lambda: superellipsoid(0.004, 0.0125, 0.017, e1=0.8, e2=0.8),
    # macchina a capsule De'Longhi Inissia EN80 (120 x 230 x 320 mm): corpo arrotondato, testa erogatore, vaschetta
    "inissia_body": lambda: superellipsoid(0.060, 0.088, 0.135, e1=0.25, e2=0.35),
    "inissia_head": lambda: superellipsoid(0.058, 0.055, 0.045, e1=0.35, e2=0.45),
    "inissia_tank": lambda: superellipsoid(0.045, 0.045, 0.11, e1=0.2, e2=0.3),
    # spallacci
    "pauldron": lambda: superellipsoid(0.07, 0.055, 0.055, e1=0.55, e2=0.6),
    # carter del carrello e della colonna
    "base_cover": lambda: superellipsoid(0.36, 0.31, 0.06, e1=0.25, e2=0.3),
    "column_cover": lambda: superellipsoid(0.085, 0.10, 0.22, e1=0.2, e2=0.35),
}


def build_all():
    return {k: save_obj(k, *f()) for k, f in SHELLS.items()}


if __name__ == "__main__":
    for k, p in build_all().items():
        print(k, p)
