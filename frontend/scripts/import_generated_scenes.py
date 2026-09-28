"""Convert generated cinematic scenes into frontend/public/scenes."""
from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\Franco\.cursor\projects\c-Users-Franco-DSSD\assets")
OUT = Path(r"c:\Users\Franco\DSSD\frontend\public\scenes")
TARGET = (1400, 788)  # ~16:9

MAP = {
    "scene-municipio.png": "municipio.jpg",
    "scene-centro.png": "centro.jpg",
    "scene-ong.png": "ong.jpg",
    "scene-rescate.png": "rescate.jpg",
    "scene-ambulancia.png": "ambulancia.jpg",
}

OUT.mkdir(parents=True, exist_ok=True)

for src_name, out_name in MAP.items():
    im = Image.open(SRC / src_name).convert("RGB")
    # cover-fit into target
    tw, th = TARGET
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    im = im.crop((left, top, left + tw, top + th))
    out = OUT / out_name
    im.save(out, "JPEG", quality=92, optimize=True)
    print("wrote", out.name, im.size)

print("done")
