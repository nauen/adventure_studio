"""R07: author IM03 and cycle through three real SCUMM object images."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_launch import authored_item_center, colored_item_pixels
from .scumm_project import GameDocument, canonical_json, parse_document, export_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, import_object_third_image, set_sequence_condition

COLORS = ((241, 35, 120), (45, 240, 149), (192, 65, 237))
TRIGGER = (255, 220, 75)


def native_verbs_visible(image):
    """An image drawn during room entry alone is not an interactive scene."""
    if image.size != (1024, 768):
        return False
    rgb = image.convert("RGB")
    # Same stock verb-area readiness check as the native two-Actor probe.
    return sum(1 for y in range(535, 635, 4)
               for x in range(200, 820, 4)
               if max(rgb.getpixel((x, y))) > 35) >= 15


def run(upstream, destination):
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    room = scrolling_fixture()
    first = len(room.palette)
    target = RoomHotspot("ImagePanel", "the panel", "A three-state panel.", 420, 75, 32, 32,
                         sprite_pixels=bytes([first])*1024, open_sprite_pixels=bytes([first+1])*1024)
    room = replace(room, palette=(*room.palette, *COLORS), hotspots=(*room.hotspots, target),
                   demo_walk_to_x=None, camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    raw = canonical_json(GameDocument("ThirdImage", (room, destination_fixture())))
    png = destination / "third.png"
    Image.new("RGB", (32, 32), COLORS[2]).save(png)
    raw = import_object_third_image(raw, "Harbor", "ImagePanel", str(png))
    for current, next_state in ((1, 2), (2, 3), (3, 1)):
        raw = append_sequence_step(raw, "Harbor", "Key", "Close", "Objektzustand setzen",
                                   None, None, "ImagePanel", next_state)
        raw = set_sequence_condition(raw, "Harbor|Key|Close", "ImagePanel", current)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), resources)
    game_dir = compile_story_game(build, upstream, destination / "game")
    frames = destination / "screenshots"
    frames.mkdir(exist_ok=True)

    def capture(label):
        xwd = frames / f"scummvm-{label}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(frames / f"scummvm-{label}.png")], check=True, timeout=10)
        xwd.unlink()

    def await_state(label, state):
        deadline = time.monotonic() + 30
        counts = []
        ready = False
        while time.monotonic() < deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited before object state was visible")
            capture(label)
            counts = [colored_item_pixels(frames, label, color) for color in COLORS]
            with Image.open(frames / f"scummvm-{label}.png") as image:
                ready = native_verbs_visible(image)
            if (ready and counts[state-1] >= 1000
                    and all(n < 40 for i,n in enumerate(counts) if i != state-1)):
                try:
                    x, y = authored_item_center(frames, label, TRIGGER)
                except ValueError:
                    # Entry can render the background and panel before the Key.
                    time.sleep(.25)
                    continue
                return {"state": state, "color_pixels": counts, "frame": label,
                        "native_trigger": [x, y]}
            time.sleep(.25)
        raise RuntimeError(f"Expected interactive native IM0{state}: {counts}, verbs={ready}")

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            results = [await_state("initial", 1)]
            for label, state in (("second", 2), ("third", 3), ("restored", 1)):
                x, y = results[-1]["native_trigger"]
                for px, py in ((234, 563), (x, y)):
                    subprocess.run(["xdotool", "mousemove", str(px), str(py), "click", "1"],
                                   check=True, timeout=10)
                    time.sleep(.2)
                results.append(await_state(label, state))
                time.sleep(.5)
            report = {"states": results, "native_im03_verified": True}
            (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
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
