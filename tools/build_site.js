// Builds the website version of Photobooth Studio (published on GitHub Pages) into one folder:
//   index.html + grids.json, the built-in backgrounds (drawn by make_backgrounds.js), small thumbnails
//   for the picker, and Backgrounds/index.json listing them. Your own Backgrounds/ and Stickers/ are never included.
// Needs Node and the canvas library:  npm install @napi-rs/canvas
// Usage:  node tools/build_site.js site
const napi = require('@napi-rs/canvas'), fs = require('fs'), path = require('path'), {execFileSync} = require('child_process');
const ROOT = path.join(__dirname, '..'), OUT = path.resolve(process.argv[2] || 'site'), BG = path.join(OUT, 'Backgrounds'), THUMB = 240;

fs.rmSync(OUT, {recursive: true, force: true});
fs.mkdirSync(path.join(BG, 'thumbs'), {recursive: true});
fs.copyFileSync(path.join(ROOT, 'studio/web/index.html'), path.join(OUT, 'index.html'));
fs.copyFileSync(path.join(ROOT, 'grids.json'), path.join(OUT, 'grids.json'));
fs.writeFileSync(path.join(OUT, '.nojekyll'), '');
execFileSync(process.execPath, [path.join(__dirname, 'make_backgrounds.js'), BG], {stdio: 'inherit'});

(async () => {
  const files = fs.readdirSync(BG).filter(f => /\.(jpe?g|png)$/i.test(f)).sort((a, b) => a.localeCompare(b));
  for (const f of files){
    const img = await napi.loadImage(path.join(BG, f)), k = THUMB / Math.max(img.width, img.height);
    const c = napi.createCanvas(Math.round(img.width * k), Math.round(img.height * k));
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    fs.writeFileSync(path.join(BG, 'thumbs', f), await c.encode('jpeg', 80));
  }
  fs.writeFileSync(path.join(BG, 'index.json'), JSON.stringify({files}, null, 1) + '\n');
  console.log(`site ready in ${OUT} (${files.length} backgrounds)`);
})();
