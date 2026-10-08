// Scroll-driven image-sequence showcase (the Apple technique): pre-rendered frames are drawn onto a canvas
// according to scroll progress. Frames come from scripts/blender/ring_scene.py (placeholder ring) or, later,
// real turntable photos run through scripts/encode-frames.py. Nothing else in the page cares which.
const BASE = "assets/frames/ring/";

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const smooth = (a, b, v) => { const t = clamp01((v - a) / (b - a)); return t * t * (3 - 2 * t); };

// Mirrors the camera choreography baked into the Blender render: 0 → far, 1 → close on the stone.
export const pushAt = (p) => smooth(0.26, 0.5, p) - smooth(0.62, 0.86, p);

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

export async function initHero({ canvas, stage, onProgress }) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ctx = canvas.getContext("2d");
  if (!ctx) return false;

  let manifest;
  try { manifest = await (await fetch(BASE + "manifest.json")).json(); } catch { return false; }
  const count = manifest.count;
  const frames = new Array(count).fill(null);
  const name = (i) => `${BASE}${String(i).padStart(4, "0")}.webp`;

  try { frames[0] = await loadImage(name(0)); } catch { return false; }

  // Coarse-to-fine loading so scrubbing works almost immediately: every 8th frame, then 4th, 2nd, rest.
  (async () => {
    for (const step of [8, 4, 2, 1]) {
      for (let i = 0; i < count; i += step) {
        if (!frames[i]) { try { frames[i] = await loadImage(name(i)); } catch { /* leave gap; nearest frame is used */ } }
      }
    }
  })();

  function nearestLoaded(i) {
    for (let d = 0; d < count; d++) {
      if (frames[i - d]) return frames[i - d];
      if (frames[i + d]) return frames[i + d];
    }
    return frames[0];
  }

  let dpr = 1, w = 0, h = 0;
  function resize() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
  }
  new ResizeObserver(() => { resize(); lastDrawn = -1; }).observe(canvas);
  resize();

  let lastDrawn = -1;
  function draw(index) {
    const img = nearestLoaded(index);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const portrait = w / h < 1;
    const side = portrait ? w * 1.55 : h * 1.05;       // square frame, ring centred inside it
    const cy = portrait ? h * 0.40 : h * 0.5;          // lift the ring above the caption on phones
    ctx.drawImage(img, (w - side) / 2 * dpr, (cy - side / 2) * dpr, side * dpr, side * dpr);
    lastDrawn = index;
  }

  let target = 0, current = 0, visible = true;
  const forced = new URLSearchParams(location.search).get("p");   // QA hook: ?p=0.4 freezes the showcase
  function readScroll() {
    if (forced !== null) { target = clamp01(+forced); return; }
    const r = stage.getBoundingClientRect();
    target = clamp01(-r.top / (stage.offsetHeight - innerHeight));
  }
  addEventListener("scroll", readScroll, { passive: true });
  readScroll();
  if (forced !== null) current = target;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }, { threshold: 0 }).observe(stage);

  function frame() {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) return;
    current += (target - current) * (reduced || forced !== null ? 1 : 0.1);
    const p = reduced ? 0.84 : current;
    const index = Math.round(p * (count - 1));
    if (index !== lastDrawn) draw(index);
    onProgress?.(p, pushAt(p));
  }
  draw(Math.round((reduced ? 0.84 : current) * (count - 1)));
  frame();
  return true;
}
