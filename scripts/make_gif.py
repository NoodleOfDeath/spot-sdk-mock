"""Stitch ``assets/frames/frame_*.png`` into ``assets/demo.gif``.

Run after ``npx playwright test capture_demo.spec.ts``.
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    frames_dir = repo / "assets" / "frames"
    out = repo / "assets" / "demo.gif"

    paths = sorted(glob.glob(str(frames_dir / "frame_*.png")))
    if not paths:
        print(f"no frames found in {frames_dir}", file=sys.stderr)
        return 1

    imgs = [Image.open(p).convert("RGB") for p in paths]
    # 1280×720 keeps the file small while staying readable on GitHub.
    imgs = [img.resize((1280, 720), Image.LANCZOS) for img in imgs]

    # Per-frame duration: rotation frames are quick (160ms), everything else
    # gets 480ms so the viewer can read the screen.
    durations = []
    for p in paths:
        durations.append(160 if "09_rotate" in Path(p).name else 480)

    imgs[0].save(
        out,
        save_all=True,
        append_images=imgs[1:],
        loop=0,
        duration=durations,
        optimize=True,
        disposal=2,
    )
    print(f"{len(imgs)} frames → {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
