#!/usr/bin/env python3
"""Compress portfolio media for web delivery."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
MANIFEST = ROOT / "scripts" / "media-optimize-map.json"

SKIP = {".pdf", ".mp4"}
LOGO_DIR = "Logos"


def run_sips(args: list[str]) -> bool:
    try:
        subprocess.run(["sips", *args], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def optimize_image(path: Path) -> tuple[str, int, int]:
  """Returns (new_relative_path, old_bytes, new_bytes)."""
  rel = path.relative_to(ROOT).as_posix()
  old_size = path.stat().st_size
  is_logo = LOGO_DIR in path.parts

  if is_logo:
    max_dim = 320
    tmp = path.with_suffix(path.suffix + ".opt.png")
    if not run_sips(["-Z", str(max_dim), str(path), "--out", str(tmp)]):
      return rel, old_size, old_size
    tmp.replace(path)
    new_size = path.stat().st_size
    return rel, old_size, new_size

  # Photos / covers — JPEG for size
  out = path.with_suffix(".jpg")
  max_dim = 1400 if "Cover Images" in path.parts else 1200
  quality = "72"
  tmp = out.with_suffix(".tmp.jpg")
  fmt_args = ["-Z", str(max_dim), "-s", "format", "jpeg", "-s", "formatOptions", quality, str(path), "--out", str(tmp)]
  if not run_sips(fmt_args):
    return rel, old_size, old_size

  new_rel = out.relative_to(ROOT).as_posix()
  if out.exists() and out != path:
    out.unlink()
  tmp.replace(out)
  if path != out and path.exists():
    path.unlink()
  new_size = out.stat().st_size
  return new_rel, old_size, new_size


def main() -> None:
  mapping: dict[str, str] = {}
  savings = 0
  for path in sorted(MEDIA.rglob("*")):
    if not path.is_file():
      continue
    ext = path.suffix.lower()
    if ext in SKIP:
      continue
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
      continue

    old_rel = path.relative_to(ROOT).as_posix()
    new_rel, old_b, new_b = optimize_image(path)
    if new_rel != old_rel:
      mapping[old_rel] = new_rel
    savings += max(0, old_b - new_b)
    print(f"{old_b/1024:.0f}KB → {new_b/1024:.0f}KB  {old_rel}" + (f" → {new_rel}" if new_rel != old_rel else ""))

  MANIFEST.write_text(json.dumps(mapping, indent=2))
  print(f"\nSaved ~{savings/1024/1024:.1f} MB | {len(mapping)} path changes")


if __name__ == "__main__":
  main()
