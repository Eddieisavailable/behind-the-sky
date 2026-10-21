"""Draw the placeholder app icons (gray-box: a sun behind a dark tree line).

Run from the repo root:  python3 tools/make-icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "public" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

NIGHT = (18, 26, 20)
SKY = (38, 54, 40)
SUN = (232, 116, 42)
RATTAN = (196, 154, 98)


def draw(size: int, safe: float) -> Image.Image:
    """safe = fraction of the canvas the artwork may use (maskable icons need ~0.8)."""
    img = Image.new("RGB", (size, size), NIGHT)
    d = ImageDraw.Draw(img)
    pad = size * (1 - safe) / 2
    s = size * safe
    # sky band
    d.rectangle([0, 0, size, pad + s * 0.72], fill=SKY)
    # the sun, half hidden behind the tree line
    r = s * 0.26
    cx, cy = size / 2, pad + s * 0.6
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN)
    # tree line: a row of triangles
    base = pad + s * 0.74
    n = 7
    w = size / n
    for i in range(n + 1):
        x = i * w - w / 2
        h = s * (0.28 if i % 2 else 0.2)
        d.polygon([(x, base), (x + w / 2, base - h), (x + w, base)], fill=NIGHT)
    d.rectangle([0, base, size, size], fill=NIGHT)
    # a rattan cutlass across the foreground
    d.line([(pad + s * 0.22, pad + s * 0.9), (pad + s * 0.78, pad + s * 0.8)], fill=RATTAN, width=max(2, int(size * 0.035)))
    return img


for size, name, safe in [
    (192, "icon-192.png", 0.92),
    (512, "icon-512.png", 0.92),
    (512, "maskable-512.png", 0.72),
    (180, "apple-touch-icon.png", 0.92),
]:
    draw(size, safe).save(OUT / name, optimize=True)
    print("wrote", OUT / name)
