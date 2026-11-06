"""Launch a font-ready SCUMM fixture and capture language-key screenshots.

This is an observable runtime smoke test, not OCR or a pixel-perfect glyph proof.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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


def verify_language_button_change(before: Path, after: Path) -> dict:
    """Check the five badge pixels, excluding the rest of the moving scene."""
    from PIL import Image

    with Image.open(before) as old, Image.open(after) as new:
        if old.size != new.size:
            raise ValueError("Language button screenshots have different sizes")
        # 1024x768 Xvfb: 640-pixel ScummVM viewport begins at (192,184).
        region = (192, 184, 392, 218)
        if old.width < region[2] or old.height < region[3]:
            raise ValueError("Language button viewport is too small")
        with tempfile.TemporaryDirectory() as temp:
            cropped_before = Path(temp) / "before.png"
            cropped_after = Path(temp) / "after.png"
            old.crop(region).save(cropped_before)
            new.crop(region).save(cropped_after)
            change = compare_screenshots(cropped_before, cropped_after)
    if change["changed_pixels"] < 20:
        raise ValueError("Clicking a graphical language button did not visibly change selection")
    return change


def language_runtime_probe(game: Path, output: Path,
                           graphical_language_buttons: bool = False) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Language probe requires Xvfb DISPLAY")
    if any(not (game / f"tentacle.{suffix}").is_file() for suffix in ("000", "001")):
        raise ValueError("Missing SCUMM game data")
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "scummvm.log"
    results = {}
    environment = {**os.environ, "SDL_AUDIODRIVER": "dummy"}
    def capture(code: str, process) -> None:
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
                capture(code, process)
            if graphical_language_buttons:
                # After entering Cellar with PL selected, compare only the
                # persistent badge row. Move the pointer away in both shots.
                subprocess.run(["xdotool", "mousemove", "900", "700"],
                               check=True, timeout=10)
                time.sleep(0.4)
                capture("pl_button_before", process)
                subprocess.run(["xdotool", "mousemove", "217", "202", "click", "1"],
                               check=True, timeout=10)
                time.sleep(3)
                subprocess.run(["xdotool", "mousemove", "900", "700"],
                               check=True, timeout=10)
                time.sleep(0.4)
                capture("de_button_after", process)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    room_evidence = verify_room_transition(output / "pl.png", output / "room_after_pl.png")
    post_room_difference = compare_screenshots(
        output / "room_after_pl.png", output / "pl_after_room.png")
    if post_room_difference["changed_pixels"] == 0:
        raise ValueError("Post-room language probe produced no visible response")
    button_evidence = (verify_language_button_change(
        output / "pl_button_before.png", output / "de_button_after.png")
        if graphical_language_buttons else None)
    report = {"engine_survived_key_selection": True,
              **room_evidence,
              "language_screenshot_differences": {
                  "de_to_ja": compare_screenshots(output / "de.png", output / "ja.png"),
                  "ja_to_pl": compare_screenshots(output / "ja.png", output / "pl.png"),
                  "room_to_pl_after_room": post_room_difference,
              },
              "post_room_probe_visibly_responded": True,
              "graphical_button_click_attempted": graphical_language_buttons,
              "graphical_button_selection_changed": button_evidence is not None,
              "graphical_button_pixel_change": button_evidence,
              "room_transition_probe_attempted": True,
              "language_persistence_visually_verified": False,
              "screenshots": results,
              "glyph_rendering_verified": False}
    (output / "language-runtime-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "--language-buttons"):
        print("Usage: python -m adventure_studio.scumm_language_runtime_probe GAME OUTPUT [--language-buttons]")
        return 2
    print(json.dumps(language_runtime_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                            graphical_language_buttons=len(sys.argv) == 4),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

