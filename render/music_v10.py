"""Colonna sonora v10 sincronizzata col montaggio: drone scuro + basso pulsante + impatti sui cartelli,
sezione caffe' = mandolino a tremolo (tarantella) che interrompe la tensione. Tutto sintetizzato.
uso: python music_v10.py edit_v10.json music_v10.wav"""
import glob, json, os, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(sys.argv[1])); OUT = sys.argv[2]
FPS = E.get("fps", 30); XF = E.get("xfade", 0.5); SR = 48000
rng = np.random.default_rng(3)


def seg_dur(sg):
    if sg["type"] == "card":
        return sg["dur"]
    fl = sorted(glob.glob(os.path.join(HERE, sg["glob"])))[sg.get("start", 0)::sg.get("step", 1)]
    if sg.get("count"):
        fl = fl[:sg["count"]]
    return len(fl) * sg.get("slow", 1) / FPS


segs = [s for s in E["segments"] if "type" in s]
starts, t = [], 0.0
for i, sg in enumerate(segs):
    starts.append(t); t += seg_dur(sg) - sg.get("xfade", XF)
TOT = t + XF + 1.0
N = int(TOT * SR); tt = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)


def txt(sg):
    return " ".join(x.get("text", "") for x in sg.get("texts", []))


hits = [starts[i] for i, sg in enumerate(segs) if sg["type"] == "card" and sg.get("color") and not sg.get("images")]
coffee0 = next(starts[i] for i, sg in enumerate(segs) if "MISSION-CRITICAL" in txt(sg))
coffee1 = next(starts[i] for i, sg in enumerate(segs) if "WORST CASE" in txt(sg))
logo_t = starts[-1]
print(flush=True); print(f"durata {TOT:.1f} s, impatti {len(hits)}, caffe' {coffee0:.1f}-{coffee1:.1f}, logo {logo_t:.1f}")


def lp(x, f, o=4):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def env_ad(n, a, d):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e[na:] = np.exp(-np.arange(n - na) / (d * SR)); return e


def add(x, t0, gl=1.0, gr=1.0):
    i0 = int(t0 * SR); n = min(len(x), N - i0)
    if n > 0:
        L[i0:i0 + n] += x[:n] * gl; R[i0:i0 + n] += x[:n] * gr


# maschera: la tensione si spegne durante il caffe' e torna per il finale
duck = np.ones(N)
for a, b, v in ((coffee0 - 0.3, coffee1 + 0.2, 0.0),):
    i0, i1 = int(a * SR), int(b * SR); duck[i0:i1] = v
_w = int(0.4 * SR); _c = np.cumsum(np.r_[np.full(_w // 2, duck[0]), duck, np.full(_w - _w // 2, duck[-1])])
duck = (_c[_w:] - _c[:-_w])[:N] / _w                           # media mobile (somme cumulative)
# 1) drone: re minore, seghe dissonanti filtrate, respiro lento
def saw(f, n, det=0.0):
    x = np.zeros(n); ph = 2 * np.pi * f * (1 + det) * np.arange(n) / SR
    for k in range(1, 14):
        x += np.sin(k * ph) / k
    return x
drone = np.zeros(N)
for f, g in ((36.71, 0.8), (73.42, 0.6), (110.0, 0.35), (174.61, 0.22), (220.0, 0.12)):
    drone += g * (saw(f, N, 0.002) + saw(f, N, -0.003)) / 2
drone = lp(drone, 420) * (0.55 + 0.45 * np.sin(2 * np.pi * tt / 9.0) ** 2)
fade_in = np.clip(tt / 6.0, 0, 1)
drone *= 0.11 * fade_in * duck
L += drone; R += drone * 0.96
# 1b) pad armonico: re minore - si bemolle - fa - do, due battute per accordo, attacco lento, filtrato e largo
bar = 60 / 90 * 4
CH = [(146.83, 174.61, 220.0, 293.66), (116.54, 146.83, 174.61, 233.08), (130.81, 174.61, 220.0, 261.63), (130.81, 164.81, 196.0, 261.63)]
padL = np.zeros(N); padR = np.zeros(N)
t_pad0 = starts[3] if len(starts) > 3 else 8.0
k = 0; tp = t_pad0
while tp < TOT:
    n = int(2 * bar * SR); i0 = int(tp * SR); n = min(n + int(0.8 * SR), N - i0)
    if n <= 0:
        break
    ts = np.arange(n) / SR
    env = np.clip(ts / 1.2, 0, 1) * np.clip((2 * bar + 0.8 - ts) / 0.8, 0, 1)
    for j, f in enumerate(CH[k % 4]):
        for det, side in ((-0.004, 0), (0.004, 1)):
            x = np.zeros(n); ph = 2 * np.pi * f * (1 + det) * ts
            for h in range(1, 7):
                x += np.sin(h * ph) / h ** 1.3
            (padL if side == 0 else padR)[i0:i0 + n] += x * env * 0.05
    tp += 2 * bar; k += 1
padL, padR = lp(padL, 1600), lp(padR, 1600)
L += padL * duck; R += padR * duck
# 1c) arpeggio morbido (seno + armoniche smorzate) nella parte centrale, sedicesimi a 90 bpm
t_arp0 = starts[min(12, len(starts) - 1)]; t_arp1 = coffee0 - 2.0
sixteenth = 60 / 90 / 4
tp = t_arp0; k = 0
while tp < t_arp1:
    chord = CH[int((tp - t_pad0) / (2 * bar)) % 4]
    f = chord[[0, 1, 2, 3, 2, 1][k % 6]] * 2
    n = int(0.35 * SR); ts = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * ts) + 0.25 * np.sin(4 * np.pi * f * ts)) * np.exp(-ts / 0.09) * np.clip(ts / 0.004, 0, 1)
    g = 0.045 * min(1, (tp - t_arp0) / 8) * duck[int(tp * SR)]
    pan = 0.5 + 0.15 * np.sin(k * 0.7)
    add(x * g, tp, 1 - pan + 0.3, pan + 0.3); tp += sixteenth; k += 1
# 2) basso pulsante a crome (90 bpm) dalla prima scena in poi, piu' forte nella parte centrale
beat = 60 / 90 / 2
t_pulse0 = starts[3] if len(starts) > 3 else 10.0
k = 0; tp = t_pulse0
notes = [36.71, 36.71, 36.71, 43.65, 36.71, 36.71, 49.0, 43.65]
while tp < logo_t:
    f = notes[k % 8]; n = int(0.30 * SR)
    x = (np.sin(2 * np.pi * f * np.arange(n) / SR) + 0.15 * np.sin(4 * np.pi * f * np.arange(n) / SR)) * env_ad(n, 0.006, 0.11)
    g = 0.17 * min(1, (tp - t_pulse0) / 20 + 0.4) * duck[int(tp * SR)]
    add(x, tp, g, g); tp += beat; k += 1
# 3) charleston di rumore a semicrome (tensione), solo nella parte centrale
tp = starts[min(8, len(starts) - 1)]
while tp < logo_t:
    n = int(0.05 * SR); x = hp(rng.standard_normal(n), 7000) * env_ad(n, 0.001, 0.012)
    g = 0.012 * duck[int(tp * SR)] * (1.0 if int(tp / (beat / 2)) % 2 else 0.55)
    add(x, tp, g * 0.8, g); tp += beat / 2
# 4) impatti sui cartelli neri + salita prima
def impact(t0, g=1.0):
    n = int(3.0 * SR); ts = np.arange(n) / SR
    f = 38 + 90 * np.exp(-ts / 0.06)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ts / 0.9)
    x += lp(rng.standard_normal(n), 900) * np.exp(-ts / 0.12) * 0.6
    add(x * 0.55 * g, t0, 1, 1)
    nr = int(1.4 * SR); tr = np.arange(nr) / SR
    noise = rng.standard_normal(nr)
    rs = np.zeros(nr)
    for j in range(0, nr, 2400):                             # rumore filtrato con taglio che sale
        fc = 200 + 2200 * (j / nr) ** 2
        rs[j:j + 2400] = hp(noise[j:j + 2400], fc, 1)
    if t0 > 1.5:
        add(lp(rs, 5000) * (tr / 1.4) ** 2.5 * 0.08 * g, t0 - 1.4, 0.95, 1)
for h in hits:
    if not (coffee0 - 0.5 <= h < coffee1):
        impact(h, 1.0 if h < 20 else 0.8)
impact(logo_t, 1.3)
# 5) caffe': mandolino a tremolo (Karplus-Strong), tarantella in la minore, 6/8
def pluck(f, dur, g=1.0):
    n = int(dur * SR); p = max(2, int(SR / f)); buf = np.convolve(rng.uniform(-1, 1, p + 4), np.ones(5) / 5, "valid")[:p] * 2.2; out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.4985 * (buf[i % p] + buf[(i + 1) % p])
    return lp(hp(out, 180), 4200) * g
A3, B3, C4, D4, E4, F4, G4, Gs4, A4, B4, C5, D5, E5 = 220, 246.9, 261.6, 293.7, 329.6, 349.2, 392.0, 415.3, 440, 493.9, 523.3, 587.3, 659.3
mel = [(E5, 1), (C5, 1), (A4, 1), (E5, 1), (C5, 1), (A4, 1), (D5, 1), (B4, 1), (Gs4, 1), (D5, 1), (B4, 1), (Gs4, 1),
       (C5, 1), (A4, 1), (E4, 1), (C5, 1), (B4, 1), (A4, 1), (B4, 2), (E4, 1), (Gs4, 2), (B4, 1),
       (A4, 1), (C5, 1), (E5, 1), (A4, 1), (C5, 1), (E5, 1), (F4, 1), (A4, 1), (D5, 1), (E4, 1), (Gs4, 1), (B4, 1), (A4, 3), (A3, 3)]
eighth = 60 / 132 / 2 * 1.0                                    # 6/8 veloce
cache = {}
tp = coffee0 + 0.25
while tp < coffee1 - 0.6:
    for f, d in mel:
        if tp >= coffee1 - 0.6:
            break
        dur = d * eighth
        if f not in cache:
            cache[f] = pluck(f, 0.5)
        n_tr = max(1, int(dur / 0.055))                        # tremolo: pennate rapide
        for j in range(n_tr):
            add(cache[f] * (0.30 if j == 0 else 0.19), tp + j * 0.055, 0.85, 1.0)
        tp += dur
# basso pizzicato in battere (la / mi)
tp = coffee0 + 0.25; k = 0
while tp < coffee1 - 0.6:
    f = (110.0, 82.41)[(k // 2) % 2]
    add(pluck(f, 0.6) * 0.40, tp, 1, 0.8); tp += 3 * eighth; k += 1
# 6) riverbero + mastering
ir_n = int(2.4 * SR); ir = lp(rng.standard_normal(ir_n), 4500) * np.exp(-np.arange(ir_n) / (0.55 * SR)); ir /= np.abs(ir).sum() ** 0.5 * 25
ir2 = np.roll(ir, int(0.011 * SR)); Lw, Rw = fftconvolve(L, ir)[:N], fftconvolve(R, 0.6 * ir + 0.4 * ir2)[:N]
L2, R2 = L * 0.8 + Lw * 0.45, R * 0.8 + Rw * 0.45
fo = np.clip((TOT - tt) / 3.0, 0, 1)
M_, S_ = (L2 + R2) / 2, (L2 - R2) / 2 * 0.75
mix = np.stack([(M_ + S_) * fo, (M_ - S_) * fo], 1)
mix = mix / (np.percentile(np.abs(mix), 99.9) + 1e-9)
mix = np.tanh(mix * 0.9)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.89                   # limitatore morbido, picco -1 dB
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16))
print("scritto", OUT)
