"""Extract framed destination scenes from hero-dssd.png for the journey UX."""
from pathlib import Path

from PIL import Image

HERO = Path(r"c:\Users\Franco\DSSD\frontend\public\hero-dssd.png")
OUT = Path(r"c:\Users\Franco\DSSD\frontend\public\scenes")
W, H = 1774, 887
TARGET = (1200, 675)  # 16:9

# (left, top, right, bottom) — tuned to original composition
SCENES = {
    "municipio": (40, 40, 620, 520),
    "centro": (420, 160, 1180, 740),
    "ong": (1080, 20, 1750, 520),
    "rescate": (0, 360, 620, 887),
    "ambulancia": (1020, 420, 1774, 887),
}


def framed_crop(src: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    crop = src.crop(box)
    # Fit into 16:9 canvas with soft letterbox from surrounding pixels
    tw, th = TARGET
    canvas = Image.new("RGB", TARGET, (7, 31, 27))
    crop = crop.convert("RGB")
    crop.thumbnail(TARGET, Image.Resampling.LANCZOS)
    x = (tw - crop.size[0]) // 2
    y = (th - crop.size[1]) // 2
    canvas.paste(crop, (x, y))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    src = Image.open(HERO).convert("RGBA")
    assert src.size == (W, H), src.size
    for name, box in SCENES.items():
        out = framed_crop(src, box)
        path = OUT / f"{name}.jpg"
        out.save(path, "JPEG", quality=90, optimize=True)
        print("wrote", path.name, out.size)
    print("done")


if __name__ == "__main__":
    main()
