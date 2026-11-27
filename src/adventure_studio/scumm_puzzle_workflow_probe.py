"""Play an authored counter + lever puzzle across a native room transition."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageChops

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_project import GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, duplicate_sequence_variant, replace_sequence_step

COLORS = ((191, 61, 220), (42, 195, 243), (215, 140, 27),
          (242, 38, 117), (44, 240, 149), (45, 130, 210))
COUNTER, LEVER, LEVER_ON, GATE, FEEDBACK, BLOCKED = COLORS
GOAL = (120, 70, 180)


def authored_project():
    room = scrolling_fixture()
    i = len(room.palette)
    def marker(name, x, color, alternate=None):
        return RoomHotspot(name, name, name, x, 100, 16, 16,
                           sprite_pixels=bytes([i+color])*256,
                           open_sprite_pixels=None if alternate is None else bytes([i+alternate])*256)
    room = replace(room, palette=(*room.palette, *COLORS),
                   hotspots=(marker("Counter", 210, 0), marker("Lever", 250, 1, 2),
                             marker("Gate", 290, 3), marker("Feedback", 350, 4, 5)),
                   use_rules=(), demo_walk_to_x=None, camera_cues=(CameraCue("set", x=320),),
                   ego_start_x=320)
    raw = canonical_json(GameDocument("NativePuzzleWorkflow", (room, destination_fixture())))
    def add(raw, obj, kind, target, value=None):
        return append_sequence_step(raw, "Harbor", obj, "Close", kind, None, None, target, value)
    raw = add(raw, "Counter", "Spielvariable ändern", "var:Count", 1)
    raw = add(raw, "Counter", "Objektzustand setzen", "Feedback", 1)
    raw = add(raw, "Lever", "Objektzustand setzen", "Lever", 2)
    raw = add(raw, "Lever", "Objektzustand setzen", "Feedback", 1)
    raw = add(raw, "Gate", "Objektzustand setzen", "Feedback", 2)
    raw = duplicate_sequence_variant(raw, "Harbor|Gate|Close", "var:Count", 2, ">=",
                                     "Lever", 2, "==", "and")
    raw = replace_sequence_step(raw, "Harbor|Gate|Close|var:Count|2|>=|and|Lever|==|2",
                                0, "Raum wechseln", None, None, "Cellar", None)
    return raw


def mask(image, rgb):
    bands = [band.point([255 if abs(n-target)<=7 else 0 for n in range(256)])
             for band,target in zip(image.split(),rgb)]
    return ImageChops.multiply(ImageChops.multiply(bands[0],bands[1]),bands[2])


def run(upstream, destination):
    build = destination / "build"
    build.mkdir(parents=True, exist_ok=True)
    raw = authored_project()
    (build/"project.json").write_text(raw, encoding="utf-8")
    doc = parse_document((build/"project.json").read_text(encoding="utf-8"))
    if canonical_json(doc) != raw:
        raise RuntimeError("Authoring project did not round-trip")
    export_document(doc, build/"resources")
    game_dir = compile_story_game(build, upstream, destination/"game")
    frames = destination/"screenshots"
    frames.mkdir(exist_ok=True)
    def capture(label):
        xwd, png = frames/f"{label}.xwd", frames/f"{label}.png"
        subprocess.run(["xwd","-root","-silent","-out",str(xwd)],check=True,timeout=10)
        subprocess.run(["convert",str(xwd),str(png)],check=True,timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB").crop((192,184,832,472))
    def count(image,rgb):
        return mask(image,rgb).histogram()[255]
    evidence = {}
    def await_color(label,rgb,minimum=100,absent=None):
        deadline = time.monotonic()+25
        stable = []
        i = 0
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited before "+label)
            i += 1
            name = f"{label}-{i:03d}"
            image = capture(name)
            pixels = count(image,rgb)
            other = count(image,absent) if absent is not None else 0
            if pixels>=minimum and other<40:
                stable.append({"frame":name,"pixels":pixels,"absent_pixels":other})
                if len(stable)==3:
                    evidence[label]=stable
                    return image
            else:
                stable=[]
            time.sleep(.15)
        raise RuntimeError("Native puzzle state missing: "+label)
    def click(label,rgb):
        image = await_color(label,rgb)
        bounds = mask(image,rgb).getbbox()
        x,y = (bounds[0]+bounds[2])/2+192,(bounds[1]+bounds[3])/2+184
        for px,py in ((234,563),(round(x),round(y))):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"],check=True,timeout=10)
            time.sleep(.2)
    with (frames/"scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],stdout=log,stderr=subprocess.STDOUT)
        try:
            await_color("initial",FEEDBACK,absent=BLOCKED)
            click("gate-before-count",GATE)
            await_color("blocked-initial",BLOCKED,absent=FEEDBACK)
            click("first-counter",COUNTER)
            await_color("first-count",FEEDBACK,absent=BLOCKED)
            click("second-counter",COUNTER)
            # Confirm both actions ran: the first and second clicks are separated
            # by a gate denial; final success after exactly two clicks proves count.
            time.sleep(2)
            click("gate-with-count-only",GATE)
            await_color("blocked-with-count-only",BLOCKED,absent=FEEDBACK)
            click("enable-lever",LEVER)
            await_color("lever-on",LEVER_ON,absent=LEVER)
            await_color("feedback-reset",FEEDBACK,absent=BLOCKED)
            click("gate-with-both-conditions",GATE)
            await_color("goal-room",GOAL,minimum=40000,absent=GATE)
            report={"native_puzzle_workflow_verified":True,"evidence":evidence}
            (destination/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            return report
        finally:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait(timeout=5)


if __name__=="__main__":
    print(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
