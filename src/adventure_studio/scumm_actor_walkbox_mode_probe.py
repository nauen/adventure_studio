"""Compare constrained and unconstrained native Actor movement in one room."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, author_room_walkbox, set_sequence_skippable

ACTOR = (242, 38, 117)
MARKERS = ((191, 61, 220), (42, 195, 243), (45, 240, 149), (210, 110, 32))


def run(upstream, destination):
    build = destination / "build"
    room = scrolling_fixture()
    index = len(room.palette)
    # Keep the complete object sprite within the 144-pixel SCUMM viewport.
    controls = tuple(RoomHotspot(name, name, name, x, 120, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("Constrained", 210), ("FreeWalk", 250),
                                                    ("Restore", 290), ("CheckFollow", 330))))
    room = replace(room, palette=(*room.palette, *MARKERS),
                   hotspots=(*room.hotspots, *controls), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=280)
    costume = gesture_fixture()
    palette = list(costume.palette)
    palette[17] = palette[18] = ACTOR
    costume = replace(costume, name="NativeWalkboxModeCostume", palette=tuple(palette))
    raw = canonical_json(GameDocument("NativeWalkboxMode", (room, destination_fixture()),
                                      (costume,), (ActorAsset("Guide", costume.name, "Harbor", 280, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "200,70; 370,70; 370,150; 200,150")
    for trigger, mode in (("Constrained", "Actor folgt Walkboxen"), ("FreeWalk", "Actor ignoriert Walkboxen")):
        for kind, x, y in ((mode, None, None), ("Actor versetzen", 280, 85),
                            ("Actor laufen lassen", 440, 85), ("Auf Actor warten", None, None)):
            raw = append_sequence_step(raw, "Harbor", trigger, "Close", kind,
                                       "Guide", None, None, None, x, y)
    for kind, who, target, amount in (("Objektzustand setzen", None, "Restore", 0),
                                       ("Warten", None, None, 12),
                                       ("Actor folgt Walkboxen", "Guide", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Restore", "Close", kind, who, None, target, amount)
    raw = set_sequence_skippable(raw, "Harbor|Restore|Close", True)
    for kind, x, y in (("Actor versetzen", 280, 85), ("Actor laufen lassen", 440, 85),
                       ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "CheckFollow", "Close", kind,
                                   "Guide", None, None, None, x, y)
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    game_dir = compile_story_game(build, upstream, destination / "game")
    frames = destination / "screenshots"
    frames.mkdir(exist_ok=True)

    def capture(label):
        xwd = frames / f"scummvm-{label}.xwd"
        png = frames / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(png)], check=True, timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB").crop((192, 184, 832, 472))

    def center(image, rgb):
        points = [(i % image.width, i // image.width) for i, pixel in enumerate(image.getdata())
                  if all(abs(a-b) <= 7 for a,b in zip(pixel, rgb))]
        if len(points) < 100:
            return None
        xs, ys = zip(*points)
        return (min(xs)+max(xs))/2, (min(ys)+max(ys))/2

    def sample(label):
        image = capture(label)
        # Ego walks at y=130 and can share this RGB. Only the authored
        # Actor's y=85 costume lane is measured (screen y=280..365).
        actor = center(image.crop((0, 96, image.width, 181)), ACTOR)
        anchor = center(image, MARKERS[0])
        return None if actor is None or anchor is None else 218+(actor[0]-anchor[0])/2

    def click(label, color):
        point = center(capture(label), color)
        if point is None:
            raise RuntimeError(f"Native interaction target missing: {label}")
        for x,y in ((234,563),(round(point[0]+192),round(point[1]+184))):
            subprocess.run(["xdotool","mousemove",str(x),str(y),"click","1"], check=True, timeout=10)
            time.sleep(.2)

    def await_stable(label, predicate, timeout=25):
        deadline = time.monotonic()+timeout
        positions = []
        while time.monotonic() < deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during walkbox mode test")
            x = sample(label)
            positions = (positions+[x])[-8:] if x is not None and predicate(x) else []
            if len(positions)==8 and max(positions)-min(positions)<4:
                return positions
            time.sleep(.25)
        raise RuntimeError(f"Native walkbox mode not observed: {label}, last position {x}")

    with (frames / "scummvm.log").open("w", encoding="utf-8") as log:
        game = subprocess.Popen(["scummvm", f"--path={game_dir.resolve()}", "tentacle"],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            await_stable("initial", lambda x: abs(x-280)<12)
            click("constrained-click", MARKERS[0])
            constrained = await_stable("constrained", lambda x: 350<x<380)
            click("free-click", MARKERS[1])
            free = await_stable("free", lambda x: abs(x-440)<12)
            click("restore-click", MARKERS[2])
            deadline = time.monotonic()+20
            while time.monotonic() < deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM exited before Escape during walkbox restore")
                if center(capture("restore-start"), MARKERS[2]) is None:
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Native restore cutscene did not begin")
            started = time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"], check=True, timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"], check=True, timeout=5)
            time.sleep(.5)
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during Escape walkbox restore")
            click("check-follow-click", MARKERS[3])
            restored = await_stable("restored", lambda x: 350<x<380)
            report = {"constrained": constrained, "free": free, "restored": restored,
                      "escape_to_follow_check_seconds":time.monotonic()-started,
                      "native_actor_walkbox_mode_verified":True}
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
