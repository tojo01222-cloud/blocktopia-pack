"""Erzeugt die 16x16-Texturen des Resourcepacks. Eigene Pixelbilder, keine fremden Dateien.

Aufruf: python3 tools/make_textures.py   (aus dem Ordner resourcepack)
Eigene Bilder: Einfach die PNG-Dateien in pack/assets/citybuild/textures/item/ ersetzen (16x16 oder 32x32).
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "pack/assets/citybuild/textures/item"
OUT.mkdir(parents=True, exist_ok=True)

T = (0, 0, 0, 0)


def img(rows, palette):
    im = Image.new("RGBA", (16, 16), T)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), palette[ch])
    return im


KEY = [
    "................",
    "....oooo........",
    "...oLLLLo.......",
    "..oLooooLo......",
    "..oLo..oLo......",
    "..oLo..oLo......",
    "..oLooooLo......",
    "...oLLLLo.......",
    "....oLLo........",
    ".....oLo........",
    ".....oLo........",
    ".....oLLoo......",
    ".....oLo........",
    ".....oLLoo......",
    ".....oLo........",
    ".....ooo........",
]


def key(name, light, dark, gem):
    pal = {"o": dark, "L": light}
    im = img(KEY, pal)
    # Edelstein im Griff
    for xy in [(5, 4), (6, 4), (5, 5), (6, 5)]:
        im.putpixel(xy, gem)
    im.save(OUT / f"{name}.png")


key("vote_key", (90, 200, 255, 255), (20, 70, 120, 255), (255, 255, 255, 255))
key("rare_key", (200, 120, 255, 255), (80, 30, 120, 255), (255, 230, 120, 255))
key("legend_key", (255, 200, 60, 255), (130, 80, 10, 255), (255, 70, 70, 255))

COIN = [
    "................",
    "................",
    "....oooooooo....",
    "...oYYYYYYYYo...",
    "..oYYhhhhhhYYo..",
    "..oYhYYYYYYhYo..",
    "..oYhYoYYoYhYo..",
    "..oYhYYoooYYhYo.",
    "..oYhYYoYYYYhYo.",
    "..oYhYYoYYYhYo..",
    "..oYhhhhhhhhYo..",
    "...oYYYYYYYYo...",
    "....oooooooo....",
    "................",
    "................",
    "................",
]
coin = img(COIN, {"o": (150, 100, 10, 255), "Y": (255, 205, 50, 255), "h": (255, 235, 130, 255)})
coin.save(OUT / "coin.png")

# Pack-Symbol (64x64)
logo = Image.new("RGBA", (64, 64), (30, 30, 40, 255))
for y in range(64):
    for x in range(64):
        t = (x + y) / 126
        logo.putpixel((x, y), (int(255 * (0.7 + 0.3 * t)), int(179 + 25 * t), int(71 - 20 * t), 255))
border = (40, 30, 10, 255)
for i in range(64):
    for w in range(3):
        for xy in [(i, w), (i, 63 - w), (w, i), (63 - w, i)]:
            logo.putpixel(xy, border)
# "C" aus Pixeln
for y in range(16, 48):
    for x in range(18, 46):
        dx, dy = x - 32, y - 32
        r2 = dx * dx + dy * dy
        if 100 <= r2 <= 256 and not (dx > 4 and abs(dy) < 8):
            logo.putpixel((x, y), (255, 255, 255, 255))
logo.save(OUT.parent.parent.parent.parent / "pack.png")
print("Texturen geschrieben nach", OUT)
