"""Observe two distinct native LookAt descriptions around an authored puzzle state change."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume import CostumeAnimation, CostumeDirection
from .scumm_costume_probe import gesture_fixture
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_puzzle_workflow_probe import mask
from .scumm_toolchain import compile_story_game
from .studio_sequences import (append_sequence_step, author_room_walkbox,
                               duplicate_sequence_variant, replace_sequence_step)

NORMAL = (191, 61, 220)
SKIP = (42, 195, 243)
READY = (215, 140, 27)
DONE = (45, 130, 210)
TEXT = (248, 40, 116)
SOLVED_TEXT = (44, 240, 149)
LINE = "The locked gate needs a switch. Look for the switch next to the gate."
SOLVED_LINE = "The switch has been activated. The gate is unlocked and the passage is ready."


def authored_project():
    room = scrolling_fixture()
    first = len(room.palette)
    markers = (
        RoomHotspot("Clue", "Read clue", "Read clue", 210, 120, 16, 16,
                    sprite_pixels=bytes([first])*256),
        RoomHotspot("Switch", "Switch", "Switch", 250, 120, 16, 16,
                    sprite_pixels=bytes([first+1])*256),
        RoomHotspot("Progress", "Puzzle progress", "Puzzle progress", 350, 120, 16, 16,
                    sprite_pixels=bytes([first+2])*256, open_sprite_pixels=bytes([first+3])*256),
    )
    room = replace(room, palette=(*room.palette, NORMAL, SKIP, READY, DONE, TEXT, SOLVED_TEXT),
                   hotspots=markers, use_rules=(), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costume = gesture_fixture()
    frame = costume.frames[0]
    directions = tuple(CostumeDirection(d, (frame.id,)) for d in ("N","E","S","W"))
    costume = replace(costume, name="NativeContextualLookCostume", animations=tuple(CostumeAnimation(name, directions)
                      for name in ("init", "stand", "walk", "talkStart", "talkStop")))
    raw = canonical_json(GameDocument("NativeContextualLook", (room, destination_fixture()),
                         (costume,), (ActorAsset("Guide", costume.name, "Harbor", 280, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "160,70; 480,70; 480,150; 160,150")
    raw = append_sequence_step(raw, "Harbor", "Clue", "LookAt",
                               "Actor Sprechfarbe", "Guide", None, None, first+4)
    raw = append_sequence_step(raw, "Harbor", "Clue", "LookAt",
                               "Textzeile ohne Audio", "Guide", None, None, None, subtitle=LINE)
    raw = duplicate_sequence_variant(raw, "Harbor|Clue|LookAt", "Progress", 2)
    raw = replace_sequence_step(raw, "Harbor|Clue|LookAt|Progress|2", 0,
                                "Actor Sprechfarbe", "Guide", None, None, first+5)
    raw = replace_sequence_step(raw, "Harbor|Clue|LookAt|Progress|2", 1,
                                "Textzeile ohne Audio", "Guide", None, None, None, subtitle=SOLVED_LINE)
    raw = append_sequence_step(raw, "Harbor", "Switch", "Close",
                               "Objektzustand setzen", None, None, "Progress", 2)
    return raw


def run(upstream, destination):
    build = destination/"build"
    build.mkdir(parents=True, exist_ok=True)
    raw = authored_project()
    (build/"project.json").write_text(raw, encoding="utf-8")
    doc = parse_document((build/"project.json").read_text(encoding="utf-8"))
    if canonical_json(doc) != raw or doc.sound_assets:
        raise RuntimeError("Text-only authoring must round-trip without audio assets")
    export_document(doc, build/"resources")
    game_dir = compile_story_game(build, upstream, destination/"game")
    frames = destination/"screenshots"
    frames.mkdir(exist_ok=True)
    evidence = {}
    def capture(label):
        xwd, png = frames/f"{label}.xwd", frames/f"{label}.png"
        subprocess.run(["xwd","-root","-silent","-out",str(xwd)],check=True,timeout=10)
        subprocess.run(["convert",str(xwd),str(png)],check=True,timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB").crop((192,184,832,472))
    def count(image, rgb):
        return mask(image,rgb).histogram()[255]
    def wait(label, state, text_color=None, timeout=25, samples=3):
        deadline=time.monotonic()+timeout
        rows=[]
        i=0
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during "+label)
            i+=1
            name=f"{label}-{i:03d}"
            image=capture(name)
            first_pixels=count(image,TEXT)
            solved_pixels=count(image,SOLVED_TEXT)
            text_pixels=first_pixels if text_color==TEXT else solved_pixels if text_color==SOLVED_TEXT else 0
            wrong_pixels=solved_pixels if text_color==TEXT else first_pixels if text_color==SOLVED_TEXT else first_pixels+solved_pixels
            state_pixels=count(image,state)
            other=count(image,DONE if state==READY else READY)
            if state_pixels>=100 and other<40 and wrong_pixels==0 and (text_color is None or text_pixels>=40):
                rows.append({"frame":name,"text_pixels":text_pixels,"state_pixels":state_pixels,
                             "opposite_state_pixels":other,"wrong_text_pixels":wrong_pixels})
                if len(rows)==samples:
                    evidence[label]=rows
                    return image
            else:
                rows=[]
            time.sleep(.1)
        raise RuntimeError(f"Native text/state missing: {label}")
    def click(label, color, look=False):
        image=capture(label)
        bounds=mask(image,color).getbbox()
        if bounds is None or count(image,color)<100:
            raise RuntimeError("Native clue target absent: "+label)
        x,y=(bounds[0]+bounds[2])/2+192,(bounds[1]+bounds[3])/2+184
        for px,py in (((330,532) if look else (234,563)),(round(x),round(y))):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"],check=True,timeout=10)
            time.sleep(.2)
    with (frames/"scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],
                              stdout=log,stderr=subprocess.STDOUT)
        try:
            wait("idle",READY)
            click("look-before-switch",NORMAL,look=True)
            wait("unsolved-description",READY,TEXT)
            wait("unsolved-text-ended",READY)
            click("activate-switch",SKIP)
            wait("switch-activated",DONE)
            click("look-after-switch",NORMAL,look=True)
            wait("solved-description",DONE,SOLVED_TEXT)
            wait("solved-text-ended",DONE)
            report={"native_contextual_look_verified":True,"evidence":evidence}
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
