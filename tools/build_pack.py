"""Packt pack/ zu citybuild-pack.zip (immer gleiche Reihenfolge und Zeitstempel), berechnet SHA-1 und zeigt die Zeilen für server.properties.

Aufruf: python3 tools/build_pack.py [https://deine-url/citybuild-pack.zip]
"""
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"
OUT = ROOT / "citybuild-pack.zip"

files = sorted(p for p in PACK.rglob("*") if p.is_file())
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        info = zipfile.ZipInfo(str(p.relative_to(PACK)).replace("\\", "/"), date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, p.read_bytes())

sha1 = hashlib.sha1(OUT.read_bytes()).hexdigest()
url = sys.argv[1] if len(sys.argv) > 1 else "https://DEINE-URL/citybuild-pack.zip"
print(f"Geschrieben: {OUT} ({OUT.stat().st_size} Bytes, {len(files)} Dateien)")
print("\nIn server.properties eintragen (Server danach neu starten):")
print(f"resource-pack={url}")
print(f"resource-pack-sha1={sha1}")
print("require-resource-pack=false")
print("resource-pack-prompt=CityBuild Resourcepack")
