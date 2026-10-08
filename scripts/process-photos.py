"""Re-frame product photos for the catalog: tight 3:4 crop around the piece, consistent margins and a
consistent neutral backdrop. Originals are kept untouched in assets/img/source/.

Run:  python -I scripts/process-photos.py
Gold is never recolored beyond a white-balance gain that maps the studio backdrop to one neutral tone.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/img/source"
OUT = ROOT / "assets/img/products"

BACKDROP = np.array([233, 235, 238], dtype=np.float32)  # shared neutral studio tone
FILL = 0.62          # how much of the crop width/height the piece should fill
MIN_CROP = 0.40      # never crop tighter than this fraction of the source width (keeps low-res shots sane)
MAX_OUT_W = 900


def border_color(a: np.ndarray) -> np.ndarray:
    h, w, _ = a.shape
    t = max(4, int(min(h, w) * 0.03))
    ring = np.concatenate([a[:t].reshape(-1, 3), a[-t:].reshape(-1, 3), a[:, :t].reshape(-1, 3), a[:, -t:].reshape(-1, 3)])
    return np.median(ring, axis=0)


def subject_box(a: np.ndarray):
    """Bounding box of gold-coloured pixels (red well above blue; the backdrop is neutral)."""
    mask = (a[..., 0] - a[..., 2]) > 45
    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        h, w, _ = a.shape
        return 0, 0, w, h
    x0, x1 = np.percentile(xs, [0.3, 99.7])
    y0, y1 = np.percentile(ys, [0.3, 99.7])
    return x0, y0, x1, y1


def process(path: Path):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img, dtype=np.float32)
    h, w, _ = a.shape

    a = np.clip(a * (BACKDROP / border_color(a)), 0, 255)   # white-balance backdrop to the shared tone
    x0, y0, x1, y1 = subject_box(a)
    sw, sh = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    crop_w = max(sw / FILL, (sh / FILL) * 0.75, MIN_CROP * w)
    crop_w = min(crop_w, w, h * 0.75)
    crop_h = crop_w * 4 / 3
    left = min(max(cx - crop_w / 2, 0), w - crop_w)
    top = min(max(cy - crop_h / 2, 0), h - crop_h)

    out = Image.fromarray(a.astype(np.uint8)).crop((round(left), round(top), round(left + crop_w), round(top + crop_h)))
    out_w = int(min(MAX_OUT_W, crop_w * 1.5))
    out = out.resize((out_w, out_w * 4 // 3), Image.LANCZOS)
    out.save(OUT / path.name, quality=88, optimize=True, progressive=True)
    print(f"{path.name:36s} src {w}x{h}  subject {sw:.0f}x{sh:.0f}  crop {crop_w:.0f}  -> {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    for p in sorted(SRC.glob("*.jpg")):
        process(p)
