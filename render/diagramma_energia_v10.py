"""Animazione dell'impianto elettrico di Giorgio (14 s, 30 fps) -> v9/d_energia/f_####.jpg
Stazione -> contatti a molla -> batteria 48 V -> convertitori -> bracci / sensori e calcolo / batteria della base / modulo caffe'.
A meta': arresto di sicurezza, i contattori staccano solo i bracci (sensori e computer restano accesi)."""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "v10", "d_energia"); os.makedirs(OUT, exist_ok=True)
K = 2; W, H = 1920 * K, 1080 * K; FPS = 30; DUR = 14.0
F = {"L": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf", "R": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "M": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf", "B": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"}
BG, INK, GREY, ACC, GRN, RED = (6, 6, 8), (236, 236, 232), (130, 133, 140), (255, 122, 26), (60, 200, 110), (225, 55, 50)
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
    "stz": (90, 430, 330, 200, "DOCK", ["1.2 kW · 54 V CC/CV", "contacts live only after", "pilot + handshake"], 1.0),
    "bat": (560, 410, 330, 240, "BATTERY", ["LiFePO4 · 15s · 48 V", "40 Ah · 1.92 kWh · BMS", "IEC 62619 · UN 38.3"], 1.5),
    "c1": (1040, 175, 330, 130, "2× DC-DC 24 V", ["one per arm, behind", "safety contactors K1/K2"], 2.0),
    "c2": (1040, 355, 330, 130, "DC-DC 24 / 12 / 5 V", ["safety, sensors, compute", "always on"], 2.3),
    "c3": (1040, 535, 330, 130, "BASE CHARGER", ["isolated, 48 V to 24 V", "10 A"], 2.6),
    "c4": (1040, 715, 330, 130, "COFFEE", ["at the dock (default)", "or 24 V module"], 2.9),
    "o1": (1480, 175, 360, 130, "ARMS", ["2× OpenArm 2.0 · 24 V", "720 W peak per arm"], 2.2),
    "o2": (1480, 355, 360, 130, "SAFETY + SENSING", ["PNOZ, scanners, Jetson,", "cameras, face"], 2.5),
    "o3": (1480, 535, 360, 130, "BASE", ["AgileX Tracer 2.0", "own 24 V battery"], 2.8),
    "o4": (1480, 715, 360, 130, "ESPRESSO", ["mission-critical"], 3.1),
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
    dr.text(S(90, 60), "ONE BATTERY. ONE PLUG. 48 V.", font=fnt("M", 54), fill=INK + (int(255 * a0),))
    dr.text(S(92, 135), "POWER & SAFETY ARCHITECTURE · CERTIFIED OFF-THE-SHELF PARTS", font=fnt("L", 30), fill=GREY + (int(255 * a0),))
    stop = 8.0 <= t < 11.8                                 # arresto di sicurezza: si staccano solo i bracci
    # fili
    for k, P in PATHS.items():
        tb = BOX["bat"][6] if k == "carica" else BOX[k.rstrip("o")][6]
        a = ease((t - tb - 0.3) / 0.6)
        if a <= 0:
            continue
        dead = stop and k in ("c1o",)
        col = (50, 50, 54) if dead else (120, 122, 128)
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
        fill = (30, 22, 14) if b == "bat" else (18, 18, 22)
        edge = RED if (stop and b == "c1") else ((60, 60, 64) if dead else (90, 92, 98))
        dr.rounded_rectangle(S(x, y, x + w, y + h), radius=int(18 * K), fill=fill + (int(255 * a),), outline=edge + (int(255 * a),), width=int(4 * K))
        tc = (80, 80, 84) if dead else INK
        dr.text(S(x + 22, y + 18), tt, font=fnt("M", 31), fill=tc + (int(255 * a),))
        for i, r_ in enumerate(rows):
            dr.text(S(x + 22, y + 64 + 32 * i), r_, font=fnt("L", 25), fill=GREY + (int(255 * a),))
    # etichetta contatti
    a = ease((t - 1.8) / 0.5)
    dr.text(S(436, 488), "spring", font=fnt("R", 24), fill=GREY + (int(255 * a),))
    dr.text(S(436, 548), "contacts", font=fnt("R", 24), fill=GREY + (int(255 * a),))
    # arresto
    if stop:
        u = ease((t - 8.0) / 0.4) * ease((11.8 - t) / 0.4)
        dr.rounded_rectangle(S(90, 858, 1840, 912), radius=int(16 * K), fill=RED + (int(235 * u),))
        dr.text(S(115, 870), "PERSON TOO CLOSE: CONTROLLED STOP, THEN ARM POWER CUT AT 0.5 s. EVERYTHING ELSE STAYS ON.", font=fnt("R", 22), fill=(255, 255, 255, int(255 * u)))
    # garanzie in basso
    a = ease((t - 4.0) / 0.6)
    badges = ["EVERYTHING ≤ 60 V DC", "BATTERY < 2 kWh", "SAFETY PL d · CAT 3 · IN HARDWARE"]
    x = 90
    for bt in badges:
        tw = dr.textlength(bt, font=fnt("R", 24)) / K
        dr.rounded_rectangle(S(x, 950, x + tw + 50, 1015), radius=int(6 * K), outline=(120, 122, 128, int(255 * a)), width=int(2 * K))
        dr.text(S(x + 25, 968), bt, font=fnt("R", 24), fill=INK + (int(255 * a),))
        x += tw + 80
    return im.resize((1920, 1080), Image.LANCZOS)


for i in range(int(DUR * FPS)):
    frame(i / FPS).save(os.path.join(OUT, f"f_{i + 1:04d}.jpg"), quality=93)
print("ok", int(DUR * FPS))
