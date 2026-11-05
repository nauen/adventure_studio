"""Real ScummVM visibility/input gate for the bounded choice-object prototype.

Requires xvfb-run, xdotool, xwd, ImageMagick, ScummVM. The SCUMM gameplay
fixture is generated independently via dialogue_demo --choices.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .scumm_launch import close_rgb, count_color_pixels, parse_key_bounds, scene_pixel


ACTOR_RGB = (120, 70, 180)
ANSWER_RGB = (225, 80, 180)
_CROP = "640x288+192+184"


def detect_answer_transition(before: int, displayed: int, dismissed: int) -> bool:
    """Separate unshown, shown and dismissed states; no guessed outcome."""
    if any(type(x) is not int or x < 0 for x in (before, displayed, dismissed)):
        raise ValueError("Invalid answer pixel counts")
    return before < 10 and displayed >= 50 and dismissed < 10


def _run(command: list[str], timeout: int = 10) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command[0]}: {result.stderr[:300]}")
    return result.stdout


def _capture(directory: Path, label: str) -> None:
    xwd = directory / f"dialogue-{label}.xwd"
    _run(["xwd", "-root", "-silent", "-out", str(xwd)])
    _run(["convert", str(xwd), str(directory / f"scummvm-{label}.png")])
    xwd.unlink()


def _color_count(directory: Path, label: str, rgb: tuple[int, int, int]) -> int:
    frame = directory / f"scummvm-{label}.png"
    histogram = _run(["convert", str(frame), "-crop", _CROP, "+repage",
                      "-format", "%c", "histogram:info:"])
    return count_color_pixels(histogram, rgb)


def _color_center(directory: Path, label: str, rgb: tuple[int, int, int]) -> tuple[int, int]:
    frame = directory / f"scummvm-{label}.png"
    color = "#" + "".join(f"{value:02X}" for value in rgb)
    bounds = _run(["convert", str(frame), "-crop", _CROP, "+repage",
                   "-fuzz", "8%", "-fill", "white", "-opaque", color,
                   "-fill", "black", "+opaque", "white", "-trim",
                   "-format", "%wx%h%O", "info:"])
    return parse_key_bounds(bounds)


def _click(x: int, y: int) -> None:
    _run(["xdotool", "mousemove", str(x), str(y), "click", "1"], timeout=5)


def run(game_directory: Path, output: Path) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Virtual X display required")
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked SCUMM dialogue game is missing")
    output.mkdir(parents=True, exist_ok=True)
    report: dict = {"game": "dialogue-choices", "passed": False}
    with (output / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            ready = False
            for _ in range(35):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before dialogue test")
                _capture(output, "before")
                if close_rgb(scene_pixel(output, "before"), (70, 130, 190)):
                    ready = True
                    break
                time.sleep(0.3)
            if not ready:
                raise RuntimeError("Initial scene not visible")
            before = _color_count(output, "before", ANSWER_RGB)
            actor_count = _color_count(output, "before", ACTOR_RGB)
            report.update({"answer_pixels_before": before, "actor_pixels": actor_count})
            if actor_count < 40 or before >= 10:
                raise RuntimeError(f"Initial character/answer visibility invalid: {report}")
            # The inherited DOTT verb GUI is in fixed 1024x768 Xvfb coords.
            _click(330, 560)  # Talk to
            x, y = _color_center(output, "before", ACTOR_RGB)
            _click(x, y)
            displayed = 0
            for _ in range(35):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM quit during dialogue")
                _capture(output, "options")
                displayed = _color_count(output, "options", ANSWER_RGB)
                if displayed >= 50:
                    break
                time.sleep(0.35)
            report["answer_pixels_visible"] = displayed
            if displayed < 50:
                raise RuntimeError(f"Talk to did not reveal answers: {report}")
            # The two identical-colored answer sprites must not be treated as
            # one ImageMagick bounding box: its center can lie in the gap.
            # Choose the first fixture answer at story-space (240,130).
            answer_x, answer_y = 192 + 240 * 2 + 16, 184 + 130 * 2 + 16
            _click(answer_x, answer_y)
            dismissed = displayed
            for _ in range(35):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM quit during answer selection")
                _capture(output, "dismissed")
                dismissed = _color_count(output, "dismissed", ANSWER_RGB)
                if dismissed < 10:
                    break
                time.sleep(0.35)
            report.update({"answer_click": [answer_x, answer_y],
                           "answer_pixels_dismissed": dismissed,
                           "passed": detect_answer_transition(before, displayed, dismissed)})
            if not report["passed"]:
                raise RuntimeError(f"Answer interaction was not proven: {report}")
            return report
        finally:
            (output / "dialogue-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                           encoding="utf-8")
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_dialogue_probe GAME_DIR OUTPUT_DIR")
        return 2
    report = run(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
