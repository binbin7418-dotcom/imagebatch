#!/usr/bin/env python3
"""
ImageBatch — marketplace-ready image batch processing for sellers.

One folder in, platform-ready files out (originals never touched):
  - Auto-orient from EXIF, then strip all metadata (privacy + size)
  - Resize to a platform preset (never upscales — reported instead)
  - Optional pad-to-square on a chosen background (marketplace thumbnails)
  - Convert format (jpg/png/webp) with sensible quality
  - Sequential renaming (shop-name-01.jpg, ...)
  - A report with per-file before/after dimensions and bytes, and the
    total size saved — plus honest warnings (too-small images, alpha
    flattened onto the background colour, unreadable files skipped).

Local only. Uses Pillow.
"""
import os
import sys

from PIL import Image, ImageOps

PRESETS = {
    "shopify":  {"label": "Shopify — up to 2048×2048", "max_w": 2048, "max_h": 2048, "square": False},
    "etsy":     {"label": "Etsy — 2000 px on the short side target, ≤2700 wide", "max_w": 2700, "max_h": 2700, "square": False},
    "square":   {"label": "Square pad — 2000×2000, centred on background", "max_w": 2000, "max_h": 2000, "square": True},
    "web":      {"label": "Web — max 1600 px, quality-optimised JPG", "max_w": 1600, "max_h": 1600, "square": False},
}
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def process_folder(src_dir, outdir, preset="shopify", fmt="jpg", bg=(255, 255, 255),
                   prefix="", quality=88):
    if preset not in PRESETS:
        raise ValueError(f"unknown preset '{preset}'")
    p = PRESETS[preset]
    os.makedirs(outdir, exist_ok=True)
    files = sorted(f for f in os.listdir(src_dir)
                   if os.path.splitext(f)[1].lower() in EXTS and os.path.isfile(os.path.join(src_dir, f)))
    rows, warnings = [], []
    total_before = total_after = 0
    for i, name in enumerate(files, 1):
        src = os.path.join(src_dir, name)
        try:
            im = Image.open(src)
            im.load()
        except Exception as e:
            warnings.append(f"{name}: could not be read ({e}) — skipped")
            continue
        before_bytes = os.path.getsize(src)
        bw, bh = im.size
        notes = []
        im = ImageOps.exif_transpose(im)
        if im.size != (bw, bh):
            notes.append("rotated upright from its EXIF orientation")
        if p["square"]:
            side = min(max(im.size), p["max_w"])
            scale = min(1.0, side / max(im.size))
            if scale < 1.0:
                im = im.resize((round(im.size[0] * scale), round(im.size[1] * scale)), Image.LANCZOS)
            canvas = Image.new("RGB", (side, side), bg)
            flat = im.convert("RGBA")
            canvas.paste(flat, ((side - flat.size[0]) // 2, (side - flat.size[1]) // 2), flat)
            im = canvas
            notes.append(f"padded to a {side}×{side} square")
        else:
            if im.size[0] > p["max_w"] or im.size[1] > p["max_h"]:
                im.thumbnail((p["max_w"], p["max_h"]), Image.LANCZOS)
                notes.append(f"resized to {im.size[0]}×{im.size[1]}")
            elif max(im.size) < 1000:
                warnings.append(f"{name}: only {im.size[0]}×{im.size[1]} — below most marketplaces' zoom threshold; ImageBatch never upscales (it would just blur)")
        if fmt == "jpg" and im.mode in ("RGBA", "LA", "P"):
            flat = Image.new("RGB", im.size, bg)
            flat.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1] if im.mode != "P" else None)
            im = flat
            notes.append("transparency flattened onto the background colour for JPG")
        elif im.mode == "P":
            im = im.convert("RGB")
        out_ext = {"jpg": ".jpg", "png": ".png", "webp": ".webp"}[fmt]
        out_name = f"{prefix}{i:02d}{out_ext}" if prefix else os.path.splitext(name)[0] + out_ext
        dst = os.path.join(outdir, out_name)
        save_kw = {"quality": quality} if fmt in ("jpg", "webp") else {}
        im.save(dst, **save_kw)
        after_bytes = os.path.getsize(dst)
        total_before += before_bytes
        total_after += after_bytes
        rows.append({"src": name, "dst": out_name, "before": f"{bw}×{bh}",
                     "after": f"{im.size[0]}×{im.size[1]}",
                     "bytes_before": before_bytes, "bytes_after": after_bytes,
                     "notes": "; ".join(notes) if notes else "metadata stripped"})
    saved = (1 - total_after / total_before) * 100 if total_before else 0.0
    lines = ["# ImageBatch — processing report", "",
             f"Source folder: {src_dir}  ·  Preset: {p['label']}  ·  Output format: {fmt.upper()}", "",
             "## Summary",
             f"- Images processed: {len(rows)} of {len(files)} found",
             f"- Total size: {total_before/1024:.0f} KB → {total_after/1024:.0f} KB ({saved:.0f}% smaller)",
             "- All EXIF/metadata stripped from outputs; originals untouched", "",
             "## Per file"]
    lines += [f"- {r['src']} → {r['dst']}: {r['before']} → {r['after']}, "
              f"{r['bytes_before']/1024:.0f} KB → {r['bytes_after']/1024:.0f} KB ({r['notes']})" for r in rows] or ["- none"]
    lines += ["", "## Warnings"]
    lines += [f"- {w}" for w in warnings] or ["- none"]
    lines += ["", "Scope note: ImageBatch prepares file mechanics (size, orientation, format, metadata). "
                   "It does not judge photo quality, lighting or composition."]
    report_path = os.path.join(outdir, "batch_report.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return {"processed": len(rows), "found": len(files), "warnings": len(warnings),
            "saved_pct": round(saved), "report_path": report_path, "outdir": outdir}


def main(argv):
    if len(argv) < 3:
        print("usage: image_batch.py <image folder> <outdir> [shopify|etsy|square|web] [jpg|png|webp] [prefix]")
        return 2
    s = process_folder(argv[1], argv[2],
                       argv[3] if len(argv) > 3 else "shopify",
                       argv[4] if len(argv) > 4 else "jpg",
                       prefix=argv[5] if len(argv) > 5 else "")
    print(f"processed={s['processed']}/{s['found']} warnings={s['warnings']} saved={s['saved_pct']}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
