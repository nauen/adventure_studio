"""Native depth ordering of two overlapping room Actors, including Escape."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_launch import colored_item_center, colored_item_pixels
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, set_sequence_skippable

COLORS = ((242, 38, 117), (44, 240, 149))
MARKERS = ((191, 61, 220), (42, 195, 243))


def run(upstream, destination):
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    room = scrolling_fixture()
    index = len(room.palette)
    triggers = tuple(RoomHotspot(name, name, name, x, 100, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("Front", 260), ("Reset", 300))))
    room = replace(room, palette=(*room.palette, *MARKERS),
                   hotspots=(*room.hotspots, *triggers), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costumes = []
    actors = []
    for i, (name, y) in enumerate((("BackActor", 85), ("FrontActor", 91))):
        costume = gesture_fixture()
        palette = list(costume.palette)
        palette[17] = palette[18] = COLORS[i]
        costume = replace(costume, name=name+"Costume", palette=tuple(palette))
        costumes.append(costume)
        actors.append(ActorAsset(name, costume.name, "Harbor", 400, y, "S"))
    raw = canonical_json(GameDocument("NativeActorLayer", (room, destination_fixture()),
                                      tuple(costumes), tuple(actors)))
    raw = append_sequence_step(raw, "Harbor", "Front", "Close", "Actor Zeichenebene",
                               "BackActor", None, None, -1)
    for kind, who, target, amount in (
            ("Objektzustand setzen", None, "Reset", 0),
            ("Warten", None, None, 12),
            ("Actor Zeichenebene", "BackActor", None, 0)):
        raw = append_sequence_step(raw, "Harbor", "Reset", "Close", kind, who, None, target, amount)
    raw = set_sequence_skippable(raw, "Harbor|Reset|Close", True)
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
        with Image.open(png) as image:
            pixels = list(image.convert("RGB").crop((660, 320, 684, 348)).getdata())
        return [sum(all(abs(a-b) <= 4 for a,b in zip(pixel, color)) for pixel in pixels)
                for color in COLORS]

    def click(label, color):
        x,y = colored_item_center(frames, label, color, fuzz_percent=4)
        for px,py in ((234,563),(x,y)):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"], check=True, timeout=10)
            time.sleep(.2)

    def await_order(label, actor, timeout=25):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during depth interaction")
            counts = capture(label)
            if counts[actor] >= 250 and counts[1-actor] < 40:
                return counts
            time.sleep(.2)
        raise RuntimeError(f"Native actor overlap order missing: {label}: {counts}")

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            initial = await_order("initial", 1)
            click("initial", MARKERS[0])
            front = await_order("front", 0)
            click("front", MARKERS[1])
            deadline = time.monotonic()+20
            while time.monotonic() < deadline:
                capture("reset-start")
                if colored_item_pixels(frames, "reset-start", MARKERS[1]) < 40:
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Native reset cutscene did not begin")
            started = time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"], check=True, timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"], check=True, timeout=5)
            restored = await_order("restored", 1, timeout=8)
            report = {"initial":initial,"front":front,"restored":restored,
                      "escape_elapsed":time.monotonic()-started,
                      "native_actor_layer_verified":True}
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
