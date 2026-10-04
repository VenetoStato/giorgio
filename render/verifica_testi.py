"""Controllo automatico delle sovrapposizioni dei testi in un edit.json: per ogni segmento, coppie di testi visibili
nello stesso istante con riquadri che si intersecano (margine 8 px), testi fuori schermo, testi oltre la fine del segmento.
uso: python verifica_testi.py edit.json"""
import sys
src = open("compose.py").read().split("tail = []")[0]          # solo definizioni + impaginazione
sys.argv = ["compose.py", sys.argv[1], "/dev/null"]
exec(compile(src, "compose.py", "exec"))
from PIL import Image, ImageDraw
dr = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def box(tx):
    f = font(tx.get("weight", "L"), tx.get("size", 60)); lines = tx["text"].split("\n")
    lh = int(tx.get("size", 60) * 1.22); tw = max(dr.textlength(l, font=f) for l in lines); th = lh * len(lines)
    pos = tx.get("pos", "center")
    P = {"center": ((W - tw) / 2, (H - th) / 2), "lower": ((W - tw) / 2, H - th - 110), "upper": ((W - tw) / 2, 90),
         "sub": ((W - tw) / 2, H / 2 + 70), "sub2": ((W - tw) / 2, H / 2 + 160), "left": (120, (H - th) / 2)}
    x, y = P[pos] if isinstance(pos, str) else pos
    if not isinstance(pos, str) and tx.get("align") == "center":
        x -= tw / 2
    return x, y, x + tw, y + th


bad = 0
for i, sg in enumerate(E["segments"]):
    tx = sg.get("texts", []); L_ = seg_len(sg)
    for a in tx:
        x0, y0, x1, y1 = box(a)
        if x0 < 40 or y0 < 40 or x1 > W - 40 or y1 > H - 40:
            print(f"seg {i}: FUORI SCHERMO {a['text']!r} {int(x0), int(y0), int(x1), int(y1)}"); bad += 1
        if a.get("align") == "left" and x1 > sg.get("text_maxx", 1150) and not a.get("wide_ok"):
            print(f"seg {i}: TROPPO LARGO (copre il soggetto) {a['text']!r} fino a x={int(x1)}"); bad += 1
        if a["t0"] >= L_ - 0.3:
            print(f"seg {i}: TESTO MAI VISIBILE {a['text']!r} t0 {a['t0']} >= durata {L_:.1f}"); bad += 1
    for j, a in enumerate(tx):
        for b in tx[j + 1:]:
            if a["t0"] < b["t1"] and b["t0"] < a["t1"]:
                A, B = box(a), box(b)
                if A[0] < B[2] + 8 and B[0] < A[2] + 8 and A[1] < B[3] + 8 and B[1] < A[3] + 8:
                    print(f"seg {i}: SOVRAPPOSTI {a['text']!r} / {b['text']!r}"); bad += 1
            elif 0 <= b["t0"] - a["t1"] < 0.15 or 0 <= a["t0"] - b["t1"] < 0.15:
                print(f"seg {i}: STACCO TROPPO BREVE {a['text']!r} -> {b['text']!r}"); bad += 1
print("PROBLEMI:", bad)
