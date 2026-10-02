"""Colonna sonora ambient sintetizzata (nessun campione esterno): pad, arpeggio morbido, pulsazione bassa, riverbero.
uso: python music.py out.wav durata_s [bpm]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 84.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:na] = np.linspace(0, 1, na) ** 2 if na else 1
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def pad(freqs, n):
    s = np.zeros(n); tt = np.arange(n) / SR
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):                    # leggero chorus
            ff = f * 2 ** (det / 12)
            ph = rng.uniform(0, 2 * np.pi)
            s += np.sin(2 * np.pi * ff * tt + ph) + 0.35 * np.sin(4 * np.pi * ff * tt + ph) + 0.12 * np.sin(6 * np.pi * ff * tt)
    return s / (len(freqs) * 3)


beat = 60.0 / BPM
bar = 4 * beat
# progressione (la minore luminosa): Am9 - Fmaj7 - C - G6, poi variazione verso l'apertura finale
chords = [[57, 64, 67, 71, 72], [53, 60, 64, 67, 69], [48, 55, 64, 67, 72], [55, 59, 62, 64, 67],
          [57, 64, 67, 71, 74], [53, 60, 65, 69, 72], [48, 55, 60, 64, 67], [55, 62, 67, 71, 74]]
mix = np.zeros(N)
n_bar = int(bar * SR)
k = 0
pos = 0
while pos < N:
    ch = chords[k % len(chords)]
    n = min(n_bar * 2, N - pos)                           # un accordo ogni 2 battute
    p = pad([hz(m) for m in ch], n) * env(n, 1.8, 1.6)
    mix[pos:pos + n] += 0.55 * p
    # basso: fondamentale un'ottava sotto, pulsazione morbida sulle semiminime (entra dopo l'introduzione)
    if pos > 2 * n_bar * 2:
        nb = np.arange(n) / SR
        lfo = 0.6 + 0.4 * np.cos(2 * np.pi * nb / beat) ** 8
        mix[pos:pos + n] += 0.22 * np.sin(2 * np.pi * hz(ch[0] - 12) * nb) * lfo * env(n, 0.3, 0.8)
    # arpeggio "glass" (pluck) nella seconda meta'
    if pos > N * 0.30:
        step = beat / 2
        for i in range(int(n / SR / step)):
            st = pos + int(i * step * SR)
            nn = min(int(1.6 * SR), N - st)
            if nn <= 0:
                break
            m_ = ch[(i * 2 + i // 4) % len(ch)] + 12
            tt = np.arange(nn) / SR
            pl = (np.sin(2 * np.pi * hz(m_) * tt) + 0.3 * np.sin(2 * np.pi * 2 * hz(m_) * tt)) * np.exp(-tt * 3.2)
            mix[st:st + nn] += 0.10 * pl * (0.6 + 0.4 * (i % 2 == 0))
    pos += n
    k += 1

# swell di apertura e coda finale
mix *= np.clip(t / 3.0, 0, 1) * np.clip((DUR - t) / 4.0, 0, 1)
# riverbero: risposta all'impulso a coda esponenziale (stereo decorrelato)
ir_len = int(3.2 * SR)
ti = np.arange(ir_len) / SR
L, R = [], []
for seed in (1, 2):
    nz = np.random.default_rng(seed).normal(0, 1, ir_len) * np.exp(-ti * 2.1)
    nz = sosfilt(butter(2, 6000, "low", fs=SR, output="sos"), nz)
    nz[0] = 1.0
    wet = fftconvolve(mix, nz)[:N]
    (L if seed == 1 else R).append(0.55 * mix + 0.08 * wet)
st = np.stack([L[0], R[0]], 1)
st = sosfilt(butter(2, 35, "high", fs=SR, output="sos"), st, axis=0)
st /= np.max(np.abs(st)) / 0.85
wavfile.write(out, SR, (st * 32767).astype(np.int16))
print("musica:", out, f"{DUR:.1f} s")
