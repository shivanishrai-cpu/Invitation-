// usage: node render2.js <html> stills <outDir> | video <out.mp4> <audio.wav>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
(async () => {
  const [html, mode, out, audio] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(2); });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(() => window.ready);
  const grab = t => page.evaluate(t => { window.render(t); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, t);
  if (mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    const ts = [0.0, 0.8, 1.7, 2.8, 4.2, 6.0, 8.0, 10.2, 11.0, 12.3, 13.8, 15.6, 17.4, 19.6, 21.6, 23.2];
    for (const [i, t] of ts.entries()) fs.writeFileSync(path.join(out, `f${String(i).padStart(2, '0')}.jpg`), Buffer.from((await grab(t)).split(',')[1], 'base64'));
  } else {
    const FPS = 30, DUR = 23.5, N = Math.round(FPS * DUR);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-i', audio,
      '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS),
      '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', String(DUR), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < N; i++) {
      if (!ff.stdin.write(Buffer.from((await grab(i / FPS)).split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 100 === 0) console.log('frame', i);
    }
    ff.stdin.end();
    await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
