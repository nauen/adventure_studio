"""Exercise native unvoiced puzzle clues, message wait and Escape."""
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
from .studio_sequences import append_sequence_step, author_room_walkbox, set_sequence_skippable

NORMAL = (191, 61, 220)
SKIP = (42, 195, 243)
READY = (215, 140, 27)
DONE = (45, 130, 210)
TEXT = (248, 40, 116)
LINE = "The locked gate needs two switches. Look for the second switch in the cellar."


def authored_project():
    room = scrolling_fixture()
    first = len(room.palette)
    markers = (
        RoomHotspot("Clue", "Read clue", "Read clue", 210, 120, 16, 16,
                    sprite_pixels=bytes([first])*256),
        RoomHotspot("SkipClue", "Repeat clue", "Repeat clue", 250, 120, 16, 16,
                    sprite_pixels=bytes([first+1])*256),
        RoomHotspot("Progress", "Puzzle progress", "Puzzle progress", 350, 120, 16, 16,
                    sprite_pixels=bytes([first+2])*256, open_sprite_pixels=bytes([first+3])*256),
    )
    room = replace(room, palette=(*room.palette, NORMAL, SKIP, READY, DONE, TEXT),
                   hotspots=markers, use_rules=(), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costume = gesture_fixture()
    frame = costume.frames[0]
    directions = tuple(CostumeDirection(d, (frame.id,)) for d in ("N","E","S","W"))
    costume = replace(costume, name="NativeTextClueCostume", animations=tuple(CostumeAnimation(name, directions)
                      for name in ("init", "stand", "walk", "talkStart", "talkStop")))
    raw = canonical_json(GameDocument("NativeTextClue", (room, destination_fixture()),
                         (costume,), (ActorAsset("Guide", costume.name, "Harbor", 280, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "160,70; 480,70; 480,150; 160,150")
    for hotspot, state in (("Clue",2), ("SkipClue",1)):
        raw = append_sequence_step(raw, "Harbor", hotspot, "Close",
                                   "Actor Sprechfarbe", "Guide", None, None, first+4)
        raw = append_sequence_step(raw, "Harbor", hotspot, "Close",
                                   "Textzeile ohne Audio", "Guide", None, None, None, subtitle=LINE)
        raw = append_sequence_step(raw, "Harbor", hotspot, "Close",
                                   "Objektzustand setzen", None, None, "Progress", state)
    raw = set_sequence_skippable(raw, "Harbor|SkipClue|Close", True)
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
    def wait(label, state, text_visible, timeout=25, samples=3):
        deadline=time.monotonic()+timeout
        rows=[]
        i=0
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during "+label)
            i+=1
            name=f"{label}-{i:03d}"
            image=capture(name)
            text_pixels=count(image,TEXT)
            state_pixels=count(image,state)
            other=count(image,DONE if state==READY else READY)
            if state_pixels>=100 and other<40 and (text_pixels>=40 if text_visible else text_pixels==0):
                rows.append({"frame":name,"text_pixels":text_pixels,"state_pixels":state_pixels,
                             "opposite_state_pixels":other})
                if len(rows)==samples:
                    evidence[label]=rows
                    return image
            else:
                rows=[]
            time.sleep(.1)
        raise RuntimeError(f"Native text/state missing: {label}")
    def click(label, color):
        image=capture(label)
        bounds=mask(image,color).getbbox()
        if bounds is None or count(image,color)<100:
            raise RuntimeError("Native clue target absent: "+label)
        x,y=(bounds[0]+bounds[2])/2+192,(bounds[1]+bounds[3])/2+184
        for px,py in ((234,563),(round(x),round(y))):
            subprocess.run(["xdotool","mousemove",str(px),str(py),"click","1"],check=True,timeout=10)
            time.sleep(.2)
    with (frames/"scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],
                              stdout=log,stderr=subprocess.STDOUT)
        try:
            wait("idle",READY,False)
            click("normal-click",NORMAL)
            wait("visible-unvoiced-clue",READY,True)
            wait("normal-completion",DONE,False)
            click("skip-click",SKIP)
            wait("visible-before-escape",DONE,True)
            started=time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"],check=True,timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"],check=True,timeout=5)
            wait("escape-completion",READY,False,timeout=8)
            report={"native_text_interaction_verified":True,"audio_assets":0,
                    "escape_seconds":time.monotonic()-started,"evidence":evidence}
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
