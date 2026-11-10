# -*- coding: utf-8 -*-
"""Фото из assets/orig/ → assets/img/<имя>-<ширина>.webp без EXIF и GPS.
Запуск локально: python3 src/images.py  (нужен Pillow). Результат коммитится.
Имена: hero-desktop, hero-mobile (фон главной), mat-* (материалы),
mebel-na-zakaz / novostroyka / pod-arendu / komplektaciya (разделы), slug направления."""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets/orig", ROOT / "assets/img"

def sizes_for(name):
    if name == "hero-desktop": return (1280, 1920, 2560), 72
    if name == "hero-mobile": return (540, 810, 1080), 72
    if name.startswith("mat-"): return (400, 800), 78
    return (480, 800, 1200), 76

def main():
    if not SRC.exists():
        print("Нет папки assets/orig — фото пока не добавлены."); return
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"): continue
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")   # поворот по EXIF
        clean = Image.new("RGB", im.size); clean.paste(im)           # копия без метаданных (EXIF, GPS)
        sizes, q = sizes_for(f.stem)
        done = []
        for w in sizes:
            if clean.width < w and w != sizes[0]: continue
            h = round(clean.height * w / clean.width)
            clean.resize((w, h), Image.LANCZOS).save(OUT / f"{f.stem}-{w}.webp", "WEBP", quality=q, method=6)
            done.append(f"{w}:{(OUT / f'{f.stem}-{w}.webp').stat().st_size // 1024}KB")
        print(f"{f.name}: {clean.width}×{clean.height} → {' '.join(done)}")

if __name__ == "__main__":
    main()
