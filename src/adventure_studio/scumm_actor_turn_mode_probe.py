"""Observe native walking with locked and restored automatic facing."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from .scumm_assets import CameraCue, RoomHotspot, scrolling_fixture, destination_fixture
from .scumm_costume import CostumeDirection
from .scumm_costume_probe import gesture_fixture
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, author_room_walkbox, set_sequence_skippable

DIRECTIONS = ("N", "E", "S", "W")
COLORS = ((215, 140, 27), (44, 240, 149), (242, 38, 117), (132, 85, 245))
MARKERS = ((191, 61, 220), (42, 195, 243), (45, 130, 210))


def run(upstream, destination):
    build = destination / "build"
    room = scrolling_fixture()
    index = len(room.palette)
    controls = tuple(RoomHotspot(name, name, name, x, 130, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("LockedWalk", 210), ("Unlock", 250),
                                                    ("CheckTurn", 290))))
    room = replace(room, palette=(*room.palette, *MARKERS),
                   hotspots=(*room.hotspots, *controls), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costume = gesture_fixture()
    palette = list(costume.palette)
    for i, color in enumerate(COLORS):
        palette[17+i] = color
    base = costume.frames[0]
    poses = tuple(replace(base, id=f"Turn{d}", pixels=bytes([i+1])*(base.width*base.height))
                  for i,d in enumerate(DIRECTIONS))
    directional = tuple(CostumeDirection(d, (f"Turn{d}",)) for d in DIRECTIONS)
    costume = replace(costume, name="NativeTurnModeCostume", palette=tuple(palette),
                      frames=poses, animations=tuple(replace(a, directions=directional)
                      for a in costume.animations if a.name in ("walk","stand","init")))
    raw = canonical_json(GameDocument("NativeTurnMode", (room, destination_fixture()),
                                      (costume,), (ActorAsset("Guide", costume.name, "Harbor", 280, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "160,70; 480,70; 480,150; 160,150")
    for kind, x, y in (("Actor Drehung sperren", None, None),
                       ("Actor laufen lassen", 440, 85), ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "LockedWalk", "Close", kind,
                                   "Guide", None, None, None, x, y)
    for kind, who, target, amount in (("Objektzustand setzen", None, "Unlock", 0),
                                       ("Warten", None, None, 12),
                                       ("Actor Drehung freigeben", "Guide", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Unlock", "Close", kind, who, None, target, amount)
    raw = set_sequence_skippable(raw, "Harbor|Unlock|Close", True)
    for kind, x, y in (("Actor versetzen", 280, 85), ("Actor laufen lassen", 440, 85),
                       ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "CheckTurn", "Close", kind,
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

    def points(image, rgb):
        return [(i % image.width, i // image.width) for i,pixel in enumerate(image.getdata())
                if all(abs(a-b) <= 7 for a,b in zip(pixel,rgb))]

    def center(points):
        if len(points)<100:
            return None
        xs,ys=zip(*points)
        return (min(xs)+max(xs))/2,(min(ys)+max(ys))/2

    def click(label,color):
        point=center(points(capture(label),color))
        if point is None:
            raise RuntimeError(f"Native interaction target missing: {label}")
        for x,y in ((234,563),(round(point[0]+192),round(point[1]+184))):
            subprocess.run(["xdotool","mousemove",str(x),str(y),"click","1"],check=True,timeout=10)
            time.sleep(.2)

    def await_pose(label, target_x, direction, timeout=25):
        deadline=time.monotonic()+timeout
        samples=[]
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during direction lock")
            image=capture(label)
            anchor=center(points(image,MARKERS[0]))
            colored=[points(image,c) for c in COLORS]
            actor=center(colored[DIRECTIONS.index(direction)])
            counts=[len(p) for p in colored]
            if anchor is not None and actor is not None:
                x=218+(actor[0]-anchor[0])/2
                if abs(x-target_x)<10 and all(n<40 for i,n in enumerate(counts)
                                              if DIRECTIONS[i]!=direction):
                    samples.append({"x":x,"direction":direction,"pixels":counts})
                    if len(samples)==5:
                        return samples
                else:
                    samples=[]
            else:
                samples=[]
            time.sleep(.25)
        raise RuntimeError(f"Native pose missing: {label}; color counts {counts}")

    with (frames / "scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],
                              stdout=log,stderr=subprocess.STDOUT)
        try:
            initial=await_pose("initial",280,"S")
            click("lock-click",MARKERS[0])
            locked=await_pose("locked-arrival",440,"S")
            click("unlock-click",MARKERS[1])
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if center(points(capture("unlock-start"),MARKERS[1])) is None:
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Native unlock cutscene did not begin")
            started=time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"],check=True,timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"],check=True,timeout=5)
            time.sleep(.5)
            click("check-click",MARKERS[2])
            restored=await_pose("unlocked-arrival",440,"E")
            report={"initial":initial,"locked":locked,"restored":restored,
                    "escape_to_arrival_seconds":time.monotonic()-started,
                    "native_actor_turn_mode_verified":True}
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
