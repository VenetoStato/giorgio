"""Montaggio del video di presentazione: sequenze renderizzate + titoli + etichette dell'esploso + musica.
uso: python compose.py edit.json out.mp4
edit.json: {"fps": 30, "size": [1920, 1080], "music": "music.wav", "segments": [...]}
segmento "frames": {"type": "frames", "glob": "p_hero/f_*.png", "step": 1, "slow": 1, "texts": [...], "tag": "SIMULAZIONE", "labels": "lab.json"}
segmento "card":   {"type": "card", "dur": 3.0, "bg": "stills/x.png" | null, "dim": 0.6, "texts": [...]}
testo: {"t0": 0.5, "t1": 3.0, "text": "...", "pos": "center"|"lower"|"upper"|[x, y], "size": 64, "weight": "L"|"R"|"M", "color": [255,255,255]}
"""
import glob
import json
import os
import subprocess
import sys

import imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
FPS = E.get("fps", 30)
W, H = E.get("size", [1920, 1080])
FONTS = {"L": "/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf", "R": "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
         "M": "/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", "B": "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
         "H": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf", "N": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf",
         "X": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"}
UI = E.get("ui")                              # cornice "tecnica": angoli, intestazione e contatore in monospazio
_fc = {}
XF = int(E.get("xfade", 0.5) * FPS)


def font(w, size):
    k = (w, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS[w], size)
    return _fc[k]


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def draw_texts(img, texts, t):
    """testi con dissolvenza in entrata/uscita (0.4 s) e leggero scorrimento verso l'alto"""
    if not texts:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0)); dh = ImageDraw.Draw(halo)   # alone scuro sfumato (opzione "halo")
    for tx in texts:
        t0, t1 = tx.get("t0", 0), tx.get("t1", 1e9)
        if not (t0 <= t < t1):
            continue
        a = min(ease((t - t0) / 0.45), ease((t1 - t) / 0.45))
        f = font(tx.get("weight", "L"), tx.get("size", 60))
        col = tuple(tx.get("color", [255, 255, 255]))
        lines = tx["text"].split("\n")
        lh = int(tx.get("size", 60) * 1.22)
        tw = max(dr.textlength(l, font=f) for l in lines); th = lh * len(lines)
        pos = tx.get("pos", "center"); dy = int((1 - a) * 14)
        if pos == "center":
            x, y = (W - tw) / 2, (H - th) / 2
        elif pos == "lower":
            x, y = (W - tw) / 2, H - th - 110
        elif pos == "upper":
            x, y = (W - tw) / 2, 90
        elif pos == "sub":                       # sotto il titolo centrale
            x, y = (W - tw) / 2, H / 2 + 70
        elif pos == "sub2":                      # nota piccola sotto il sottotitolo
            x, y = (W - tw) / 2, H / 2 + 160
        elif pos == "left":
            x, y = 120, (H - th) / 2
        elif pos == "ll":                        # in basso a sinistra (stile titolo tecnico)
            x, y = 120, H - th - 130
        elif pos == "kick":                      # occhiello sopra al titolo in basso a sinistra
            x, y = 122, H - 130 - tx.get("above", 120) - th
        else:
            x, y = pos
        if (pos == "ll" or tx.get("_ll")) and tx.get("band", True):        # sfumatura scura dal basso, solo a sinistra
            band = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(band)
            for yy in range(int(H * 0.45), H, 2):
                k_ = (yy - H * 0.45) / (H * 0.55)
                bd.line((0, yy, W, yy), fill=int(165 * a * k_ ** 1.4))
            blk = Image.new("RGBA", (W, H), (0, 0, 0, 255)); blk.putalpha(band)
            layer.alpha_composite(blk)
        if pos in ("lower", "upper") and tx.get("band", True):   # fascia scura morbida dietro ai sottotitoli (leggibili sul bianco)
            band = Image.new("L", (W, int(th + 220)), 0); bd = ImageDraw.Draw(band)
            for yy in range(band.size[1]):
                k_ = 1 - abs(yy - band.size[1] / 2) / (band.size[1] / 2)
                bd.line((0, yy, W, yy), fill=int(150 * a * min(1, k_ * 1.6)))
            blk = Image.new("RGBA", band.size, (0, 0, 0, 255)); blk.putalpha(band)
            layer.alpha_composite(blk, (0, max(0, int(y - 110))))
        trk = tx.get("track", 0)
        for i, l in enumerate(lines):
            lx = x + (tw - dr.textlength(l, font=f)) / 2 if tx.get("align", "center") == "center" else x
            if trk:
                cxp = lx
                for ch in l:
                    if tx.get("shadow", True):
                        dr.text((cxp + 2, y + i * lh + dy + 2), ch, font=f, fill=(0, 0, 0, int(110 * a)))
                    dr.text((cxp, y + i * lh + dy), ch, font=f, fill=col + (int(255 * a),))
                    cxp += dr.textlength(ch, font=f) + trk
                continue
            if tx.get("halo"):
                dh.text((lx, y + i * lh + dy + 2), l, font=f, fill=(0, 0, 0, int(200 * a)), stroke_width=6, stroke_fill=(0, 0, 0, int(200 * a)))
            if tx.get("shadow", True):
                dr.text((lx + 2, y + i * lh + dy + 2), l, font=f, fill=(0, 0, 0, int(110 * a)))
            dr.text((lx, y + i * lh + dy), l, font=f, fill=col + (int(255 * a),))
    sh = layer.filter(ImageFilter.GaussianBlur(6)) if any(tx.get("glow") for tx in texts) else None
    out = img.convert("RGBA")
    if halo.getbbox():
        out = Image.alpha_composite(out, halo.filter(ImageFilter.GaussianBlur(14)))
    if sh is not None:
        out = Image.alpha_composite(out, sh)
    return Image.alpha_composite(out, layer).convert("RGB")


def draw_tag(img, tag):
    if not tag:
        return img
    dr = ImageDraw.Draw(img)
    if UI:
        f = font("X", 20); t_ = f"[ {tag} ]"
        tw = dr.textlength(t_, font=f)
        dr.text((W - tw - 62, 52), t_, font=f, fill=(255, 255, 255))
        return img
    f = font("M", 22)
    tw = dr.textlength(tag, font=f)
    dr.rounded_rectangle((W - tw - 70, 40, W - 40, 80), radius=8, fill=(0, 0, 0))
    dr.text((W - tw - 55, 46), tag, font=f, fill=(255, 255, 255))
    return img


def draw_ui(img, sg, t, k_glob):
    """cornice tecnica: angoli sottili, intestazione e tempo in monospazio"""
    dr = ImageDraw.Draw(img); c = (255, 255, 255); L = 34; m = 40
    for (x0, y0, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        dr.line((x0, y0, x0 + sx * L, y0), fill=c, width=2); dr.line((x0, y0, x0, y0 + sy * L), fill=c, width=2)
    f = font("X", 20)
    dr.text((62, 52), UI.get("head", "GIORGIO // REV.10"), font=f, fill=c)
    dr.text((62, H - 76), f"T+{k_glob / FPS:06.2f}", font=f, fill=(200, 200, 200))
    return img


def stable_labels(lab, names, k=9):
    """ancore lisciate (media mobile su 2k+1 fotogrammi) + colonna e quota di ogni cartellino decise una volta sola,
    dalla posizione mediana: niente salti da un fotogramma all'altro"""
    gs = [g for g in names if all(g in r for r in lab)]
    A = {g: np.array([r[g] for r in lab], float) for g in gs}
    for g in gs:
        a_ = A[g]; c_ = np.cumsum(np.vstack([np.repeat(a_[:1], k, 0), a_, np.repeat(a_[-1:], k, 0)]), 0)
        A[g] = (c_[2 * k:] - np.vstack([np.zeros((1, 2)), c_[:-2 * k - 1]]))[:len(a_)] / (2 * k + 1)
    med = {g: np.median(A[g], 0) for g in gs}
    lay = {}
    for side in (-1, 1):
        col = sorted([g for g in gs if (med[g][0] >= 0.5) == (side > 0)], key=lambda g: med[g][1])
        gap = 100; n = len(col)
        y0 = max(150, min(H - 140 - gap * (n - 1) - 82, np.mean([med[g][1] * H for g in col] or [H / 2]) - gap * (n - 1) / 2 - 41))
        for i, g in enumerate(col):
            lay[g] = (side, y0 + i * gap)
    rows = [{g: list(A[g][i]) for g in gs} for i in range(len(lab))]
    return rows, lay


def draw_labels(img, lab_row, names, a, style=None, lay=None):
    """etichette ancorate alle parti: punto + linea + testo. style "colonne": testi in due colonne ai lati, senza sovrapposizioni,
    su cartellino bianco (leggibili su sfondi chiari)"""
    if a <= 0.01:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    f1, f2 = font("M", 26), font("L", 21)
    al = int(255 * a)
    if style == "colonne":                       # impaginazione fissa per tutto il segmento (lay): i cartellini non saltano
        f1, f2 = font("M", 30), font("R", 24)
        for g, (side, ty) in (lay or {}).items():
            if g not in lab_row or g not in names:
                continue
            x, y = lab_row[g][0] * W, lab_row[g][1] * H
            t1, t2 = names[g]
            tw = max(dr.textlength(t1, font=f1), dr.textlength(t2, font=f2))
            bx = W - 80 - tw - 40 if side > 0 else 80
            ax = bx if side > 0 else bx + tw + 40
            dr.line((x, y, ax, ty + 41), fill=(255, 255, 255, int(170 * a)), width=2)
            dr.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 140, 60, al), outline=(255, 255, 255, al), width=2)
            dr.rounded_rectangle((bx, ty, bx + tw + 40, ty + 82), radius=14, fill=(255, 255, 255, int(240 * a)), outline=(215, 215, 215, al))
            dr.text((bx + 20, ty + 9), t1, font=f1, fill=(25, 27, 31, al))
            dr.text((bx + 20, ty + 46), t2, font=f2, fill=(85, 88, 95, al))
        return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    for g, (u, v) in lab_row.items():
        if g not in names:
            continue
        x, y = u * W, v * H
        side = 1 if x > W * 0.5 else -1
        x2, y2 = x + side * 140, y - 40
        dr.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 140, 60, al))
        dr.line((x, y, x2, y2, x2 + side * 30, y2), fill=(255, 255, 255, al), width=2)
        t1, t2 = names[g]
        tx = x2 + side * 40 if side > 0 else x2 - 40 - max(dr.textlength(t1, font=f1), dr.textlength(t2, font=f2))
        dr.text((tx + 1, y2 - 30 + 1), t1, font=f1, fill=(0, 0, 0, al // 2)); dr.text((tx, y2 - 30), t1, font=f1, fill=(255, 255, 255, al))
        dr.text((tx, y2 + 2), t2, font=f2, fill=(235, 235, 235, al))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

_imc = {}


def draw_images(img, ims, t):
    """immagini sovrapposte (logo): {"path", "t0", "t1", "pos": [x, y] centro, "w": larghezza px}"""
    if not ims:
        return img
    out = img.convert("RGBA")
    for im in ims:
        t0, t1 = im.get("t0", 0), im.get("t1", 1e9)
        if not (t0 <= t < t1):
            continue
        a = min(ease((t - t0) / 0.45), ease((t1 - t) / 0.45))
        k = (im["path"], im["w"])
        if k not in _imc:
            src = Image.open(os.path.join(HERE, im["path"])).convert("RGBA")
            _imc[k] = src.resize((im["w"], int(src.size[1] * im["w"] / src.size[0])), Image.LANCZOS)
        lg = _imc[k].copy()
        lg.putalpha(lg.getchannel("A").point(lambda v: int(v * a)))
        x, y = im.get("pos", [W // 2, H // 2])
        out.alpha_composite(lg, (int(x - lg.size[0] / 2), int(y - lg.size[1] / 2)))
    return out.convert("RGB")


_enc = {}


def draw_battery(img, hud, src_i, t):
    """indicatore batteria dalla registrazione: livello, stato (in viaggio / contatti chiusi, in carica)"""
    if hud["json"] not in _enc:
        _enc[hud["json"]] = json.load(open(os.path.join(HERE, hud["json"])))
    E_ = _enc[hud["json"]]
    socv, chg, pw = E_[min(src_i, len(E_) - 1)]
    a = ease(t / 0.5)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    x0, y0 = 70, 60
    dr.rounded_rectangle((x0 - 25, y0 - 22, x0 + 560, y0 + 150), radius=22, fill=(0, 0, 0, int(150 * a)))
    bw, bh = 170, 74
    dr.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=10, outline=(255, 255, 255, int(255 * a)), width=5)
    dr.rectangle((x0 + bw + 2, y0 + 22, x0 + bw + 12, y0 + bh - 22), fill=(255, 255, 255, int(255 * a)))
    col = (60, 220, 110) if chg else ((255, 140, 60) if socv < 0.30 else (240, 240, 240))
    dr.rectangle((x0 + 9, y0 + 9, x0 + 9 + int((bw - 18) * socv), y0 + bh - 9), fill=col + (int(255 * a),))
    if chg:
        cx, cy = x0 + bw / 2, y0 + bh / 2
        dr.polygon([(cx + 8, cy - 28), (cx - 14, cy + 4), (cx, cy + 4), (cx - 8, cy + 28), (cx + 14, cy - 4), (cx, cy - 4)], fill=(255, 255, 255, int(255 * a)))
    dr.text((x0 + bw + 32, y0 - 4), f"{100 * socv:.0f} %", font=font("M", 64), fill=(255, 255, 255, int(255 * a)))
    st = hud.get("charging_text", "contatti chiusi · in carica a 48 V") if chg else hud.get("travel_text", "batteria bassa: va da solo alla stazione")
    dr.text((x0, y0 + bh + 18), st, font=font("R", 30), fill=col + (int(255 * a),))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def _th(tx):
    return int(tx.get("size", 60) * 1.22) * len(tx["text"].split("\n"))


def layout_segment(sg, seg_len, xf_next):
    """impaginazione automatica in basso a sinistra: occhiello (kick) sopra il titolo (ll), sottotitolo (llsub) sotto;
    ogni testo finisce prima della dissolvenza verso il segmento successivo"""
    tx_ = sg.get("texts", [])
    for t in tx_:
        t["t1"] = min(t.get("t1", 1e9), max(t.get("t0", 0) + 0.6, seg_len - xf_next - 0.05))
    def over(a, b):
        return a.get("t0", 0) < b.get("t1", 1e9) and b.get("t0", 0) < a.get("t1", 1e9)
    subs = [t for t in tx_ if t.get("pos") == "llsub"]
    for t in subs:
        t["pos"] = [122, H - 105 - _th(t)]; t["align"] = "left"
    titles = [t for t in tx_ if t.get("pos") == "ll"]
    for t in titles:
        below = [u for u in subs if over(t, u)]
        bottom = min(u["pos"][1] for u in below) - 14 if below else H - 130
        t["pos"] = [120, bottom - _th(t)]; t["align"] = "left"; t["_ll"] = True
    for t in [t for t in tx_ if t.get("pos") == "kick"]:
        tops = [u["pos"][1] for u in titles if over(t, u)]
        top = min(tops) if tops else H - 260
        t["pos"] = [122, top - 12 - _th(t)]; t["align"] = "left"


def seg_frames(sg):
    """genera i fotogrammi PIL del segmento"""
    if sg["type"] == "card":
        n = int(sg["dur"] * FPS)
        if sg.get("bg"):
            bg = Image.open(os.path.join(HERE, sg["bg"])).convert("RGB").resize((W, H))
            if sg.get("blur"):
                bg = bg.filter(ImageFilter.GaussianBlur(sg["blur"]))
            bg = Image.blend(Image.new("RGB", (W, H), tuple(sg.get("tint", [0, 0, 0]))), bg, 1 - sg.get("dim", 0.6))
        else:
            bg = Image.new("RGB", (W, H), tuple(sg.get("color", [0, 0, 0])))
        for i in range(n):
            t = i / FPS
            img = bg
            if sg.get("zoom"):
                z = 1 + sg["zoom"] * i / max(1, n - 1)
                cw, ch = int(W / z), int(H / z)
                img = bg.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H))
            img = draw_images(img, sg.get("images"), t)
            img = draw_texts(img, sg.get("texts", []), t)
            if sg.get("chat"):
                img = draw_chat(img, sg["chat"], t)
            yield draw_tag(img, sg.get("tag"))
        return
    files = sorted(glob.glob(os.path.join(HERE, sg["glob"])))[sg.get("start", 0)::sg.get("step", 1)]
    if sg.get("count"):
        files = files[:sg["count"]]
    lab = json.load(open(os.path.join(HERE, sg["labels"]))) if sg.get("labels") else None
    lay = None
    if lab and sg.get("label_style") == "colonne":
        lab, lay = stable_labels(lab, sg["names"])
    slow = sg.get("slow", 1)
    k = 0
    prev = None
    for fi, fn in enumerate(files):
        cur = Image.open(fn).convert("RGB").resize((W, H))
        reps = slow
        for r in range(reps):
            img = cur if (prev is None or r == 0 and slow == 1) else Image.blend(prev, cur, (r + 1) / reps) if slow > 1 else cur
            t = k / FPS
            if lab is not None:
                row = lab[min(fi * sg.get("step", 1) + sg.get("start", 0), len(lab) - 1)]
                a = ease((t - sg.get("lab_t0", 1.5)) / 0.8)
                img = draw_labels(img, row, sg["names"], a, sg.get("label_style"), lay)
            if sg.get("battery"):
                hb = sg["battery"]
                img = draw_battery(img, hb, hb.get("src0", 0) + (fi * sg.get("step", 1) + sg.get("start", 0)) * hb.get("src_step", 1), t)
            img = draw_images(img, sg.get("images"), t)
            if UI and sg.get("ui", True):
                img = draw_ui(img, sg, t, k)
            img = draw_texts(img, sg.get("texts", []), t)
            yield draw_tag(img, sg.get("tag"))
            k += 1
        prev = cur


def draw_chat(img, chat, t):
    """interfaccia chat minimale: messaggio dell'utente, poi piano di Giorgio"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    y = 300
    for msg in chat:
        if t < msg["t"]:
            continue
        a = ease((t - msg["t"]) / 0.4)
        f = font("R", 42) if msg["who"] != "sys" else font("L", 30)
        txt = msg["text"]
        tw = dr.textlength(txt, font=f)
        if msg["who"] == "user":
            x0 = W - 260 - tw; col = (255, 140, 60, int(235 * a)); fg = (255, 255, 255, int(255 * a))
        elif msg["who"] == "giorgio":
            x0 = 260; col = (245, 245, 245, int(235 * a)); fg = (20, 20, 25, int(255 * a))
        else:
            x0 = 260; col = (0, 0, 0, 0); fg = (230, 230, 230, int(220 * a))
        if msg["who"] != "sys":
            dr.rounded_rectangle((x0 - 28, y - 18, x0 + tw + 28, y + 52), radius=30, fill=col)
        dr.text((x0, y), txt, font=f, fill=fg)
        y += 110 if msg["who"] != "sys" else 60
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


tmp = OUT + ".noaudio.mp4"
wr = imageio.get_writer(tmp, fps=FPS, quality=None, macro_block_size=8, codec="libx264", pixelformat="yuv420p",
                        output_params=["-crf", "20", "-preset", "slow", "-movflags", "+faststart"])
def seg_len(sg):
    if sg["type"] == "card":
        return sg["dur"]
    fl = sorted(glob.glob(os.path.join(HERE, sg["glob"])))[sg.get("start", 0)::sg.get("step", 1)]
    if sg.get("count"):
        fl = fl[:sg["count"]]
    return len(fl) * sg.get("slow", 1) / FPS


for _i, _sg in enumerate(E["segments"]):
    _nx = E["segments"][_i + 1].get("xfade", XF / FPS) if _i + 1 < len(E["segments"]) else 0.0
    layout_segment(_sg, seg_len(_sg), _nx)
tail = []                                     # ultimi fotogrammi del segmento precedente (dissolvenza incrociata)
nframes = 0
for si, sg in enumerate(E["segments"]):
    frames = seg_frames(sg)
    head = []
    first = True
    xf = sg.get("xfade", XF / FPS)
    xf_n = int(xf * FPS)
    for img in frames:
        if tail and len(head) < len(tail):
            head.append(img)
            if len(head) == len(tail):
                for j, (a_, b_) in enumerate(zip(tail, head)):
                    wr.append_data(np.asarray(Image.blend(a_, b_, ease((j + 1) / (len(tail) + 1))))); nframes += 1
                tail = []
            continue
        buf = sg.setdefault("_buf", [])
        buf.append(img)
        if len(buf) > xf_n:
            wr.append_data(np.asarray(buf.pop(0))); nframes += 1
    tail = sg.get("_buf", []) if si < len(E["segments"]) - 1 else []
    if si == len(E["segments"]) - 1:
        for img in sg.get("_buf", []):
            wr.append_data(np.asarray(img)); nframes += 1
    print(f"segmento {si} ({sg['type']}) ok, totale {nframes / FPS:.1f} s", flush=True)
wr.close()
dur = nframes / FPS
ff = imageio_ffmpeg.get_ffmpeg_exe()
if E.get("music"):
    mus = os.path.join(HERE, E["music"])
    subprocess.run([ff, "-y", "-i", tmp, "-i", mus, "-filter_complex", f"[1:a]atrim=0:{dur:.2f},afade=t=out:st={max(0, dur - 3):.2f}:d=3[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", OUT], check=True, capture_output=True)
    os.remove(tmp)
else:
    os.replace(tmp, OUT)
print("video:", OUT, f"{dur:.1f} s")
