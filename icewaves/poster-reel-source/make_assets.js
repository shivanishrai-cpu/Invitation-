// Renders the CapCut asset pack from the poster-reel page's own drawing functions.
// usage: node make_assets.js <outDir>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(2); });
  await page.goto('http://127.0.0.1:8765/poster-reel.html');
  await page.evaluate(() => window.ready);
  const save = async (name, fnSrc) => {
    const url = await page.evaluate(src => {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, W, H);
      (new Function(src))();
      return off.toDataURL('image/png');
    }, fnSrc);
    fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
  };
  // backgrounds
  await save('bg-green.png', "set('green')");
  await save('bg-mustard.png', "set('mustard')");
  await save('bg-cream.png', "set('cream')");
  // text images (drawn fully popped-in)
  await save('text-1-hook.png', "drawText([{ text: 'A new wave' }, { text: 'just hit' }, { text: 'Uliyathaduka', size: 104 }], 10, 0, 100, 600)");
  await save('text-2-kunafa-on-top.png', "drawText([{ text: 'Kunafa on top', size: 110 }], 10, 0, 100, 600)");
  await save('text-3-pistachio.png', "drawText([{ text: 'Pistachio' }, { text: 'Kunafa Shake', size: 88 }], 10, 0, 100, 600)");
  await save('text-4-biscoff.png', "drawText([{ text: 'Biscoff' }, { text: 'Kunafa Shake', size: 88 }], 10, 0, 100, 600)");
  await save('text-5-catch-the-wave.png', "drawText([{ text: 'Catch the wave', size: 116 }], 10, 0, 100, 600)");
  await save('text-6-visit-uliyathaduka.png', "drawText([{ text: 'Visit us in', size: 60 }], 10, 0, 100, 600); pin(225, 695, 1.05, 1); drawText([{ text: 'Uliyathaduka', size: 100 }], 10, 0, 100, 695, 565)");
  await save('badge-160.png', "priceBadge(540, 960, 10, 0, 100)");
  await save('sparkle.png', "star(540, 960, 160, 1)");
  // green-screen wave wipe, 1 s, frame 15 = fully covered
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', path.join(out, 'wave-greenscreen.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < 30; i++) {
    const url = await page.evaluate(p => {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
      ctx.fillStyle = '#00FF00'; ctx.fillRect(0, 0, W, H);
      drawWave(p);
      return off.toDataURL('image/png');
    }, (i + 0.5) / 30);
    ff.stdin.write(Buffer.from(url.split(',')[1], 'base64'));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
