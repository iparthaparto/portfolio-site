#!/usr/bin/env python3
"""Crop video letterbox / white screenshot frames; skip logos and covers."""
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
OUT_DIR = ROOT / "assets" / "media-clean"
MANIFEST = OUT_DIR / "manifest.json"
TRIM_MIN_RATIO = 0.018
SKIP_PREFIXES = ("Logos/", "Cover Images/", "Cover%20Images/")
SKIP_NAMES = ("HIS-final logo.png", "HIS-final%20logo.png")
# Portrait video frames with thin white picture-frame margins
PORTRAIT_INSET = frozenset({"Influ.png", "Munawar.png", "Faizu.png"})
INSET_RATIO = 0.045


def should_skip(name: str) -> bool:
    if any(name.startswith(p) or p in name for p in SKIP_PREFIXES):
        return True
    if any(s in name for s in SKIP_NAMES):
        return True
    return False


def row_border_stats(row):
    white = (row.min(axis=1) >= 243).mean()
    black = (row.max(axis=1) <= 32).mean()
    return white, black


def trim_borders(arr):
    h, w = arr.shape[:2]

    def scan_axis(is_row):
        size = h if is_row else w
        start, end = 0, size - 1

        def at(i):
            return arr[i] if is_row else arr[:, i]

        while start < end - 8:
            white, black = row_border_stats(at(start))
            if white > 0.82 or black > 0.82:
                start += 1
            else:
                break
        while end > start + 8:
            white, black = row_border_stats(at(end))
            if white > 0.82 or black > 0.82:
                end -= 1
            else:
                break
        return start, end + 1

    top, bottom = scan_axis(True)
    left, right = scan_axis(False)

    # Extra pass for thin white picture-frame margins
    for _ in range(20):
        changed = False
        if top < bottom - 8:
            white, black = row_border_stats(arr[top])
            if white > 0.88 or black > 0.88:
                top += 1
                changed = True
        if bottom > top + 8:
            white, black = row_border_stats(arr[bottom - 1])
            if white > 0.88 or black > 0.88:
                bottom -= 1
                changed = True
        if left < right - 8:
            white, black = row_border_stats(arr[:, left])
            if white > 0.88 or black > 0.88:
                left += 1
                changed = True
        if right > left + 8:
            white, black = row_border_stats(arr[:, right - 1])
            if white > 0.88 or black > 0.88:
                right -= 1
                changed = True
        if not changed:
            break

    return left, top, right, bottom


def process_image(src: Path, dest: Path):
    im = Image.open(src).convert("RGB")
    arr = np.array(im)
    h, w = arr.shape[:2]
    l, t, r, b = trim_borders(arr)
    trim_ratio = 1 - ((r - l) * (b - t)) / (w * h)

    if trim_ratio < TRIM_MIN_RATIO or (r - l) < 80 or (b - t) < 80:
        return None

    out = im.crop((l, t, r, b))
    ow, oh = out.size
    min_width = 1400 if max(ow, oh) < 1200 else 1200
    if ow < min_width:
        scale = min_width / ow
        out = out.resize((min_width, int(oh * scale)), Image.Resampling.LANCZOS)

    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=105, threshold=4))
    out = ImageEnhance.Contrast(out).enhance(1.03)
    out = ImageEnhance.Sharpness(out).enhance(1.06)

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix.lower() in (".jpg", ".jpeg"):
        out.save(dest, "JPEG", quality=93, optimize=True)
    else:
        out.save(dest, "PNG", optimize=True)

    return {
        "original": [w, h],
        "output": list(out.size),
        "trim_ratio": round(trim_ratio, 4),
        "local": "assets/media-clean/" + dest.name,
    }


def safe_filename(name: str) -> str:
    return name.replace(" ", "-").replace("/", "-")


def main():
    html = HTML.read_text(encoding="utf-8")
    urls = sorted(set(re.findall(
        r'https://gkrcjpqlelrxgyanzyrg\.supabase\.co[^"\']+\.(?:png|jpg|jpeg|webp)',
        html, re.I
    )))
    manifest = {}
    count = 0

    for url in urls:
        name = urllib.parse.unquote(url.split("/portfolio-media/")[-1].split("?")[0])
        if should_skip(name):
            manifest[name] = {"url": url, "skipped": True}
            continue

        dest = OUT_DIR / safe_filename(name)
        tmp = OUT_DIR / ".tmp" / safe_filename(name)
        tmp.parent.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(url, tmp)
            meta = process_image(tmp, dest)
            tmp.unlink(missing_ok=True)
            if meta:
                manifest[name] = {"url": url, **meta}
                count += 1
            else:
                manifest[name] = {"url": url, "unchanged": True}
                if dest.exists():
                    dest.unlink()
        except Exception as e:
            manifest[name] = {"url": url, "error": str(e)}

    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Trimmed {count} images → {OUT_DIR}")


if __name__ == "__main__":
    main()
