"""Observe real native walk interruption, stability and subsequent movement."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_launch import colored_item_center, colored_item_pixels
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, set_sequence_skippable

ACTOR = (242, 38, 117)
CONTROLS = ((191, 61, 220), (42, 195, 243), (45, 240, 149))


def run(upstream, destination):
    build = destination / "build"
    room = scrolling_fixture()
    index = len(room.palette)
    controls = tuple(RoomHotspot(name, name, name, x, 115, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("StopNormal", 250), ("StopEscape", 290), ("Resume", 330))))
    room = replace(room, palette=(*room.palette, *CONTROLS),
                   hotspots=(*room.hotspots, *controls), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=280)
    costume = gesture_fixture()
    palette = list(costume.palette)
    palette[17] = palette[18] = ACTOR
    costume = replace(costume, name="NativeStopCostume", palette=tuple(palette))
    raw = canonical_json(GameDocument("NativeActorStop", (room, destination_fixture()),
                                      (costume,), (ActorAsset("Guide", costume.name, "Harbor", 180, 85, "S"),)))
    for trigger, delay in (("StopNormal", 1), ("StopEscape", 12)):
        for kind, amount, x, y in (("Actor versetzen", None, 180, 85),
                                   ("Actor laufen lassen", None, 470, 85),
                                   ("Warten", delay, None, None),
                                   ("Actor stoppen", None, None, None)):
            raw = append_sequence_step(raw, "Harbor", trigger, "Close", kind,
                                       None if kind == "Warten" else "Guide", None, None, amount, x, y)
        if trigger == "StopEscape":
            raw = set_sequence_skippable(raw, "Harbor|StopEscape|Close", True)
    raw = append_sequence_step(raw, "Harbor", "Resume", "Close", "Actor laufen lassen",
                               "Guide", None, None, None, 455, 85)
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    game_dir = compile_story_game(build, upstream, destination / "game")
    frames = destination / "screenshots"
    frames.mkdir(exist_ok=True)

    def capture(label):
        xwd = frames / f"scummvm-{label}.xwd"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(frames / f"scummvm-{label}.png")], check=True, timeout=10)
        xwd.unlink()

    def position(label):
        capture(label)
        if colored_item_pixels(frames, label, ACTOR) < 100:
            return None
        x, _ = colored_item_center(frames, label, ACTOR, fuzz_percent=4)
        anchor, _ = colored_item_center(frames, label, CONTROLS[0], fuzz_percent=4)
        return 258 + (x-anchor)/2

    def click(label, color):
        capture(label)
        x, y = colored_item_center(frames, label, color, fuzz_percent=4)
        for px, py in ((234,563),(x,y)):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"], check=True, timeout=10)

    def await_position(label, predicate, timeout=20):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during native walk")
            try:
                x = position(label)
                if x is not None and predicate(x):
                    return x
            except ValueError:
                pass
            time.sleep(.10)
        raise RuntimeError(f"Native Actor position missing: {label}")

    def stationary(label):
        values = []
        for i in range(10):
            values.append(await_position(f"{label}-{i:02d}", lambda x: True))
            time.sleep(.25)
        if max(values)-min(values) > 4 or not 195 < values[-1] < 445:
            raise RuntimeError(f"Actor did not stop before destination: {values}")
        return values

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            await_position("before", lambda x: abs(x-180)<12)
            time.sleep(1)
            click("normal-click", CONTROLS[0])
            await_position("normal-moving", lambda x: 205<x<440)
            time.sleep(1.5)
            normal = stationary("normal-stopped")
            click("escape-click", CONTROLS[1])
            await_position("escape-moving", lambda x: 195<x<230)
            subprocess.run(["xdotool","keydown","Escape"], check=True, timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"], check=True, timeout=5)
            time.sleep(.5)
            escaped = stationary("escape-stopped")
            click("resume-click", CONTROLS[2])
            resumed = await_position("resumed", lambda x: abs(x-455)<10)
            report = {"normal":normal, "escaped":escaped, "resumed_x":resumed,
                      "native_actor_stop_verified":True}
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
