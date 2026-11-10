"""Stock-ScummVM acceptance of four authored directional NPC speaking frames."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .scumm_dialogue_probe import (_capture, _click, _color_count, _run,
                                   ACTOR_RGB, ANSWER_RGB, initial_dialogue_ready)
from .scumm_launch import close_rgb, scene_pixel


FACING_COLORS = (("N", (220, 80, 80)), ("E", (35, 225, 35)),
                 ("S", (70, 70, 230)), ("W", (240, 220, 30)))
ACTOR_REGION = (680, 810, 330, 430)


def scan_costume_colors(frame: Path) -> tuple[int, ...]:
    from PIL import Image

    with Image.open(frame) as source:
        rgb = source.convert("RGB")
        left, right, top, bottom = ACTOR_REGION
        return tuple(sum(close_rgb(rgb.getpixel((x, y)), color, 25)
                         for y in range(top, bottom) for x in range(left, right))
                     for _, color in FACING_COLORS)


def observe_facing_order(baseline: tuple[int, ...], measurements: list[tuple[int, ...]],
                         threshold: int = 16) -> tuple[str, ...]:
    """A later direction cannot substitute for a missing earlier one."""
    if len(baseline) != len(FACING_COLORS) or any(len(row) != len(baseline) for row in measurements):
        raise ValueError("Expected four measured Costume color channels")
    seen = []
    for row in measurements:
        if len(seen) == len(FACING_COLORS):
            break
        expected = len(seen)
        if row[expected] >= baseline[expected] + threshold:
            seen.append(FACING_COLORS[expected][0])
        elif any(row[index] >= baseline[index] + threshold
                 for index in range(expected + 1, len(FACING_COLORS))):
            raise ValueError(f"Speaking direction skipped {FACING_COLORS[expected][0]}")
    return tuple(seen)


def run(game_directory: Path, output: Path) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Virtual X display required")
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked SCUMM dialogue game is missing")
    output.mkdir(parents=True, exist_ok=True)
    report = {"game": "four-facing-native-dialogue", "passed": False}
    with (output / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            ready = False
            for _ in range(40):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before NPC was ready")
                _capture(output, "before")
                if (close_rgb(scene_pixel(output, "before"), (70, 130, 190))
                        and initial_dialogue_ready(
                            True, _color_count(output, "before", ACTOR_RGB),
                            _color_count(output, "before", ANSWER_RGB))):
                    ready = True
                    break
                time.sleep(0.3)
            if not ready:
                raise RuntimeError("Native dialogue room/actor was not ready")

            baseline = scan_costume_colors(output / "scummvm-before.png")
            report["baseline"] = dict(zip((name for name, _ in FACING_COLORS), baseline))
            _click(330, 560)  # Talk to, inherited DOTT verb bar
            _click(192 + 185 * 2 + 16, 184 + 110 * 2 + 16)  # Native talk hotspot
            measurements: list[tuple[int, ...]] = []
            seen: tuple[str, ...] = ()
            for _ in range(200):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during four-facing dialogue")
                _capture(output, "current")
                colors = scan_costume_colors(output / "scummvm-current.png")
                measurements.append(colors)
                observed = observe_facing_order(baseline, measurements)
                if len(observed) > len(seen):
                    seen = observed
                    _capture(output, f"facing-{seen[-1].lower()}")
                if len(seen) == 4:
                    break
                time.sleep(0.20)
            report["visible_order"] = seen
            report["peak_pixels"] = dict(zip((name for name, _ in FACING_COLORS),
                                             (max(row[i] for row in measurements)
                                              for i in range(4))))
            if len(seen) != 4:
                raise RuntimeError(f"Not all four native directional frames appeared: {report}")

            stable = 0
            after = []
            for _ in range(65):
                _capture(output, "current")
                row = scan_costume_colors(output / "scummvm-current.png")
                after.append(row)
                stable = stable + 1 if row == baseline else 0
                if stable >= 6:
                    break
                time.sleep(0.3)
            report["stand_samples"] = [list(row) for row in after[-6:]]
            report["passed"] = stable >= 6
            if not report["passed"]:
                raise RuntimeError(f"Directional dialogue did not return to standing pose: {report}")
            _capture(output, "stand")
            return report
        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            (output / "four-facing-report.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_four_facing_probe GAME_DIR OUTPUT_DIR")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
