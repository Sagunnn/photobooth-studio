// Draws the built-in background designs (3000×3000 JPEGs, square so they cover portrait and landscape templates).
// Needs Node and the canvas library:  npm install @napi-rs/canvas
// Usage:  node tools/make_backgrounds.js Backgrounds            (all designs)
//         node tools/make_backgrounds.js Backgrounds Laundry    (only names containing "Laundry")
const napi = require('@napi-rs/canvas'), fs = require('fs'), path = require('path');
const OUT = process.argv[2], ONLY = process.argv[3], N = 3000;
const rand = seed => () => (seed = seed * 16807 % 2147483647) / 2147483647;
const TAU = Math.PI * 2;
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

function canvas(){ const c = napi.createCanvas(N, N); return [c, c.getContext('2d')]; }
function vgrad(x, stops){ const g = x.createLinearGradient(0, 0, 0, N); stops.forEach(([o, c]) => g.addColorStop(o, c)); x.fillStyle = g; x.fillRect(0, 0, N, N); }
function grain(x, amt = 3, seed = 9){   // a little noise so gradients don't band when printed
  const d = x.getImageData(0, 0, N, N), p = d.data, r = rand(seed);
  for (let i = 0; i < p.length; i += 4){ const n = (r() - 0.5) * 2 * amt; p[i] += n; p[i+1] += n; p[i+2] += n; }
  x.putImageData(d, 0, 0);
}
function perPixel(x, fn){ const d = x.createImageData(N, N), p = d.data;
  for (let y = 0; y < N; y++) for (let X = 0; X < N; X++){ const [r, g, b] = fn(X, y), i = (y * N + X) * 4; p[i] = r; p[i+1] = g; p[i+2] = b; p[i+3] = 255; }
  x.putImageData(d, 0, 0); }
function bubble(x, cx, cy, r, alpha = 1){   // soap bubble: clear middle, bright rim, rainbow sheen, highlight
  x.save(); x.globalAlpha = alpha;
  let g = x.createRadialGradient(cx, cy, r * 0.2, cx, cy, r);
  g.addColorStop(0, 'rgba(255,255,255,0.04)'); g.addColorStop(0.8, 'rgba(255,255,255,0.14)'); g.addColorStop(0.96, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0.0)');
  x.fillStyle = g; x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.fill();
  const s = x.createLinearGradient(cx - r, cy - r, cx + r, cy + r);
  s.addColorStop(0, 'rgba(255,120,200,0.35)'); s.addColorStop(0.5, 'rgba(120,220,255,0.3)'); s.addColorStop(1, 'rgba(255,230,120,0.35)');
  x.strokeStyle = s; x.lineWidth = Math.max(2, r * 0.05); x.beginPath(); x.arc(cx, cy, r * 0.97, 0, TAU); x.stroke();
  x.fillStyle = 'rgba(255,255,255,0.75)'; x.beginPath(); x.ellipse(cx - r * 0.42, cy - r * 0.45, r * 0.22, r * 0.11, -0.7, 0, TAU); x.fill();
  x.beginPath(); x.arc(cx + r * 0.45, cy + r * 0.4, r * 0.05, 0, TAU); x.fill();
  x.restore();
}
function rrect(x, X, Y, w, h, r){ x.beginPath(); x.roundRect(X, Y, w, h, r); }
function scatter(seed, count, minGap, margin = -100){   // points spread out (no two closer than minGap)
  const r = rand(seed), out = []; let tries = 0;
  while (out.length < count && tries++ < count * 60){ const p = [margin + r() * (N - 2*margin), margin + r() * (N - 2*margin)];
    if (out.every(q => Math.hypot(q[0] - p[0], q[1] - p[1]) >= minGap)) out.push(p); }
  return out;
}

/* ---------- laundry pieces ---------- */
const INK = '#24324a';
function washer(x, cx, cy, s, rot, body = '#ffffff', water = '#7cc4f5'){
  x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.lineWidth = 9; x.strokeStyle = INK; x.lineJoin = 'round';
  x.fillStyle = INK; rrect(x, -110, 160, 40, 18, 6); x.fill(); rrect(x, 70, 160, 40, 18, 6); x.fill();   // feet
  x.fillStyle = body; rrect(x, -130, -170, 260, 340, 30); x.fill(); x.stroke();
  x.fillStyle = '#e8eef5'; rrect(x, -130, -170, 260, 70, [30, 30, 0, 0]); x.fill(); x.stroke();
  x.fillStyle = '#ff8fb1'; x.beginPath(); x.arc(-90, -135, 14, 0, TAU); x.fill(); x.stroke();
  x.fillStyle = '#ffd23f'; x.beginPath(); x.arc(-50, -135, 14, 0, TAU); x.fill(); x.stroke();
  x.fillStyle = '#9be7c4'; rrect(x, 20, -150, 80, 30, 8); x.fill(); x.stroke();
  x.fillStyle = '#c9d3e0'; x.beginPath(); x.arc(0, 40, 100, 0, TAU); x.fill(); x.stroke();
  x.save(); x.beginPath(); x.arc(0, 40, 74, 0, TAU); x.clip();
  x.fillStyle = '#dff2ff'; x.fillRect(-80, -40, 160, 160);
  x.fillStyle = water; x.beginPath(); x.moveTo(-80, 50);
  for (let i = -80; i <= 80; i += 10) x.lineTo(i, 40 + Math.sin(i / 14) * 9); x.lineTo(80, 130); x.lineTo(-80, 130); x.fill();
  x.fillStyle = 'rgba(255,255,255,0.85)'; for (const [bx, by, br] of [[-30, 70, 10], [10, 90, 7], [36, 62, 12], [-6, 58, 5]]){ x.beginPath(); x.arc(bx, by, br, 0, TAU); x.fill(); }
  x.restore();
  x.beginPath(); x.arc(0, 40, 74, 0, TAU); x.stroke();
  x.strokeStyle = 'rgba(255,255,255,0.9)'; x.lineWidth = 8; x.lineCap = 'round'; x.beginPath(); x.arc(0, 40, 56, 3.6, 4.4); x.stroke();
  x.restore();
}
function shirt(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.beginPath(); x.moveTo(-40, 0); x.lineTo(-90, 30); x.lineTo(-70, 72); x.lineTo(-50, 62); x.lineTo(-50, 170); x.lineTo(50, 170); x.lineTo(50, 62); x.lineTo(70, 72); x.lineTo(90, 30); x.lineTo(40, 0); x.quadraticCurveTo(0, 26, -40, 0); x.closePath();
  x.fillStyle = col; x.fill(); x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round'; x.stroke(); x.restore(); }
function sock(x, cx, cy, s, rot, col, band = '#ffffff'){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.beginPath(); x.moveTo(-22, 0); x.lineTo(22, 0); x.lineTo(22, 112); x.quadraticCurveTo(22, 150, -12, 150); x.lineTo(-52, 150); x.quadraticCurveTo(-74, 150, -74, 130); x.quadraticCurveTo(-74, 110, -52, 108); x.lineTo(-22, 104); x.closePath();
  x.fillStyle = col; x.fill(); x.save(); x.clip(); x.fillStyle = band; x.fillRect(-30, 14, 60, 14); x.fillRect(-30, 38, 60, 14); x.restore();
  x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round'; x.stroke(); x.restore(); }
function dress(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.beginPath(); x.moveTo(-30, 0); x.lineTo(-40, 60); x.lineTo(-82, 190); x.lineTo(82, 190); x.lineTo(40, 60); x.lineTo(30, 0); x.quadraticCurveTo(0, 16, -30, 0); x.closePath();
  x.fillStyle = col; x.fill(); x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round'; x.stroke();
  x.beginPath(); x.moveTo(-40, 62); x.lineTo(40, 62); x.stroke(); x.restore(); }
function towel(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  rrect(x, -60, 0, 120, 160, 6); x.fillStyle = col; x.fill(); x.save(); x.clip(); x.fillStyle = 'rgba(255,255,255,0.8)'; x.fillRect(-60, 118, 120, 12); x.fillRect(-60, 138, 120, 6); x.restore();
  rrect(x, -60, 0, 120, 160, 6); x.lineWidth = 8; x.strokeStyle = INK; x.stroke(); x.restore(); }
function shorts(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.beginPath(); x.moveTo(-60, 0); x.lineTo(60, 0); x.lineTo(72, 112); x.lineTo(14, 112); x.lineTo(0, 50); x.lineTo(-14, 112); x.lineTo(-72, 112); x.closePath();
  x.fillStyle = col; x.fill(); x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round'; x.stroke(); x.restore(); }
function pin(x, px, py){ x.save(); x.fillStyle = '#b07a4f'; x.strokeStyle = INK; x.lineWidth = 5; rrect(x, px - 7, py - 16, 14, 34, 4); x.fill(); x.stroke(); x.restore(); }
function bottle(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round';
  x.fillStyle = '#ffffff'; rrect(x, -26, -110, 52, 34, 8); x.fill(); x.stroke();
  x.fillStyle = col; x.beginPath(); x.moveTo(-50, -76); x.lineTo(50, -76); x.quadraticCurveTo(70, -70, 70, -40); x.lineTo(70, 90); x.quadraticCurveTo(70, 110, 50, 110); x.lineTo(-50, 110); x.quadraticCurveTo(-70, 110, -70, 90); x.lineTo(-70, -40); x.quadraticCurveTo(-70, -70, -50, -76); x.fill(); x.stroke();
  x.fillStyle = '#ffffff'; rrect(x, -44, -10, 88, 70, 10); x.fill(); x.stroke();
  x.fillStyle = '#7cc4f5'; for (const [bx, by, br] of [[-14, 26, 12], [12, 16, 9], [14, 40, 7]]){ x.beginPath(); x.arc(bx, by, br, 0, TAU); x.fill(); }
  x.restore(); }
function basket(x, cx, cy, s, rot){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.lineWidth = 8; x.strokeStyle = INK; x.lineJoin = 'round';
  x.fillStyle = '#ff8fb1'; x.beginPath(); x.arc(-30, -20, 40, Math.PI, 0); x.fill(); x.stroke();
  x.fillStyle = '#7cc4f5'; x.beginPath(); x.arc(30, -14, 34, Math.PI, 0); x.fill(); x.stroke();
  x.fillStyle = '#f6c445'; x.beginPath(); x.moveTo(-90, -20); x.lineTo(90, -20); x.lineTo(70, 100); x.lineTo(-70, 100); x.closePath(); x.fill(); x.stroke();
  x.beginPath(); for (const yy of [20, 60]){ x.moveTo(-84, yy); x.lineTo(84, yy); } for (const xx of [-40, 0, 40]){ x.moveTo(xx, -20); x.lineTo(xx * 0.8, 100); } x.stroke();
  x.restore(); }
function bubbleIcon(x, cx, cy, s){ x.save(); x.translate(cx, cy); x.scale(s, s); x.lineWidth = 7; x.strokeStyle = INK; x.fillStyle = '#dff2ff';
  for (const [bx, by, br] of [[0, 0, 40], [48, -30, 24], [44, 30, 16]]){ x.beginPath(); x.arc(bx, by, br, 0, TAU); x.fill(); x.stroke(); }
  x.fillStyle = '#fff'; x.beginPath(); x.ellipse(-14, -14, 12, 7, -0.7, 0, TAU); x.fill(); x.restore(); }

/* ---------- designs ---------- */
const D = {};

D['Laundry - Soap Bubbles'] = x => {
  vgrad(x, [[0, '#a9dcff'], [0.55, '#d4eeff'], [1, '#eef8ff']]); grain(x, 2);
  const r = rand(11);
  for (let i = 0; i < 170; i++){ const rad = 18 + Math.pow(r(), 2.4) * 300; bubble(x, r() * N, r() * N, rad, 0.75 + r() * 0.25); }
};
D['Laundry - Washing Machines'] = x => {
  x.fillStyle = '#ffe3ea'; x.fillRect(0, 0, N, N);
  const r = rand(5), bodies = ['#ffffff', '#fff7d6', '#e6f6ff', '#eafff3'];
  for (let row = -1, i = 0; row < 8; row++) for (let col = -1; col < 9; col++, i++){
    const cx = col * 400 + (row % 2 ? 200 : 0) + 100, cy = row * 440 + 160;
    washer(x, cx, cy, 0.78, (r() - 0.5) * 0.25, bodies[i % 4]);
  }
  for (let i = 0; i < 140; i++){ x.fillStyle = 'rgba(255,255,255,0.8)'; x.beginPath(); x.arc(r() * N, r() * N, 6 + r() * 14, 0, TAU); x.fill(); }
};
D['Laundry - Laundromat Tiles'] = x => {
  const s = 150;
  for (let y = 0; y < N / s; y++) for (let X = 0; X < N / s; X++){ x.fillStyle = (X + y) % 2 ? '#bfe8d9' : '#f7fbf9'; x.fillRect(X * s, y * s, s, s); }
  x.strokeStyle = 'rgba(36,50,74,0.10)'; x.lineWidth = 4; x.beginPath();
  for (let i = 0; i <= N; i += s){ x.moveTo(i, 0); x.lineTo(i, N); x.moveTo(0, i); x.lineTo(N, i); } x.stroke();
  grain(x, 4, 3);
};
D['Laundry - Clothesline'] = x => {
  vgrad(x, [[0, '#d9efff'], [1, '#f4fbff']]); grain(x, 2);
  const r = rand(21), cols = ['#ff8fb1', '#7cc4f5', '#ffd23f', '#9be7c4', '#c7b8ff', '#ffb38a', '#ffffff'];
  const items = [shirt, sock, dress, towel, shorts, sock, shirt];
  for (let line = 0; line < 7; line++){
    const y0 = 160 + line * 450, sag = 70;
    const yAt = X => y0 + sag * Math.sin(Math.PI * X / N);
    x.strokeStyle = '#8a6d52'; x.lineWidth = 7; x.beginPath(); for (let X = 0; X <= N; X += 20) X ? x.lineTo(X, yAt(X)) : x.moveTo(X, yAt(X)); x.stroke();
    let X = 60 + r() * 120;
    while (X < N - 40){
      const k = Math.floor(r() * items.length), f = items[k], col = cols[Math.floor(r() * cols.length)], y = yAt(X), s = 0.95 + r() * 0.3, tilt = (r() - 0.5) * 0.12;
      f(x, X, y, s, tilt, col);
      const half = (f === sock ? 18 : f === towel ? 50 : f === shorts ? 50 : 34) * s;
      pin(x, X - half, y); if (f !== sock) pin(x, X + half, y);
      X += (f === sock ? 150 : 230) * s + 40 + r() * 90;
    }
  }
};
D['Laundry - Pink Suds'] = x => {
  vgrad(x, [[0, '#ffc9dc'], [1, '#ffeef5']]); grain(x, 2);
  const r = rand(31);
  const foam = (yc, spread, count) => { for (let i = 0; i < count; i++){ const cx = r() * (N + 200) - 100, cy = yc + (r() - 0.5) * spread, rad = 40 + r() * 140;
    const g = x.createRadialGradient(cx - rad * 0.3, cy - rad * 0.3, rad * 0.1, cx, cy, rad);
    g.addColorStop(0, '#ffffff'); g.addColorStop(0.75, 'rgba(255,255,255,0.95)'); g.addColorStop(0.92, 'rgba(255,214,229,0.9)'); g.addColorStop(1, 'rgba(255,214,229,0)');
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.fill(); } };
  foam(N + 20, 420, 420); foam(-20, 260, 260);
  for (let i = 0; i < 110; i++){ const rad = 14 + Math.pow(r(), 2.2) * 150; bubble(x, r() * N, 250 + r() * (N - 600), rad, 0.9); }
};
D['Laundry - Spin Cycle'] = x => {
  const c = N / 2, A = hex('#1565c0'), B = hex('#7dd3fc'), Wt = [255, 255, 255];
  perPixel(x, (X, y) => { const dx = X - c, dy = y - c, rr = Math.hypot(dx, dy), th = Math.atan2(dy, dx);
    let t = 0.5 + 0.5 * Math.sin(5 * th + rr * 0.0105); t = t * t * (3 - 2 * t);
    let col = mix(A, B, t); if (t > 0.93) col = mix(col, Wt, (t - 0.93) / 0.07 * 0.7);
    const shade = 0.82 + 0.18 * Math.min(1, rr / 1400); return col.map(v => v * shade); });
  grain(x, 3, 5); const r = rand(41);
  for (let i = 0; i < 90; i++){ const rad = 12 + Math.pow(r(), 2.4) * 170; bubble(x, r() * N, r() * N, rad, 0.85); }
};
D['Laundry - Retro Laundromat'] = x => {
  x.fillStyle = '#fff1d6'; x.fillRect(0, 0, N, N);
  const cols = ['#e76f51', '#f4a261', '#e9c46a', '#2a9d8f', '#264653'], w = 110;
  x.save(); x.translate(N / 2, N / 2); x.rotate(-0.5);
  for (const off of [-1900, -650, 600, 1850]) cols.forEach((c, i) => { x.strokeStyle = c; x.lineWidth = w; x.beginPath();
    for (let X = -2600; X <= 2600; X += 20){ const Y = off + (i - 2) * w + Math.sin(X / 380) * 120; X === -2600 ? x.moveTo(X, Y) : x.lineTo(X, Y); } x.stroke(); });
  x.restore();
  const r = rand(51); for (let i = 0; i < 160; i++){ const cx = r() * N, cy = r() * N, rad = 8 + r() * 26;
    x.strokeStyle = 'rgba(42,157,143,0.55)'; x.lineWidth = 5; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.stroke(); }
  grain(x, 4, 8);
};
D['Laundry - Icons Pattern'] = x => {
  x.fillStyle = '#fff6cc'; x.fillRect(0, 0, N, N);
  const r = rand(61), cols = ['#ff8fb1', '#7cc4f5', '#9be7c4', '#c7b8ff', '#ffb38a'];
  const pts = scatter(17, 140, 290);
  pts.forEach(([cx, cy], i) => { const k = i % 6, rot = (r() - 0.5) * 0.7, c = cols[Math.floor(r() * 5)];
    if (k === 0) washer(x, cx, cy, 0.5, rot);
    else if (k === 1) shirt(x, cx, cy - 70, 0.75, rot, c);
    else if (k === 2) sock(x, cx + 20, cy - 60, 0.8, rot, c);
    else if (k === 3) bottle(x, cx, cy, 0.75, rot, c);
    else if (k === 4) basket(x, cx, cy, 0.7, rot);
    else bubbleIcon(x, cx, cy, 1.1); });
};
D['Laundry - Steel Drum'] = x => {
  const r = rand(71);
  perPixel(x, (X, y) => { const v = 200 + 10 * Math.sin(y * 0.004) + 6 * Math.sin(y * 0.031 + X * 0.0007); return [v - 4, v, v + 6]; });
  const d = x.getImageData(0, 0, N, N), p = d.data;   // brushed streaks
  for (let y = 0; y < N; y++){ const s = (r() - 0.5) * 16; for (let X = 0; X < N; X++){ const i = (y * N + X) * 4, n = s + (r() - 0.5) * 6; p[i] += n; p[i+1] += n; p[i+2] += n; } }
  x.putImageData(d, 0, 0);
  const sp = 96, hr = 17;
  for (let row = 0; row * sp * 0.866 < N + sp; row++) for (let col = -1; col * sp < N + sp; col++){
    const cx = col * sp + (row % 2 ? sp / 2 : 0), cy = row * sp * 0.866;
    x.fillStyle = 'rgba(255,255,255,0.7)'; x.beginPath(); x.arc(cx, cy + 3, hr + 2, 0, TAU); x.fill();
    const g = x.createRadialGradient(cx, cy - 4, 2, cx, cy, hr); g.addColorStop(0, '#1f2937'); g.addColorStop(1, '#4b5563');
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, hr, 0, TAU); x.fill();
  }
};

D['Classic - Pastel Blend'] = x => {
  const TL = hex('#ffd3c4'), TR = hex('#e2d4ff'), BL = hex('#c6f1e1'), BR = hex('#cbe6ff');
  perPixel(x, (X, y) => { const u = X / N, v = y / N; return mix(mix(TL, TR, u), mix(BL, BR, u), v); }); grain(x, 3);
};
D['Classic - Sunset Glow'] = x => { vgrad(x, [[0, '#ffd08a'], [0.45, '#ff8a8a'], [1, '#9d7be0']]); grain(x, 3);
  const g = x.createRadialGradient(N / 2, N * 0.42, 0, N / 2, N * 0.42, N * 0.6); g.addColorStop(0, 'rgba(255,240,200,0.55)'); g.addColorStop(1, 'rgba(255,240,200,0)'); x.fillStyle = g; x.fillRect(0, 0, N, N); };
D['Classic - Midnight Stars'] = x => {
  const g = x.createRadialGradient(N / 2, N * 0.4, 0, N / 2, N / 2, N * 0.75); g.addColorStop(0, '#22346a'); g.addColorStop(1, '#0a0f22'); x.fillStyle = g; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(81);
  for (let i = 0; i < 1400; i++){ x.fillStyle = `rgba(255,255,255,${0.25 + r() * 0.75})`; x.beginPath(); x.arc(r() * N, r() * N, 1.5 + Math.pow(r(), 3) * 5, 0, TAU); x.fill(); }
  for (let i = 0; i < 45; i++){ const cx = r() * N, cy = r() * N, s = 18 + r() * 40;
    const gl = x.createRadialGradient(cx, cy, 0, cx, cy, s * 1.6); gl.addColorStop(0, 'rgba(255,240,200,0.6)'); gl.addColorStop(1, 'rgba(255,240,200,0)'); x.fillStyle = gl; x.beginPath(); x.arc(cx, cy, s * 1.6, 0, TAU); x.fill();
    x.fillStyle = '#fff6d8'; x.beginPath(); x.moveTo(cx, cy - s); x.quadraticCurveTo(cx + s * 0.12, cy - s * 0.12, cx + s, cy); x.quadraticCurveTo(cx + s * 0.12, cy + s * 0.12, cx, cy + s);
    x.quadraticCurveTo(cx - s * 0.12, cy + s * 0.12, cx - s, cy); x.quadraticCurveTo(cx - s * 0.12, cy - s * 0.12, cx, cy - s); x.fill(); }
};
D['Classic - Confetti'] = x => {
  x.fillStyle = '#fffdf7'; x.fillRect(0, 0, N, N);
  const r = rand(91), C = ['#ff4f8b', '#ffd23f', '#5b8cff', '#34d399', '#a78bfa', '#ff8a3d'];
  for (let i = 0; i < 650; i++){ const cx = r() * N, cy = r() * N, c = C[i % 6], a = r() * Math.PI, t = i % 3, s = 0.8 + r() * 0.9;
    x.save(); x.translate(cx, cy); x.rotate(a); x.scale(s, s); x.fillStyle = c; x.strokeStyle = c; x.lineCap = 'round';
    if (t === 0) { rrect(x, -18, -8, 36, 16, 3); x.fill(); }
    else if (t === 1) { x.beginPath(); x.arc(0, 0, 10, 0, TAU); x.fill(); }
    else { x.lineWidth = 8; x.beginPath(); x.moveTo(-22, 0); x.quadraticCurveTo(-11, -14, 0, 0); x.quadraticCurveTo(11, 14, 22, 0); x.stroke(); }
    x.restore(); }
};
D['Classic - Gold Glitter'] = x => {
  x.fillStyle = '#0d0d10'; x.fillRect(0, 0, N, N);
  const r = rand(101), golds = ['#f8e08e', '#e6c15a', '#c9a14a', '#fff3c4', '#b8862b'];
  for (let i = 0; i < 70; i++){ const cx = r() * N, cy = r() * N, rad = 40 + r() * 160, g = x.createRadialGradient(cx, cy, 0, cx, cy, rad);
    g.addColorStop(0, 'rgba(230,193,90,0.22)'); g.addColorStop(0.7, 'rgba(230,193,90,0.12)'); g.addColorStop(1, 'rgba(230,193,90,0)'); x.fillStyle = g; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.fill(); }
  for (let i = 0; i < 90000; i++){ const y = r() * N, edge = Math.min(y, N - y) / (N / 2);   // denser near the top and bottom
    if (r() < edge * 0.85) continue;
    x.fillStyle = golds[Math.floor(r() * 5)]; x.globalAlpha = 0.4 + r() * 0.6; const s = 2 + r() * 5; x.fillRect(r() * N, y, s, s); }
  x.globalAlpha = 1;
};
D['Classic - Pink Bokeh'] = x => {
  vgrad(x, [[0, '#ff8fb1'], [1, '#ffd0e0']]); grain(x, 2);
  const r = rand(111);
  for (let i = 0; i < 150; i++){ const cx = r() * N, cy = r() * N, rad = 30 + Math.pow(r(), 1.6) * 260, a = 0.12 + r() * 0.3;
    const g = x.createRadialGradient(cx, cy, 0, cx, cy, rad); g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(0.85, `rgba(255,255,255,${a * 0.8})`); g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.fill(); }
};
D['Classic - Candy Stripes'] = x => {
  x.fillStyle = '#fff4f7'; x.fillRect(0, 0, N, N);
  x.save(); x.translate(N / 2, N / 2); x.rotate(Math.PI / 4);
  for (let i = -30; i < 30; i++){ x.fillStyle = '#ffc8d8'; x.fillRect(i * 240, -N, 120, 2 * N); x.fillStyle = '#bfeee0'; x.fillRect(i * 240 + 150, -N, 24, 2 * N); }
  x.restore(); grain(x, 2);
};
D['Classic - Mint Polka Dots'] = x => {
  x.fillStyle = '#bfeee0'; x.fillRect(0, 0, N, N); x.fillStyle = '#ffffff';
  for (let row = 0; row * 150 < N + 150; row++) for (let col = -1; col * 150 < N + 150; col++){ x.beginPath(); x.arc(col * 150 + (row % 2 ? 75 : 0), row * 150, 34, 0, TAU); x.fill(); }
  grain(x, 2);
};
D['Classic - Terrazzo'] = x => {
  x.fillStyle = '#f4efe8'; x.fillRect(0, 0, N, N); grain(x, 4);
  const r = rand(121), C = ['#e07a5f', '#81b29a', '#f2cc8f', '#3d405b', '#f4a6a6'];
  for (let i = 0; i < 1100; i++){ const cx = r() * N, cy = r() * N, s = 8 + Math.pow(r(), 2) * 55, n = 5 + Math.floor(r() * 4), a0 = r() * TAU;
    x.fillStyle = C[Math.floor(r() * 5)]; x.beginPath();
    for (let k = 0; k < n; k++){ const a = a0 + k / n * TAU, rr = s * (0.55 + r() * 0.45); k ? x.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)) : x.moveTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)); }
    x.closePath(); x.fill(); }
};
D['Classic - Groovy Waves'] = x => {
  const cols = ['#f6bd60', '#f28482', '#84a59d', '#f5cac3', '#f7ede2', '#f6bd60', '#f28482', '#84a59d', '#f5cac3', '#f7ede2', '#f6bd60', '#f28482', '#84a59d'];
  const bh = N / (cols.length - 2);
  cols.forEach((c, i) => { x.fillStyle = c; x.beginPath(); x.moveTo(0, N + 10);
    for (let X = 0; X <= N; X += 15) x.lineTo(X, (i - 1) * bh + Math.sin(X / 300 + i * 0.6) * 90); x.lineTo(N, N + 10); x.closePath(); x.fill(); });
  grain(x, 3);
};
D['Classic - Holographic'] = x => {
  const hsl = (h, s, l) => { const k = n => (n + h * 12) % 12, a = s * Math.min(l, 1 - l); return [0, 8, 4].map(n => 255 * (l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1)))); };
  perPixel(x, (X, y) => { const h = ((X * 0.00028 + y * 0.0002 + 0.12 * Math.sin(X * 0.0021) + 0.12 * Math.sin(y * 0.0017 + 1.3)) % 1 + 1) % 1; return hsl(h, 0.65, 0.84); });
  grain(x, 3);
};
D['Classic - Blush Florals'] = x => {
  x.fillStyle = '#fde2e4'; x.fillRect(0, 0, N, N); grain(x, 2);
  const r = rand(131), petals = ['#ffffff', '#f9bec7', '#ffd6a5', '#cdb4db'];
  for (const [cx, cy] of scatter(29, 160, 230)){
    const s = 0.7 + r() * 0.6, a = r() * TAU, c = petals[Math.floor(r() * 4)];
    x.save(); x.translate(cx, cy); x.rotate(a); x.scale(s, s);
    x.fillStyle = '#a7c4a0'; for (const k of [0.3, 3.5]){ x.save(); x.rotate(k); x.beginPath(); x.ellipse(95, 0, 50, 20, 0, 0, TAU); x.fill(); x.restore(); }
    x.fillStyle = c; for (let k = 0; k < 5; k++){ x.save(); x.rotate(k / 5 * TAU); x.beginPath(); x.arc(0, -42, 36, 0, TAU); x.fill(); x.restore(); }
    x.fillStyle = '#f6c445'; x.beginPath(); x.arc(0, 0, 24, 0, TAU); x.fill();
    x.restore(); }
};

/* ---------- more themes (trend research: Y2K, wedding, party, graduation, seasonal, minimal) ---------- */
try { napi.GlobalFonts.registerFromPath('/System/Library/Fonts/Supplemental/Chalkduster.ttf', 'Chalkduster'); } catch {}
function noise2(seed){ const r = rand(seed), G = 256, t = Float32Array.from({length: G * G}, r), sm = v => v * v * (3 - 2 * v);
  return (X, Y) => { const xi = Math.floor(X), yi = Math.floor(Y), u = sm(X - xi), v = sm(Y - yi), a = (i, j) => t[((yi + j) & 255) * G + ((xi + i) & 255)];
    return (a(0, 0) * (1 - u) + a(1, 0) * u) * (1 - v) + (a(0, 1) * (1 - u) + a(1, 1) * u) * v; }; }
function fbm(n, X, Y, oct = 5){ let s = 0, a = 0.5, f = 1; for (let i = 0; i < oct; i++){ s += a * n(X * f, Y * f); a /= 2; f *= 2; } return s; }
function heart(x, cx, cy, s){ x.beginPath(); x.moveTo(cx, cy + s * 0.9);
  x.bezierCurveTo(cx - s * 1.5, cy - s * 0.1, cx - s * 0.6, cy - s * 1.15, cx, cy - s * 0.35);
  x.bezierCurveTo(cx + s * 0.6, cy - s * 1.15, cx + s * 1.5, cy - s * 0.1, cx, cy + s * 0.9); x.closePath(); }
function sparkle4(x, cx, cy, s){ x.beginPath(); x.moveTo(cx, cy - s); x.quadraticCurveTo(cx + s * 0.12, cy - s * 0.12, cx + s, cy); x.quadraticCurveTo(cx + s * 0.12, cy + s * 0.12, cx, cy + s);
  x.quadraticCurveTo(cx - s * 0.12, cy + s * 0.12, cx - s, cy); x.quadraticCurveTo(cx - s * 0.12, cy - s * 0.12, cx, cy - s); x.closePath(); }
function star5(x, cx, cy, R, r = R * 0.45, rot = 0){ x.beginPath(); for (let i = 0; i < 10; i++){ const a = rot + i * Math.PI / 5 - Math.PI / 2, rr = i % 2 ? r : R;
  i ? x.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)) : x.moveTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)); } x.closePath(); }
function blossom(x, cx, cy, s, rot, col){ x.save(); x.translate(cx, cy); x.rotate(rot); x.fillStyle = col;
  for (let k = 0; k < 5; k++){ x.save(); x.rotate(k / 5 * TAU); x.beginPath(); x.ellipse(0, -s * 0.95, s * 0.62, s * 0.78, 0, 0, TAU); x.fill(); x.restore(); }
  x.fillStyle = '#f26a8d'; x.beginPath(); x.arc(0, 0, s * 0.32, 0, TAU); x.fill(); x.fillStyle = '#ffe08a';
  for (let k = 0; k < 6; k++){ const a = k / 6 * TAU; x.beginPath(); x.arc(Math.cos(a) * s * 0.5, Math.sin(a) * s * 0.5, s * 0.09, 0, TAU); x.fill(); } x.restore(); }
function softVignette(x, a = 0.12){ const g = x.createRadialGradient(N / 2, N / 2, N * 0.3, N / 2, N / 2, N * 0.75); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`); x.fillStyle = g; x.fillRect(0, 0, N, N); }

/* Y2K */
D['Y2K - Chrome Stars'] = x => {
  const g = x.createLinearGradient(0, 0, N, N); g.addColorStop(0, '#ffb8e0'); g.addColorStop(0.5, '#cdb8ff'); g.addColorStop(1, '#a8e6ff'); x.fillStyle = g; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(201);
  for (const [cx, cy] of scatter(203, 110, 230)){ const s = 30 + Math.pow(r(), 1.8) * 150, c = x.createLinearGradient(cx - s, cy - s, cx + s, cy + s);
    c.addColorStop(0, '#ffffff'); c.addColorStop(0.35, '#b9c3d6'); c.addColorStop(0.55, '#ffffff'); c.addColorStop(0.8, '#8e9ab3'); c.addColorStop(1, '#f2f5fb');
    sparkle4(x, cx, cy, s); x.fillStyle = c; x.fill(); x.lineWidth = Math.max(2, s * 0.04); x.strokeStyle = 'rgba(255,255,255,0.9)'; x.stroke(); }
  for (let i = 0; i < 400; i++){ x.fillStyle = 'rgba(255,255,255,0.8)'; x.beginPath(); x.arc(r() * N, r() * N, 2 + r() * 5, 0, TAU); x.fill(); }
};
D['Y2K - Pink Leopard'] = x => {
  x.fillStyle = '#ffc6de'; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(211);
  for (const [cx, cy] of scatter(213, 900, 120)){ const s = 0.7 + r() * 0.6, rot = r() * TAU;
    x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
    x.fillStyle = '#ff94c2'; x.beginPath(); x.ellipse(0, 0, 26, 20, 0, 0, TAU); x.fill();
    x.strokeStyle = '#5a1f3d'; x.lineCap = 'round'; x.lineWidth = 15; let a = r() * TAU;
    const segs = 3 + Math.floor(r() * 2); for (let k = 0; k < segs; k++){ const len = 0.7 + r() * 0.7; x.beginPath(); x.arc(0, 0, 34 + r() * 6, a, a + len); x.stroke(); a += len + 0.35 + r() * 0.4; }
    x.restore(); }
  for (let i = 0; i < 500; i++){ x.fillStyle = '#5a1f3d'; x.beginPath(); x.ellipse(r() * N, r() * N, 5 + r() * 8, 4 + r() * 6, r() * 3, 0, TAU); x.fill(); }
};
D['Y2K - Pink Gingham'] = x => {
  x.fillStyle = '#ffffff'; x.fillRect(0, 0, N, N); x.fillStyle = 'rgba(255,120,175,0.42)';
  for (let i = 0; i < N; i += 140){ x.fillRect(i, 0, 70, N); x.fillRect(0, i, N, 70); } grain(x, 3);
};
D['Y2K - Halftone Pop'] = x => {
  x.fillStyle = '#fff15c'; x.fillRect(0, 0, N, N); x.fillStyle = '#ff3d8b';
  x.save(); x.translate(N / 2, N / 2); x.rotate(Math.PI / 4); const sp = 64;
  for (let v = -2200; v < 2200; v += sp) for (let u = -2200; u < 2200; u += sp){
    const t = 0.5 + 0.5 * Math.sin(u / 520) * Math.cos(v / 610); x.beginPath(); x.arc(u, v, 3 + 27 * t, 0, TAU); x.fill(); }
  x.restore();
};
D['Y2K - Butterflies'] = x => {
  vgrad(x, [[0, '#e9dcff'], [1, '#ffe1f0']]); grain(x, 2);
  const r = rand(221), cols = [['#c7b8ff', '#9b87f5'], ['#ffb3d1', '#ff7fb0'], ['#a8e6ff', '#6cc6f0'], ['#fff1a8', '#f6cf4a']];
  for (const [cx, cy] of scatter(223, 120, 260)){ const s = 0.6 + r() * 0.9, [a, b] = cols[Math.floor(r() * 4)];
    x.save(); x.translate(cx, cy); x.rotate((r() - 0.5) * 1.2); x.scale(s, s); x.lineWidth = 6; x.strokeStyle = '#ffffff';
    for (const sx of [-1, 1]){ x.fillStyle = a; x.beginPath(); x.ellipse(sx * 46, -30, 46, 58, sx * 0.5, 0, TAU); x.fill(); x.stroke();
      x.fillStyle = b; x.beginPath(); x.ellipse(sx * 34, 36, 30, 36, -sx * 0.4, 0, TAU); x.fill(); x.stroke();
      x.fillStyle = 'rgba(255,255,255,0.7)'; x.beginPath(); x.arc(sx * 52, -36, 12, 0, TAU); x.fill(); }
    x.fillStyle = '#5b4b8a'; x.beginPath(); x.ellipse(0, 0, 8, 46, 0, 0, TAU); x.fill();
    x.strokeStyle = '#5b4b8a'; x.lineWidth = 4; x.beginPath(); x.moveTo(-3, -42); x.quadraticCurveTo(-14, -70, -26, -76); x.moveTo(3, -42); x.quadraticCurveTo(14, -70, 26, -76); x.stroke();
    x.restore(); }
};

/* wedding */
D['Wedding - Eucalyptus'] = x => {
  x.fillStyle = '#f7f3ea'; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(231), greens = ['#9bb5a0', '#7fa088', '#b7c9b9', '#8daa93'];
  const sprig = (x0, y0, ang, len) => { const x2 = x0 + Math.cos(ang) * len, y2 = y0 + Math.sin(ang) * len, cx1 = (x0 + x2) / 2 + (r() - 0.5) * len * 0.4, cy1 = (y0 + y2) / 2 + (r() - 0.5) * len * 0.4;
    x.strokeStyle = '#8a7f6a'; x.lineWidth = 6; x.beginPath(); x.moveTo(x0, y0); x.quadraticCurveTo(cx1, cy1, x2, y2); x.stroke();
    const n = Math.floor(len / 60); for (let i = 1; i <= n; i++){ const t = i / (n + 1), m = 1 - t, px = m * m * x0 + 2 * m * t * cx1 + t * t * x2, py = m * m * y0 + 2 * m * t * cy1 + t * t * y2, side = i % 2 ? 1 : -1, sz = 30 + (1 - t) * 18;
      x.fillStyle = greens[Math.floor(r() * 4)]; x.globalAlpha = 0.92; x.beginPath(); x.ellipse(px + side * Math.sin(ang) * sz * 0.9, py - side * Math.cos(ang) * sz * 0.9, sz, sz * 0.8, ang, 0, TAU); x.fill(); x.globalAlpha = 1; } };
  for (let i = 0; i < 60; i++){ const edge = i % 4, t = r() * N;
    const [x0, y0, a] = edge === 0 ? [t, -40, Math.PI / 2] : edge === 1 ? [N + 40, t, Math.PI] : edge === 2 ? [t, N + 40, -Math.PI / 2] : [-40, t, 0];
    sprig(x0, y0, a + (r() - 0.5) * 1.1, 450 + r() * 600); }
  for (const [cx, cy] of scatter(233, 40, 400, 300)) sprig(cx, cy, r() * TAU, 220 + r() * 160);
};
D['Wedding - Rose Wall'] = x => {
  x.fillStyle = '#e9a9b4'; x.fillRect(0, 0, N, N);
  const r = rand(241), roses = [['#fbe3e8', '#e8b9c4'], ['#f7c5cf', '#d98c9d'], ['#ffffff', '#e6d3d8'], ['#fbd3b8', '#e3a684'], ['#f4b6c2', '#c97a8c']];
  for (const [cx, cy] of scatter(243, 260, 105, -60)){ x.fillStyle = '#7fa088'; x.beginPath(); x.ellipse(cx + 70, cy + 40, 50, 22, r() * TAU, 0, TAU); x.fill(); }
  const pts2 = []; for (let row = 0; row * 120 < N + 200; row++) for (let col = 0; col * 140 < N + 200; col++) pts2.push([col * 140 + (row % 2 ? 70 : 0) + (r() - 0.5) * 50 - 60, row * 120 + (r() - 0.5) * 50 - 60]);
  for (const [cx, cy] of pts2){ const s = 74 + r() * 26, [a, b] = roses[Math.floor(r() * roses.length)], rot = r() * TAU;
    const g = x.createRadialGradient(cx, cy, s * 0.1, cx, cy, s); g.addColorStop(0, b); g.addColorStop(0.55, a); g.addColorStop(1, b);
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, s, 0, TAU); x.fill();
    x.strokeStyle = b; x.lineCap = 'round';
    for (let k = 0; k < 6; k++){ const rr = s * (0.92 - k * 0.14), st = rot + k * 1.9; x.lineWidth = 6 - k * 0.6; x.globalAlpha = 0.9; x.beginPath(); x.arc(cx, cy, rr, st, st + 3.6); x.stroke(); }
    x.globalAlpha = 1; x.fillStyle = b; x.beginPath(); x.arc(cx, cy, s * 0.12, 0, TAU); x.fill(); }
};
D['Wedding - Marble & Gold'] = x => {
  const n = noise2(251), n2 = noise2(252), base = hex('#f7f5f2'), vein = hex('#a9a39c'), gold = hex('#c9a14a');
  perPixel(x, (X, Y) => { const f = fbm(n, X / 520, Y / 520), t = Math.sin((X * 0.8 + Y * 0.55) * 0.0032 + f * 7);
    const f2 = fbm(n2, X / 300, Y / 300, 4), t2 = Math.sin((X * 0.3 - Y * 0.9) * 0.004 + f2 * 6);
    let c = base; const v = Math.max(0, 1 - Math.abs(t) / 0.09); if (v > 0) c = mix(c, vein, Math.pow(v, 1.6) * 0.55);
    const v2 = Math.max(0, 1 - Math.abs(t2) / 0.05); if (v2 > 0) c = mix(c, vein, v2 * 0.25);
    const g = Math.max(0, 1 - Math.abs(t2 - 0.6) / 0.02); if (g > 0) c = mix(c, gold, g * 0.85);
    const shade = 1 - 0.04 * fbm(n, X / 900 + 30, Y / 900, 3); return c.map(q => q * shade); });
  grain(x, 2);
};
D['Wedding - Rose Gold'] = x => {
  const g = x.createLinearGradient(0, 0, N, N); g.addColorStop(0, '#f6d5c8'); g.addColorStop(0.5, '#e7b29e'); g.addColorStop(1, '#f9e1d8'); x.fillStyle = g; x.fillRect(0, 0, N, N); grain(x, 4);
  x.strokeStyle = 'rgba(255,255,255,0.5)'; x.lineWidth = 3; const s = 300, h = s * 0.866;
  x.beginPath(); for (let y = -h; y < N + h; y += h){ x.moveTo(0, y); x.lineTo(N, y); }
  for (let k = -12; k < 24; k++){ x.moveTo(k * s, 0); x.lineTo(k * s + N / Math.tan(Math.PI / 3), N); x.moveTo(k * s, 0); x.lineTo(k * s - N / Math.tan(Math.PI / 3), N); } x.stroke();
  x.fillStyle = '#c98f74'; for (let y = 0, row = 0; y < N + h; y += h, row++) for (let X = (row % 2 ? s / 2 : 0); X < N + s; X += s){ x.beginPath(); x.arc(X, y, 7, 0, TAU); x.fill(); }
};
D['Wedding - Linen'] = x => {
  const r = rand(261), rows = Float32Array.from({length: N}, () => (r() - 0.5) * 10), cols = Float32Array.from({length: N}, () => (r() - 0.5) * 10), base = hex('#f1ebdf');
  perPixel(x, (X, Y) => { const v = rows[Y] + cols[X]; return [base[0] + v, base[1] + v, base[2] + v * 0.9]; }); grain(x, 4); softVignette(x, 0.06);
};

/* party */
D['Party - Art Deco Gold'] = x => {
  x.fillStyle = '#121214'; x.fillRect(0, 0, N, N); const g = x.createLinearGradient(0, 0, N, N); g.addColorStop(0, '#f3dc8a'); g.addColorStop(0.5, '#c9a14a'); g.addColorStop(1, '#f0d37c');
  x.strokeStyle = g; x.lineWidth = 5; const R = 160;
  for (let row = 0; row * R * 0.5 < N + R; row++) for (let col = -1; col * R < N + R; col++){ const cx = col * R + (row % 2 ? R / 2 : 0), cy = row * R * 0.5;
    x.fillStyle = '#121214'; x.beginPath(); x.arc(cx, cy, R / 2, Math.PI, 0); x.fill();
    for (const k of [0.5, 0.38, 0.26, 0.14]){ x.beginPath(); x.arc(cx, cy, R * k, Math.PI, 0); x.stroke(); }
    x.beginPath(); for (let a = 1; a < 6; a++){ const th = Math.PI + a * Math.PI / 6; x.moveTo(cx + Math.cos(th) * R * 0.14, cy + Math.sin(th) * R * 0.14); x.lineTo(cx + Math.cos(th) * R * 0.26, cy + Math.sin(th) * R * 0.26); } x.stroke(); }
};
D['Party - Rose Sequins'] = x => {
  x.fillStyle = '#8a4a52'; x.fillRect(0, 0, N, N);
  const r = rand(271), cols = [hex('#f2b8a2'), hex('#e8a0a8'), hex('#f5d0b5'), hex('#d98c93'), hex('#ffe3d3')], sp = 36;
  for (let row = 0; row * sp * 0.85 < N + sp; row++) for (let col = -1; col * sp < N + sp; col++){
    const cx = col * sp + (row % 2 ? sp / 2 : 0), cy = row * sp * 0.85, base = cols[Math.floor(r() * 5)], b = 0.75 + r() * 0.5;
    const c = base.map(v => Math.min(255, v * b)), g = x.createRadialGradient(cx - 6, cy - 8, 1, cx, cy, 23);
    g.addColorStop(0, `rgb(${Math.min(255, c[0] + 60)},${Math.min(255, c[1] + 60)},${Math.min(255, c[2] + 60)})`); g.addColorStop(0.5, `rgb(${c.join(',')})`); g.addColorStop(1, `rgb(${c.map(v => v * 0.65).join(',')})`);
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, 22, 0, TAU); x.fill(); x.fillStyle = 'rgba(80,30,40,0.35)'; x.beginPath(); x.arc(cx, cy, 3, 0, TAU); x.fill(); }
};
D['Party - Balloon Wall'] = x => {
  x.fillStyle = '#fff1ea'; x.fillRect(0, 0, N, N);
  const r = rand(281), cols = ['#f9c6d0', '#fde2a7', '#c8e7f5', '#d9c8f5', '#ffffff', '#f7b2bd', '#bfe6d6'];
  const pts2 = scatter(283, 1400, 115, -120).sort((a, b) => a[1] - b[1]);
  for (const [cx, cy] of pts2){ const s = 80 + r() * 60, c = cols[Math.floor(r() * cols.length)], g = x.createRadialGradient(cx - s * 0.35, cy - s * 0.4, s * 0.05, cx, cy, s * 1.05);
    g.addColorStop(0, '#ffffff'); g.addColorStop(0.25, c); g.addColorStop(1, `rgba(0,0,0,0.08)`);
    x.fillStyle = c; x.beginPath(); x.ellipse(cx, cy, s, s * 1.08, 0, 0, TAU); x.fill(); x.fillStyle = g; x.fill();
    x.fillStyle = 'rgba(255,255,255,0.7)'; x.beginPath(); x.ellipse(cx - s * 0.38, cy - s * 0.45, s * 0.14, s * 0.24, -0.6, 0, TAU); x.fill(); }
};
D['Party - Disco Fever'] = x => {
  const c = [N / 2, N / 2], n = 36;
  for (let i = 0; i < n; i++){ x.fillStyle = i % 2 ? '#ff7a1a' : '#ffa94d'; x.beginPath(); x.moveTo(...c); x.arc(c[0], c[1], N, i / n * TAU, (i + 1) / n * TAU); x.closePath(); x.fill(); }
  const g = x.createRadialGradient(c[0], c[1], 0, c[0], c[1], N * 0.7); g.addColorStop(0, 'rgba(255,230,150,0.75)'); g.addColorStop(0.4, 'rgba(255,200,120,0.2)'); g.addColorStop(1, 'rgba(120,30,0,0.35)'); x.fillStyle = g; x.fillRect(0, 0, N, N);
  const r = rand(291); x.fillStyle = '#ffffff'; for (let i = 0; i < 70; i++){ x.globalAlpha = 0.5 + r() * 0.5; sparkle4(x, r() * N, r() * N, 14 + r() * 40); x.fill(); } x.globalAlpha = 1; grain(x, 3);
};
D['Party - Neon Grid'] = x => {
  const hz = N * 0.6; vgrad(x, [[0, '#14002b'], [0.45, '#3b0a5c'], [0.6, '#ff2f8a'], [0.6001, '#12002a'], [1, '#12002a']]);
  const r = rand(301); for (let i = 0; i < 500; i++){ x.fillStyle = `rgba(255,255,255,${0.3 + r() * 0.7})`; x.beginPath(); x.arc(r() * N, r() * hz * 0.8, 1.5 + r() * 3, 0, TAU); x.fill(); }
  const [sc, sx] = canvas(); const sg = sx.createLinearGradient(0, hz - 600, 0, hz); sg.addColorStop(0, '#ffe066'); sg.addColorStop(1, '#ff3d8b');
  sx.fillStyle = sg; sx.beginPath(); sx.arc(N / 2, hz, 560, Math.PI, 0); sx.fill(); sx.globalCompositeOperation = 'destination-out';
  for (let k = 0; k < 7; k++){ const y = hz - 40 - k * 62, hgt = 26 - k * 3; if (hgt > 0) sx.fillRect(0, y, N, hgt); } x.drawImage(sc, 0, 0);
  x.strokeStyle = '#ff4fd8'; x.lineWidth = 5; x.shadowColor = '#ff4fd8'; x.shadowBlur = 24;
  x.beginPath(); for (let k = -24; k <= 24; k++){ x.moveTo(N / 2 + k * 30, hz); x.lineTo(N / 2 + k * 420, N); }
  for (let k = 1; k <= 14; k++){ const y = hz + (N - hz) * Math.pow(k / 14, 2); x.moveTo(0, y); x.lineTo(N, y); } x.stroke(); x.shadowBlur = 0;
  x.strokeStyle = '#3df5ff'; x.lineWidth = 4; x.beginPath(); x.moveTo(0, hz); x.lineTo(N, hz); x.stroke();
};
D['Party - Color Pop'] = x => {
  x.fillStyle = '#fffaf0'; x.fillRect(0, 0, N, N);
  const r = rand(311), C = ['#ff4f8b', '#ffd23f', '#2ec4b6', '#5b5bd6', '#111111', '#ff8a3d'];
  scatter(313, 200, 230).forEach(([cx, cy], i) => { const c = C[Math.floor(r() * C.length)], k = i % 6, s = 0.8 + r() * 0.6;
    x.save(); x.translate(cx, cy); x.rotate(r() * TAU); x.scale(s, s); x.fillStyle = c; x.strokeStyle = c; x.lineWidth = 16; x.lineCap = 'round'; x.lineJoin = 'round';
    if (k === 0){ x.beginPath(); x.moveTo(-60, 0); for (let t = -60; t <= 60; t += 10) x.lineTo(t, Math.sin(t / 12) * 18); x.stroke(); }
    else if (k === 1){ x.beginPath(); x.moveTo(0, -45); x.lineTo(42, 30); x.lineTo(-42, 30); x.closePath(); x.fill(); }
    else if (k === 2){ x.beginPath(); x.arc(0, 0, 34, 0, TAU); x.fill(); }
    else if (k === 3){ x.beginPath(); x.arc(0, 10, 44, Math.PI, 0); x.fill(); }
    else if (k === 4){ for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++){ x.beginPath(); x.arc(a * 26, b * 26, 7, 0, TAU); x.fill(); } }
    else { x.beginPath(); x.moveTo(-60, 10); for (let t = 0; t < 6; t++) x.lineTo(-60 + (t + 1) * 20, t % 2 ? 10 : -12); x.stroke(); }
    x.restore(); });
};

/* graduation */
function capShape(x, cx, cy, s, rot, fill){ x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s);
  x.fillStyle = fill; x.beginPath(); x.moveTo(-34, 6); x.lineTo(-34, 30); x.quadraticCurveTo(0, 46, 34, 30); x.lineTo(34, 6); x.closePath(); x.fill();
  x.beginPath(); x.moveTo(0, -30); x.lineTo(70, -4); x.lineTo(0, 22); x.lineTo(-70, -4); x.closePath(); x.fill();
  x.strokeStyle = fill; x.lineWidth = 4; x.beginPath(); x.moveTo(0, -4); x.lineTo(48, 6); x.lineTo(48, 40); x.stroke(); x.fillRect(43, 38, 10, 18); x.restore(); }
D['Graduation - Chalkboard'] = x => {
  x.fillStyle = '#26332e'; x.fillRect(0, 0, N, N);
  const r = rand(321); for (let i = 0; i < 90; i++){ const cx = r() * N, cy = r() * N, rad = 120 + r() * 380, g = x.createRadialGradient(cx, cy, 0, cx, cy, rad);
    g.addColorStop(0, 'rgba(255,255,255,0.05)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(cx - rad, cy - rad, rad * 2, rad * 2); }
  grain(x, 7);
  const words = ['Class of', 'A+', 'Congrats!', 'You did it!', '1 + 1 = 2', 'GRAD', 'x + y = z', 'Smart!', 'ABC', '100%', 'Yay!', 'E = mc2', 'Hooray!', 'Well done'];
  scatter(323, 55, 420).forEach(([cx, cy], i) => { x.save(); x.translate(cx, cy); x.rotate((r() - 0.5) * 0.5);
    x.globalAlpha = 0.82; x.strokeStyle = x.fillStyle = '#f4f1e8'; x.lineWidth = 6; x.lineCap = 'round'; x.lineJoin = 'round';
    const k = i % 4;
    if (k === 3){ x.beginPath(); x.moveTo(0, -38); x.lineTo(80, -8); x.lineTo(0, 22); x.lineTo(-80, -8); x.closePath(); x.moveTo(-40, 6); x.lineTo(-40, 40); x.quadraticCurveTo(0, 58, 40, 40); x.lineTo(40, 6); x.moveTo(0, -8); x.lineTo(56, 4); x.lineTo(56, 48); x.stroke(); }
    else if (k === 2){ star5(x, 0, 0, 48); x.stroke(); }
    else { x.font = `${60 + Math.floor(r() * 50)}px Chalkduster`; x.textAlign = 'center'; x.fillText(words[Math.floor(r() * words.length)], 0, 0); }
    x.restore(); });
};
D['Graduation - Navy & Gold'] = x => {
  const g = x.createRadialGradient(N / 2, N / 2, 0, N / 2, N / 2, N * 0.75); g.addColorStop(0, '#1d2f5c'); g.addColorStop(1, '#0c1630'); x.fillStyle = g; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(331), gold = ['#f2c14e', '#e0a93b', '#fff1c1', '#ffffff'];
  for (let i = 0; i < 500; i++){ const cx = r() * N, cy = r() * N; x.save(); x.translate(cx, cy); x.rotate(r() * TAU); x.fillStyle = gold[Math.floor(r() * 4)]; x.globalAlpha = 0.7 + r() * 0.3;
    i % 2 ? x.fillRect(-14, -5, 28, 10) : (star5(x, 0, 0, 12 + r() * 10), x.fill()); x.restore(); }
  x.globalAlpha = 1; for (const [cx, cy] of scatter(333, 40, 420, 100)) capShape(x, cx, cy, 1.2 + r() * 0.8, (r() - 0.5) * 1.2, '#e8b74a');
};

/* seasonal */
D['Christmas - Tartan'] = x => {
  x.fillStyle = '#a61e2a'; x.fillRect(0, 0, N, N);
  const band = (pos, w, col, a) => { x.globalAlpha = a; x.fillStyle = col; for (let o = 0; o < N; o += 600){ x.fillRect(o + pos, 0, w, N); x.fillRect(0, o + pos, N, w); } };
  band(0, 230, '#173f2a', 0.55); band(330, 60, '#173f2a', 0.55); band(270, 26, '#0d0d0d', 0.35); band(440, 14, '#f2d16b', 0.8); band(520, 8, '#ffffff', 0.6);
  x.globalAlpha = 0.06; x.strokeStyle = '#000'; x.lineWidth = 2; x.beginPath(); for (let k = -N; k < N; k += 7){ x.moveTo(k, 0); x.lineTo(k + N, N); } x.stroke(); x.globalAlpha = 1; grain(x, 4);
};
D['Christmas - Snowfall'] = x => {
  vgrad(x, [[0, '#0b2545'], [1, '#1f4f7a']]); grain(x, 3);
  const r = rand(341);
  for (let i = 0; i < 2600; i++){ x.fillStyle = `rgba(255,255,255,${0.35 + r() * 0.65})`; x.beginPath(); x.arc(r() * N, r() * N, 2 + Math.pow(r(), 3) * 9, 0, TAU); x.fill(); }
  for (let i = 0; i < 60; i++){ const cx = r() * N, cy = r() * N, rad = 25 + r() * 45, g = x.createRadialGradient(cx, cy, 0, cx, cy, rad); g.addColorStop(0, 'rgba(255,255,255,0.5)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.fill(); }
  x.strokeStyle = 'rgba(255,255,255,0.9)'; x.lineCap = 'round';
  for (const [cx, cy] of scatter(343, 55, 340)){ const s = 26 + r() * 40; x.lineWidth = Math.max(3, s * 0.1); x.save(); x.translate(cx, cy); x.rotate(r());
    for (let k = 0; k < 6; k++){ x.rotate(TAU / 6); x.beginPath(); x.moveTo(0, 0); x.lineTo(0, -s); x.moveTo(0, -s * 0.55); x.lineTo(-s * 0.22, -s * 0.78); x.moveTo(0, -s * 0.55); x.lineTo(s * 0.22, -s * 0.78); x.stroke(); } x.restore(); }
};
D['Halloween - Spooky Night'] = x => {
  vgrad(x, [[0, '#1b0b2e'], [0.6, '#4a1f73'], [1, '#c2551f']]); grain(x, 3);
  const r = rand(351); for (let i = 0; i < 500; i++){ x.fillStyle = `rgba(255,255,255,${0.3 + r() * 0.6})`; x.beginPath(); x.arc(r() * N, r() * N * 0.7, 1.5 + r() * 3, 0, TAU); x.fill(); }
  const mx = N * 0.62, my = N * 0.24, gl = x.createRadialGradient(mx, my, 200, mx, my, 700); gl.addColorStop(0, 'rgba(255,236,170,0.45)'); gl.addColorStop(1, 'rgba(255,236,170,0)'); x.fillStyle = gl; x.fillRect(0, 0, N, N);
  x.fillStyle = '#ffe9a8'; x.beginPath(); x.arc(mx, my, 260, 0, TAU); x.fill(); x.fillStyle = 'rgba(200,170,90,0.3)'; for (const [a, b, c] of [[-80, -40, 50], [60, 70, 36], [30, -110, 26]]){ x.beginPath(); x.arc(mx + a, my + b, c, 0, TAU); x.fill(); }
  const bat = (cx, cy, s, rot) => { x.save(); x.translate(cx, cy); x.rotate(rot); x.scale(s, s); x.fillStyle = '#120818'; x.beginPath(); x.moveTo(0, -6);
    for (const d of [-1, 1]){ x.moveTo(0, -6); x.quadraticCurveTo(d * 30, -34, d * 74, -22); x.quadraticCurveTo(d * 62, -6, d * 64, 10); x.quadraticCurveTo(d * 50, 0, d * 42, 12); x.quadraticCurveTo(d * 30, 2, d * 20, 16); x.quadraticCurveTo(d * 10, 6, 0, 18); }
    x.fill(); x.beginPath(); x.ellipse(0, 4, 12, 18, 0, 0, TAU); x.fill(); x.beginPath(); x.moveTo(-9, -10); x.lineTo(-6, -24); x.lineTo(-1, -12); x.moveTo(9, -10); x.lineTo(6, -24); x.lineTo(1, -12); x.fill(); x.restore(); };
  for (const [cx, cy] of scatter(353, 45, 300)) bat(cx, cy, 0.8 + r() * 1.4, (r() - 0.5) * 0.6);
  x.fillStyle = '#120818'; x.beginPath(); x.moveTo(0, N); for (let X = 0; X <= N; X += 20) x.lineTo(X, N - 220 - Math.sin(X / 380) * 90 - Math.sin(X / 140) * 25); x.lineTo(N, N); x.fill();
};
D['Valentine - Hearts'] = x => {
  x.fillStyle = '#ffd6e0'; x.fillRect(0, 0, N, N); grain(x, 2);
  const r = rand(361), C = ['#ff4f7b', '#ffffff', '#ff8fab', '#e63962'];
  for (let row = 0; row * 170 < N + 170; row++) for (let col = -1; col * 200 < N + 200; col++){ const cx = col * 200 + (row % 2 ? 100 : 0), cy = row * 170;
    x.save(); x.translate(cx, cy); x.rotate((r() - 0.5) * 0.6); heart(x, 0, 0, 34 + r() * 16); x.fillStyle = C[(row + col + 8) % 4]; x.fill(); x.restore(); }
};
D['Spring - Cherry Blossom'] = x => {
  vgrad(x, [[0, '#e6f2ff'], [1, '#fff0f5']]); grain(x, 2);
  const r = rand(371), pinks = ['#ffc2d1', '#ffb3c6', '#ffe5ec', '#fda4ba'];
  const branch = (x0, y0, ang, len, w, d) => { const x1 = x0 + Math.cos(ang) * len, y1 = y0 + Math.sin(ang) * len;
    x.strokeStyle = '#5c3b2e'; x.lineWidth = w; x.lineCap = 'round'; x.beginPath(); x.moveTo(x0, y0); x.quadraticCurveTo((x0 + x1) / 2 + (r() - 0.5) * len * 0.3, (y0 + y1) / 2 + (r() - 0.5) * len * 0.3, x1, y1); x.stroke();
    for (let k = 0; k < 4 + d; k++){ const t = r(); blossom(x, x0 + (x1 - x0) * t + (r() - 0.5) * 70, y0 + (y1 - y0) * t + (r() - 0.5) * 70, 22 + r() * 16, r() * TAU, pinks[Math.floor(r() * 4)]); }
    if (d > 0){ branch(x1, y1, ang + 0.35 + r() * 0.35, len * 0.72, w * 0.68, d - 1); branch(x1, y1, ang - 0.35 - r() * 0.35, len * 0.72, w * 0.68, d - 1); }
    else for (let k = 0; k < 5; k++) blossom(x, x1 + (r() - 0.5) * 90, y1 + (r() - 0.5) * 90, 24 + r() * 14, r() * TAU, pinks[Math.floor(r() * 4)]); };
  branch(-60, 260, 0.2, 520, 44, 2); branch(N + 60, 620, Math.PI - 0.2, 520, 44, 2); branch(-60, N - 560, -0.1, 480, 40, 2); branch(N + 60, N - 220, Math.PI + 0.2, 480, 40, 2);
  branch(-60, N / 2 + 120, 0.1, 380, 34, 1); branch(N + 60, N / 2 - 300, Math.PI, 380, 34, 1);
  for (let i = 0; i < 220; i++){ x.save(); x.translate(r() * N, r() * N); x.rotate(r() * TAU); x.fillStyle = pinks[Math.floor(r() * 4)]; x.globalAlpha = 0.85; x.beginPath(); x.ellipse(0, 0, 14, 9, 0, 0, TAU); x.fill(); x.restore(); }
};
D['Summer - Tropical Leaves'] = x => {
  x.fillStyle = '#d8f3dc'; x.fillRect(0, 0, N, N);
  const r = rand(381), greens = ['#2d6a4f', '#40916c', '#52b788', '#1b4332', '#74c69d'];
  const frond = (cx, cy, ang, len, col) => { x.save(); x.translate(cx, cy); x.rotate(ang); x.strokeStyle = col; x.fillStyle = col; x.lineWidth = 10; x.lineCap = 'round';
    x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(len * 0.5, -len * 0.12, len, 0); x.stroke();
    for (let i = 1; i < 16; i++){ const t = i / 16, px = len * t, py = -len * 0.12 * 4 * t * (1 - t) * 0.5, l = (0.25 + 0.5 * Math.sin(Math.PI * t)) * len * 0.42;
      for (const s of [-1, 1]){ x.save(); x.translate(px, py); x.rotate(s * (0.9 - t * 0.3)); x.beginPath(); x.ellipse(l / 2, 0, l / 2, l * 0.09 + 6, 0, 0, TAU); x.fill(); x.restore(); } }
    x.restore(); };
  const leaf = (cx, cy, ang, len, col) => { x.save(); x.translate(cx, cy); x.rotate(ang); x.fillStyle = col; x.beginPath(); x.ellipse(len / 2, 0, len / 2, len * 0.28, 0, 0, TAU); x.fill();
    x.strokeStyle = 'rgba(255,255,255,0.35)'; x.lineWidth = 6; x.beginPath(); x.moveTo(0, 0); x.lineTo(len, 0); for (let k = 1; k < 6; k++){ const t = k / 6 * len; x.moveTo(t, 0); x.lineTo(t + 50, -len * 0.18); x.moveTo(t, 0); x.lineTo(t + 50, len * 0.18); } x.stroke(); x.restore(); };
  for (const [cx, cy] of scatter(383, 130, 260, -200)){ const c = greens[Math.floor(r() * 5)]; r() < 0.55 ? frond(cx, cy, r() * TAU, 420 + r() * 300, c) : leaf(cx, cy, r() * TAU, 300 + r() * 250, c); }
};
D['Autumn - Falling Leaves'] = x => {
  x.fillStyle = '#fdf0d5'; x.fillRect(0, 0, N, N); grain(x, 3);
  const r = rand(391), C = ['#c1121f', '#e85d04', '#faa307', '#9c6644', '#dc2f02'];
  for (const [cx, cy] of scatter(393, 170, 210)){ const s = 50 + r() * 50, c = C[Math.floor(r() * 5)];
    x.save(); x.translate(cx, cy); x.rotate(r() * TAU); x.fillStyle = c; x.beginPath();
    const half = [[0, -1], [0.12, -0.7], [0.3, -0.78], [0.26, -0.45], [0.62, -0.62], [0.54, -0.38], [0.9, -0.32], [0.64, -0.1], [0.74, 0.04], [0.36, 0.12], [0.42, 0.34], [0.06, 0.22], [0, 0.3]];
    const outline = [...half, ...half.slice(1, -1).reverse().map(([a, b]) => [-a, b])];   // maple leaf: right half, then mirrored
    outline.forEach(([a, b], i) => i ? x.lineTo(a * s, b * s) : x.moveTo(a * s, b * s)); x.closePath(); x.fill();
    x.strokeStyle = 'rgba(255,255,255,0.4)'; x.lineWidth = 3; x.beginPath(); for (const [a, b] of [[0, -1], [1, -0.2], [-1, -0.2], [0.45, 0.5], [-0.45, 0.5]]){ x.moveTo(0, 0.2 * s); x.lineTo(a * s * 0.8, b * s * 0.8); } x.stroke();
    x.strokeStyle = c; x.lineWidth = 5; x.beginPath(); x.moveTo(0, 0.3 * s); x.lineTo(0, 0.75 * s); x.stroke(); x.restore(); }
};
D['Baby - Pastel Clouds'] = x => {
  vgrad(x, [[0, '#cfe8ff'], [1, '#fde2f3']]); grain(x, 2);
  const r = rand(401);
  for (const [cx, cy] of scatter(403, 70, 330)){ const s = 0.6 + r() * 0.9; x.save(); x.translate(cx, cy); x.scale(s, s);
    x.fillStyle = 'rgba(160,180,220,0.25)'; for (const [a, b, c] of [[-70, 18, 50], [0, 0, 70], [70, 18, 50], [-30, 30, 50], [30, 30, 50]]){ x.beginPath(); x.arc(a + 6, b + 10, c, 0, TAU); x.fill(); }
    x.fillStyle = '#ffffff'; for (const [a, b, c] of [[-70, 18, 50], [0, 0, 70], [70, 18, 50], [-30, 30, 50], [30, 30, 50]]){ x.beginPath(); x.arc(a, b, c, 0, TAU); x.fill(); } x.restore(); }
  for (let i = 0; i < 90; i++){ x.fillStyle = i % 2 ? '#fff3b0' : '#ffffff'; star5(x, r() * N, r() * N, 14 + r() * 18, undefined, r()); x.fill(); }
  for (let i = 0; i < 300; i++){ x.fillStyle = 'rgba(255,255,255,0.8)'; x.beginPath(); x.arc(r() * N, r() * N, 3 + r() * 4, 0, TAU); x.fill(); }
};

/* minimal (soft colour with film grain, the Korean photo-studio look) */
for (const [name, col] of [['Cream', '#f2ede4'], ['Charcoal', '#2b2b2e'], ['Sage', '#c9d5c5'], ['Butter', '#f6e8a6'], ['Powder Blue', '#cfe0f0'], ['Blush', '#f3d3d3']])
  D['Minimal - ' + name] = x => { x.fillStyle = col; x.fillRect(0, 0, N, N); grain(x, 9, 7); softVignette(x, 0.08); };

/* newspaper (laundry front page): columns of small article text, headlines, rules and halftone photos */
for (const [file, fam] of [['Times New Roman.ttf', 'Times New Roman'], ['Times New Roman Bold.ttf', 'Times New Roman'], ['Times New Roman Italic.ttf', 'Times New Roman']])
  try { napi.GlobalFonts.registerFromPath('/System/Library/Fonts/Supplemental/' + file, fam); } catch {}
const STORIES = [
  ['LOCAL SOCK GOES MISSING', 'A single blue sock was reported missing on Tuesday after a routine wash at the corner laundromat. Its partner, found folded and alone, declined to comment. Staff searched every drum and lint trap but found no trace. Anyone with information is asked to look behind the dryer.'],
  ['BUBBLES HIT RECORD HIGH', 'Bubble levels across the city reached a record high this week after a new detergent arrived in shops. Residents reported foam in hallways, on staircases and in one very surprised lift. Experts recommend half a cap per load and an open window.'],
  ['FRIENDS CAUGHT IN SPIN CYCLE', 'A group of friends who climbed into a giant washing machine for a photo were caught in the spin cycle on Saturday. All are safe, a little dizzy and remarkably fresh. Witnesses say the group came out smiling and smelling of spring linen.'],
  ['DETERGENT PRICES FALL', 'Shoppers cheered as detergent prices fell for the third month in a row. Store owners say lavender and fresh cotton remain the favourite scents, while sales of the unscented kind stay steady.'],
  ['MYSTERY OF THE ODD SOCK', 'Scientists still cannot explain why socks vanish in the wash. A new study suggests most of them are simply hiding inside duvet covers, waiting quietly for the next laundry day.'],
  ['TOWN CELEBRATES CLEAN WEEK', 'The town held its yearly clean week with music, bubbles and a parade of washing baskets. The mayor ironed the ribbon before cutting it, to loud applause from the crowd.'],
  ['LINT FOUND IN DRYER AGAIN', 'In news that surprised nobody, lint was once again found in the dryer this morning. Officials remind everyone to empty the filter after every load, for safety and for softer towels.'],
  ['FRESH LINEN SEASON OPENS', 'Fresh linen season opened with clear skies and a gentle breeze, perfect for drying sheets on the line. Forecasters expect sunshine all weekend and very few clouds.'],
  ['SOFTENER SHORTAGE ENDS', 'Towels across the region are soft again now that the fabric softener shortage has ended. Delivery lorries arrived overnight and a queue formed outside the shop before dawn.'],
  ['WEATHER: PERFECT WASHDAY', 'Sunny with light clouds and a warm breeze, making it a perfect day for hanging out the washing. Chance of bubbles: high. Chance of a lost sock: very high.'],
];
function newsprint(x, seed, ink){
  const r = rand(seed), cols = 6, M = 70, gut = 46, cw = (N - 2 * M - gut * (cols - 1)) / cols;
  let story = Math.floor(r() * STORIES.length), body = [], newStory = true;
  x.fillStyle = ink; x.strokeStyle = ink;
  for (let c = 0; c < cols; c++){
    const X = M + c * (cw + gut); let y = M;
    if (c){ x.globalAlpha = 0.5; x.lineWidth = 2; x.beginPath(); x.moveTo(X - gut / 2, M); x.lineTo(X - gut / 2, N - M); x.stroke(); }
    while (y < N - M - 60){
      x.globalAlpha = 0.9;
      if (newStory){   // headline, sometimes a halftone photo, then the story
        const [head, text] = STORIES[story % STORIES.length]; story++; newStory = false;
        const fs = 46 + Math.floor(r() * 16); x.font = `bold ${fs}px "Times New Roman"`; let line = '';
        for (const w of head.split(' ')){ const t = line ? line + ' ' + w : w; if (x.measureText(t).width > cw && line){ y += fs; x.fillText(line, X, y); line = w; } else line = t; }
        y += fs; x.fillText(line, X, y); y += 18;
        if (r() < 0.35 && y < N - M - 520){
          const ph = 260 + r() * 200; x.globalAlpha = 0.85;
          x.save(); x.beginPath(); x.rect(X, y, cw, ph); x.clip(); x.fillStyle = '#d9d5cc'; x.fillRect(X, y, cw, ph); x.fillStyle = ink;
          const bx = X + r() * cw, by = y + r() * ph;
          for (let yy = y; yy < y + ph; yy += 9) for (let xx = X; xx < X + cw; xx += 9){
            const t = 0.5 + 0.5 * Math.sin((xx - bx) / 60) * Math.cos((yy - by) / 50); x.beginPath(); x.arc(xx, yy, 0.6 + 3.8 * t, 0, TAU); x.fill(); }
          x.restore(); x.fillStyle = ink; y += ph + 12; x.font = 'italic 20px "Times New Roman"'; x.fillText('Photo: The Daily Wash', X, y + 16); y += 34;
        }
        body = text.split(' ');
      }
      x.font = '22px "Times New Roman"';   // the story's text, wrapped to the column
      while (body.length && y < N - M - 30){ let t = ''; while (body.length){ const tt = t ? t + ' ' + body[0] : body[0]; if (x.measureText(tt).width > cw && t) break; t = tt; body.shift(); }
        y += 27; x.fillText(t, X, y); }
      if (!body.length){ y += 16; x.globalAlpha = 0.6; x.lineWidth = 2; x.beginPath(); x.moveTo(X, y); x.lineTo(X + cw, y); x.stroke(); y += 22; newStory = true; }
    }
  }
  x.globalAlpha = 1;
}
D['Newspaper - Newsprint'] = x => { x.fillStyle = '#f1eee6'; x.fillRect(0, 0, N, N); grain(x, 6, 11); newsprint(x, 501, '#262626'); grain(x, 3, 12); };
D['Newspaper - Aged'] = x => {
  x.fillStyle = '#eadcb6'; x.fillRect(0, 0, N, N); grain(x, 7, 13); newsprint(x, 502, '#3b2f22');
  const r = rand(503);
  for (let i = 0; i < 5; i++){ const cx = r() * N, cy = r() * N, rad = 110 + r() * 160;   // coffee rings
    x.strokeStyle = 'rgba(120,80,30,0.18)'; x.lineWidth = 10 + r() * 10; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.stroke();
    x.fillStyle = 'rgba(150,100,40,0.06)'; x.beginPath(); x.arc(cx, cy, rad, 0, TAU); x.fill(); }
  x.strokeStyle = 'rgba(255,255,255,0.35)'; x.lineWidth = 6; x.beginPath(); x.moveTo(N / 2, 0); x.lineTo(N / 2 + 20, N); x.moveTo(0, N / 2); x.lineTo(N, N / 2 - 15); x.stroke();   // folds
  x.strokeStyle = 'rgba(80,50,20,0.12)'; x.lineWidth = 3; x.beginPath(); x.moveTo(N / 2 + 4, 0); x.lineTo(N / 2 + 24, N); x.moveTo(0, N / 2 + 4); x.lineTo(N, N / 2 - 11); x.stroke();
  const g = x.createRadialGradient(N / 2, N / 2, N * 0.35, N / 2, N / 2, N * 0.75); g.addColorStop(0, 'rgba(120,80,30,0)'); g.addColorStop(1, 'rgba(120,80,30,0.35)'); x.fillStyle = g; x.fillRect(0, 0, N, N);
  grain(x, 4, 14);
};

/* ---------- train (top-view photobooth): gravel under the track, station tiles, tickets, a rail map ---------- */
D['Train - Ballast'] = x => {   // railway gravel seen from above
  x.fillStyle = '#6f6a65'; x.fillRect(0, 0, N, N); grain(x, 10, 31);
  const r = rand(32), tones = ['#9a958f', '#8a847d', '#a8a29b', '#7d7873', '#b3aea6', '#8f8578', '#a49a8c', '#6e6863'];
  for (let i = 0; i < 26000; i++){
    const cx = r() * N, cy = r() * N, a = 10 + r() * 20, b = a * (0.55 + r() * 0.4), rot = r() * Math.PI;
    x.fillStyle = 'rgba(30,26,22,0.45)'; x.beginPath(); x.ellipse(cx + 4, cy + 5, a, b, rot, 0, TAU); x.fill();
    x.fillStyle = tones[Math.floor(r() * tones.length)]; x.beginPath(); x.ellipse(cx, cy, a, b, rot, 0, TAU); x.fill();
    x.fillStyle = 'rgba(255,255,255,0.16)'; x.beginPath(); x.ellipse(cx - a * 0.25, cy - b * 0.3, a * 0.45, b * 0.35, rot, 0, TAU); x.fill();
  }
  grain(x, 6, 33);
};
D['Train - Metro Tiles'] = x => {   // white bevelled station tiles with a coloured band
  x.fillStyle = '#d9dcdc'; x.fillRect(0, 0, N, N);
  const tw = 240, th = 120, r = rand(41);
  for (let row = 0; row * th < N; row++) for (let col = -1; col * tw < N; col++){
    const X = col * tw + (row % 2 ? tw / 2 : 0) + 4, Y = row * th + 4, band = row >= 11 && row <= 13;
    const base = band ? (row === 12 ? '#1f7a5a' : '#f2c14e') : '#f6f6f2';
    const g = x.createLinearGradient(X, Y, X, Y + th - 8); g.addColorStop(0, 'rgba(255,255,255,0.55)'); g.addColorStop(0.5, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(0,0,0,0.12)');
    rrect(x, X, Y, tw - 8, th - 8, 14); x.fillStyle = base; x.fill(); x.fillStyle = g; x.fill();
    x.fillStyle = `rgba(0,0,0,${r() * 0.04})`; x.fill();
  }
  grain(x, 3, 42);
};
function ticket(x, cx, cy, w, h, rot, col, ink, r){
  x.save(); x.translate(cx, cy); x.rotate(rot);
  const shape = (dx, dy, fill) => {   // the ticket with a round notch in each end
    x.save(); x.translate(dx, dy); x.beginPath(); x.roundRect(-w / 2, -h / 2, w, h, 10); x.clip();
    x.beginPath(); x.roundRect(-w / 2, -h / 2, w, h, 10); for (const sx of [-w / 2, w / 2]){ x.moveTo(sx + h * 0.13, 0); x.arc(sx, 0, h * 0.13, 0, TAU); }
    x.fillStyle = fill; x.fill('evenodd'); x.restore(); };
  shape(8, 10, 'rgba(0,0,0,0.18)'); shape(0, 0, col);
  x.strokeStyle = ink; x.globalAlpha = 0.55; x.lineWidth = 3; x.setLineDash([10, 9]); x.beginPath(); x.moveTo(w * 0.22, -h / 2 + 10); x.lineTo(w * 0.22, h / 2 - 10); x.stroke(); x.setLineDash([]);
  x.strokeRect(-w / 2 + 14, -h / 2 + 14, w * 0.72 - 14, h - 28); x.globalAlpha = 1;
  x.fillStyle = ink; x.textAlign = 'center'; x.textBaseline = 'middle';
  const words = [['ADMIT ONE', 'PHOTO EXPRESS'], ['RETURN', 'CLASS 1'], ['SINGLE', 'ALL STATIONS'], ['BOARDING', 'PLATFORM 1']][Math.floor(r() * 4)];
  x.font = `900 ${h * 0.22}px "Arial Black", Arial`; x.fillText(words[0], -w * 0.14, -h * 0.13);
  x.font = `700 ${h * 0.13}px "Courier New", monospace`; x.fillText(words[1], -w * 0.14, h * 0.17);
  x.save(); x.translate(w * 0.36, 0); x.rotate(-Math.PI / 2); x.font = `700 ${h * 0.14}px "Courier New", monospace`; x.fillStyle = '#b3202c';
  x.fillText('Nº ' + String(Math.floor(r() * 9000) + 1000), 0, 0); x.restore();
  x.restore();
}
D['Train - Tickets'] = x => {
  vgrad(x, [[0, '#f3e6c8'], [1, '#e9d6ad']]); grain(x, 5, 51);
  const r = rand(52), cols = ['#f4d58d', '#f7b7a3', '#a9d6e5', '#cde5b0', '#f2e8cf', '#e9c46a'];
  for (const [cx, cy] of scatter(53, 52, 400)) ticket(x, cx, cy, 480, 220, (r() - 0.5) * 0.9, cols[Math.floor(r() * cols.length)], '#3b2f2a', r);
  softVignette(x, 0.16); grain(x, 3, 54);
};
D['Train - Rail Map'] = x => {   // a colourful metro map: straight and 45° lines with stations
  x.fillStyle = '#f7f5ef'; x.fillRect(0, 0, N, N);
  x.strokeStyle = 'rgba(0,0,0,0.05)'; x.lineWidth = 2; x.beginPath(); for (let i = 0; i <= N; i += 150){ x.moveTo(i, 0); x.lineTo(i, N); x.moveTo(0, i); x.lineTo(N, i); } x.stroke();
  const r = rand(61), cols = ['#e63946', '#2a9d8f', '#f4a261', '#457b9d', '#9b5de5', '#f15bb5', '#43aa8b', '#ffbe0b'], step = 150, stops = [];
  for (let L = 0; L < 15; L++){
    let X = Math.round(r() * 20) * step, Y = Math.round(r() * 20) * step, dir = Math.floor(r() * 8); const pts = [[X, Y]];
    for (let k = 0; k < 14; k++){ if (r() < 0.35) dir = (dir + (r() < 0.5 ? 1 : 7)) % 8;
      const a = dir * Math.PI / 4, n = 1 + Math.floor(r() * 3); X += Math.round(Math.cos(a)) * step * n; Y += Math.round(Math.sin(a)) * step * n; pts.push([X, Y]); }
    x.strokeStyle = cols[L % cols.length]; x.lineWidth = 34; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); pts.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.stroke();
    pts.forEach((p, i) => { if (i % 2 === 0) stops.push(p); });
  }
  for (const [a, b] of stops){ x.fillStyle = '#ffffff'; x.strokeStyle = '#1d1d1f'; x.lineWidth = 9; x.beginPath(); x.arc(a, b, 26, 0, TAU); x.fill(); x.stroke(); }
  grain(x, 2, 62);
};

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  for (const [name, draw] of Object.entries(D)){
    if (ONLY && !name.includes(ONLY)) continue;
    const [c, x] = canvas(); draw(x);
    fs.writeFileSync(path.join(OUT, name + '.jpg'), await c.encode('jpeg', 92));
    console.log('made', name);
  }
})();
