# ImageBatch — Marketplace-Ready Product Photos, In Bulk

One folder of product photos in, platform-ready files out — originals
untouched, everything local.

## What it does
- Auto-orients photos from their EXIF tag, then strips **all** metadata
- Resizes to a platform preset — Shopify 2048, Etsy, square-padded 2000,
  web 1600 — and **never upscales** (a small image is reported, not blurred up)
- Optional pad-to-square on a clean background for marketplace thumbnails
- Converts JPG/PNG/WebP; transparency is flattened onto the background for JPG
- Optional sequential renaming (shop-01.jpg, shop-02.jpg, …)
- A report with per-file before/after dimensions and bytes, total size
  saved, and honest warnings

## Verified behaviour
On a 3-image test folder (a 4000×3000 photo, an EXIF-rotated photo, a
transparent PNG): the big photo was resized to 2048×1536, the rotated one
came out upright at 500×300, the PNG flattened onto white — all metadata
gone from every output and the folder totalled 67% smaller, with the two
below-zoom-threshold images flagged instead of upscaled.

## Run from source
```
python image_batch.py photos_in photos_out shopify jpg shop-
```
Requires Pillow. The Windows package bundles everything.
