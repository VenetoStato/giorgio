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
         "M": "/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", "B": "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"}
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
        else:
            x, y = pos
        if pos in ("lower", "upper"):                    # fascia scura morbida dietro ai sottotitoli (leggibili sul bianco)
            band = Image.new("L", (W, int(th + 220)), 0); bd = ImageDraw.Draw(band)
            for yy in range(band.size[1]):
                k_ = 1 - abs(yy - band.size[1] / 2) / (band.size[1] / 2)
                bd.line((0, yy, W, yy), fill=int(150 * a * min(1, k_ * 1.6)))
            blk = Image.new("RGBA", band.size, (0, 0, 0, 255)); blk.putalpha(band)
            layer.alpha_composite(blk, (0, max(0, int(y - 110))))
        for i, l in enumerate(lines):
            lx = x + (tw - dr.textlength(l, font=f)) / 2 if tx.get("align", "center") == "center" else x
            if tx.get("shadow", True):
                dr.text((lx + 2, y + i * lh + dy + 2), l, font=f, fill=(0, 0, 0, int(110 * a)))
            dr.text((lx, y + i * lh + dy), l, font=f, fill=col + (int(255 * a),))
    sh = layer.filter(ImageFilter.GaussianBlur(6)) if any(tx.get("glow") for tx in texts) else None
    out = img.convert("RGBA")
    if sh is not None:
        out = Image.alpha_composite(out, sh)
    return Image.alpha_composite(out, layer).convert("RGB")


def draw_tag(img, tag):
    if not tag:
        return img
    dr = ImageDraw.Draw(img); f = font("M", 22)
    tw = dr.textlength(tag, font=f)
    dr.rounded_rectangle((W - tw - 70, 40, W - 40, 80), radius=8, fill=(0, 0, 0))
    dr.text((W - tw - 55, 46), tag, font=f, fill=(255, 255, 255))
    return img


def draw_labels(img, lab_row, names, a):
    """etichette dell'esploso: punto + linea + testo, ancorati ai gruppi di parti"""
    if a <= 0.01:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    f1, f2 = font("M", 26), font("L", 21)
    for g, (u, v) in lab_row.items():
        if g not in names:
            continue
        x, y = u * W, v * H
        side = 1 if x > W * 0.5 else -1
        x2, y2 = x + side * 140, y - 40
        al = int(255 * a)
        dr.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 140, 60, al))
        dr.line((x, y, x2, y2, x2 + side * 30, y2), fill=(255, 255, 255, al), width=2)
        t1, t2 = names[g]
        tx = x2 + side * 40 if side > 0 else x2 - 40 - max(dr.textlength(t1, font=f1), dr.textlength(t2, font=f2))
        dr.text((tx + 1, y2 - 30 + 1), t1, font=f1, fill=(0, 0, 0, al // 2)); dr.text((tx, y2 - 30), t1, font=f1, fill=(255, 255, 255, al))
        dr.text((tx, y2 + 2), t2, font=f2, fill=(235, 235, 235, al))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


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
            img = draw_texts(img, sg.get("texts", []), t)
            if sg.get("chat"):
                img = draw_chat(img, sg["chat"], t)
            yield draw_tag(img, sg.get("tag"))
        return
    files = sorted(glob.glob(os.path.join(HERE, sg["glob"])))[sg.get("start", 0)::sg.get("step", 1)]
    if sg.get("count"):
        files = files[:sg["count"]]
    lab = json.load(open(os.path.join(HERE, sg["labels"]))) if sg.get("labels") else None
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
                img = draw_labels(img, row, sg["names"], a)
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
