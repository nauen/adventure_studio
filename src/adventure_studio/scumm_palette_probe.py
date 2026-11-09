"""Visual integration probe for a linked SCUMM v6 indexed-water fixture.

Requires ScummVM, xwd, ImageMagick and an X display. A successful test proves
palette animation is visible, not merely that a room contains a CYCL chunk.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .palette_demo import WATER_PALETTE
from .scumm_launch import close_rgb, parse_srgb_pixel


def pixel_from_frame(image: Path, x: int, y: int) -> tuple[int, int, int]:
    result = subprocess.run(["convert", str(image), "-format", f"%[pixel:p{{{x},{y}}}]", "info:"],
                            capture_output=True, text=True, timeout=10, check=False)
    if result.returncode:
        raise RuntimeError(f"Frame pixel query failed: {result.stderr}")
    return parse_srgb_pixel(result.stdout)


def analyze_palette_frames(samples: list[tuple[tuple[int, int, int], tuple[int, int, int]]]) -> dict:
    """One water pixel must change within the ramp; an unaffected sky pixel must not."""
    if len(samples) < 2:
        raise ValueError("At least two frames required")
    water_colors = [water for water, _ in samples]
    static_colors = [static for _, static in samples]
    ramp_only = all(any(close_rgb(color, expected, 18) for expected in WATER_PALETTE)
                    for color in water_colors)
    animated = len(set(water_colors)) >= 2
    stable_sky = all(close_rgb(color, static_colors[0], 8) for color in static_colors)
    return {"palette_colors_only": ramp_only, "water_color_changed": animated,
            "sky_remained_static": stable_sky,
            "distinct_water_colors": len(set(water_colors)),
            "passed": ramp_only and animated and stable_sky}


def run(game_directory: Path, output_directory: Path) -> None:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("An X display is required")
    if not all((game_directory / f"tentacle.{suffix}").is_file() for suffix in ("000", "001")):
        raise ValueError("Missing linked SCUMM compatibility game")
    output_directory.mkdir(parents=True, exist_ok=True)
    with (output_directory / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            samples = []
            # 320x200 game viewport is scaled 2x and centered on 1024x768.
            # World (80,135) is in our water ramp; (200,70) is static sky.
            for index in range(20):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM terminated; inspect scummvm.log")
                time.sleep(0.35)
                xwd = output_directory / f"palette-{index:02d}.xwd"
                png = output_directory / f"palette-{index:02d}.png"
                capture = subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)],
                                         capture_output=True, text=True, timeout=10, check=False)
                if capture.returncode:
                    raise RuntimeError(f"X capture failed: {capture.stderr}")
                converted = subprocess.run(["convert", str(xwd), str(png)],
                                           capture_output=True, text=True, timeout=10, check=False)
                if converted.returncode:
                    raise RuntimeError(f"Frame conversion failed: {converted.stderr}")
                xwd.unlink()
                samples.append((pixel_from_frame(png, 352, 454), pixel_from_frame(png, 592, 324)))
            report = analyze_palette_frames(samples[4:])  # ignore startup/splash frames
            report["sample_count"] = len(samples[4:])
            report["water_rgb_samples"] = [list(w) for w, _ in samples[4:]]
            (output_directory / "palette-report.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if not report["passed"]:
                raise RuntimeError(f"SCUMM palette animation visually unverified: {report}")
            print(f"SCUMM water palette cycled through {report['distinct_water_colors']} colors; sky stable")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_palette_probe GAME_DIRECTORY OUTPUT_DIRECTORY")
        return 2
    run(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
