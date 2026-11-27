"""Observe actual stand poses after native walks, including Escape rebinding."""
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
from .scumm_toolchain import compile_story_game
from .studio_sequences import append_sequence_step, author_room_walkbox, set_sequence_skippable

COLORS = ((242, 38, 117), (44, 240, 149), (215, 140, 27))
MARKERS = ((191, 61, 220), (42, 195, 243), (45, 130, 210))


def measure_pose(lane):
    """Find one dense native Costume block; ignore sparse same-palette Ego pixels.

    Only pixels in the uniquely identified Costume columns count toward the
    pose verdict. Multiple dense blocks are ambiguous and fail closed.
    """
    columns = [[0] * lane.width for _ in COLORS]
    for i, pixel in enumerate(lane.getdata()):
        for pose, rgb in enumerate(COLORS):
            if all(abs(a-b) <= 7 for a,b in zip(pixel,rgb)):
                columns[pose][i % lane.width] += 1
    density = [sum(values) for values in zip(*columns)]
    blocks = []
    start = None
    for x, count in enumerate((*density, 0)):
        if count >= 24:
            if start is None:
                start = x
        elif start is not None:
            if x-start >= 8 and sum(density[start:x]) >= 100:
                blocks.append((start, x))
            start = None
    if len(blocks) != 1:
        return None, [sum(values) for values in columns]
    left, right = blocks[0]
    return (left+right-1)/2, [sum(values[left:right]) for values in columns]


def run(upstream, destination):
    build = destination / "build"
    room = scrolling_fixture()
    index = len(room.palette)
    controls = tuple(RoomHotspot(name, name, name, x, 120, 16, 16,
                                sprite_pixels=bytes([index+i])*256)
                     for i, (name, x) in enumerate((("Alternative", 210), ("Restore", 250),
                                                    ("CheckStand", 290))))
    room = replace(room, palette=(*room.palette, *MARKERS),
                   hotspots=(*room.hotspots, *controls), demo_walk_to_x=None,
                   camera_cues=(CameraCue("set", x=320),), ego_start_x=320)
    costume = gesture_fixture()
    palette = list(costume.palette)
    for i, color in enumerate(COLORS):
        palette[17+i] = color
    base = costume.frames[0]
    frames = tuple(replace(base, id=name, pixels=bytes([i+1])*(base.width*base.height))
                   for i, name in enumerate(("DefaultStand", "AlternateStand", "Walking")))
    def directions(frame):
        return tuple(CostumeDirection(d, (frame,)) for d in ("N","E","S","W"))
    costume = replace(costume, name="NativeStandBindingCostume", palette=tuple(palette),
                      frames=frames, animations=(
                          CostumeAnimation("walk", directions("Walking")),
                          CostumeAnimation("stand", directions("DefaultStand")),
                          CostumeAnimation("init", directions("DefaultStand")),
                          CostumeAnimation("rest", directions("AlternateStand"), 24)))
    raw = canonical_json(GameDocument("NativeStandBinding", (room, destination_fixture()),
                                      (costume,), (ActorAsset("Guide", costume.name, "Harbor", 280, 85, "S"),)))
    raw = author_room_walkbox(raw, "Harbor", 1, "160,70; 480,70; 480,150; 160,150")
    raw = append_sequence_step(raw, "Harbor", "Alternative", "Close",
                               "Actor Standanimation", "Guide", "rest", None, None)
    for kind, x, y in (("Actor laufen lassen", 440, 85), ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Alternative", "Close", kind,
                                   "Guide", None, None, None, x, y)
    for kind, who, anim, target, amount in (
            ("Objektzustand setzen", None, None, "Restore", 0),
            ("Warten", None, None, None, 12),
            ("Actor Standanimation", "Guide", "stand", None, None)):
        raw = append_sequence_step(raw, "Harbor", "Restore", "Close", kind, who, anim, target, amount)
    raw = set_sequence_skippable(raw, "Harbor|Restore|Close", True)
    for kind, x, y in (("Actor laufen lassen", 280, 85), ("Auf Actor warten", None, None)):
        raw = append_sequence_step(raw, "Harbor", "CheckStand", "Close", kind,
                                   "Guide", None, None, None, x, y)
    build.mkdir(parents=True, exist_ok=True)
    (build / "project.json").write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), build / "resources")
    game_dir = compile_story_game(build, upstream, destination / "game")
    screenshots = destination / "screenshots"
    screenshots.mkdir(exist_ok=True)

    def capture(label):
        xwd = screenshots / f"scummvm-{label}.xwd"
        png = screenshots / f"scummvm-{label}.png"
        subprocess.run(["xwd", "-root", "-silent", "-out", str(xwd)], check=True, timeout=10)
        subprocess.run(["convert", str(xwd), str(png)], check=True, timeout=10)
        xwd.unlink()
        with Image.open(png) as im:
            return im.convert("RGB").crop((192, 184, 832, 472))

    def points(image, rgb):
        return [(i % image.width, i // image.width) for i,pixel in enumerate(image.getdata())
                if all(abs(a-b) <= 7 for a,b in zip(pixel,rgb))]

    def center(pixels):
        if len(pixels)<100:
            return None
        xs,ys=zip(*pixels)
        return (min(xs)+max(xs))/2,(min(ys)+max(ys))/2

    def click(label,color):
        point=center(points(capture(label),color))
        if point is None:
            raise RuntimeError(f"Native interaction target missing: {label}")
        for x,y in ((234,563),(round(point[0]+192),round(point[1]+184))):
            subprocess.run(["xdotool","mousemove",str(x),str(y),"click","1"],check=True,timeout=10)
            time.sleep(.2)

    def await_pose(label,target_x,pose,timeout=25):
        deadline=time.monotonic()+timeout
        samples=[]
        counts=[]
        while time.monotonic()<deadline:
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited during stand binding")
            image=capture(label)
            anchor=center(points(image,MARKERS[0]))
            lane=image.crop((0,96,image.width,181))
            actor_x, counts=measure_pose(lane)
            if anchor is not None and actor_x is not None:
                x=218+(actor_x-anchor[0])/2
                if (abs(x-target_x)<10 and counts[pose]>=100
                        and all(n<40 for i,n in enumerate(counts) if i!=pose)):
                    samples.append({"x":x,"pose":pose,"pixels":counts})
                    if len(samples)==5:
                        return samples
                else:
                    samples=[]
            else:
                samples=[]
            time.sleep(.2)
        raise RuntimeError(f"Native stand pose missing: {label}, counts={counts}")

    with (screenshots / "scummvm.log").open("w",encoding="utf-8") as log:
        game=subprocess.Popen(["scummvm",f"--path={game_dir.resolve()}","tentacle"],
                              stdout=log,stderr=subprocess.STDOUT)
        try:
            initial=await_pose("initial",280,0)
            click("alternative-click",MARKERS[0])
            alternative=await_pose("alternative-arrival",440,1)
            click("restore-click",MARKERS[1])
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if game.poll() is not None:
                    raise RuntimeError("ScummVM exited before stand binding restore")
                if center(points(capture("restore-start"),MARKERS[1])) is None:
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Native restore cutscene did not begin")
            started=time.monotonic()
            subprocess.run(["xdotool","keydown","Escape"],check=True,timeout=5)
            try:
                time.sleep(.25)
            finally:
                subprocess.run(["xdotool","keyup","Escape"],check=True,timeout=5)
            time.sleep(.5)
            # Rebinding is not an animation command. Only the next arrival
            # should use the restored native stand frame.
            if game.poll() is not None:
                raise RuntimeError("ScummVM exited after stand binding Escape")
            click("check-click",MARKERS[2])
            restored=await_pose("restored-arrival",280,0)
            report={"initial":initial,"alternative":alternative,"restored":restored,
                    "escape_to_arrival_seconds":time.monotonic()-started,
                    "native_actor_stand_animation_verified":True}
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
