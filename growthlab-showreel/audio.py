"""Original soundtrack for the GrowthLab showreel, synthesized with NumPy/SciPy.

120 BPM, D minor (Dm-Bb-F-C). Kick / clap / hats, sidechained bass, pads, arpeggio, risers into every cut,
impacts on every transition, UI foley synced to the animation (pops, taps, typing, coins) and a big logo hit.
The voice-over (build/vo.npy from voiceover.py) ducks the music automatically. Writes build/audio.wav.
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
rng = np.random.default_rng(26)

# Timeline (mirrors HITS / scene timings in index.html)
CUTS = [2.0, 5.0, 9.0, 13.0, 16.5]
WORDS = [16.5, 17.0, 17.5]
LOGO, BOOM = 18.0, 18.5
GROOVE = (2.0, 16.5)
BREAKS = [(12.5, 13.0), (16.0, 16.5)]  # drums drop out before these cuts for tension

drums, music, fx, send = (np.zeros((N, 2)) for _ in range(4))


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


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def saw(freq, dur, detune=0.0):
    ph = (tt(dur) * freq * (1 + detune) + rng.random()) % 1.0
    return 2 * ph - 1


def in_break(t):
    return any(a <= t < b for a, b in BREAKS)


# ---- instruments ---------------------------------------------------------------
def kick(big=False):
    t = tt(0.65 if big else 0.4)
    f = 42 + (150 if big else 115) * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4 if big else 8))
    click = filt(noise(len(t) / SR), "highpass", 2500) * np.exp(-t * 300) * 0.4
    return np.tanh((body + click) * 2.0)


def clap():
    t = tt(0.35)
    n = filt(noise(0.35), "bandpass", [900, 5500])
    e = sum((t >= o) * np.exp(-np.clip(t - o, 0, None) * (65 if o < 0.02 else 15)) for o in (0, 0.01, 0.021))
    return n * e * 0.6 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 32) * 0.22


def hat(open_=False):
    d = 0.24 if open_ else 0.05
    return filt(noise(d), "highpass", 7800) * np.exp(-tt(d) * (13 if open_ else 75))


def pluck(m, dur=0.22, bright=4200):
    t = tt(dur)
    f = mtof(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.3 + saw(f, dur) * 0.4 + np.sin(2 * np.pi * f * t) * 0.6
    return filt(s, "lowpass", bright) * np.exp(-t * 15) * np.minimum(1, t * 400)


def bassnote(m, dur):
    t = tt(dur)
    s = saw(mtof(m), dur) + 0.7 * np.sin(2 * np.pi * mtof(m - 12) * t)
    return np.tanh(filt(s, "lowpass", 380) * 1.8) * np.minimum(1, t * 220) * np.exp(-t * 3)


def pad(notes, dur, cutoff=1500, attack=0.4):
    t = tt(dur)
    s = sum(saw(mtof(m), dur, d) for m in notes for d in (-0.005, 0.0, 0.006))
    s = filt(s / (len(notes) * 3), "lowpass", cutoff)
    return s * np.minimum(1, t / attack) * np.minimum(1, np.clip(dur - t, 0, None) / 0.25)


def riser(dur, top=14):
    t = tt(dur)
    ramp = (t / dur) ** 2.4
    n = filt(noise(dur), "highpass", 1200) * ramp * 0.5
    sw = np.sin(2 * np.pi * np.cumsum(220 * (top ** (t / dur))) / SR) * ramp * 0.22
    return n + sw


def impact(scale=1.0, dur=1.6):
    t = tt(dur)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.4)
    rumble = filt(noise(dur), "lowpass", 380) * np.exp(-t * 5) * 0.6
    crash = filt(noise(dur), "highpass", 3200) * np.exp(-t * 3) * 0.35
    return (np.tanh((boom + rumble) * 1.6) + crash) * scale


def whoosh(dur=0.5, lo=500, hi=4500):
    t = tt(dur)
    return filt(noise(dur), "bandpass", [lo, hi]) * np.sin(np.pi * t / dur) ** 2 * 0.5


def pop(freq=1200, dur=0.09):
    t = tt(dur)
    return np.sin(2 * np.pi * np.cumsum(freq * (1 + 0.7 * np.exp(-t * 60))) / SR) * np.exp(-t * 42)


def tick(freq=3500):
    return filt(noise(0.015), "bandpass", [freq * 0.7, freq * 1.3]) * np.exp(-tt(0.015) * 300)


def tap():
    t = tt(0.08)
    return np.sin(2 * np.pi * 900 * t) * np.exp(-t * 90) + filt(noise(0.08), "highpass", 4000) * np.exp(-t * 200) * 0.5


def coin(scale=1.0):
    t = tt(0.6)
    a = np.sin(2 * np.pi * 1318.5 * t) * (t < 0.075) * np.exp(-t * 25)
    b = np.sin(2 * np.pi * 1975.5 * t) * (t >= 0.075) * np.exp(-np.clip(t - 0.075, 0, None) * 7)
    return (a + b + 0.3 * np.sin(2 * np.pi * 3951 * t) * (t >= 0.075) * np.exp(-np.clip(t - 0.075, 0, None) * 12)) * scale


def chime(notes, step=0.07, dur=0.5):
    out = np.zeros(int((step * len(notes) + dur) * SR))
    for k, m in enumerate(notes):
        t = tt(dur)
        s = np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 8) + 0.3 * np.sin(4 * np.pi * mtof(m) * t) * np.exp(-t * 14)
        i = int(k * step * SR)
        out[i:i + len(s)] += s
    return out


def glitch_burst(dur=0.3):
    s = np.sign(np.sin(2 * np.pi * np.cumsum(rng.choice([180, 600, 1400, 90], int(dur * SR))) / SR))
    s *= np.repeat(rng.random(int(dur * 60) + 1) > 0.35, int(SR / 60) + 1)[: int(dur * SR)]
    return filt(s, "lowpass", 6000) * 0.35


# ---- arrangement ------------------------------------------------------------------
CHORDS = [  # bass, pad, arp — Dm, Bb, F, C
    (38, [50, 53, 57], [62, 65, 69, 74]),
    (34, [50, 53, 58], [58, 62, 65, 70]),
    (41, [53, 57, 60], [65, 69, 72, 77]),
    (36, [52, 55, 60], [64, 67, 72, 76]),
]
chord_at = lambda t: CHORDS[int(t // 2.0) % 4]

kicks = [0.0]
for b in range(int(GROOVE[0] / BEAT), int(GROOVE[1] / BEAT)):
    st = b * BEAT
    if not in_break(st):
        kicks.append(st)
kicks += WORDS + [LOGO, BOOM]
big = set(CUTS + WORDS + [0.0, LOGO, BOOM])
for st in kicks:
    add(drums, st, kick(big=st in big), 0.95)
# intro: half-time heartbeat kicks under the kinetic type
for st in (0.5, 1.0, 1.5):
    add(drums, st, kick(), 0.55)

for b in range(int(GROOVE[0] / BEAT), int(GROOVE[1] / BEAT)):
    st = b * BEAT
    if in_break(st):
        continue
    if b % 2 == 1:
        add(drums, st, clap(), 0.55, pan=0.05, rev=0.35)
    for k in range(4):
        h = st + k * BEAT / 4
        add(drums, h, hat(open_=(k == 2)), 0.15 if k == 2 else (0.10 if k % 2 else 0.065), pan=0.35 if k % 2 else -0.25)

for e in range(int(GROOVE[0] / 0.25), int(GROOVE[1] / 0.25)):
    st = e * 0.25
    if in_break(st):
        continue
    add(music, st, bassnote(chord_at(st)[0] + (12 if e % 4 == 3 else 0), 0.24), 0.45)

for bar in range(9):
    st = bar * 2.0
    d = min(2.0, GROOVE[1] - st)
    if d > 0:
        add(music, st, pad(chord_at(st)[1], d + 0.05, 700 if st < 2 else 1300 + bar * 170, 0.6 if st < 2 else 0.05), 0.32, rev=0.5)

for s16 in range(int(5.0 / 0.125), int(GROOVE[1] / 0.125)):
    st = s16 * 0.125
    if in_break(st):
        continue
    m = chord_at(st)[2][[0, 1, 2, 3, 2, 1, 3, 2][s16 % 8]]
    add(music, st, pluck(m, bright=2500 + 300 * (st - 5)), 0.12, pan=-0.3, rev=0.25)
    add(music, st + 0.375, pluck(m), 0.05, pan=0.5)
for s16 in range(int(2.0 / 0.125), int(5.0 / 0.125)):  # shimmer arp under the globe
    st = s16 * 0.125
    add(music, st, pluck(chord_at(st)[2][s16 % 4] + 12, 0.15), 0.05, pan=0.6 if s16 % 2 else -0.6, rev=0.4)
# break fills: filtered snare roll into the cut
for a, b in BREAKS:
    n = 8
    for k in range(n):
        add(drums, a + k * (b - a) / n, clap(), 0.12 + 0.4 * k / n, rev=0.3)

# ---- transitions -------------------------------------------------------------------
for c in CUTS:
    add(fx, c - 1.0, riser(1.0), 0.45, rev=0.3)
    add(fx, c, impact(0.6, 1.4), 0.8, rev=0.4)
add(fx, 0.0, impact(0.75), 0.85, rev=0.4)
add(fx, 1.75, whoosh(0.3), 0.6)                       # zoom-through into the globe
add(fx, 4.7, whoosh(0.35, 300, 3000), 0.6, pan=-0.3)  # circle wipe
add(fx, 8.6, whoosh(0.8, 400, 6000), 0.65)            # diagonal colour bands sweep
add(fx, 12.72, glitch_burst(0.45), 0.6)               # RGB glitch cut
add(fx, 0.98, glitch_burst(0.1), 0.35)
add(fx, 1.44, glitch_burst(0.3), 0.4)
for w in WORDS:
    add(fx, w, impact(0.7, 0.6), 0.85, rev=0.5)
    add(fx, w, clap(), 0.6, rev=0.6)
add(fx, LOGO - 0.5, riser(0.5, 20), 0.55)
add(fx, 17.85, whoosh(0.25, 800, 8000), 0.6)          # zoom into "ESCALA."
add(fx, LOGO, impact(0.7, 1.0), 0.8, rev=0.5)
add(fx, BOOM, impact(1.1, 1.5), 1.0, rev=0.8)          # logo explodes into particles

# ---- UI foley, synced to the animation ------------------------------------------------
for k in range(12):  # intro letters landing
    add(fx, 0.22 + k * 0.05 + (0.18 if k >= 6 else 0), tick(2500 + k * 120), 0.12, pan=-0.5 + k * 0.08)
def typing(t0, n, cps, pan=-0.2):
    for k in range(n):
        add(fx, t0 + k / cps, tick(3000 + 800 * ((k * 7) % 3)), 0.07, pan=pan)
typing(0.75, 34, 38)
typing(2.65, 43, 46)
typing(3.65, 41, 52)
typing(4.3, 36, 60)
for st, f in [(3.05, 1600), (3.3, 1300), (3.55, 1900)]:      # globe data tags
    add(fx, st, pop(f), 0.2, pan=0.4, rev=0.3)
for k, st in enumerate([5.45, 5.6, 5.75, 5.9, 6.05]):       # floating tags around the phone
    add(fx, st, pop(1100 + k * 150), 0.18, pan=-0.5 if k % 2 == 0 else 0.5, rev=0.2)
add(fx, 5.45, whoosh(0.8, 1500, 7000), 0.35)                # feed flick scroll
add(fx, 6.3, pop(700, 0.15), 0.35, rev=0.3)                 # double-tap like
for k in range(14):                                          # hearts floating up
    add(fx, 6.35 + k * 0.11, pop(1800 + (k % 5) * 180, 0.05), 0.07, pan=-0.3 + (k % 3) * 0.3)
for st in (6.55, 6.9, 7.2):                                  # live comments
    add(fx, st, pop(1000, 0.08), 0.2, pan=-0.2, rev=0.2)
add(fx, 7.5, tap(), 0.5)                                     # tap "Comprar ahora"
add(fx, 7.55, chime([81, 88], 0.06, 0.3), 0.12, rev=0.3)
add(fx, 8.0, coin(), 0.4, rev=0.4)                           # sale notification
add(fx, 8.02, chime([86, 90, 93], 0.06, 0.5), 0.1, rev=0.4)
for i in range(5):                                           # funnel stages drop in
    add(fx, 9.15 + i * 0.22, pop(500 + i * 120, 0.14), 0.3, rev=0.3)
for i in range(4):                                           # connectors + rate labels
    add(fx, 10.2 + i * 0.28, whoosh(0.3, 2000, 8000), 0.18, pan=0.5 if i % 2 == 0 else -0.5)
    add(fx, 10.5 + i * 0.28, pop(1500 + i * 200, 0.07), 0.18, pan=0.5 if i % 2 == 0 else -0.5)
cnt = np.linspace(0, 1, 26) ** 0.6                           # sales counter ticks, accelerating
for u in cnt:
    add(fx, 10.4 + 1.55 * u, tick(4200), 0.1)
add(fx, 12.0, coin(1.2), 0.45, rev=0.5)
add(fx, 12.06, coin(0.8), 0.25, pan=0.4, rev=0.5)
for i, st in enumerate([13.2, 13.32, 13.44]):                # KPI cards
    add(fx, st, pop(900 + i * 200, 0.08), 0.2, pan=0.4, rev=0.2)
for k in range(12):                                          # bars growing
    add(fx, 13.6 + k * 0.07, pop(600 + k * 70, 0.06), 0.12, pan=-0.5 + k / 12)
t_line = tt(1.0)                                             # trend line drawing: rising sine
add(fx, 14.5, np.sin(2 * np.pi * np.cumsum(500 * 3 ** t_line) / SR) * np.sin(np.pi * t_line) * 0.4, 0.15, rev=0.4)
add(fx, 15.5, pop(1300, 0.12), 0.35, rev=0.4)                # +247% tag
add(fx, 15.5, chime([86, 93, 98], 0.05, 0.6), 0.12, rev=0.5)
draw_t = tt(0.45)                                            # logo stroke being drawn
add(fx, LOGO, filt(noise(0.45), "bandpass", [2000, 9000]) * (draw_t / 0.45) * 0.4, 0.4, rev=0.4)
for k in range(9):                                           # wordmark letters
    add(fx, 18.55 + k * 0.045, tick(2000 + k * 250), 0.15, pan=-0.4 + k * 0.1)
add(fx, 19.1, chime([93, 98, 100, 105], 0.05, 0.8), 0.13, rev=0.7)  # shine sweep sparkle

# logo chord
add(music, BOOM, pad([26, 38, 50, 57, 62, 65, 69, 76], 1.5, 2800, 0.02), 0.5, rev=0.8)
add(music, LOGO, pad([50, 57, 62], 0.5, 1200, 0.3), 0.25, rev=0.5)

# ---- mix -----------------------------------------------------------------------------
tline = np.arange(N) / SR
duck = np.ones(N)
for st in kicks:  # sidechain pump from the kick
    m = (tline >= st) & (tline < st + 0.5)
    duck[m] -= 0.65 * np.exp(-(tline[m] - st) * 10)
duck = np.clip(duck, 0.3, 1)[:, None]

ir_t = tt(2.2)
rev = np.zeros((N, 2))
for ch in range(2):
    ir = filt(rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45), "lowpass", 6000)
    rev[:, ch] = fftconvolve(send[:, ch], ir)[:N] * 0.035

vo_path = os.path.join(OUT, "vo.npy")
if os.path.exists(vo_path):
    vo = filt(np.load(vo_path)[:N], "highpass", 100)
    vo = filt(vo, "highpass", 2500) * 0.35 + vo                     # presence
    vo = np.tanh(vo * 2.4) / np.tanh(2.4) * 0.9                     # trailer-style saturation
    win = int(0.12 * SR)
    env = np.convolve(np.abs(vo), np.ones(win) / win, mode="same")
    vo_duck = (1 - 0.6 * np.clip(env / 0.12, 0, 1))[:, None]        # auto-duck the bed under the voice
    ir = filt(rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.22), "lowpass", 5000)
    vo_rev = fftconvolve(vo, ir)[:N] * 0.005
    vo = np.stack([vo + vo_rev, vo + vo_rev * 0.8], axis=1)
else:
    vo_duck, vo = 1.0, np.zeros((N, 2))

bed = drums * 0.85 + music * duck + fx * 0.8 + rev
mix = bed * vo_duck + vo * 1.25
mix = filt(mix.T, "highpass", 28).T
mix = np.tanh(mix * 1.15)
mix *= np.clip((DUR - tline) / 0.45, 0, 1)[:, None]
mix /= np.max(np.abs(mix)) / 0.89

os.makedirs(OUT, exist_ok=True)
with wave.open(os.path.join(OUT, "audio.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", os.path.join(OUT, "audio.wav"))
