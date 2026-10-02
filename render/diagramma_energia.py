"""Animazione dell'impianto elettrico di Giorgio (14 s, 30 fps) -> v9/d_energia/f_####.jpg
Stazione -> contatti a molla -> batteria 48 V -> convertitori -> bracci / sensori e calcolo / batteria della base / modulo caffe'.
A meta': arresto di sicurezza, i contattori staccano solo i bracci (sensori e computer restano accesi)."""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "v9", "d_energia"); os.makedirs(OUT, exist_ok=True)
K = 2; W, H = 1920 * K, 1080 * K; FPS = 30; DUR = 14.0
F = {w: "/usr/share/fonts/truetype/ubuntu/Ubuntu-%s.ttf" % w for w in ("L", "R", "M", "B")}
BG, INK, GREY, ACC, GRN, RED = (244, 244, 242), (30, 32, 36), (120, 122, 128), (255, 140, 56), (40, 170, 90), (215, 50, 45)
_fc = {}


def fnt(w, s):
    if (w, s) not in _fc:
        _fc[(w, s)] = ImageFont.truetype(F[w], int(s * K))
    return _fc[(w, s)]


def ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def S(*v):
    return [x * K for x in v]


# riquadri: nome -> (x, y, w, h, titolo, righe, t_comparsa)
BOX = {
    "stz": (90, 430, 330, 200, "Stazione di ricarica", ["rete 230 V, uscita 48 V", "25 A; contatti attivi solo", "con il robot agganciato"], 1.0),
    "bat": (560, 410, 330, 240, "Batteria LiFePO4", ["48 V · 40 Ah · 1,92 kWh", "BMS, certificata", "IEC 62619 · UN 38.3"], 1.5),
    "c1": (1040, 175, 330, 130, "DC-DC 48 V / 24 V", ["+ contattori di sicurezza", "(relè Pilz PNOZ)"], 2.0),
    "c2": (1040, 355, 330, 130, "DC-DC multiuscita", ["48 V in, 24 / 19 / 5 V out", "sempre acceso"], 2.3),
    "c3": (1040, 535, 330, 130, "Caricatore 24 V", ["per la batteria della base"], 2.6),
    "c4": (1040, 715, 330, 130, "Uscita modulo zaino", ["protetta, 48 V"], 2.9),
    "o1": (1480, 175, 360, 130, "Braccia OpenArm 2.0", ["24 V · ~150 W tipici", "picco ~700 W"], 2.2),
    "o2": (1480, 355, 360, 130, "Sensori e calcolo", ["scanner SICK, Jetson Orin,", "camere, volto LED · ~90 W"], 2.5),
    "o3": (1480, 535, 360, 130, "Base AgileX Tracer 2.0", ["batteria propria 24 V,", "ricaricata da Giorgio"], 2.8),
    "o4": (1480, 715, 360, 130, "Modulo caffè", ["~25 Wh a tazzina"], 3.1),
}
ROWS = {"c1": "o1", "c2": "o2", "c3": "o3", "c4": "o4"}


def mid_l(b): x, y, w, h = BOX[b][:4]; return (x, y + h / 2)
def mid_r(b): x, y, w, h = BOX[b][:4]; return (x + w, y + h / 2)


PATHS = {"carica": [mid_r("stz"), mid_l("bat")]}
for c, o in ROWS.items():
    PATHS[c] = [mid_r("bat"), (960, mid_r("bat")[1]), (960, mid_l(c)[1]), mid_l(c)]
    PATHS[c + "o"] = [mid_r(c), mid_l(o)]


def plen(P):
    return sum(math.dist(P[i], P[i + 1]) for i in range(len(P) - 1))


def point_at(P, s):
    for i in range(len(P) - 1):
        L = math.dist(P[i], P[i + 1])
        if s <= L:
            u = s / L if L else 0; return (P[i][0] + (P[i + 1][0] - P[i][0]) * u, P[i][1] + (P[i + 1][1] - P[i][1]) * u)
        s -= L
    return P[-1]


def frame(t):
    im = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(im, "RGBA")
    a0 = ease(t / 0.8)
    dr.text(S(90, 60), "Energia: una batteria, una presa, tutto a 48 V", font=fnt("M", 54), fill=INK + (int(255 * a0),))
    dr.text(S(92, 135), "progetto dell'impianto · componenti commerciali già certificati", font=fnt("L", 30), fill=GREY + (int(255 * a0),))
    stop = 8.0 <= t < 11.8                                 # arresto di sicurezza: si staccano solo i bracci
    # fili
    for k, P in PATHS.items():
        tb = BOX["bat"][6] if k == "carica" else BOX[k.rstrip("o")][6]
        a = ease((t - tb - 0.3) / 0.6)
        if a <= 0:
            continue
        dead = stop and k in ("c1o",)
        col = (190, 190, 190) if dead else (70, 72, 78)
        dr.line([tuple(S(*p)) for p in P], fill=col + (int(255 * a),), width=int(6 * K), joint="curve")
    # flusso (pallini): carica dalla stazione, poi dalla batteria verso le uscite
    if t > 3.3:
        for k, P in PATHS.items():
            if stop and k == "c1o":
                continue
            L = plen(P); sp = 230.0; gap = 70.0
            ph = ((t - 3.3) * sp) % gap
            n = 0
            s_ = ph
            while s_ < L:
                x, y = point_at(P, s_)
                r = 8 * K
                c = GRN if k == "carica" else ACC
                dr.ellipse((x * K - r, y * K - r, x * K + r, y * K + r), fill=c + (235,))
                s_ += gap; n += 1
    # riquadri
    for b, (x, y, w, h, tt, rows, tb) in BOX.items():
        a = ease((t - tb) / 0.5)
        if a <= 0:
            continue
        dead = stop and b == "o1"
        fill = (255, 248, 240) if b == "bat" else (255, 255, 255)
        edge = RED if (stop and b == "c1") else ((200, 200, 200) if dead else INK)
        dr.rounded_rectangle(S(x, y, x + w, y + h), radius=int(18 * K), fill=fill + (int(255 * a),), outline=edge + (int(255 * a),), width=int(4 * K))
        tc = (170, 170, 170) if dead else INK
        dr.text(S(x + 22, y + 18), tt, font=fnt("M", 31), fill=tc + (int(255 * a),))
        for i, r_ in enumerate(rows):
            dr.text(S(x + 22, y + 64 + 32 * i), r_, font=fnt("L", 25), fill=GREY + (int(255 * a),))
    # etichetta contatti
    a = ease((t - 1.8) / 0.5)
    dr.text(S(436, 488), "contatti", font=fnt("R", 24), fill=GREY + (int(255 * a),))
    dr.text(S(436, 548), "a molla", font=fnt("R", 24), fill=GREY + (int(255 * a),))
    # arresto
    if stop:
        u = ease((t - 8.0) / 0.4) * ease((11.8 - t) / 0.4)
        dr.rounded_rectangle(S(560, 858, 1840, 912), radius=int(16 * K), fill=RED + (int(235 * u),))
        dr.text(S(590, 866), "Persona troppo vicina: arresto. Solo i bracci restano senza potenza", font=fnt("M", 27), fill=(255, 255, 255, int(255 * u)))
    # garanzie in basso
    a = ease((t - 4.0) / 0.6)
    badges = ["≤ 60 V: bassa tensione di sicurezza (SELV)", "batteria ≤ 2 kWh", "sicurezza in hardware, non nell'IA"]
    x = 90
    for bt in badges:
        tw = dr.textlength(bt, font=fnt("R", 27)) / K
        dr.rounded_rectangle(S(x, 950, x + tw + 50, 1015), radius=int(30 * K), fill=INK + (int(235 * a),))
        dr.text(S(x + 25, 966), bt, font=fnt("R", 27), fill=(255, 255, 255, int(255 * a)))
        x += tw + 80
    return im.resize((1920, 1080), Image.LANCZOS)


for i in range(int(DUR * FPS)):
    frame(i / FPS).save(os.path.join(OUT, f"f_{i + 1:04d}.jpg"), quality=93)
print("ok", int(DUR * FPS))
