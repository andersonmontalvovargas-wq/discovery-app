// Renders index.html frame-by-frame with headless Chromium and pipes JPEGs into ffmpeg.
//   node render.cjs                 -> build/video.mp4 (silent, 60 fps)
//   node render.cjs --stills 1 6.5  -> build/still-1.png, build/still-6.5.png
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FPS = Number(process.env.FPS || 60);
const DUR = 20;
const OUT = path.join(__dirname, 'build');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => window.ready);

  const args = process.argv.slice(2);
  if (args[0] === '--stills') {
    for (const t of args.slice(1)) {
      await page.evaluate(t => window.draw(t), Number(t));
      await page.screenshot({ path: path.join(OUT, `still-${t}.png`) });
    }
    await browser.close();
    return;
  }

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg',
    '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', path.join(OUT, 'video.mp4')],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const frames = DUR * FPS;
  const start = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.draw(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % FPS === 0) process.stdout.write(`\rframe ${i}/${frames}  ${((Date.now() - start) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log(`\ndone in ${((Date.now() - start) / 1000).toFixed(0)}s`);
})();
