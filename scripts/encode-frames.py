"""Convert a folder of Blender PNG frames (RGBA) into web-ready WebP frames for the scroll showcase.

Run:  python -I scripts/encode-frames.py "C:/path/to/frames" [quality]
Writes assets/frames/ring/0000.webp ... and assets/frames/ring/manifest.json (frame count + size).
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/frames/ring"
EDGE_FADE = 0.22          # fraction of frame width over which shadow fades to 0 at the edges
ALPHA_FLOOR = 16          # of 255 (the shadow-catcher floor leaves ~3-5%)


def main():
    src = Path(sys.argv[1])
    quality = int(sys.argv[2]) if len(sys.argv) > 2 else 84
    files = sorted(src.glob("*.png"))
    if not files:
        sys.exit(f"No PNG frames in {src}")
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.webp"):
        old.unlink()
    total = 0
    size = None
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGBA")
        # The shadow-catcher floor leaves ~1-3% alpha across the whole frame, which shows as a faint box on a white
        # page. Subtract that baseline so only the real contact shadow and the piece remain.
        px = np.asarray(im).copy()
        a = px[..., 3].astype(np.float32)
        a = np.clip((a - ALPHA_FLOOR) / (255 - ALPHA_FLOOR), 0, 1)
        # The soft floor shadow must also die out before the frame edge or it shows as a box. Only semi-transparent
        # pixels (shadow) are faded; the opaque piece is untouched, even where it touches the edge.
        h, w = a.shape
        yy, xx = np.mgrid[0:h, 0:w]
        edge = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / (EDGE_FADE * w)
        edge = np.clip(edge, 0, 1); edge = edge * edge * (3 - 2 * edge)
        solid = np.clip((a - 0.55) / 0.35, 0, 1); solid = solid * solid * (3 - 2 * solid)
        a = a * (edge + (1 - edge) * solid)
        px[..., 3] = (a * 255).astype(np.uint8)
        im = Image.fromarray(px, "RGBA")
        size = im.size
        dest = OUT / f"{i:04d}.webp"
        im.save(dest, "WEBP", quality=quality, alpha_quality=88, method=6)
        total += dest.stat().st_size
    (OUT / "manifest.json").write_text(json.dumps({"count": len(files), "width": size[0], "height": size[1]}))
    print(f"{len(files)} frames, {size[0]}x{size[1]}, {total / 1e6:.1f} MB total, avg {total / len(files) / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
