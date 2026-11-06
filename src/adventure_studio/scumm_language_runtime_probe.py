"""Launch a font-ready SCUMM fixture and capture language-key screenshots.

This is an observable runtime smoke test, not OCR or a pixel-perfect glyph proof.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path



def compare_screenshots(before: Path, after: Path) -> dict:
    """Measure changed pixels, without treating changes as proof of legible text."""
    try:
        from PIL import Image, ImageChops
    except ImportError as error:
        raise RuntimeError("Room image comparison requires Pillow") from error

    with Image.open(before) as old, Image.open(after) as new:
        if old.size != new.size:
            raise ValueError("Room screenshots have different dimensions")
        old_rgb = old.convert("RGB")
        new_rgb = new.convert("RGB")
        difference = ImageChops.difference(old_rgb, new_rgb)
        pixels = (difference.get_flattened_data() if hasattr(difference, "get_flattened_data")
                  else difference.getdata())
        changed = sum(1 for pixel in pixels if max(pixel) >= 24)
        total = old_rgb.width * old_rgb.height
    ratio = changed / total
    return {"changed_pixels": changed, "changed_ratio": round(ratio, 6)}


def verify_room_transition(before: Path, after: Path) -> dict:
    """Reject a mere surviving key press without a substantial scene change."""
    comparison = compare_screenshots(before, after)
    ratio = comparison["changed_ratio"]
    if ratio < 0.05:
        raise ValueError(f"Room transition not visually confirmed: {ratio:.3%} changed pixels")
    return {"room_transition_changed_pixels": comparison["changed_pixels"],
            "room_transition_changed_ratio": ratio,
            "room_transition_visually_confirmed": True}


def language_runtime_probe(game: Path, output: Path) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Language probe requires Xvfb DISPLAY")
    if any(not (game / f"tentacle.{suffix}").is_file() for suffix in ("000", "001")):
        raise ValueError("Missing SCUMM game data")
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "scummvm.log"
    results = {}
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            time.sleep(5)
            if process.poll() is not None:
                raise RuntimeError("ScummVM exited before language input")
            # Keep Polish selected while changing rooms, then repeat the
            # translated line without changing GameLanguage.
            for key, code in (("1", "de"), ("4", "ja"), ("5", "pl"),
                              ("0", "room_after_pl"), ("6", "pl_after_room")):
                subprocess.run(["xdotool", "key", key], check=True, timeout=10)
                time.sleep(2)
                if process.poll() is not None:
                    raise RuntimeError(f"ScummVM exited after selecting {code}")
                raw = output / f"{code}.xwd"
                png = output / f"{code}.png"
                for attempt in range(4):
                    subprocess.run(["xwd", "-root", "-silent", "-out", str(raw)],
                                   check=True, timeout=10)
                    subprocess.run(["convert", str(raw), str(png)], check=True, timeout=10)
                    if png.stat().st_size >= 1000:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(f"ScummVM exited while capturing {code}")
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Invalid {code} screenshot after four captures")
                results[code] = png.name
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    room_evidence = verify_room_transition(output / "pl.png", output / "room_after_pl.png")
    report = {"engine_survived_key_selection": True,
              **room_evidence,
              "language_screenshot_differences": {
                  "de_to_ja": compare_screenshots(output / "de.png", output / "ja.png"),
                  "ja_to_pl": compare_screenshots(output / "ja.png", output / "pl.png"),
                  "room_to_pl_after_room": compare_screenshots(
                      output / "room_after_pl.png", output / "pl_after_room.png"),
              },
              "room_transition_probe_attempted": True,
              "language_persistence_visually_verified": False,
              "screenshots": results,
              "glyph_rendering_verified": False}
    (output / "language-runtime-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_language_runtime_probe GAME OUTPUT")
        return 2
    print(json.dumps(language_runtime_probe(Path(sys.argv[1]), Path(sys.argv[2])),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

