"""Generates the Spanish voice-over (Kokoro TTS, offline) aligned to the showreel timeline.

Writes build/vo.npy (44.1 kHz mono float, 20 s), mixed in by audio.py. Needs `pip install kokoro-onnx soundfile` and the
model files from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
(kokoro-v1.0.onnx, voices-v1.0.bin) in $KOKORO_DIR (default: ./models).
"""
import os

import numpy as np
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("KOKORO_DIR", os.path.join(HERE, "models"))
# Spanish male voice blended with a brighter young male voice: younger timbre, Spanish diction kept.
VOICE_MIX = {"em_alex": 0.65, "am_eric": 0.35}
BASE_SPEED = 1.12
SR = 44100
DUR = 20.0

# (start, latest end, text). Brand names are spelled phonetically for the Spanish phonemizer.
LINES = [
    (0.30, 1.95, "Diseño en movimiento."),
    (2.20, 4.90, "Inteligencia artificial que entiende a tus clientes."),
    (5.45, 8.95, "Chatbots en guatsap que responden al instante. Veinticuatro siete."),
    (9.25, 12.90, "Flujos automáticos que convierten cada anuncio en ventas."),
    (13.20, 16.40, "Más conversiones. Respuestas en menos de un segundo."),
    (16.30, 16.98, "¡Automatiza!"),
    (17.00, 17.50, "¡Conversa!"),
    (17.52, 18.00, "¡Vende!"),
    (18.55, 19.85, "Flouchat, ei ai."),
]


def trim(x, sr, thresh=0.01):
    idx = np.where(np.abs(x) > thresh)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.01 * sr))
    b = min(len(x), idx[-1] + int(0.05 * sr))
    return x[a:b]


def main():
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    voice = sum(k.get_voice_style(name) * w for name, w in VOICE_MIX.items())
    out = np.zeros(int(SR * DUR))
    for start, end, text in LINES:
        speed = BASE_SPEED
        for _ in range(3):
            s, sr = k.create(text, voice=voice, speed=speed, lang="es")
            s = trim(np.asarray(s, dtype=np.float64), sr)
            dur = len(s) / sr
            if dur <= end - start or speed >= 1.6:
                break
            speed = min(1.6, speed * dur / (end - start) * 1.02)
        s = resample_poly(s, SR, sr)
        s /= np.max(np.abs(s)) + 1e-9
        i = int(start * SR)
        j = min(len(out), i + len(s))
        out[i:j] += s[: j - i]
        print(f"{start:5.2f}s  {len(s) / SR:4.2f}s (max {end - start:4.2f})  x{speed:.2f}  {text}")
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    np.save(os.path.join(HERE, "build", "vo.npy"), out)


if __name__ == "__main__":
    main()
