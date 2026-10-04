"""Synthesizes the 20s showreel soundtrack (120 BPM, Am-F-C-G) synced to the visual cuts.

Writes build/audio.wav. Requires numpy + scipy.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
DUR = 20.0
N = int(SR * DUR)
BEAT = 0.5
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
rng = np.random.default_rng(7)

# Scene cuts (must match HITS in index.html)
CUTS = [2.0, 5.0, 9.0, 13.0]
WORDS = [16.5, 17.0, 17.5]
LOGO = 18.0
DROP_END = 16.5

drums = np.zeros((N, 2))
music = np.zeros((N, 2))
fx = np.zeros((N, 2))
send = np.zeros((N, 2))


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def add(bus, start, sig, gain=1.0, pan=0.0, rev=0.0):
    i = int(round(start * SR))
    if i >= N:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(N, i + len(sig))
    s = sig[: j - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i:j, 0] += s * l * 1.414
    bus[i:j, 1] += s * r * 1.414
    if rev:
        send[i:j, 0] += s * l * rev
        send[i:j, 1] += s * r * rev


def filt(x, kind, f):
    return sosfilt(butter(2, f, btype=kind, fs=SR, output="sos"), x)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def saw(freq, dur, detune=0.0):
    t = tt(dur)
    ph = (t * freq * (1 + detune) + rng.random()) % 1.0
    return 2 * ph - 1


# ---- instruments -----------------------------------------------------------
def kick(big=False):
    t = tt(0.6 if big else 0.42)
    f = 44 + (130 if big else 110) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4.5 if big else 7.5))
    click = filt(noise(len(t) / SR), "highpass", 2000) * np.exp(-t * 260) * 0.35
    return np.tanh((body + click) * 1.8)


def clap():
    t = tt(0.35)
    n = filt(noise(0.35), "bandpass", [900, 5200])
    e = np.zeros_like(t)
    for off in (0, 0.011, 0.023):
        e += (t >= off) * np.exp(-np.clip(t - off, 0, None) * (60 if off < 0.02 else 16))
    return n * e * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.25


def hat(open_=False):
    d = 0.22 if open_ else 0.05
    t = tt(d)
    return filt(noise(d), "highpass", 7500) * np.exp(-t * (14 if open_ else 70))


def pluck(m, dur=0.22):
    t = tt(dur)
    f = mtof(m)
    sq = np.sign(np.sin(2 * np.pi * f * t)) * 0.35 + np.sin(2 * np.pi * f * t)
    return filt(sq, "lowpass", 3800) * np.exp(-t * 16) * np.minimum(1, t * 400)


def bassnote(m, dur):
    t = tt(dur)
    s = saw(mtof(m), dur) + 0.6 * np.sin(2 * np.pi * mtof(m - 12) * t)
    s = filt(s, "lowpass", 420)
    return np.tanh(s * 1.6) * np.minimum(1, t * 200) * np.exp(-t * 3.5)


def pad(notes, dur, cutoff=1400, attack=0.4):
    t = tt(dur)
    s = sum(saw(mtof(m), dur, d) for m in notes for d in (-0.004, 0.0, 0.005))
    s = filt(s / (len(notes) * 3), "lowpass", cutoff)
    env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / 0.3)
    return s * env


def riser(dur):
    t = tt(dur)
    ramp = (t / dur) ** 2.2
    n = filt(noise(dur), "highpass", 1500) * ramp * 0.5
    f = 250 * (12 ** (t / dur))
    sw = np.sin(2 * np.pi * np.cumsum(f) / SR) * ramp * 0.25
    return n + sw


def impact(scale=1.0, dur=1.6):
    t = tt(dur)
    boom = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.6)
    rumble = filt(noise(dur), "lowpass", 400) * np.exp(-t * 5) * 0.6
    crash = filt(noise(dur), "highpass", 3500) * np.exp(-t * 3.2) * 0.35
    return np.tanh((boom + rumble) * 1.5) * scale + crash * scale


def whoosh(dur=0.5):
    t = tt(dur)
    env = np.sin(np.pi * t / dur) ** 2
    return filt(noise(dur), "bandpass", [600, 4000]) * env * 0.5


def pop(freq=1200, dur=0.09):
    t = tt(dur)
    f = freq * (1 + 0.6 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40)


def coin():
    t = tt(0.5)
    a = np.sin(2 * np.pi * 1318.5 * t) * (t < 0.07) * np.exp(-t * 30)
    b = np.sin(2 * np.pi * 1975.5 * t) * (t >= 0.07) * np.exp(-np.clip(t - 0.07, 0, None) * 9)
    return a + b


# ---- arrangement -----------------------------------------------------------
CHORDS = [  # (bass midi, pad notes, arp notes)
    (45, [57, 60, 64], [69, 72, 76, 81]),   # Am
    (41, [53, 57, 60], [65, 69, 72, 77]),   # F
    (48, [55, 60, 64], [67, 72, 76, 79]),   # C
    (43, [55, 59, 62], [67, 71, 74, 79]),   # G
]
chord_at = lambda t: CHORDS[int(t // 2.0) % 4]

kicks = []
for b in range(int(DROP_END / BEAT)):
    st = b * BEAT
    if 1.75 <= st < 2.0 or 12.5 <= st < 13.0:
        continue
    kicks.append(st)
kicks += WORDS + [LOGO]
for st in kicks:
    add(drums, st, kick(big=st in WORDS + [LOGO, 0.0]), 0.95 if st >= 2 else 0.8)

for b in range(int(2.0 / BEAT), int(DROP_END / BEAT)):
    st = b * BEAT
    if b % 2 == 1:
        add(drums, st, clap(), 0.55, pan=0.05, rev=0.35)
    for k in range(4):
        h = st + k * BEAT / 4
        if 12.5 <= h < 13.0 and k % 2:
            continue
        add(drums, h, hat(open_=(k == 2)), 0.16 if k == 2 else (0.11 if k % 2 else 0.07), pan=0.35 if k % 2 else -0.25)

# bass: rolling eighths from the drop
for e in range(int(2.0 / 0.25), int(DROP_END / 0.25)):
    st = e * 0.25
    if 12.5 <= st < 13.0:
        continue
    m = chord_at(st)[0] + (12 if e % 4 == 3 else 0)
    add(music, st, bassnote(m, 0.24), 0.42)

# pads per bar, opening up over time
for bar in range(int(DROP_END // 2) + 1):
    st = bar * 2.0
    d = min(2.0, DROP_END - st)
    if d <= 0:
        continue
    cut = 700 if st < 2 else 1400 + bar * 180
    add(music, st, pad(chord_at(st)[1], d + 0.05, cut, 0.5 if st < 2 else 0.05), 0.32, rev=0.5)

# arpeggio sixteenths from scene 3 onward, with ping-pong echo
for s16 in range(int(5.0 / 0.125), int(DROP_END / 0.125)):
    st = s16 * 0.125
    if 12.5 <= st < 13.0:
        continue
    notes = chord_at(st)[2]
    m = notes[[0, 1, 2, 3, 2, 1, 2, 3][s16 % 8]]
    add(music, st, pluck(m), 0.13, pan=-0.3, rev=0.25)
    add(music, st + 0.375, pluck(m), 0.06, pan=0.5)

# intro: filtered arp shimmer in scene 2
for s16 in range(int(2.0 / 0.125), int(5.0 / 0.125)):
    st = s16 * 0.125
    m = chord_at(st)[2][s16 % 4] + 12
    add(music, st, pluck(m, 0.15), 0.05, pan=0.6 if s16 % 2 else -0.6, rev=0.4)

# transitions
for c in CUTS:
    add(fx, c - 0.9, riser(0.9), 0.45, rev=0.3)
    add(fx, c, impact(0.55, 1.4), 0.75, rev=0.4)
    add(fx, c - 0.25, whoosh(0.5), 0.55, pan=-0.4)
add(fx, 0.0, impact(0.7), 0.8, rev=0.4)
add(fx, DROP_END - 1.5, riser(1.5), 0.5, rev=0.3)
for w in WORDS:
    add(fx, w, impact(0.6, 0.5), 0.8, rev=0.5)
    add(fx, w, clap(), 0.6, rev=0.6)
add(fx, LOGO - 0.5, riser(0.5), 0.6)
add(fx, LOGO, impact(1.0, 2.0), 1.0, rev=0.7)

# UI sound design: message pops, taps, typing, node spawns, coin
for st, f in [(5.75, 1500), (6.7, 1100), (7.15, 1250), (7.7, 1400), (8.25, 1500), (8.55, 1700),
              (5.9, 900), (6.85, 900), (7.4, 900), (8.6, 900)]:
    add(fx, st, pop(f), 0.22, pan=0.3 if f > 1300 else -0.3, rev=0.2)
add(fx, 8.05, pop(2600, 0.04), 0.3)
for k in range(10):
    add(fx, 6.15 + k * 0.055, filt(noise(0.012), "highpass", 3000), 0.05, pan=-0.2)
for st in [9.2, 9.6, 10.0, 10.45, 10.55, 11.2]:
    add(fx, st, pop(800 + st * 60, 0.12), 0.2, pan=0.0, rev=0.3)
add(fx, 11.2, coin(), 0.28, rev=0.4)
for st in [2.15, 2.3, 3.0, 3.35, 3.7, 13.1, 13.55, 13.7]:
    add(fx, st, pop(2200, 0.05), 0.08, pan=0.5, rev=0.2)

# logo: big chord + sparkle
add(music, LOGO, pad([33, 45, 52, 57, 60, 64, 71], 2.0, 2600, 0.02), 0.5, rev=0.8)
for k, m in enumerate([81, 84, 88, 93, 96]):
    add(music, LOGO + 0.5 + k * 0.09, pluck(m, 0.6), 0.12, pan=-0.6 + k * 0.3, rev=0.8)

# ---- mix --------------------------------------------------------------------
tline = np.arange(N) / SR
duck = np.ones(N)
for st in kicks:
    m = tline >= st
    duck[m] -= 0.65 * np.exp(-(tline[m] - st) * 11)
duck = np.clip(duck, 0.3, 1)[:, None]

ir_t = np.arange(int(2.2 * SR)) / SR
rev = np.zeros((N, 2))
for ch in range(2):
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45)
    ir = filt(ir, "lowpass", 6000)
    rev[:, ch] = fftconvolve(send[:, ch], ir)[:N] * 0.035

mix = drums + music * duck + fx + rev
mix = filt(mix.T, "highpass", 28).T
mix = np.tanh(mix * 1.1)
fade = np.clip((DUR - tline) / 0.35, 0, 1)[:, None]
mix *= fade
mix /= np.max(np.abs(mix)) / 0.89

os.makedirs(OUT, exist_ok=True)
with wave.open(os.path.join(OUT, "audio.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", os.path.join(OUT, "audio.wav"))
