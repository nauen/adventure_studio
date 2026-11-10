"""Stock ScummVM evidence of two native COST frames during one NPC line."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .scumm_dialogue_probe import (_capture, _click, _color_count,
                                   ACTOR_RGB, ANSWER_RGB, initial_dialogue_ready)
from .scumm_four_facing_probe import scan_costume_colors
from .scumm_launch import close_rgb, scene_pixel


def observed_speaking_change(baseline: tuple[int, ...], samples: list[tuple[int, ...]],
                             threshold: int = 16) -> bool:
    """Both looping frames must render; sampling can start mid-COST cycle."""
    return all(any(row[index] >= baseline[index] + threshold for row in samples)
               for index in (0, 1))


def observed_independent_line_pairs(baseline: tuple[int, ...],
                                    samples: list[tuple[int, ...]],
                                    threshold: int = 16) -> tuple[str, ...]:
    """Both colors of line one precede both colors of line two, cycle phase free."""
    first = set()
    second = set()
    for row in samples:
        active = {index for index in range(4)
                  if row[index] >= baseline[index] + threshold}
        if active & {2, 3}:
            if first != {0, 1}:
                return tuple(("red", "green")[index] for index in sorted(first))
            second.update(active & {2, 3})
        elif not second:
            first.update(active & {0, 1})
    return tuple(("red", "green")[index] for index in sorted(first)) + tuple(
        ("blue", "yellow")[index - 2] for index in sorted(second))


def run(game_directory: Path, output: Path, two_lines: bool = False) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Virtual X display required")
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked native dialogue game is missing")
    output.mkdir(parents=True, exist_ok=True)
    report = {"game": "independent-line-sequences" if two_lines else
              "animated-speaking-native-dialogue", "passed": False}
    with (output / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "dummy"})
        try:
            for _ in range(40):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before NPC was ready")
                _capture(output, "before")
                if (close_rgb(scene_pixel(output, "before"), (70, 130, 190))
                    and initial_dialogue_ready(
                        True, _color_count(output, "before", ACTOR_RGB),
                        _color_count(output, "before", ANSWER_RGB))):
                    break
                time.sleep(0.3)
            else:
                raise RuntimeError("Native dialogue room/actor was not ready")
            baseline = scan_costume_colors(output / "scummvm-before.png")
            _click(330, 560)
            _click(192 + 185 * 2 + 16, 184 + 110 * 2 + 16)
            samples: list[tuple[int, ...]] = []
            red_captured = False
            observed: tuple[str, ...] = ()
            for sample in range(160 if two_lines else 120):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited during animated NPC line")
                _capture(output, "current")
                row = scan_costume_colors(output / "scummvm-current.png")
                samples.append(row)
                if sample in (0, 8, 20, 40):
                    _capture(output, f"checkpoint-{sample:03d}")
                if not red_captured and row[0] >= baseline[0] + 16:
                    _capture(output, "frame-red")
                    red_captured = True
                if two_lines:
                    seen = observed_independent_line_pairs(baseline, samples)
                    if len(seen) > len(observed):
                        for color in seen[len(observed):]:
                            _capture(output, f"frame-{color}")
                        observed = seen
                    if len(seen) == 4:
                        break
                elif observed_speaking_change(baseline, samples):
                    _capture(output, "frame-green")
                    break
                time.sleep(0.10)
            report["two_frames_visible"] = observed_speaking_change(baseline, samples)
            report["peak_pixels"] = {
                name: max(row[index] for row in samples)
                for index, name in enumerate(("red", "green", "blue", "yellow")
                                             if two_lines else ("red", "green"))
            }
            if two_lines:
                report["visible_order"] = observed
                if len(observed) != 4:
                    raise RuntimeError(f"Both native NPC lines did not show independent frames: {report}")
            elif not report["two_frames_visible"]:
                raise RuntimeError(f"Two speaking frames did not appear in sequence: {report}")
            consecutive_stand = 0
            for _ in range(90):
                _capture(output, "current")
                row = scan_costume_colors(output / "scummvm-current.png")
                consecutive_stand = consecutive_stand + 1 if row == baseline else 0
                if consecutive_stand >= 6:
                    break
                time.sleep(0.2)
            report["stand_frames"] = consecutive_stand
            report["passed"] = consecutive_stand >= 6
            if not report["passed"]:
                raise RuntimeError(f"Animated dialogue did not return to standing pose: {report}")
            _capture(output, "stand")
            return report
        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            (output / "speaking-sequence-report.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "--two-lines"):
        raise SystemExit("Usage: python -m adventure_studio.scumm_speaking_sequence_probe GAME_DIR OUTPUT_DIR [--two-lines]")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]),
                         two_lines=len(sys.argv) == 4), indent=2))
