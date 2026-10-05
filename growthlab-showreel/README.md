# GrowthLab — Motion Design Showreel

A 20-second vertical showreel (1080×1920, 9:16, 60 fps, H.264 + AAC, under 15 MB) on **digital marketing**:
SEO, Meta Ads and Google Ads, social media, email marketing, conversion funnels and analytics.
Everything is made with code:

- **Picture.** `index.html` is a deterministic Canvas 2D animation. Every frame is a pure function of time
  (`window.draw(t)`). `render.cjs` steps through it frame by frame in headless Chromium (Playwright) and pipes
  the frames into ffmpeg.
- **Music.** `audio.py` synthesizes an original 120 BPM track in D minor with NumPy/SciPy: kick, clap, hi-hats,
  sidechained bass, pads, an arpeggio, risers, impacts and UI foley.
- **Voice-over.** `voiceover.py` generates Spanish VO offline with Kokoro TTS, using a 65 % `em_alex` +
  35 % `am_eric` voice blend.

**GrowthLab is a fictional brand** created for this piece. Its logo (a rounded square with rising bars and a
growth arrow) is drawn in code. The reel uses no third-party logos.

## Scene breakdown

Every cut lands on a beat of the 120 BPM grid (1 beat = 0.5 s).

| Time | Scene | HUD label | What it shows | Transition into it |
|---|---|---|---|---|
| 0–2 s | **MOTION DESIGN** | 01 KINETIC TYPOGRAPHY | Letters rise one by one with overshoot and rotation. "DESIGN" is drawn as a neon outline, then filled with a gradient on the beat. Also: expanding shockwaves on every beat, radial speed lines, RGB-split glitch and a typed `> SEO · ADS · SOCIAL · EMAIL · DATA`. | Opens from a single dot |
| 2–5 s | **MARKETING DIGITAL** | 02 3D PARTICLES | A rotating dot-matrix globe (≈900 land particles plus ocean particles, with perspective and front/back depth shading). 14 audience connection arcs are drawn with traveling light pulses, and city beacons pulse. Three HUD rings spin around the globe. Data tags are anchored to cities by leader lines: "CTR 4.8%", "AUDIENCIA: 25–34" and "ROAS 6.2x". A terminal types out a targeting command. | Zoom-through plus white flash |
| 5–9 s | **REDES SOCIALES & PUBLICIDAD** | 03 UI ANIMATION | A phone flies in and its generic "feed" flick-scrolls with motion streaks, then lands on a sponsored ad (drawn product creative with a −30 % badge). Then: a double-tap heart, floating hearts and a like counter climbing to 8.4K. Live comments rise over the ad. A finger taps "Comprar ahora" with a ripple, and the button turns into "Pedido confirmado". A "¡Nueva venta! +$89.00" notification drops in with a coin burst. Metric pills float around the phone. | Circular wipe (magenta) |
| 9–13 s | **EMBUDO DE CONVERSIÓN** | 04 MOTION INFOGRAPHICS | Five funnel slabs drop in: Anuncio → Landing → Lead → Email → Venta. 220 user particles pour through the funnel, and most drop out sideways at their stage. Curved connectors draw themselves on alternating sides, each with a conversion-rate tag and traveling light pulses. A sales counter runs to 642 and lands on the beat. | Diagonal bands of colour |
| 13–16.5 s | **RESULTADOS** | 05 DATA VISUALIZATION | A progress ring fills to 94 %. Three KPI cards count up (ROAS 6.2x, CPA $12.40 → $4.10, conversions +318 %), each with a sparkline. A 12-month bar chart grows with staggered bounce and a trend line draws across it. A "▲ +247 % CRECIMIENTO" tag pops in on the beat with burst lines. | RGB glitch with slice displacement |
| 16.5–18 s | **ATRAE. CONVIERTE. ESCALA.** | 06 BEAT-SYNC TYPE | One word per beat slams in with chromatic echoes. The backgrounds alternate lime, black and violet, and rows of the repeated word scroll in alternating directions behind it. "ESCALA." zooms through the camera into the logo. | White flash; a flash and camera shake on each beat |
| 18–20 s | **Logo reveal** | 07 LOGO ANIMATION | The icon is traced as a neon stroke, fills with a gradient, then explodes into particles with a triple shockwave. The wordmark "GROWTHLAB" builds letter by letter and a light sweep crosses it. Then the slogan "Crecimiento impulsado por datos" and the credits "MOTION DESIGN SHOWREEL · 2026" appear. The reel fades to black. | Zoom into the word plus white flash |

These elements run for the whole reel:
- **Background:** a deep dark ground with moving colour glows, floating bokeh particles, a scrolling perspective floor grid, film grain and a vignette.
- **HUD:** framing corners, a 60 fps timecode, a blinking REC dot, a progress bar with section ticks, and an animated label for each scene.
- **Camera shake:** a decaying shake on every hit (0, 2, 5, 9, 13, 16.5, 17, 17.5, 18 and 18.5 s).

## Audio

- **Arrangement.** A Dm–B♭–F–C loop at 120 BPM. The drums drop out (with a snare roll) before the 13 s and 16.5 s cuts to build tension. A riser leads into every cut, an impact hits on every transition, and a big boom plus chord lands when the logo explodes (18.5 s).
- **UI foley, synced to the animation.** Letter ticks, terminal typing, tag pops, scroll whoosh, heart pops, the tap on "Comprar" (7.5 s), coins for the sale (8.0 s) and for the sales counter (12.0 s), bar pops, a trend-line sweep and a sparkle on the logo shine.
- **Voice-over.** One short line per scene. Each line is placed so that the onset of its **last word** lands exactly on a beat: the last word's length is estimated, then snapped to the gap between words. English brands are spelled the way they are pronounced ("Gúgol Ads", "lid", "imeil", "Grouz Lab").

  | Last word on | Line |
  |---|---|
  | 1.0 s | Diseño en movimiento. |
  | 4.0 s | Marketing digital que conecta con tu audiencia. |
  | 8.0 s | Anuncios en Meta y Google Ads que convierten likes en ventas. |
  | 12.0 s | Del anuncio al email, cada lead se convierte en venta. |
  | 15.5 s | Más retorno. Menos costo. Crecimiento real. |
  | 16.5 / 17 / 17.5 s | ¡Atrae! ¡Convierte! ¡Escala! |
  | 19.0 s | GrowthLab. |
- **Mix.** The music ducks automatically under the voice (envelope follower), and the kick drives a sidechain pump. The master is normalized to −13 LUFS with peaks at or below −1 dBTP.

## Files

| File | Purpose |
|---|---|
| `index.html` | The animation. Open it in a browser to watch it in real time; `index.html?t=7.2` freezes one frame. |
| `render.cjs` | Frame-by-frame renderer. `node render.cjs` writes `build/video.mp4`; `node render.cjs --stills 3 7.5` writes test frames. |
| `audio.py` | Music, sound effects and the final mix (`build/audio.wav`). |
| `voiceover.py` | Kokoro TTS voice-over aligned to the beats (`build/vo.npy`). |
| `build.sh` | Full pipeline: render, voice, music, then a 2-pass H.264 encode (5 Mbps) and AAC 192k mux into `growthlab-showreel.mp4`. |
| `fonts/` | Local Google Fonts: Montserrat (display, 900), Space Grotesk (UI) and JetBrains Mono (technical labels). |
| `web/index.html` | Share page: a monitor-framed player, a "Ver con sonido" button and a clickable scene list. |

## Build

You need Node 18+ with Playwright and Chromium, Python 3 with `numpy scipy kokoro-onnx soundfile`, and ffmpeg.
Download the Kokoro model files `kokoro-v1.0.onnx` and `voices-v1.0.bin` from
<https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0> into `models/`.

```bash
./build.sh   # ~3 min on 4 cores -> growthlab-showreel.mp4 (~13 MB)
```
