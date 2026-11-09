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


def initial_dialogue_ready(scene_visible: bool, actor_pixels: int, answer_pixels: int) -> bool:
    """Wait for the actor as well as the backdrop before attempting input."""
    return scene_visible and actor_pixels >= 40 and answer_pixels < 10


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


def _answer_row_count(directory: Path, label: str, y: int) -> int:
    frame = directory / f"scummvm-{label}.png"
    histogram = _run(["convert", str(frame), "-crop", f"640x34+192+{184 + y * 2}",
                      "+repage", "-format", "%c", "histogram:info:"])
    return count_color_pixels(histogram, ANSWER_RGB)


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


def run(game_directory: Path, output: Path, voice: bool = False,
        nested: bool = False, multispeaker: bool = False,
        linear_multispeaker: bool = False, gesture: bool = False) -> dict:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Virtual X display required")
    if not all((game_directory / f"tentacle.{part}").is_file() for part in ("000", "001")):
        raise ValueError("Linked SCUMM dialogue game is missing")
    output.mkdir(parents=True, exist_ok=True)
    report: dict = {"game": "dialogue-choices", "passed": False, "voice": voice,
                    "nested": nested, "multispeaker": multispeaker,
                    "linear_multispeaker": linear_multispeaker, "gesture": gesture}
    pcm_path = output / "dialogue-voice.raw"
    with (output / "scummvm.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["scummvm", f"--path={game_directory.resolve()}", "tentacle"],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "SDL_AUDIODRIVER": "disk" if voice else "dummy",
                                        **({"SDL_DISKAUDIOFILE": str(pcm_path)} if voice else {})})
        epoch = time.monotonic()
        try:
            ready = False
            before = 0
            actor_count = 0
            for _ in range(35):
                if process.poll() is not None:
                    raise RuntimeError("ScummVM exited before dialogue test")
                _capture(output, "before")
                scene_visible = close_rgb(scene_pixel(output, "before"), (70, 130, 190))
                if scene_visible:
                    before = _color_count(output, "before", ANSWER_RGB)
                    actor_count = _color_count(output, "before", ACTOR_RGB)
                if initial_dialogue_ready(scene_visible, actor_count, before):
                    ready = True
                    break
                time.sleep(0.3)
            report.update({"answer_pixels_before": before, "actor_pixels": actor_count})
            if not ready:
                raise RuntimeError(f"Initial scene/character not ready: {report}")
            if voice:
                _run(["xdotool", "key", "1"])  # sorted languages: de, en
                time.sleep(0.6)
            # The inherited DOTT verb GUI is in fixed 1024x768 Xvfb coords.
            _click(330, 560)  # Talk to
            x, y = ((192 + 185 * 2 + 16, 184 + 110 * 2 + 16)
                    if multispeaker or linear_multispeaker else
                    _color_center(output, "before", ACTOR_RGB))
            _click(x, y)
            if linear_multispeaker:
                # Each of two consecutive actorSay lines paints different
                # black glyphs in the native room's top speech strip.
                from PIL import Image

                def line_ink() -> set[tuple[int, int]]:
                    with Image.open(output / "scummvm-linear.png") as frame:
                        rgb = frame.convert("RGB")
                        return {(col, row) for row in range(184, 216)
                                for col in range(300, 800)
                                if close_rgb(rgb.getpixel((col, row)), (0, 0, 0), 10)}

                def gesture_ink() -> int:
                    with Image.open(output / "scummvm-linear.png") as frame:
                        rgb = frame.convert("RGB")
                        # The camera follows Ego while walking to the NPC.
                        # The speaker therefore moves left on screen even
                        # though its authored world coordinates stay fixed.
                        return sum(close_rgb(rgb.getpixel((col, row)), (220, 80, 80), 25)
                                   for row in range(270, 375) for col in range(530, 675))

                first = None
                second = None
                colored = 0
                for _ in range(85):
                    if process.poll() is not None:
                        raise RuntimeError("ScummVM exited during linear NPC dialogue")
                    _capture(output, "linear")
                    ink = line_ink()
                    if gesture:
                        colored = max(colored, gesture_ink())
                    if first is None and len(ink) >= 100:
                        first = ink
                        _capture(output, "linear-first")
                    elif first is not None and second is None and len(ink) >= 100 and len(
                            first.symmetric_difference(ink)) > 150:
                        second = ink
                        _capture(output, "linear-second")
                    if second is not None and (not gesture or colored >= 10):
                        if gesture:
                            _capture(output, "gesture-frame")
                        break
                    time.sleep(0.25)
                report.update({"first_speaker_pixels": len(first or ()),
                               "second_speaker_pixels": len(second or ()),
                               "gesture_frame_pixels": colored,
                               "answer_pixels_visible": 0,
                               "passed": bool(first and second and (not gesture or colored >= 10))})
                if not report["passed"]:
                    raise RuntimeError(f"Native two-speaker text or authored Costume gesture was not visible: {report}")
                return report
            if voice:
                # The native cursor/actor walk to the NPC must complete first.
                time.sleep(3.6)
                _capture(output, "spoken")
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
            # Keep the flat fixture's native input position unchanged.
            answer_x = 192 + 240 * 2 + 16
            answer_y = 184 + (120 if nested or multispeaker else 130) * 2 + 16
            _click(330, 560)  # Re-select Talk to; SCUMM may reset the verb.
            _click(answer_x, answer_y)
            if multispeaker:
                # In stock ScummVM, actorSay uses the Actor's black speech
                # color, unlike the player's magenta answer caption. The
                # tested Actor position places its text in this clear strip
                # inside the room, where neither an answer object nor the
                # inherited verb GUI can produce black pixels.
                text_pixels = 0
                for _ in range(60):
                    if process.poll() is not None:
                        raise RuntimeError("ScummVM exited while the native Actor was speaking")
                    _capture(output, "speaker")
                    histogram = _run(["convert", str(output / "scummvm-speaker.png"),
                                      "-crop", "500x32+300+184", "+repage",
                                      "-format", "%c", "histogram:info:"])
                    text_pixels = count_color_pixels(histogram, (0, 0, 0))
                    if text_pixels >= 100:
                        break
                    time.sleep(0.25)
                report["speaker_text_pixels"] = text_pixels
                if text_pixels < 100:
                    raise RuntimeError("No distinct black native Actor speech after answer caption")
            if nested:
                nested_visible = False
                for _ in range(35):
                    _capture(output, "nested")
                    if (_answer_row_count(output, "nested", 120) < 10
                            and _answer_row_count(output, "nested", 100) >= 50):
                        nested_visible = True
                        break
                    time.sleep(0.35)
                if not nested_visible:
                    raise RuntimeError("Second-level answer objects did not replace first menu")
                report["nested_stage_visible"] = True
                _click(330, 560)
                _click(answer_x, 184 + 100 * 2 + 16)  # Back to first stage
                returned = False
                for _ in range(35):
                    _capture(output, "returned")
                    if (_answer_row_count(output, "returned", 120) >= 50
                            and _answer_row_count(output, "returned", 100) < 10):
                        returned = True
                        break
                    time.sleep(0.35)
                if not returned:
                    raise RuntimeError("Nested conversation did not return to entry menu")
                report["returned_to_first_stage"] = True
                _click(330, 560)
                _click(192 + 264 * 2 + 16, answer_y)  # Second root answer ends conversation
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
            if voice:
                report["selected_language"] = "de"
            return report
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if voice:
                pcm = pcm_path.read_bytes() if pcm_path.exists() else b""
                report["pcm_bytes"] = len(pcm)
                report["pcm_active_fraction"] = round(
                    sum(value not in (0, 128) for value in pcm) / len(pcm), 4) if pcm else 0.0
                report["voice_audible"] = report["pcm_bytes"] >= 8192 and report["pcm_active_fraction"] > 0.05
                if not report["voice_audible"]:
                    report["passed"] = False
            (output / "dialogue-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                           encoding="utf-8")


def main() -> int:
    voice = len(sys.argv) == 4 and sys.argv[1] == "--voice"
    nested = len(sys.argv) == 4 and sys.argv[1] == "--nested"
    multispeaker = len(sys.argv) == 4 and sys.argv[1] == "--multispeaker"
    linear_multispeaker = len(sys.argv) == 4 and sys.argv[1] == "--linear-multispeaker"
    gesture = len(sys.argv) == 4 and sys.argv[1] == "--gesture"
    if (len(sys.argv) != 3 and not voice and not nested and not multispeaker and not linear_multispeaker and not gesture):
        print("Usage: python -m adventure_studio.scumm_dialogue_probe [--voice|--nested|--multispeaker|--linear-multispeaker|--gesture] GAME_DIR OUTPUT_DIR")
        return 2
    report = run(Path(sys.argv[2] if voice or nested or multispeaker or linear_multispeaker or gesture else sys.argv[1]),
                 Path(sys.argv[3] if voice or nested or multispeaker or linear_multispeaker or gesture else sys.argv[2]),
                 voice=voice, nested=nested, multispeaker=multispeaker,
                 linear_multispeaker=linear_multispeaker or gesture, gesture=gesture)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

