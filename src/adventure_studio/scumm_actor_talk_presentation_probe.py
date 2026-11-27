"""Observe two authored native subtitle colors and offsets, including Escape."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_actor_zclip_transfer_probe import author_transfer_project
from .scumm_assets import RoomHotspot
from .scumm_launch import colored_item_center, colored_item_pixels
from .scumm_project import SoundAsset, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .scumm_two_actor_four_mask_probe import ACTOR_IDS
from .scumm_voc_fixture import original_voc_effect
from .studio_sequences import append_sequence_step, set_sequence_skippable

COLORS = ((248, 40, 116), (45, 245, 151))
MARKER = (191, 61, 220)
LINE = "I can speak here."


def run(upstream, destination):
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    doc = parse_document(author_transfer_project(destination, "transparent"))
    harbor = next(room for room in doc.rooms if room.name == "Harbor")
    first = len(harbor.palette)
    marker = RoomHotspot("TalkObserve", "Observe voice", "Observe voice",
                         285, 100, 16, 16, sprite_pixels=bytes([first + 2]) * 256)
    harbor = replace(harbor, palette=(*harbor.palette, *COLORS, MARKER),
                     hotspots=(*harbor.hotspots, marker),
                     demo_walk_to_x=None, demo_walk_to_y=None)
    doc = replace(doc, rooms=tuple(harbor if room.name == "Harbor" else room for room in doc.rooms),
                  interaction_sequences=tuple(seq for seq in doc.interaction_sequences
                      if (seq.room, seq.hotspot_id, seq.verb) != ("Harbor", "Key", "Close")),
                  sound_assets=(*doc.sound_assets, SoundAsset("TalkVoice", "Harbor",
                      original_voc_effect(duration_ms=8000))))
    actor = ACTOR_IDS[0]
    raw = canonical_json(doc)
    for kind, who, target, amount, x, y, subtitle in (
        ("Actor Sprechfarbe", actor, None, first, None, None, None),
        ("Actor Sprechtext-Position", actor, None, None, -24, -16, None),
        ("Gesprochene Zeile", actor, "TalkVoice", None, None, None, LINE),
        ("Warten", None, None, 20, None, None, None),
        ("Actor Sprechfarbe", actor, None, first + 1, None, None, None),
        ("Actor Sprechtext-Position", actor, None, None, 24, -40, None),
    ):
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", kind,
                                   who, None, target, amount, x, y, subtitle=subtitle)
    raw = set_sequence_skippable(raw, "Harbor|Key|Close", True)
    raw = append_sequence_step(raw, "Harbor", "TalkObserve", "Close",
                               "Gesprochene Zeile", actor, None, "TalkVoice", None, subtitle=LINE)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), resources)
    game_dir = compile_story_game(build, upstream, destination / "game")
    frames = destination / "screenshots"
    frames.mkdir(exist_ok=True)

    def capture(label):
        xwd = frames / f"scummvm-{label}.xwd"
        png = frames / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(png)], check=True, timeout=10)
        xwd.unlink()
        return png

    def measure(png, color):
        with Image.open(png) as source:
            image = source.convert("RGB").crop((192, 184, 832, 472))
            points = [(i % image.width, i // image.width)
                      for i, pixel in enumerate(image.getdata())
                      if all(abs(a-b) <= 3 for a,b in zip(pixel, color))]
        if not points:
            return {"pixels": 0, "bounds": None}
        xs, ys = zip(*points)
        return {"pixels": len(points), "bounds": [min(xs), min(ys), max(xs), max(ys)]}

    def click(color, label):
        x, y = colored_item_center(frames, label, color, fuzz_percent=4)
        for px, py in ((234, 563), (x, y)):
            subprocess.run(["xdotool", "mousemove", str(px), str(py), "click", "1"],
                           check=True, timeout=10)
            time.sleep(.2)

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                png = capture("before")
                if (colored_item_pixels(frames, "before", (255, 220, 75)) >= 10
                        and colored_item_pixels(frames, "before", MARKER) >= 40):
                    break
                if game.poll() is not None:
                    raise RuntimeError("ScummVM exited before subtitle interaction")
                time.sleep(.3)
            else:
                raise RuntimeError("Native subtitle interaction targets missing")
            baseline = [measure(png, color) for color in COLORS]
            if any(row["pixels"] for row in baseline):
                raise RuntimeError("Subtitle colors already occur in the idle scene")

            def await_text(label, color, timeout):
                end = time.monotonic() + timeout
                while time.monotonic() < end:
                    if game.poll() is not None:
                        raise RuntimeError("ScummVM exited during subtitle interaction")
                    row = measure(capture(label), color)
                    if row["pixels"] >= 40:
                        return row
                    time.sleep(.15)
                raise RuntimeError(f"Native subtitle color not observed: {label}")

            click((255, 220, 75), "before")
            initial = await_text("speaking-first", COLORS[0], 20)
            started = time.monotonic()
            subprocess.run(["xdotool", "keydown", "Escape"], check=True, timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool", "keyup", "Escape"], check=True, timeout=5)
            time.sleep(1)
            capture("after-escape")
            click(MARKER, "after-escape")
            final = await_text("speaking-final", COLORS[1], 10)
            elapsed = time.monotonic() - started
            dx = (final["bounds"][0] + final["bounds"][2]
                  - initial["bounds"][0] - initial["bounds"][2]) / 2
            dy = (final["bounds"][1] + final["bounds"][3]
                  - initial["bounds"][1] - initial["bounds"][3]) / 2
            report = {"before": baseline, "initial": initial, "after_escape": final,
                      "dx": dx, "dy": dy, "escape_elapsed": elapsed,
                      "native_actor_talk_presentation_verified": dx >= 40 and dy <= -20 and elapsed < 18}
            (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            if not report["native_actor_talk_presentation_verified"]:
                raise RuntimeError(f"Native subtitle position or Escape not demonstrated: {report}")
            return report
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
