"""Spanish voice-over, neutral Latin American accent and natural delivery (Kokoro TTS, offline) aligned to the showreel beats.

Each line has a time window and a beat: the line is placed so that the onset of its LAST word lands exactly
on that beat (120 BPM grid). Writes build/vo.npy (48 kHz mono, 20 s), mixed by audio.py.

Needs `pip install kokoro-onnx soundfile` and kokoro-v1.0.onnx + voices-v1.0.bin from
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 in $KOKORO_DIR (default ./models).
"""
import os

import numpy as np
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("KOKORO_DIR", os.path.join(HERE, "models"))
VOICE_MIX = {"em_alex": 0.70, "am_liam": 0.30}  # young adult male (median F0 ~130 Hz), Spanish diction
LANG = "es-419"  # neutral Latin American Spanish (seseo) instead of Castilian
BASE_SPEED = 1.0  # natural pace; only sped up when a line would not fit its window
MAX_SPEED = 1.3
MAX_SPEED_WORD = 1.6  # one-word hits must fit in half a beat
SR = 48000
DUR = 20.0

# (window start, window end, beat for the last word, text). English brands spelled as pronounced.
LINES = [
    (0.15, 1.95, 1.0, "Diseño en movimiento."),
    (2.15, 4.95, 4.0, "Márketin digital que conecta con tu audiencia."),
    (5.15, 8.95, 8.0, "Anuncios en Meta y Gúgol Ads que convierten laiks en ventas."),
    (9.10, 12.95, 12.0, "Del anuncio al imeil, cada lid se convierte en venta."),
    (13.10, 16.40, 15.5, "Más retorno. Menos costo. Crecimiento real."),
    (16.50, 16.98, 16.5, "Atrae."),
    (17.00, 17.48, 17.0, "Convierte."),
    (17.50, 18.25, 17.5, "Escala."),
    (18.30, 19.70, 19.0, "Grouz Lab."),
]


def trim(x, sr, thresh=0.012):
    idx = np.where(np.abs(x) > thresh)[0]
    if not len(idx):
        return x
    return x[max(0, idx[0] - int(0.008 * sr)): min(len(x), idx[-1] + int(0.06 * sr))]


def last_word_onset(phrase, word_dur, sr):
    """Estimate where the last word starts: phrase length minus the isolated word's length,
    snapped to the quietest 10 ms frame within +-90 ms (the gap between words)."""
    guess = len(phrase) / sr - word_dur * 0.95
    hop = int(0.01 * sr)
    rms = np.sqrt(np.convolve(phrase ** 2, np.ones(hop) / hop, mode="same"))
    a, b = int((guess - 0.09) * sr), int((guess + 0.09) * sr)
    a, b = max(0, a), min(len(phrase) - 1, b)
    if b <= a:
        return max(0.0, guess)
    return (a + int(np.argmin(rms[a:b]))) / sr


def synth(k, voice, text, speed):
    s, sr = k.create(text, voice=voice, speed=speed, lang=LANG)
    return trim(np.asarray(s, dtype=np.float64), sr), sr


def main():
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    voice = sum(k.get_voice_style(name) * w for name, w in VOICE_MIX.items())
    out = np.zeros(int(SR * DUR))
    for w0, w1, beat, text in LINES:
        single = len(text.split()) == 1
        speed, cap = BASE_SPEED, (MAX_SPEED_WORD if single else MAX_SPEED)
        for _ in range(6):
            s, sr = synth(k, voice, text, speed)
            if single:
                onset = 0.0
            else:
                last = text.split()[-1]
                wd, _ = synth(k, voice, last, speed)
                onset = last_word_onset(s, len(wd) / sr, sr)
            start, end = beat - onset, beat - onset + len(s) / sr
            over = max(w0 - start, 0) + max(end - w1, 0)
            if over <= 0.005 or speed >= cap:
                break
            speed = min(cap, speed * (1 + over / (len(s) / sr)) * 1.03)
        s = resample_poly(s, SR, sr)
        s /= np.max(np.abs(s)) + 1e-9
        keep = int((w1 - start) * SR)  # never spill past the window: short fade at its end
        if len(s) > keep:
            s = s[:keep]
            s[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
        i = int(round(start * SR))
        j = min(len(out), i + len(s))
        out[i:j] += s[: j - i]
        print(f"{start:6.2f}-{end:5.2f}s  last word @ {beat:5.2f}  x{speed:.2f}  {text}")
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    np.save(os.path.join(HERE, "build", "vo.npy"), out)


if __name__ == "__main__":
    main()
