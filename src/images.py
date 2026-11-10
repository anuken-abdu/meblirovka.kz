# -*- coding: utf-8 -*-
"""Фото из assets/orig/ → assets/img/<имя>-480/800/1200.webp без EXIF и GPS.
Запуск локально: python3 src/images.py  (нужен Pillow). Результат коммитится."""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets/orig", ROOT / "assets/img"
SIZES = (480, 800, 1200)

def main():
    if not SRC.exists():
        print("Нет папки assets/orig — фото пока не добавлены."); return
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".heic"): continue
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")   # поворот по EXIF, затем EXIF выбрасывается
        clean = Image.new("RGB", im.size); clean.paste(im)           # копия без метаданных
        for w in SIZES:
            if clean.width < w and w != SIZES[0]: continue
            h = round(clean.height * w / clean.width)
            clean.resize((w, h), Image.LANCZOS).save(OUT / f"{f.stem}-{w}.webp", "WEBP", quality=78, method=6)
        print(f"{f.name}: {clean.width}×{clean.height} → webp {SIZES}")

if __name__ == "__main__":
    main()
