"""Prüft das Resourcepack: gültiges JSON, alle Texturen und Modelle vorhanden, PNG-Größen, pack.mcmeta.

Aufruf: python3 tools/validate_pack.py   Beendet mit Fehlercode 1, wenn etwas nicht stimmt.
"""
import json
import sys
from pathlib import Path

from PIL import Image

PACK = Path(__file__).resolve().parent.parent / "pack"
errors = []


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"{path.relative_to(PACK)}: kein gültiges JSON ({e})")
        return None


def resolve(ref, kind, ext):
    ns, _, name = ref.partition(":") if ":" in ref else ("minecraft", "", ref)
    return PACK / "assets" / ns / kind / f"{name}.{ext}"


meta = load(PACK / "pack.mcmeta")
if meta:
    p = meta.get("pack", {})
    if not isinstance(p.get("min_format"), int) or not isinstance(p.get("max_format"), int):
        errors.append("pack.mcmeta: min_format und max_format müssen Zahlen sein")
    elif p["min_format"] > p["max_format"]:
        errors.append("pack.mcmeta: min_format ist größer als max_format")
    if not p.get("description"):
        errors.append("pack.mcmeta: description fehlt")

logo = PACK / "pack.png"
if not logo.exists():
    errors.append("pack.png fehlt")

for item in sorted((PACK / "assets").glob("*/items/*.json")):
    data = load(item)
    if not data:
        continue
    model = data.get("model", {})
    if model.get("type") == "minecraft:model":
        target = resolve(model.get("model", ""), "models", "json")
        if not target.exists():
            errors.append(f"{item.relative_to(PACK)}: Modell {model.get('model')} fehlt")

for model in sorted((PACK / "assets").glob("*/models/**/*.json")):
    data = load(model)
    if not data:
        continue
    for layer, ref in (data.get("textures") or {}).items():
        if ref.startswith("#"):
            continue
        target = resolve(ref, "textures", "png")
        if not target.exists():
            errors.append(f"{model.relative_to(PACK)}: Textur {ref} fehlt")

for png in sorted(PACK.rglob("*.png")):
    with Image.open(png) as im:
        w, h = im.size
        if png.parent.name == "item" and (w != h or w % 16 != 0):
            errors.append(f"{png.relative_to(PACK)}: Größe {w}x{h} (quadratisch, Vielfaches von 16 nötig)")

if errors:
    print("FEHLER:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("Resourcepack in Ordnung:", len(list((PACK / 'assets').glob('*/items/*.json'))), "Item-Modelle")
