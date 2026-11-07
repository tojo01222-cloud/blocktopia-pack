#!/usr/bin/env python3
"""Erzeugt die drei Pflicht-Resourcepacks von Blocktopia.

  1. blocktopia-items   Item-Icons (Münzen, Scheine, Boosts, Bücher, Pässe, Zauberstäbe ...) für CbItems
  2. blocktopia-gui     Schrift-Symbole (Seltenheiten, Münze, Herz, Stern, Krone ...) für Chat, Tab und Menüs
  3. blocktopia-sounds  eigene Töne (Kisten, Mythisch, Menü, BedWars)

Alles ist von diesem Skript selbst gezeichnet bzw. erzeugt, keine fremden Dateien.
Aufruf (aus dem Ordner resourcepack):  python3 tools/make_packs.py [BASIS-URL]
Ergebnis: dist/*.zip, dist/packs.txt (URL + SHA-1 für cb-worlds/config.yml) und
          ../cb-items/src/main/resources/custom-models.txt
"""
import hashlib
import json
import math
import random
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
DIST = ROOT / "dist"
WORK = ROOT / "build"
BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://DEINE-URL"

RARITY = {  # (Hauptfarbe, Dunkel, Hell)
    "COMMON": ((176, 184, 196), (80, 88, 100), (232, 236, 242)),
    "RARE": ((64, 160, 255), (20, 60, 140), (170, 220, 255)),
    "EPIC": ((176, 96, 255), (70, 30, 130), (225, 180, 255)),
    "LEGENDARY": ((255, 176, 40), (140, 80, 10), (255, 232, 140)),
    "MYTHIC": ((255, 70, 150), (120, 20, 80), (255, 190, 225)),
}
S = 128  # Zeichengröße, wird auf 32 verkleinert


def canvas():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def glow(im, color, radius=7, strength=1.0):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    alpha = im.split()[3].filter(ImageFilter.GaussianBlur(radius))
    alpha = alpha.point(lambda v: int(min(255, v * strength)))
    tint = Image.new("RGBA", im.size, color + (0,))
    tint.putalpha(alpha)
    layer.alpha_composite(tint)
    layer.alpha_composite(im)
    return layer


def poly(d, pts, fill, outline):
    d.polygon(pts, fill=fill, outline=outline)


def circle(d, cx, cy, r, fill, outline, width=4):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)


def star_pts(cx, cy, r1, r2, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def shape_coin(d, c, dk, lt):
    circle(d, 64, 64, 46, c, dk, 6)
    circle(d, 64, 64, 34, None, lt, 4)
    poly(d, star_pts(64, 64, 20, 9), lt, dk)


def shape_money(d, c, dk, lt):
    d.rounded_rectangle([12, 34, 116, 94], 8, fill=c, outline=dk, width=6)
    circle(d, 64, 64, 18, lt, dk, 4)
    d.rectangle([22, 44, 34, 52], fill=lt)
    d.rectangle([94, 76, 106, 84], fill=lt)


def shape_bank(d, c, dk, lt):
    for i, y in enumerate((78, 54, 30)):
        d.rounded_rectangle([20 + i * 4, y, 108 - i * 4, y + 22], 5, fill=c, outline=dk, width=5)
        d.line([30 + i * 4, y + 6, 70, y + 6], fill=lt, width=3)


def shape_clock(d, c, dk, lt):
    circle(d, 64, 64, 46, c, dk, 6)
    circle(d, 64, 64, 36, lt, dk, 3)
    d.line([64, 64, 64, 38], fill=dk, width=6)
    d.line([64, 64, 84, 74], fill=dk, width=6)
    circle(d, 64, 64, 5, dk, dk)


def shape_pass(d, c, dk, lt):
    d.rounded_rectangle([10, 32, 118, 96], 10, fill=c, outline=dk, width=6)
    d.line([40, 38, 40, 90], fill=dk, width=3)
    for y in range(40, 90, 10):
        d.ellipse([37, y, 43, y + 5], fill=lt)
    poly(d, star_pts(78, 64, 22, 10), lt, dk)


def shape_tome(d, c, dk, lt):
    d.rounded_rectangle([24, 14, 106, 112], 8, fill=c, outline=dk, width=6)
    d.rectangle([24, 14, 38, 112], fill=dk)
    d.rectangle([46, 30, 94, 82], outline=lt, width=4)
    poly(d, star_pts(70, 56, 16, 7), lt, dk)
    d.rectangle([46, 92, 94, 98], fill=lt)


def shape_voucher(d, c, dk, lt):
    circle(d, 40, 64, 24, c, dk, 6)
    circle(d, 40, 64, 10, None, dk, 5)
    d.rectangle([62, 59, 112, 70], fill=c, outline=dk, width=4)
    d.rectangle([92, 70, 100, 86], fill=c, outline=dk, width=4)
    d.rectangle([104, 70, 112, 82], fill=c, outline=dk, width=4)


def shape_xp(d, c, dk, lt):
    d.rectangle([54, 16, 74, 38], fill=lt, outline=dk, width=4)
    d.ellipse([22, 34, 106, 112], fill=(120, 230, 90), outline=dk, width=6)
    d.ellipse([38, 50, 60, 72], fill=(220, 255, 200))
    circle(d, 80, 90, 7, lt, dk, 3)


def shape_potion(d, c, dk, lt):
    d.rectangle([54, 14, 74, 40], fill=lt, outline=dk, width=4)
    d.polygon([(54, 40), (74, 40), (108, 100), (20, 100)], fill=c, outline=dk)
    d.line([(54, 40), (20, 100), (108, 100), (74, 40)], fill=dk, width=6)
    d.ellipse([46, 66, 62, 82], fill=lt)


def shape_orb(d, c, dk, lt):
    circle(d, 64, 64, 44, c, dk, 6)
    d.ellipse([40, 38, 64, 60], fill=lt)
    d.arc([22, 22, 106, 106], 200, 340, fill=lt, width=4)


def shape_cube(d, c, dk, lt):
    top = [(64, 18), (112, 42), (64, 66), (16, 42)]
    left = [(16, 42), (64, 66), (64, 116), (16, 92)]
    right = [(112, 42), (64, 66), (64, 116), (112, 92)]
    poly(d, top, lt, dk)
    poly(d, left, c, dk)
    poly(d, right, dk, dk)
    d.line(top + [top[0]], fill=dk, width=4)


def shape_anvil(d, c, dk, lt):
    d.polygon([(12, 30), (116, 30), (100, 58), (76, 62), (76, 84), (96, 96), (96, 108), (32, 108), (32, 96), (52, 84), (52, 62), (28, 58)], fill=c, outline=dk)
    d.line([(12, 30), (116, 30)], fill=lt, width=6)
    d.line([(32, 108), (96, 108)], fill=dk, width=6)


def shape_sparkle(d, c, dk, lt):
    poly(d, star_pts(64, 64, 50, 12, 4, -math.pi / 2), c, dk)
    poly(d, star_pts(94, 34, 18, 5, 4, -math.pi / 2), lt, dk)
    poly(d, star_pts(32, 96, 14, 4, 4, -math.pi / 2), lt, dk)


def shape_tag(d, c, dk, lt):
    d.polygon([(14, 40), (90, 40), (116, 64), (90, 88), (14, 88)], fill=c, outline=dk)
    d.line([(14, 40), (90, 40), (116, 64), (90, 88), (14, 88), (14, 40)], fill=dk, width=6)
    circle(d, 36, 64, 7, lt, dk, 3)
    d.line([54, 64, 90, 64], fill=lt, width=5)


def shape_drop(d, c, dk, lt):
    d.polygon([(64, 12), (100, 70), (96, 92), (64, 114), (32, 92), (28, 70)], fill=c, outline=dk)
    d.line([(64, 12), (100, 70), (96, 92), (64, 114), (32, 92), (28, 70), (64, 12)], fill=dk, width=6)
    d.ellipse([44, 66, 58, 82], fill=lt)


def shape_egg(d, c, dk, lt):
    d.ellipse([28, 14, 100, 116], fill=c, outline=dk, width=6)
    d.polygon([(34, 66), (48, 52), (62, 70), (78, 50), (94, 66), (90, 72), (78, 62), (62, 82), (48, 64), (38, 74)], fill=lt)


def shape_wand(d, c, dk, lt):
    d.line([22, 108, 84, 46], fill=dk, width=16)
    d.line([22, 108, 84, 46], fill=(120, 80, 40), width=8)
    poly(d, star_pts(92, 36, 28, 12), c, dk)
    circle(d, 92, 36, 7, lt, dk, 2)


def shape_badge(d, c, dk, lt):
    poly(d, star_pts(64, 64, 52, 24, 6), c, dk)
    circle(d, 64, 64, 18, lt, dk, 4)


def shape_feather(d, c, dk, lt):
    d.polygon([(24, 110), (40, 60), (70, 24), (110, 14), (100, 56), (68, 92), (36, 106)], fill=c, outline=dk)
    d.line([(24, 110), (100, 30)], fill=lt, width=5)
    d.line([(24, 110), (100, 30)], fill=dk, width=1)


def shape_book(d, c, dk, lt):
    shape_tome(d, c, dk, lt)
    d.line([30, 100, 98, 24], fill=(60, 40, 20), width=7)


def shape_eye(d, c, dk, lt):
    d.polygon([(10, 64), (64, 28), (118, 64), (64, 100)], fill=lt, outline=dk)
    circle(d, 64, 64, 22, c, dk, 5)
    circle(d, 64, 64, 9, dk, dk)


SHAPES = {
    "coins": shape_coin, "money": shape_money, "bank": shape_bank, "boost": shape_clock, "pass": shape_pass,
    "tome": shape_tome, "voucher": shape_voucher, "xp": shape_xp, "potion": shape_potion, "teleport": shape_eye,
    "pocket": shape_cube, "repair": shape_anvil, "trail": shape_sparkle, "title": shape_tag, "chatcolor": shape_drop,
    "companion": shape_egg,
}
SPECIAL = {  # Special-Items ohne Vanilla-Aussehen: id -> (Form, Seltenheit)
    "mod_scepter": (shape_wand, "RARE"), "watcher_compass": (shape_eye, "RARE"), "guardian_badge": (shape_badge, "RARE"),
    "architect_staff": (shape_wand, "EPIC"), "eraser_staff": (shape_wand, "EPIC"), "healing_rod": (shape_wand, "EPIC"),
    "blink_rod": (shape_wand, "EPIC"), "sky_feather": (shape_feather, "LEGENDARY"), "item_forge": (shape_book, "LEGENDARY"),
    "crate_orb": (shape_orb, "MYTHIC"),
}


def render_icon(shape, rarity, seed):
    c, dk, lt = RARITY[rarity]
    rnd = random.Random(seed)
    # kleine Farbabweichung pro Item, damit nicht alle Icons einer Seltenheit gleich aussehen
    shift = rnd.randint(-18, 18)
    c = tuple(max(0, min(255, v + shift)) for v in c)
    im = canvas()
    d = ImageDraw.Draw(im)
    shape(d, c, dk, lt)
    if rarity in ("EPIC", "LEGENDARY", "MYTHIC"):
        im = glow(im, c, 6, 0.9 if rarity == "EPIC" else 1.3)
    return im.resize((32, 32), Image.LANCZOS)


def write_zip(path, files, meta):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        entries = dict(files)
        entries["pack.mcmeta"] = json.dumps(meta, indent=2, ensure_ascii=False).encode()
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, entries[name])
    return hashlib.sha1(path.read_bytes()).hexdigest()


def png_bytes(im):
    import io
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def mcmeta(desc):
    return {"pack": {"description": desc, "min_format": 75, "max_format": 99}}


# ---------------------------------------------------------------- Pack 1: Items
def build_items():
    data = yaml.safe_load((REPO / "cb-items/src/main/resources/items.yml").read_text(encoding="utf-8"))["items"]
    files, ids = {}, []

    def add(model_id, im):
        files[f"assets/blocktopia/textures/item/{model_id}.png"] = png_bytes(im)
        files[f"assets/blocktopia/models/item/{model_id}.json"] = json.dumps(
            {"parent": "minecraft:item/generated", "textures": {"layer0": f"blocktopia:item/{model_id}"}}).encode()
        files[f"assets/blocktopia/items/{model_id}.json"] = json.dumps(
            {"model": {"type": "minecraft:model", "model": f"blocktopia:item/{model_id}"}}).encode()
        ids.append(model_id)

    for item_id, v in data.items():
        use = (v.get("use") or {}).get("type")
        if use in SHAPES:
            add(item_id, render_icon(SHAPES[use], v.get("rarity", "COMMON"), item_id))
    for item_id, (shape, rarity) in SPECIAL.items():
        add("special_" + item_id, render_icon(shape, rarity, item_id))
    # Schlüssel/Münze aus dem alten Pack bleiben unter citybuild: erhalten (CbRewards)
    old = REPO / "resourcepack/pack"
    for p in old.rglob("*"):
        if p.is_file() and p.name != "pack.mcmeta" and p.name != "pack.png":
            files[str(p.relative_to(old)).replace("\\", "/")] = p.read_bytes()
    sha = write_zip(DIST / "blocktopia-items.zip", files, mcmeta("§6Blocktopia §7Items"))
    (REPO / "cb-items/src/main/resources/custom-models.txt").write_text(
        "# Wird von resourcepack/tools/make_packs.py erzeugt: Items, die das Pack mit eigenem Modell mitbringt.\n"
        + "\n".join(sorted(ids)) + "\n", encoding="utf-8")
    return sha, len(ids)


# ---------------------------------------------------------------- Pack 2: GUI-Symbole
GLYPHS = [  # (Zeichen, Name, Zeichenfunktion)
    ("", "common", lambda d: circle(d, 64, 64, 40, (176, 184, 196), (80, 88, 100), 6)),
    ("", "rare", lambda d: circle(d, 64, 64, 40, (64, 160, 255), (20, 60, 140), 6)),
    ("", "epic", lambda d: circle(d, 64, 64, 40, (176, 96, 255), (70, 30, 130), 6)),
    ("", "legendary", lambda d: circle(d, 64, 64, 40, (255, 176, 40), (140, 80, 10), 6)),
    ("", "mythic", lambda d: circle(d, 64, 64, 40, (255, 70, 150), (120, 20, 80), 6)),
    ("", "coin", lambda d: shape_coin(d, (255, 200, 60), (140, 90, 10), (255, 240, 160))),
    ("", "star", lambda d: poly(d, star_pts(64, 64, 54, 24), (255, 210, 70), (140, 90, 10))),
    ("", "heart", lambda d: d.polygon([(64, 112), (14, 58), (22, 30), (46, 20), (64, 38), (82, 20), (106, 30), (114, 58)], fill=(255, 70, 90), outline=(130, 20, 40))),
    ("", "crown", lambda d: d.polygon([(12, 96), (12, 40), (40, 66), (64, 28), (88, 66), (116, 40), (116, 96)], fill=(255, 200, 60), outline=(140, 90, 10))),
    ("", "sword", lambda d: (d.line([20, 108, 100, 28], fill=(210, 220, 235), width=14), d.line([34, 84, 60, 110], fill=(140, 90, 10), width=10))),
    ("", "bed", lambda d: (d.rectangle([12, 56, 116, 96], fill=(230, 60, 60), outline=(100, 20, 20), width=5), d.rectangle([12, 44, 40, 70], fill=(240, 240, 240)))),
    ("", "bolt", lambda d: d.polygon([(74, 8), (28, 70), (58, 70), (46, 120), (100, 52), (68, 52)], fill=(255, 230, 60), outline=(140, 100, 10))),
    ("", "check", lambda d: d.line([(22, 66), (50, 94), (106, 32)], fill=(90, 230, 120), width=16)),
    ("", "cross", lambda d: (d.line([28, 28, 100, 100], fill=(255, 90, 90), width=16), d.line([100, 28, 28, 100], fill=(255, 90, 90), width=16))),
    ("", "arrow", lambda d: d.polygon([(14, 50), (70, 50), (70, 22), (116, 64), (70, 106), (70, 78), (14, 78)], fill=(255, 190, 60), outline=(140, 90, 10))),
    ("", "gem", lambda d: d.polygon([(34, 20), (94, 20), (116, 52), (64, 112), (12, 52)], fill=(90, 220, 255), outline=(20, 90, 140))),
]


def build_gui():
    files, providers = {}, []
    for ch, name, fn in GLYPHS:
        im = canvas()
        d = ImageDraw.Draw(im)
        fn(d)
        files[f"assets/blocktopia/textures/font/{name}.png"] = png_bytes(im.resize((16, 16), Image.LANCZOS))
        providers.append({"type": "bitmap", "file": f"blocktopia:font/{name}.png", "ascent": 12, "height": 9, "chars": [ch]})
    files["assets/minecraft/font/default.json"] = json.dumps({"providers": providers}, indent=2).encode()
    # Hinweis-Datei, damit die Zeichen leicht zu finden sind
    files["assets/blocktopia/GLYPHS.txt"] = ("\n".join(f"U+{ord(c):04X}  {n}" for c, n, _ in GLYPHS)).encode()
    sha = write_zip(DIST / "blocktopia-gui.zip", files, mcmeta("§6Blocktopia §7Symbole"))
    return sha, len(GLYPHS)


# ---------------------------------------------------------------- Pack 3: Töne
def synth(path, expr, duration, extra=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d={duration}",
           "-af", f"volume=0.6{extra}", "-ac", "1", "-c:a", "libvorbis", "-q:a", "4", str(path)]
    subprocess.run(cmd, check=True)


SOUNDS = {  # Name -> (Ausdruck, Dauer, Filter)
    "ui.click": ("0.6*sin(2*PI*1400*t)*exp(-t*40)", 0.12, ""),
    "ui.confirm": ("0.5*sin(2*PI*(660+440*floor(t*8)/2)*t)*exp(-t*3)", 0.5, ""),
    "crate.tick": ("0.5*sin(2*PI*900*t)*exp(-t*55)", 0.1, ""),
    "crate.reveal": ("0.4*(sin(2*PI*523*t)+sin(2*PI*659*t)+sin(2*PI*784*t))*exp(-t*2.2)", 1.4, ""),
    "crate.epic": ("0.35*(sin(2*PI*440*t)+sin(2*PI*554*t)+sin(2*PI*659*t)+sin(2*PI*880*t))*exp(-t*1.6)", 1.8, ""),
    "crate.mythic": ("0.3*(sin(2*PI*(220+400*t)*t)+sin(2*PI*880*t)+sin(2*PI*1320*t))*exp(-t*0.9)", 3.2, ",aecho=0.8:0.7:90:0.5"),
    "game.bed_break": ("0.7*sin(2*PI*(300-180*t)*t)*exp(-t*2.5)+0.2*sin(2*PI*90*t)*exp(-t*3)", 1.2, ""),
    "game.win": ("0.4*(sin(2*PI*392*t)+sin(2*PI*523*t)+sin(2*PI*659*t)+sin(2*PI*784*t))*exp(-t*1.2)", 2.4, ",aecho=0.8:0.6:120:0.4"),
}


def build_sounds():
    files, events = {}, {}
    tmp = WORK / "sounds"
    for name, (expr, dur, extra) in SOUNDS.items():
        out = tmp / (name.replace(".", "_") + ".ogg")
        synth(out, expr, dur, extra)
        files[f"assets/blocktopia/sounds/{name.replace('.', '/')}.ogg"] = out.read_bytes()
        events[name] = {"sounds": [f"blocktopia:{name.replace('.', '/')}"]}
    files["assets/blocktopia/sounds.json"] = json.dumps(events, indent=2).encode()
    sha = write_zip(DIST / "blocktopia-sounds.zip", files, mcmeta("§6Blocktopia §7Töne"))
    return sha, len(SOUNDS)


def main():
    DIST.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    results = [("items", *build_items()), ("gui", *build_gui()), ("sounds", *build_sounds())]
    lines = ["# In plugins/CbWorlds/config.yml unter resourcepack.packs eintragen (url + sha1 pro Pack):", ""]
    for name, sha, count in results:
        print(f"blocktopia-{name}.zip  {count} Einträge  SHA-1 {sha}")
        lines += [f"{name}:", f"  url: \"{BASE_URL}/blocktopia-{name}.zip\"", f"  sha1: \"{sha}\"", ""]
    (DIST / "packs.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nGeschrieben: {DIST}/packs.txt")


if __name__ == "__main__":
    main()
