"""Generate PWA icons into public/icons/. Run: python scripts/generate_pwa_icons.py"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("pip install pillow") from None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "icons"
OUT.mkdir(parents=True, exist_ok=True)


def make_icon(size: int, path: Path) -> None:
    img = Image.new("RGBA", (size, size), "#0a1628")
    d = ImageDraw.Draw(img)
    margin = size // 6
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=max(8, size // 8),
        fill="#143550",
        outline="#56c9ff",
        width=max(2, size // 64),
    )
    cx, cy = size // 2, size // 2
    r = size // 5
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill="#56c9ff")
    img.save(path, "PNG")
    print("wrote", path)


for s in (32, 180, 192, 512):
    make_icon(s, OUT / f"icon-{s}.png")
make_icon(180, OUT / "apple-touch-icon.png")
make_icon(32, OUT / "favicon-32.png")
