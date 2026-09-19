"""Generate synthetic dental radiograph images with authored ground-truth regions.

100% synthetic — no real patients. Each image visibly labels a tooth region so a
vision model can perform LOCATE + RELEVANCE (never diagnosis), and its ground-truth
region is recorded in imaging_study.region_label for the fail-safe validation gate.

Run: python db/make_images.py   -> writes db/assets/imaging/IMG-*.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "assets" / "imaging"

# id -> (title region label baked into image, ground-truth region)
IMAGES = {
    "IMG-001": "Lower right — tooth #30 region",
    "IMG-002": "Upper right — tooth #3 region",
    "IMG-003": "Lower left — tooth #19 region (low detail)",
    "IMG-004": "Upper front — tooth #8 region",
    "IMG-005": "Lower right — tooth #30 region",
}

W, H = 900, 460


def _font(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw(path: Path, label: str, low_detail: bool = False):
    img = Image.new("L", (W, H), 18)  # dark radiograph background
    d = ImageDraw.Draw(img)
    # jaw arch of tooth-like blocks
    cx, cy = W // 2, H - 90
    import math
    n = 16
    for i in range(n):
        ang = math.pi * (i + 0.5) / n
        x = cx - int(360 * math.cos(ang))
        y = cy - int(150 * math.sin(ang))
        shade = 70 if low_detail else 150
        d.rounded_rectangle([x - 16, y - 26, x + 16, y + 26], radius=6, fill=shade, outline=210)
    # region marker box (upper area) — the "locate" target
    if not low_detail:
        d.rectangle([W - 320, 40, W - 40, 120], outline=230, width=2)
    d.text((30, 24), "SYNTHETIC DATA — PROTOTYPE", fill=200, font=_font(22))
    d.text((30, H - 34), label, fill=225, font=_font(20))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main():
    for iid, label in IMAGES.items():
        draw(OUT / f"{iid}.png", label, low_detail=(iid == "IMG-003"))
        print(f"wrote {OUT / (iid + '.png')}")


if __name__ == "__main__":
    main()
